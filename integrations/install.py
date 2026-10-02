#!/usr/bin/env python3
"""Install or safely update all Mesa skills and one client's native roles."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("develop-mesa-model", "document-abm-with-odd", "evaluate-mesa-model")
ROLES = (
    "mesa_model_worker", "independent_model_qa", "mesa_model_reviewer",
    "mesa_model_verifier", "model_spec_analyst", "mesa_geo_specialist",
    "odd_documenter", "odd_auditor", "experiment_designer", "evaluation_analyst",
)
CLIENTS = ("codex", "claude-code")
RECORD = "mesa-skills-install.json"
LOCK = ".mesa-skills-install.lock"
FORBIDDEN = {"__pycache__", ".pytest_cache", ".git", "internal"}


@dataclass
class Plan:
    client: str
    roots: dict[str, Path]
    payload: dict[str, tuple[bytes, int]]
    previous: dict[str, tuple[bytes, int]]
    record: dict
    old_record: bytes | None
    changes: list[str]
    removals: list[str]
    unchanged: bool

    def destination(self, key: str) -> Path:
        category, relative = key.split("/", 1)
        return self.roots[category] / relative

    @property
    def state(self) -> Path:
        return self.roots["state"] / RECORD

    @property
    def anchors(self) -> list[Path]:
        return sorted({self.roots["skills"].parent, self.roots["state"]})


def directory_chain(path: Path) -> None:
    """Inspect ancestors, never traversing an arbitrary destination symlink."""
    for item in reversed((path, *path.parents)):
        if os.path.lexists(item) and not stat.S_ISDIR(item.lstat().st_mode):
            raise ValueError(f"not a real directory (or symlink): {item}")


def roots_for(client: str) -> dict[str, Path]:
    raw_home = Path(os.environ.get("HOME") or str(Path.home())).absolute()
    home = raw_home.resolve(strict=True)  # OS/user home aliases are legitimate.
    if not home.is_dir():
        raise ValueError(f"HOME is not a directory: {home}")
    variable, default = ("CODEX_HOME", ".codex") if client == "codex" else ("CLAUDE_CONFIG_DIR", ".claude")
    configured = os.environ.get(variable)
    state = Path(configured) if configured else home / default
    if not state.is_absolute():
        raise ValueError(f"{variable} must be an absolute directory: {state}")
    # Map a HOME alias prefix without accepting symlinks below that root.
    if state.is_relative_to(raw_home):
        state = home / state.relative_to(raw_home)
    state = Path(os.path.abspath(state))
    skills = home / ".agents" / "skills" if client == "codex" else state / "skills"
    roots = {"skills": skills, "agents": state / "agents", "state": state}
    if state.is_relative_to(skills) or roots["agents"].is_relative_to(skills) or skills.is_relative_to(roots["agents"]):
        raise ValueError("client home and recovery paths must be outside skill/agent discovery directories")
    for root in roots.values():
        directory_chain(root)
    return roots


def role_names(client: str) -> set[str]:
    return {role + ".toml" if client == "codex" else role.replace("_", "-") + ".md" for role in ROLES}


def valid_key(key: str, client: str) -> bool:
    if not isinstance(key, str) or "\\" in key or "\x00" in key:
        return False
    parts = key.split("/")
    if any(part in {"", ".", ".."} | FORBIDDEN for part in parts):
        return False
    if PurePosixPath(key).suffix in {".pyc", ".pyo"}:
        return False
    return ((len(parts) >= 3 and parts[0] == "skills" and parts[1] in SKILLS)
            or (len(parts) == 2 and parts[0] == "agents" and parts[1] in role_names(client)))


def read_regular(path: Path) -> tuple[bytes, int]:
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError(f"not a regular file (or symlink): {path}")
    return path.read_bytes(), stat.S_IMODE(mode)


def fingerprint(value: tuple[bytes, int]) -> dict:
    data, mode = value
    return {"sha256": hashlib.sha256(data).hexdigest(), "mode": mode}


def traversal_error(error: OSError) -> None:
    raise error


def source_payload(client: str) -> tuple[dict[str, tuple[bytes, int]], dict[str, str]]:
    payload = {}
    labels = {}
    for name in SKILLS:
        package = ROOT / "skills" / name
        directory_chain(package)
        if not package.is_dir():
            raise ValueError(f"missing skill package: {package}")
        for folder, dirs, files in os.walk(package, followlinks=False, onerror=traversal_error):
            for child in dirs:
                directory_chain(Path(folder) / child)
                if child in FORBIDDEN:
                    raise ValueError(f"generated/private source directory: {Path(folder) / child}")
            for child in sorted(files):
                path = Path(folder) / child
                key = "skills/" + name + "/" + path.relative_to(package).as_posix()
                if not valid_key(key, client):
                    raise ValueError(f"unexpected source path: {path}")
                data, mode = read_regular(path)
                payload[key] = (data, 0o755 if mode & 0o111 else 0o644)
        skill_key = f"skills/{name}/SKILL.md"
        if skill_key not in payload:
            raise ValueError(f"missing complete skill package: {package / 'SKILL.md'}")
        text = payload[skill_key][0].decode("utf-8")
        frontmatter = text.split("---", 2)[1] if text.startswith("---\n") else ""
        version = re.search(r'^\s+version:\s*[\"\']?([^\s\"\']+)', frontmatter, re.MULTILINE)
        labels[name] = version.group(1) if version else "unspecified"
        # Shipped Markdown's local links must stay within its complete package.
        for key, (data, _) in list(payload.items()):
            if not key.startswith(f"skills/{name}/") or not key.endswith(".md"):
                continue
            for link in re.findall(r"\]\(([^\s)]+)\)", data.decode("utf-8")):
                parsed = urlsplit(link.strip("<>"))
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = Path(os.path.normpath(str(ROOT / key / ".." / unquote(parsed.path))))
                if not target.is_relative_to(package) or not target.exists():
                    raise ValueError(f"missing or escaping local resource: {ROOT / key}: {link}")
    source_agents = ROOT / "integrations" / client / "agents"
    directory_chain(source_agents)
    for name in sorted(role_names(client)):
        data, mode = read_regular(source_agents / name)
        payload["agents/" + name] = (data, 0o755 if mode & 0o111 else 0o644)
    return payload, labels


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate installation-record key: {key}")
        result[key] = value
    return result


def load_record(path: Path, client: str, roots: dict[str, Path]) -> tuple[dict | None, bytes | None]:
    if not os.path.lexists(path):
        return None, None
    raw, _ = read_regular(path)
    try:
        record = json.loads(raw, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError) as error:
        raise ValueError(f"invalid installation record {path}: {error}") from error
    if not isinstance(record, dict) or set(record) != {"format", "client", "roots", "bundles", "files"}:
        raise ValueError(f"invalid installation record structure: {path}")
    if type(record["format"]) is not int or record["format"] != 1 or record["client"] != client:
        raise ValueError(f"installation record format/client mismatch: {path}")
    if record["roots"] != {key: str(value) for key, value in roots.items()}:
        raise ValueError(f"installation record root identity mismatch: {path}; configured roots cannot transfer ownership")
    if not isinstance(record["bundles"], dict) or set(record["bundles"]) != set(SKILLS) or not all(isinstance(v, str) for v in record["bundles"].values()):
        raise ValueError(f"invalid bundle labels in installation record: {path}")
    files = record["files"]
    if not isinstance(files, dict):
        raise ValueError(f"invalid file baseline in installation record: {path}")
    required = {f"skills/{name}/SKILL.md" for name in SKILLS} | {"agents/" + name for name in role_names(client)}
    if not required.issubset(files):
        raise ValueError(f"incomplete installation record: {path}")
    for key, item in files.items():
        if (not valid_key(key, client) or not isinstance(item, dict) or set(item) != {"sha256", "mode"}
                or not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                or type(item["mode"]) is not int or item["mode"] not in {0o644, 0o755}):
            raise ValueError(f"invalid or escaping installation record path/baseline: {key!r} in {path}")
    return record, raw


def prepare(client: str, *, _owned_locks: list[Path] | None = None) -> Plan:
    roots = roots_for(client)
    payload, labels = source_payload(client)
    state = roots["state"] / RECORD
    old, raw = load_record(state, client, roots)
    plan = Plan(client, roots, payload, {}, {}, raw, [], [], False)
    conflicts = []
    for anchor in plan.anchors:
        if anchor / LOCK not in (_owned_locks or []) and os.path.lexists(anchor / LOCK):
            conflicts.append(f"installation lock exists: {anchor / LOCK}; another installer or retained recovery requires attention")
    if old is None:
        for name in SKILLS:
            destination = roots["skills"] / name
            if os.path.lexists(destination):
                conflicts.append(f"unowned skill destination already exists: {destination}")
    baseline = old["files"] if old else {}
    for key in sorted(set(payload) | set(baseline)):
        target = plan.destination(key)
        try:
            directory_chain(target.parent)
            if os.path.lexists(target):
                if key not in baseline:
                    conflicts.append(f"unowned destination already exists: {target}")
                    continue
                value = read_regular(target)
                if fingerprint(value) != baseline[key]:
                    conflicts.append(f"locally modified installed file: {target}")
                    continue
                plan.previous[key] = value
        except (OSError, ValueError) as error:
            conflicts.append(str(error))
    if conflicts:
        raise ValueError("\n".join(dict.fromkeys(conflicts)) + "\nNothing changed. Preserve and inspect conflicting paths, then manually reconcile known copies or restore the prior baseline; do not delete state to bypass ownership checks.")
    plan.changes = sorted(key for key, value in payload.items() if plan.previous.get(key) != value)
    plan.removals = sorted(key for key in baseline if key not in payload and key in plan.previous)
    plan.record = {"format": 1, "client": client, "roots": {key: str(value) for key, value in roots.items()},
                   "bundles": labels, "files": {key: fingerprint(value) for key, value in sorted(payload.items())}}
    plan.unchanged = not plan.changes and not plan.removals and plan.record == old
    return plan


def make_directories(path: Path, created: list[Path]) -> None:
    directory_chain(path)
    missing = []
    cursor = path
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    for item in reversed(missing):
        item.mkdir()
        created.append(item)


def write_copy(path: Path, value: tuple[bytes, int]) -> None:
    data, mode = value
    with path.open("xb") as stream:
        stream.write(data)
    path.chmod(mode)


def replace_file(source: Path, target: Path) -> None:
    """Each staged copy and its target must be on the same filesystem."""
    os.replace(source, target)


def apply(initial: Plan) -> Plan:
    created: list[Path] = []
    locks: list[Path] = []
    recovery: dict[Path, Path] = {}
    operations: list[tuple[Path, Path | None, Path | None]] = []
    attempted: list[tuple[Path, Path | None]] = []
    retain = False
    outcome = "Installed files were not changed."
    failure_message = ""
    try:
        for anchor in initial.anchors:
            make_directories(anchor, created)
            lock = anchor / LOCK
            try:
                lock.mkdir()
            except FileExistsError as error:
                raise ValueError(f"installation lock exists: {lock}; do not run overlapping installers") from error
            locks.append(lock)
        # Recheck the complete selection while holding our exact locks.
        plan = prepare(initial.client, _owned_locks=locks)
        if plan.unchanged:
            outcome = "Installation unchanged; installed files and record are consistent."
            return plan
        for anchor in plan.anchors:
            recovery[anchor] = Path(tempfile.mkdtemp(prefix=".mesa-skills-recovery-", dir=anchor))
        for index, key in enumerate(plan.changes + plan.removals):
            target = plan.destination(key)
            anchor = plan.roots["skills"].parent if key.startswith("skills/") else plan.roots["state"]
            directory = recovery[anchor]
            backup = directory / f"{index}.previous" if key in plan.previous else None
            staged = directory / f"{index}.new" if key in plan.payload else None
            if backup:
                write_copy(backup, plan.previous[key])
            if staged:
                write_copy(staged, plan.payload[key])
            operations.append((target, backup, staged))
        state_directory = recovery[plan.roots["state"]]
        backup = state_directory / "record.previous" if plan.old_record is not None else None
        if backup:
            write_copy(backup, (plan.old_record, 0o600))
        staged = state_directory / "record.new"
        write_copy(staged, ((json.dumps(plan.record, indent=2, sort_keys=True) + "\n").encode(), 0o600))
        operations.append((plan.state, backup, staged))  # Publish baseline last.
        instructions = "Previous copies for this interrupted installation are listed below. Restore them to their exact targets (remove a target only when its previous value is ABSENT), inspect the entire bundle, then remove the listed locks after ensuring no installer is running. Do not rerun while recovery is unresolved.\n"
        instructions += "\n".join(f"{target} <- {backup or 'ABSENT'}" for target, backup, _ in operations)
        instructions += "\nLocks: " + ", ".join(map(str, locks)) + "\n"
        # Persist complete mappings before mutation so an interrupted rollback
        # can leave useful recovery without having to finish writing a report.
        for directory in recovery.values():
            (directory / "RECOVERY.txt").write_text(instructions, encoding="utf-8")
        # Stage everything before touching an installed file. Ancestor creation is
        # tracked so an unsuccessful first install can remove its empty folders.
        for target, _, staged in operations:
            make_directories(target.parent, created)
            if staged and target.parent.stat().st_dev != staged.stat().st_dev:
                raise ValueError(f"cannot stage outside discovery on target filesystem: {target}")
        # An unknown outcome must retain recovery by default. Only a confirmed
        # commit or complete restoration below permits cleanup again.
        retain = True
        for target, backup, staged in operations:
            directory_chain(target.parent)
            attempted.append((target, backup))
            if staged:
                replace_file(staged, target)
            else:
                target.unlink()
        outcome = "Installation complete (committed); new installed files and record are consistent."
        retain = False
        return plan
    except (OSError, ValueError, KeyboardInterrupt) as error:
        # Keep recovery protected throughout restoration, including a second
        # cancellation or an unexpected exception in a restoration operation.
        retain = True
        error_detail = str(error) or type(error).__name__
        failures = []
        for target, backup in reversed(attempted):
            try:
                directory_chain(target.parent)
                if backup:
                    # Copy the backup for restoration so recovery always retains
                    # the original previous bytes even if a later restore fails.
                    restore = backup.with_suffix(".restore")
                    shutil.copyfile(backup, restore)
                    restore.chmod(stat.S_IMODE(backup.stat().st_mode))
                    replace_file(restore, target)
                elif os.path.lexists(target):
                    target.unlink()
            except (OSError, ValueError, KeyboardInterrupt) as restore_error:
                failures.append(f"{target}: {str(restore_error) or type(restore_error).__name__}")
        if failures:
            raise ValueError(f"installation failed: {error_detail}\nRestoration incomplete: " + "\n".join(failures) +
                             "\nPreserved recovery copies: " + ", ".join(map(str, recovery.values())) +
                             "\n" + instructions) from error
        outcome = ("Previous installation restored; installed files and record are consistent."
                   if attempted else "Installed files were not changed.")
        retain = False
        failure_message = f"installation failed: {error_detail}\n{outcome}"
        raise ValueError(failure_message) from error
    finally:
        if retain:
            print("Installation incomplete or outcome unknown; recovery copies and blocking locks retained.\n"
                  "Recovery instructions: " + ", ".join(str(path / "RECOVERY.txt") for path in recovery.values()) +
                  "\nRetained locks: " + ", ".join(map(str, locks)), file=sys.stderr)
        else:
            cleanup_errors = []
            cleanup_note = (outcome + "\nCleanup only: do not restore old backups. "
                            "Remove any remaining directories and locks listed below after ensuring no installer is running.\n" +
                            "\n".join(map(str, [*recovery.values(), *locks])) + "\n")
            # Transition every rollback note before deleting any backups. If a
            # note cannot be changed, keep all copies and locks; no remaining
            # instruction may refer to backups already deleted during cleanup.
            for directory in recovery.values():
                try:
                    (directory / "RECOVERY.txt").write_text(cleanup_note, encoding="utf-8")
                except (OSError, KeyboardInterrupt) as cleanup_error:
                    cleanup_errors.append(f"cleanup note {directory}: {str(cleanup_error) or type(cleanup_error).__name__}")
            if not cleanup_errors:
                for directory in recovery.values():
                    try:
                        shutil.rmtree(directory)
                    except (OSError, KeyboardInterrupt) as cleanup_error:
                        cleanup_errors.append(f"cleanup directory {directory}: {str(cleanup_error) or type(cleanup_error).__name__}")
            remaining_recovery = [path for path in recovery.values() if os.path.lexists(path)]
            if remaining_recovery:
                cleanup_errors.append("Recovery cleanup is unfinished; installation locks retained to prevent another update.")
            for lock in reversed(locks):
                if not remaining_recovery:
                    try:
                        lock.rmdir()
                    except (OSError, KeyboardInterrupt) as cleanup_error:
                        cleanup_errors.append(f"cleanup lock {lock}: {str(cleanup_error) or type(cleanup_error).__name__}")
                if os.path.lexists(lock):
                    try:
                        (lock / "RECOVERY.txt").write_text(cleanup_note, encoding="utf-8")
                    except (OSError, KeyboardInterrupt) as cleanup_error:
                        cleanup_errors.append(f"cleanup note {lock}: {str(cleanup_error) or type(cleanup_error).__name__}")
            for directory in reversed(created):
                try:
                    directory.rmdir()
                except OSError:
                    pass  # Never remove a pre-existing or nonempty shared folder.
            if cleanup_errors:
                remaining = [path for path in [*recovery.values(), *locks] if os.path.lexists(path)]
                raise ValueError((failure_message + "\n" if failure_message else outcome + "\n") +
                                 "Cleanup incomplete; do not restore old backups. After ensuring no installer is running, "
                                 "remove only the remaining cleanup directories/locks below.\n" +
                                 "\n".join(cleanup_errors) + "\nRemaining cleanup paths: " +
                                 (", ".join(map(str, remaining)) or "none"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=CLIENTS, required=True)
    parser.add_argument("--dry-run", action="store_true", help="preflight and preview without destination or state writes")
    args = parser.parse_args(argv)
    try:
        plan = prepare(args.client)
        print(f"Client: {args.client}")
        for category, path in plan.roots.items():
            print(f"{category}: {path}")
        for name, label in plan.record["bundles"].items():
            print(f"{name}: Experimental {label}")
        if not args.dry_run:
            plan = apply(plan)
        action = "unchanged" if plan.unchanged else "install" if plan.old_record is None else "update"
        print(f"{'Dry run: ' if args.dry_run else ''}{action}; three skills and ten roles; {len(plan.changes)} files to copy, {len(plan.removals)} files to remove.")
        for key in plan.changes:
            print(f"copy {plan.destination(key)}")
        for key in plan.removals:
            print(f"remove {plan.destination(key)}")
        if not plan.unchanged:
            print(f"record {plan.state}")
            print("Start a fresh client session after installation changes.")
        return 0
    except (OSError, ValueError) as error:
        print(f"Installer stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
