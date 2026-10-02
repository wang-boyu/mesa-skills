"""Independent offline acceptance of the user-level copy/update contract.

Every subprocess explicitly isolates all three client-home variables. No client
executable, network, personal installation, model environment or Git is needed.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time
from urllib.parse import unquote, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("develop-mesa-model", "document-abm-with-odd", "evaluate-mesa-model")
ROLES = (
    "mesa_model_worker", "independent_model_qa", "mesa_model_reviewer",
    "mesa_model_verifier", "model_spec_analyst", "mesa_geo_specialist",
    "odd_documenter", "odd_auditor", "experiment_designer", "evaluation_analyst",
)
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class Client:
    name: str

    def role_name(self, role):
        if self.name == "codex":
            return role + ".toml"
        return role.replace("_", "-") + ".md"

    def root(self, homes):
        return homes.codex if self.name == "codex" else homes.claude

    def skills(self, homes):
        return homes.home / ".agents" / "skills" if self.name == "codex" else homes.claude / "skills"

    def agents(self, homes):
        return self.root(homes) / "agents"

    def record(self, homes):
        return self.root(homes) / "mesa-skills-install.json"


@pytest.fixture(params=(Client("codex"), Client("claude-code")), ids=lambda x: x.name)
def client(request):
    return request.param


@dataclass
class Homes:
    base: Path
    home: Path
    codex: Path
    claude: Path
    env: dict


@pytest.fixture
def homes(tmp_path, monkeypatch):
    home = tmp_path / "fake home"
    codex = tmp_path / "configured codex"
    claude = tmp_path / "configured claude"
    for path in (home, codex, claude):
        path.mkdir()
    overrides = {"HOME": str(home), "CODEX_HOME": str(codex), "CLAUDE_CONFIG_DIR": str(claude)}
    for name, value in overrides.items():
        monkeypatch.setenv(name, value)
    env = os.environ.copy()
    env.update(overrides)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    for key in overrides:
        assert Path(env[key]).is_relative_to(tmp_path)
    return Homes(tmp_path, home, codex, claude, env)


def write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data, str) else data)
    path.chmod(mode)
    return path


def snapshot(root, *, mtimes=False):
    """Compare bytes/modes/links without dereferencing them or relying on calls."""
    if not root.exists():
        return {}
    result = {}
    for path in (root, *root.rglob("*")):
        info = path.lstat()
        content = (os.readlink(path) if stat.S_ISLNK(info.st_mode) else
                   path.read_bytes() if stat.S_ISREG(info.st_mode) else None)
        result[str(path.relative_to(root))] = (
            info.st_mode, content,
            info.st_mtime_ns if mtimes and stat.S_ISREG(info.st_mode) else None,
        )
    return result


def source(tmp_path, client, *, actual=False, name="source A"):
    product = tmp_path / name
    write(product / "integrations" / "install.py", (ROOT / "integrations" / "install.py").read_bytes())
    for skill in SKILLS:
        target = product / "skills" / skill
        if actual:
            shutil.copytree(ROOT / "skills" / skill, target)
        else:
            write(target / "SKILL.md", f'---\nname: {skill}\nmetadata:\n  version: "0.3.2"\n---\nA\n')
            write(target / "references" / "kept.txt", f"A {skill}\n")
            write(target / "references" / "obsolete.txt", f"old {skill}\n")
            write(target / "scripts" / "tool.py", "print('fixture')\n", 0o751)
    for role in ROLES:
        path = Path("integrations") / client.name / "agents" / client.role_name(role)
        write(product / path, (ROOT / path).read_bytes())
    assert not (product / ".git").exists() and not (product / "internal").exists()
    assert not product.is_relative_to(ROOT)
    return product


def newer(product, client):
    other = product.with_name("source B")
    shutil.copytree(product, other)
    for skill in SKILLS:
        folder = other / "skills" / skill
        write(folder / "references" / "kept.txt", f"B {skill}\n")
        (folder / "references" / "obsolete.txt").unlink()
        write(folder / "assets" / "added.txt", f"new {skill}\n")
        (folder / "scripts" / "tool.py").chmod(0o644)
    role = other / "integrations" / client.name / "agents" / client.role_name("odd_documenter")
    role.write_bytes(role.read_bytes() + b"\nUpdated fixture bytes.\n")
    # Identical version labels must never mask different payload bytes or modes.
    for skill in SKILLS:
        assert (other / "skills" / skill / "SKILL.md").read_bytes() == (product / "skills" / skill / "SKILL.md").read_bytes()
    return other


def command(homes, script, *args, cwd=None):
    for key in ("HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR"):
        assert key in homes.env
        assert (key != "HOME" and homes.env[key] == "") or Path(homes.env[key]).is_relative_to(homes.base)
    return subprocess.run(
        [sys.executable, "-I", "-S", str(script), *map(str, args)],
        env=homes.env, cwd=cwd or homes.base, text=True, capture_output=True,
        check=False, timeout=15,
    )


def install(product, homes, client, *args, cwd=None):
    return command(homes, product / "integrations" / "install.py", "--client", client.name, *args, cwd=cwd)


def success(result):
    assert result.returncode == 0, (result.stdout, result.stderr)


def refused_unchanged(product, homes, client):
    before = snapshot(homes.base)
    result = install(product, homes, client)
    assert result.returncode != 0, result.stdout
    assert result.stderr.strip()
    assert snapshot(homes.base) == before
    return result


def expected_files(product, homes, client):
    expected = {}
    for skill in SKILLS:
        for path in (product / "skills" / skill).rglob("*"):
            if path.is_file():
                expected[client.skills(homes) / path.relative_to(product / "skills")] = path
    for role in ROLES:
        filename = client.role_name(role)
        expected[client.agents(homes) / filename] = product / "integrations" / client.name / "agents" / filename
    return expected


def assert_payload(product, homes, client):
    for target, original in expected_files(product, homes, client).items():
        assert target.is_file() and not target.is_symlink()
        assert target.read_bytes() == original.read_bytes()
        assert stat.S_IMODE(target.stat().st_mode) == (0o755 if original.stat().st_mode & 0o111 else 0o644)


def seed_unrelated(homes):
    for base in (homes.home / ".agents", homes.codex, homes.claude):
        for relative in ("skills/another/SKILL.md", "agents/custom.txt", "config.json"):
            write(base / relative, "user-owned: " + relative, 0o600)


def fault_run(product, homes, client, code, *args):
    harness = "\n".join((
        "import errno, os, pathlib, runpy, sys, time",
        "helper, client, *args = sys.argv[1:]",
        "module = runpy.run_path(helper)",
        "scope = module['main'].__globals__",
        code,
        "raise SystemExit(module['main'](['--client', client]))",
    ))
    return command(homes, "-c", harness, product / "integrations" / "install.py", client.name, *args)


def test_complete_actual_packages_preserve_other_content_and_work_without_source(tmp_path, homes, client):
    product = source(tmp_path, client, actual=True)
    seed_unrelated(homes)
    before = snapshot(homes.base, mtimes=True)
    source_before = snapshot(product, mtimes=True)
    result = install(product, homes, client)
    success(result)
    for path in (client.skills(homes), client.agents(homes)):
        assert str(path) in result.stdout
    for skill in SKILLS:
        assert f"{skill}: Experimental 0.1.0" in result.stdout
    assert "session" in result.stdout.lower()
    assert_payload(product, homes, client)
    assert {p.name for p in client.skills(homes).iterdir()} == set(SKILLS) | {"another"}
    assert {p.name for p in client.agents(homes).iterdir()} == {client.role_name(x) for x in ROLES} | {"custom.txt"}
    after = snapshot(homes.base, mtimes=True)
    for relative, value in before.items():
        if stat.S_ISREG(value[0]):
            assert after[relative] == value
    assert snapshot(product, mtimes=True) == source_before
    unselected = homes.claude if client.name == "codex" else homes.codex
    assert not (unselected / "mesa-skills-install.json").exists()
    if client.name == "codex":
        assert not (homes.codex / "skills").exists() or set((homes.codex / "skills").iterdir()) == {homes.codex / "skills" / "another"}
    # Remove the independent source fixture: installed packages must remain useful.
    shutil.rmtree(product)
    models = [tmp_path / "model one", tmp_path / "model two"]
    for model in models:
        model.mkdir()
        for skill in SKILLS:
            package = client.skills(homes) / skill
            for document in package.rglob("*.md"):
                for raw in LINK.findall(document.read_text()):
                    url = urlsplit(raw.split()[0].strip("<>"))
                    if url.scheme or url.netloc or not url.path:
                        continue
                    target = (document.parent / unquote(url.path)).resolve()
                    assert target.is_relative_to(package) and target.is_file(), (document, raw)
            for script in package.glob("scripts/*.py"):
                if not script.name.startswith("_"):
                    helped = command(homes, script, "--help", cwd=model)
                    success(helped)
                    assert helped.stdout and not helped.stderr
        assert not any((model / name).exists() for name in (".agents", ".codex", ".claude"))
    assert not list(client.skills(homes).rglob("__pycache__"))
    assert not list(client.skills(homes).rglob("*.pyc"))


def test_dry_run_install_update_and_identical_noop_write_nothing(tmp_path, homes, client):
    product = source(tmp_path, client)
    before = snapshot(tmp_path, mtimes=True)
    preview = install(product, homes, client, "--dry-run")
    success(preview)
    assert "dry" in preview.stdout.lower()
    assert snapshot(tmp_path, mtimes=True) == before
    success(install(product, homes, client))
    before = snapshot(tmp_path, mtimes=True)
    again = install(product, homes, client)
    success(again)
    assert "unchanged" in again.stdout.lower()
    assert snapshot(tmp_path, mtimes=True) == before
    updated = newer(product, client)
    before = snapshot(tmp_path, mtimes=True)
    success(install(updated, homes, client, "--dry-run"))
    assert snapshot(tmp_path, mtimes=True) == before


def test_same_version_update_adds_changes_removes_and_preserves_user_extras(tmp_path, homes, client):
    product = source(tmp_path, client)
    seed_unrelated(homes)
    success(install(product, homes, client))
    extras = [write(client.skills(homes) / skill / "references" / "personal.txt", "keep", 0o600) for skill in SKILLS]
    before = {path: (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns) for path in extras}
    updated = newer(product, client)
    result = install(updated, homes, client)
    success(result)
    assert "updat" in result.stdout.lower()
    assert_payload(updated, homes, client)
    for skill in SKILLS:
        assert not (client.skills(homes) / skill / "references" / "obsolete.txt").exists()
    for path, value in before.items():
        assert (path.read_bytes(), path.stat().st_mode, path.stat().st_mtime_ns) == value
    record = json.loads(client.record(homes).read_text())
    assert set(record) == {"format", "client", "roots", "bundles", "files"}
    assert set(record["bundles"]) == set(SKILLS)
    assert record["client"] == client.name
    assert all("personal.txt" not in path and "obsolete.txt" not in path for path in record["files"])
    assert not list(homes.base.rglob(".mesa-skills-recovery-*"))
    assert not list(homes.base.rglob(".mesa-skills-install.lock"))


@pytest.mark.parametrize("change", ["bytes", "mode", "obsolete", "added-unowned"])
def test_local_changes_or_new_destination_conflicts_stop_entire_update(tmp_path, homes, client, change):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    updated = newer(product, client)
    folder = client.skills(homes) / SKILLS[-1]
    if change == "mode":
        conflict = folder / "scripts" / "tool.py"
        conflict.chmod(0o700)
    elif change == "added-unowned":
        conflict = write(folder / "assets" / "added.txt", "my file")
    else:
        conflict = folder / "references" / ("obsolete.txt" if change == "obsolete" else "kept.txt")
        conflict.write_text("my edits")
    result = refused_unchanged(updated, homes, client)
    assert str(conflict) in result.stderr


@pytest.mark.parametrize("kind", ["file", "empty-directory", "matching-package", "symlink", "dangling-symlink"])
@pytest.mark.parametrize("target_kind", ["skill", "role"])
def test_fresh_install_does_not_adopt_or_overwrite_unowned_destinations(tmp_path, homes, client, kind, target_kind):
    product = source(tmp_path, client)
    target = (client.skills(homes) / SKILLS[-1] if target_kind == "skill" else
              client.agents(homes) / client.role_name("odd_documenter"))
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == "file":
        target.write_text("unowned")
    elif kind == "empty-directory":
        target.mkdir()
    elif kind == "matching-package":
        if target_kind == "skill":
            shutil.copytree(product / "skills" / SKILLS[-1], target)
        else:
            shutil.copy2(product / "integrations" / client.name / "agents" / target.name, target)
    else:
        external = tmp_path / "external"
        if kind == "symlink":
            external.mkdir()
            write(external / "keep.txt", "do not touch")
        target.symlink_to(external)
    result = refused_unchanged(product, homes, client)
    assert str(target) in result.stderr


@pytest.mark.parametrize("part", ["skill-root", "agents", "client-root", "package-child", "owned-file", "record"])
def test_destination_symlinks_never_redirect_writes(tmp_path, homes, client, part):
    product = source(tmp_path, client)
    if part in {"package-child", "owned-file", "record"}:
        success(install(product, homes, client))
    target = {
        "skill-root": client.skills(homes), "agents": client.agents(homes),
        "client-root": client.root(homes),
        "package-child": client.skills(homes) / SKILLS[-1] / "references",
        "owned-file": client.skills(homes) / SKILLS[-1] / "SKILL.md",
        "record": client.record(homes),
    }[part]
    external = tmp_path / "external linked target"
    if target.exists():
        target.rename(external)
    elif part in {"skill-root", "agents"}:
        external.mkdir()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(external)
    refused_unchanged(product, homes, client)


def test_missing_owned_files_are_restored_and_absent_obsolete_files_are_accepted(tmp_path, homes, client):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    (client.skills(homes) / SKILLS[0] / "SKILL.md").unlink()
    (client.agents(homes) / client.role_name("odd_documenter")).unlink()
    (client.skills(homes) / SKILLS[-1] / "references" / "obsolete.txt").unlink()
    updated = newer(product, client)
    success(install(updated, homes, client))
    assert_payload(updated, homes, client)


@pytest.mark.parametrize("corruption", ["missing", "invalid-json", "wrong-client", "root-change", "escape", "absolute", "unknown-skill", "unknown-agent", "bad-hash", "bad-mode"])
def test_invalid_or_missing_state_cannot_authorize_or_adopt_writes(tmp_path, homes, client, corruption):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    record_path = client.record(homes)
    record = json.loads(record_path.read_text())
    if corruption == "missing":
        record_path.unlink()
    elif corruption == "invalid-json":
        record_path.write_text("{broken")
    else:
        key = next(iter(record["files"]))
        if corruption == "wrong-client":
            record["client"] = "claude-code" if client.name == "codex" else "codex"
        elif corruption == "root-change":
            record["roots"]["skills"] = str(tmp_path / "elsewhere")
        elif corruption == "bad-hash":
            record["files"][key]["sha256"] = "invalid"
        elif corruption == "bad-mode":
            record["files"][key]["mode"] = 0o777
        else:
            new_key = {"escape": "skills/../outside", "absolute": str(tmp_path / "outside"),
                       "unknown-skill": "skills/unrelated/SKILL.md", "unknown-agent": "agents/custom.txt"}[corruption]
            record["files"][new_key] = record["files"].pop(key)
        record_path.write_text(json.dumps(record))
    refused_unchanged(newer(product, client), homes, client)


def test_changed_configured_root_does_not_transfer_codex_skill_ownership(tmp_path, homes):
    client = Client("codex")
    product = source(tmp_path, client)
    success(install(product, homes, client))
    another = tmp_path / "another codex root"
    another.mkdir()
    homes.env["CODEX_HOME"] = str(another)
    refused_unchanged(product, homes, client)


def test_home_alias_is_resolved_but_codex_home_does_not_move_skill_root(tmp_path, homes, client):
    alias = tmp_path / "home alias"
    alias.symlink_to(homes.home, target_is_directory=True)
    homes.env["HOME"] = str(alias)
    product = source(tmp_path, client)
    success(install(product, homes, client))
    assert_payload(product, homes, client)
    record = json.loads(client.record(homes).read_text())
    assert record["roots"]["skills"] == str(client.skills(homes).resolve())
    if client.name == "codex":
        assert not (homes.codex / "skills").exists()


@pytest.mark.parametrize("source_kind", ["skill", "role"])
@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "dangling-symlink", "fifo"])
def test_incomplete_or_nonregular_sources_refuse_before_any_install(tmp_path, homes, client, source_kind, kind):
    product = source(tmp_path, client)
    target = (product / "skills" / SKILLS[-1] / "SKILL.md" if source_kind == "skill" else
              product / "integrations" / client.name / "agents" / client.role_name("odd_documenter"))
    data = target.read_bytes()
    target.unlink()
    if kind == "directory":
        target.mkdir()
    elif "symlink" in kind:
        external = tmp_path / "external-source"
        if kind == "symlink":
            external.write_bytes(data)
        target.symlink_to(external)
    elif kind == "fifo":
        os.mkfifo(target)
    refused_unchanged(product, homes, client)


@pytest.mark.parametrize("relative", ["__pycache__/cached.pyc", ".pytest_cache/v/nodeids", ".git/config", "internal/private.md", "scripts/cache.pyo"])
def test_generated_or_private_package_content_is_not_installed(tmp_path, homes, client, relative):
    product = source(tmp_path, client)
    write(product / "skills" / SKILLS[-1] / relative, "not product")
    refused_unchanged(product, homes, client)


def test_source_directory_symlink_and_read_failure_do_not_omit_payload(tmp_path, homes, client):
    product = source(tmp_path, client)
    folder = product / "skills" / SKILLS[-1] / "references"
    code = "\n".join((
        "original = os.scandir",
        "def broken(path):",
        "    if os.fspath(path) == args[0]:",
        "        raise PermissionError(errno.EACCES, 'injected unreadable source', path)",
        "    return original(path)",
        "os.scandir = broken",
    ))
    before = snapshot(tmp_path)
    result = fault_run(product, homes, client, code, folder)
    assert result.returncode != 0 and "injected unreadable source" in result.stderr
    assert snapshot(tmp_path) == before
    external = tmp_path / "external references"
    folder.rename(external)
    folder.symlink_to(external)
    refused_unchanged(product, homes, client)


@pytest.mark.parametrize("phase", ["payload", "record"])
def test_ordinary_write_failure_restores_previous_bundle_and_state(tmp_path, homes, client, phase):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    updated = newer(product, client)
    before = snapshot(tmp_path)
    target = (client.record(homes) if phase == "record" else
              client.skills(homes) / SKILLS[-1] / "references" / "kept.txt")
    code = "\n".join((
        "original = scope['replace_file']",
        "failed = False",
        "def broken(source, target):",
        "    global failed",
        "    if str(target) == args[0] and not failed:",
        "        failed = True",
        "        raise OSError(errno.ENOSPC, 'injected write failure', str(target))",
        "    return original(source, target)",
        "scope['replace_file'] = broken",
    ))
    result = fault_run(updated, homes, client, code, target)
    assert result.returncode != 0 and "injected write failure" in result.stderr
    assert snapshot(tmp_path) == before
    assert_payload(product, homes, client)


def test_failed_restoration_keeps_old_copies_and_explicit_recovery_outside_discovery(tmp_path, homes, client):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    record_before = client.record(homes).read_bytes()
    updated = newer(product, client)
    old_file = client.skills(homes) / SKILLS[-1] / "references" / "kept.txt"
    old_bytes = old_file.read_bytes()
    code = "\n".join((
        "original = scope['replace_file']",
        "restoring = False",
        "def broken(source, target):",
        "    global restoring",
        "    if str(target) == args[0]:",
        "        restoring = True",
        "        raise OSError(errno.ENOSPC, 'injected record failure', str(target))",
        "    if restoring and str(target) == args[1]:",
        "        raise OSError(errno.EACCES, 'injected restoration failure', str(target))",
        "    return original(source, target)",
        "scope['replace_file'] = broken",
    ))
    result = fault_run(updated, homes, client, code, client.record(homes), old_file)
    assert result.returncode != 0
    assert "recovery" in result.stderr.lower() and "injected restoration failure" in result.stderr
    assert client.record(homes).read_bytes() == record_before
    recoveries = list(homes.base.rglob(".mesa-skills-recovery-*"))
    assert recoveries
    for recovery in recoveries:
        assert not recovery.is_relative_to(client.skills(homes))
        assert not recovery.is_relative_to(client.agents(homes))
        assert str(recovery) in result.stderr
    assert any(path.is_file() and path.read_bytes() == old_bytes for root in recoveries for path in root.rglob("*"))
    # Another attempt must not overwrite the preserved recovery or stale baseline.
    refused_unchanged(updated, homes, client)


def test_overlapping_installer_refuses_then_first_finishes(tmp_path, homes, client):
    product = source(tmp_path, client)
    entered, release = tmp_path / "entered", tmp_path / "release"
    harness = "\n".join((
        "import pathlib, runpy, sys, time",
        "helper, client, entered, release = sys.argv[1:]",
        "module = runpy.run_path(helper)",
        "scope = module['main'].__globals__",
        "original = scope['replace_file']",
        "first = True",
        "def pause(source, target):",
        "    global first",
        "    if first:",
        "        first = False",
        "        pathlib.Path(entered).write_text('ready')",
        "        deadline = time.monotonic() + 10",
        "        while not pathlib.Path(release).exists():",
        "            if time.monotonic() > deadline: raise RuntimeError('test barrier timed out')",
        "            time.sleep(0.01)",
        "    return original(source, target)",
        "scope['replace_file'] = pause",
        "raise SystemExit(module['main'](['--client', client]))",
    ))
    process = subprocess.Popen(
        [sys.executable, "-I", "-S", "-c", harness, str(product / "integrations" / "install.py"), client.name, str(entered), str(release)],
        env=homes.env, cwd=tmp_path, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 10
        while not entered.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert entered.exists(), process.communicate(timeout=1)
        before = snapshot(tmp_path)
        result = install(product, homes, client)
        assert result.returncode != 0
        assert any(word in result.stderr.lower() for word in ("lock", "overlap", "running"))
        assert snapshot(tmp_path) == before
        if client.name == "codex":
            alternate = tmp_path / "other configured codex"
            alternate.mkdir()
            homes.env["CODEX_HOME"] = str(alternate)
            before = snapshot(tmp_path)
            alternate_result = install(product, homes, client)
            assert alternate_result.returncode != 0
            assert str(homes.home / ".agents" / ".mesa-skills-install.lock") in alternate_result.stderr
            assert snapshot(tmp_path) == before
            homes.env["CODEX_HOME"] = str(homes.codex)
    finally:
        release.write_text("continue")
        stdout, stderr = process.communicate(timeout=15)
    assert process.returncode == 0, (stdout, stderr)
    assert_payload(product, homes, client)


def test_unselected_client_is_not_inspected(tmp_path, homes, client):
    product = source(tmp_path, client)
    forbidden = homes.claude if client.name == "codex" else homes.codex
    # Fault at OS entry points: even metadata/traversal of the other root fails.
    code = "\n".join((
        "def no_home_fallback(cls):",
        "    raise AssertionError('real-home fallback attempted')",
        "pathlib.Path.home = classmethod(no_home_fallback)",
        "blocked = args[0]",
        "def guarded(original):",
        "    def call(path, *rest, **kwargs):",
        "        value = os.fspath(path) if not isinstance(path, int) else ''",
        "        if isinstance(value, str) and (value == blocked or value.startswith(blocked + os.sep)):",
        "            raise AssertionError('unselected client was inspected: ' + value)",
        "        return original(path, *rest, **kwargs)",
        "    return call",
        "for name in ('stat', 'lstat', 'scandir', 'listdir', 'open'):",
        "    setattr(os, name, guarded(getattr(os, name)))",
    ))
    result = fault_run(product, homes, client, code, forbidden)
    success(result)
    assert_payload(product, homes, client)


@pytest.mark.parametrize("flag", ["--project", "--scope", "--skill", "--force", "--uninstall", "--check"])
def test_retired_or_dangerous_alternate_modes_are_not_accepted(tmp_path, homes, client, flag):
    product = source(tmp_path, client)
    before = snapshot(tmp_path)
    result = install(product, homes, client, flag)
    assert result.returncode != 0
    assert snapshot(tmp_path) == before


def test_default_client_roots_stay_under_explicit_fake_home(tmp_path, homes, client):
    # Explicit empty client overrides exercise documented defaults, while HOME
    # stays explicitly isolated and both variables are still supplied to the child.
    homes.env["CODEX_HOME"] = ""
    homes.env["CLAUDE_CONFIG_DIR"] = ""
    homes.codex = homes.home / ".codex"
    homes.claude = homes.home / ".claude"
    product = source(tmp_path, client)
    success(install(product, homes, client))
    assert_payload(product, homes, client)
    assert client.record(homes).is_file()
    unselected = homes.claude if client.name == "codex" else homes.codex
    assert not unselected.exists()


@pytest.mark.parametrize("already_installed", [False, True])
def test_partial_staging_failure_leaves_existing_files_untouched(tmp_path, homes, client, already_installed):
    product = source(tmp_path, client)
    if already_installed:
        success(install(product, homes, client))
        product = newer(product, client)
    before = snapshot(tmp_path)
    code = "\n".join((
        "original = scope['write_copy']",
        "count = 0",
        "def broken(path, value):",
        "    global count",
        "    count += 1",
        "    if count == 3:",
        "        path.write_bytes(b'partial staged bytes')",
        "        raise OSError(errno.ENOSPC, 'injected staging failure', str(path))",
        "    return original(path, value)",
        "scope['write_copy'] = broken",
    ))
    result = fault_run(product, homes, client, code)
    assert result.returncode != 0 and "injected staging failure" in result.stderr
    assert snapshot(tmp_path) == before


def test_obsolete_file_removal_failure_restores_applied_updates(tmp_path, homes, client):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    updated = newer(product, client)
    before = snapshot(tmp_path)
    target = client.skills(homes) / SKILLS[-1] / "references" / "obsolete.txt"
    code = "\n".join((
        "original = pathlib.Path.unlink",
        "def broken(path, *rest, **kwargs):",
        "    if str(path) == args[0]:",
        "        raise PermissionError(errno.EACCES, 'injected removal failure', str(path))",
        "    return original(path, *rest, **kwargs)",
        "pathlib.Path.unlink = broken",
    ))
    result = fault_run(updated, homes, client, code, target)
    assert result.returncode != 0 and "injected removal failure" in result.stderr
    assert snapshot(tmp_path) == before
    assert_payload(product, homes, client)


def test_managed_parent_file_obstruction_refuses_before_changes(tmp_path, homes, client):
    product = source(tmp_path, client)
    target = client.agents(homes)
    write(target, "unrelated obstructing file", 0o600)
    result = refused_unchanged(product, homes, client)
    assert str(target) in result.stderr


@pytest.mark.parametrize("cleanup_kind", ["recovery-directory", "lock-directory"])
@pytest.mark.parametrize("apply_outcome", ["committed", "restored"])
def test_cleanup_failure_reports_coherent_bundle_and_only_cleanup_actions(
    tmp_path, homes, client, cleanup_kind, apply_outcome,
):
    product = source(tmp_path, client)
    success(install(product, homes, client))
    baseline_record = client.record(homes).read_bytes()
    updated = newer(product, client)
    # Codex has two staging anchors: failure on the second removal establishes
    # that some backups have already disappeared. Claude has one shared anchor.
    removal_number = 2 if client.name == "codex" else 1
    code = "\n".join((
        "shutil = scope['shutil']",
        "original_rmtree = shutil.rmtree",
        "original_rmdir = pathlib.Path.rmdir",
        "removals = 0",
        "lock_failed = False",
        "def broken_rmtree(path, *rest, **kwargs):",
        "    global removals",
        "    if pathlib.Path(path).name.startswith('.mesa-skills-recovery-'):",
        "        removals += 1",
        "        if args[0] == 'recovery-directory' and removals == int(args[2]):",
        "            raise PermissionError(errno.EACCES, 'injected recovery cleanup failure', str(path))",
        "    return original_rmtree(path, *rest, **kwargs)",
        "def broken_rmdir(path, *rest, **kwargs):",
        "    global lock_failed",
        "    if args[0] == 'lock-directory' and path.name == '.mesa-skills-install.lock' and not lock_failed:",
        "        lock_failed = True",
        "        raise PermissionError(errno.EACCES, 'injected lock cleanup failure', str(path))",
        "    return original_rmdir(path, *rest, **kwargs)",
        "shutil.rmtree = broken_rmtree",
        "pathlib.Path.rmdir = broken_rmdir",
        "original_replace = scope['replace_file']",
        "apply_failed = False",
        "def broken_replace(source, target):",
        "    global apply_failed",
        "    if args[1] == 'restored' and str(target) == args[3] and not apply_failed:",
        "        apply_failed = True",
        "        raise OSError(errno.ENOSPC, 'injected apply failure before cleanup', str(target))",
        "    return original_replace(source, target)",
        "scope['replace_file'] = broken_replace",
    ))
    result = fault_run(updated, homes, client, code, cleanup_kind, apply_outcome, removal_number, client.record(homes))
    assert result.returncode != 0
    assert "cleanup" in result.stderr.lower()
    expected_product = updated if apply_outcome == "committed" else product
    assert_payload(expected_product, homes, client)
    record = json.loads(client.record(homes).read_text())
    if apply_outcome == "restored":
        assert client.record(homes).read_bytes() == baseline_record
    else:
        assert client.record(homes).read_bytes() != baseline_record
        assert all("obsolete.txt" not in name for name in record["files"])
        assert not any((client.skills(homes) / skill / "references" / "obsolete.txt").exists() for skill in SKILLS)
    # The outcome must be stated separately from cleanup failure. Neither a
    # committed bundle nor a fully restored bundle needs partial backup replay.
    assert apply_outcome in result.stderr.lower()
    remnants = list(homes.base.rglob(".mesa-skills-recovery-*")) + list(homes.base.rglob(".mesa-skills-install.lock"))
    assert remnants
    for remnant in remnants:
        assert str(remnant) in result.stderr
        assert not remnant.is_relative_to(client.skills(homes))
        assert not remnant.is_relative_to(client.agents(homes))
    recovery_documents = [path for remnant in remnants for path in remnant.rglob("*.txt")]
    assert recovery_documents
    for path in recovery_documents:
        instructions = path.read_text().lower()
        assert "cleanup" in instructions and "do not restore" in instructions
        assert " <- " not in instructions
    # A retry must preserve coherent state and unfinished cleanup for inspection.
    refused_unchanged(updated, homes, client)


def assert_interruption_recovery(homes, client, before, managed, result):
    """Check human recovery directions against the independently captured baseline."""
    recoveries = list(homes.base.rglob(".mesa-skills-recovery-*"))
    locks = list(homes.base.rglob(".mesa-skills-install.lock"))
    assert recoveries and locks, "incomplete state lost its recovery copies or blocking locks"
    documents = [path / "RECOVERY.txt" for path in recoveries]
    assert all(path.is_file() for path in documents)
    mappings = {}
    for document in documents:
        instructions = document.read_text()
        assert "cleanup only" not in instructions.lower()
        assert "do not restore" not in instructions.lower()
        assert "installed files were not changed" not in instructions.lower()
        for line in instructions.splitlines():
            if " <- " not in line:
                continue
            target_text, backup_text = line.split(" <- ", 1)
            target = Path(target_text)
            backup = None if backup_text == "ABSENT" else Path(backup_text)
            assert target in managed, target
            baseline = before.get(str(target.relative_to(homes.base)))
            if baseline is None:
                assert backup is None, (target, backup)
            else:
                assert backup is not None and backup.is_file(), (target, backup)
                assert any(backup.is_relative_to(root) for root in recoveries)
                assert backup.read_bytes() == baseline[1]
                assert stat.S_IMODE(backup.stat().st_mode) == stat.S_IMODE(baseline[0])
            assert target not in mappings or mappings[target] == backup
            mappings[target] = backup
    assert mappings
    after = snapshot(homes.base)
    for target in managed:
        relative = str(target.relative_to(homes.base))
        if before.get(relative) != after.get(relative):
            assert target in mappings, f"changed target lacks recovery instructions: {target}"
    for path in (*recoveries, *locks):
        assert not path.is_relative_to(client.skills(homes))
        assert not path.is_relative_to(client.agents(homes))
        assert str(path) in result.stderr, f"diagnostic omitted retained path: {path}"
    assert "recovery" in result.stderr.lower()
    assert "cleanup only" not in result.stderr.lower()
    assert "installed files were not changed" not in result.stderr.lower()
    return mappings, recoveries, locks


def assert_unrelated_files_preserved(homes, before, managed):
    after = snapshot(homes.base)
    selected = {str(path.relative_to(homes.base)) for path in managed}
    for relative, value in before.items():
        if stat.S_ISREG(value[0]) and relative not in selected:
            assert after[relative] == value


@pytest.mark.parametrize("already_installed", [False, True], ids=["first-install", "update"])
def test_sigint_after_completed_replacement_restores_or_preserves_recovery(tmp_path, homes, client, already_installed):
    product = source(tmp_path, client)
    seed_unrelated(homes)
    if already_installed:
        success(install(product, homes, client))
        candidate = newer(product, client)
    else:
        candidate = product
    managed = set(expected_files(product, homes, client)) | set(expected_files(candidate, homes, client)) | {client.record(homes)}
    before = snapshot(tmp_path)
    code = "\n".join((
        "import signal",
        "signal.signal(signal.SIGINT, signal.default_int_handler)",
        "original = scope['replace_file']",
        "interrupted = False",
        "def interrupt_after_write(source, target):",
        "    global interrupted",
        "    original(source, target)",
        "    if not interrupted:",
        "        interrupted = True",
        "        print('SIGINT after completed replacement: ' + str(target), flush=True)",
        "        signal.raise_signal(signal.SIGINT)",
        "scope['replace_file'] = interrupt_after_write",
    ))
    result = fault_run(candidate, homes, client, code)
    assert result.returncode != 0
    assert "SIGINT after completed replacement:" in result.stdout
    assert_unrelated_files_preserved(homes, before, managed)
    if snapshot(tmp_path) == before:
        # Successful restoration leaves the original baseline usable immediately.
        success(install(candidate, homes, client))
        assert_payload(candidate, homes, client)
    else:
        assert_interruption_recovery(homes, client, before, managed, result)
        refused_unchanged(candidate, homes, client)


@pytest.mark.parametrize("initial_failure, restoration_failure", [
    ("sigint", "sigint"), ("sigint", "oserror"), ("oserror", "sigint"),
    ("oserror", "sigint-after-write"),
])
def test_interrupted_restoration_retains_usable_backups_mapping_and_locks(
    tmp_path, homes, client, initial_failure, restoration_failure,
):
    product = source(tmp_path, client)
    seed_unrelated(homes)
    success(install(product, homes, client))
    candidate = newer(product, client)
    managed = set(expected_files(product, homes, client)) | set(expected_files(candidate, homes, client)) | {client.record(homes)}
    before = snapshot(tmp_path)
    code = "\n".join((
        "import signal",
        "signal.signal(signal.SIGINT, signal.default_int_handler)",
        "original = scope['replace_file']",
        "applying = True",
        "restore_failed = False",
        "def interrupted_replace(source, target):",
        "    global applying, restore_failed",
        "    if applying:",
        "        original(source, target)",
        "        applying = False",
        "        print('completed replacement before initial failure', flush=True)",
        "        if args[0] == 'sigint': signal.raise_signal(signal.SIGINT)",
        "        raise OSError(errno.ENOSPC, 'injected apply failure', str(target))",
        "    if not restore_failed:",
        "        restore_failed = True",
        "        print('interrupted restoration attempt', flush=True)",
        "        if args[1] == 'sigint-after-write':",
        "            original(source, target)",
        "            signal.raise_signal(signal.SIGINT)",
        "        if args[1] == 'sigint': signal.raise_signal(signal.SIGINT)",
        "        raise OSError(errno.EACCES, 'injected restoration failure', str(target))",
        "    return original(source, target)",
        "scope['replace_file'] = interrupted_replace",
    ))
    result = fault_run(candidate, homes, client, code, initial_failure, restoration_failure)
    assert result.returncode != 0
    assert "completed replacement before initial failure" in result.stdout
    assert_unrelated_files_preserved(homes, before, managed)
    mappings, recoveries, locks = assert_interruption_recovery(homes, client, before, managed, result)
    assert "interrupted restoration attempt" in result.stdout
    refused_unchanged(candidate, homes, client)
    # Follow only the reported mappings in this fake home to prove that retained
    # copies can actually recover the prior installation, including its record.
    for target, backup in mappings.items():
        if backup is None:
            if target.exists():
                target.unlink()
        else:
            shutil.copy2(backup, target)
    for target in managed:
        relative = str(target.relative_to(homes.base))
        assert snapshot(homes.base).get(relative) == before.get(relative)
    for directory in (*recoveries, *locks):
        shutil.rmtree(directory)
    success(install(candidate, homes, client))
    assert_payload(candidate, homes, client)
    assert_unrelated_files_preserved(homes, before, managed)


def test_unexpected_exception_after_replacement_cannot_discard_recovery(tmp_path, homes, client):
    product = source(tmp_path, client)
    seed_unrelated(homes)
    success(install(product, homes, client))
    candidate = newer(product, client)
    managed = set(expected_files(product, homes, client)) | set(expected_files(candidate, homes, client)) | {client.record(homes)}
    before = snapshot(tmp_path)
    code = "\n".join((
        "original = scope['replace_file']",
        "failed = False",
        "def unexpected(source, target):",
        "    global failed",
        "    original(source, target)",
        "    if not failed:",
        "        failed = True",
        "        raise RuntimeError('injected unexpected error after replacement')",
        "scope['replace_file'] = unexpected",
    ))
    result = fault_run(candidate, homes, client, code)
    assert result.returncode != 0
    assert "injected unexpected error after replacement" in result.stderr
    assert_unrelated_files_preserved(homes, before, managed)
    if snapshot(tmp_path) == before:
        success(install(candidate, homes, client))
        assert_payload(candidate, homes, client)
    else:
        assert_interruption_recovery(homes, client, before, managed, result)
        refused_unchanged(candidate, homes, client)
