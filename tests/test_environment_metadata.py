"""Independent metadata observations, error handling and isolated CLI evidence.

The subprocess guard detects attempted writes/imports/probes during the reporter;
file snapshots also compare final package and working-directory state. These
checks do not establish anything about installed packages' runtime behavior.
"""
from __future__ import annotations

from importlib import metadata, util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("develop-mesa-model", "evaluate-mesa-model")
CORE = ("Mesa", "NetworkX")
GEOGRAPHIC = (
    "Mesa-Geo", "NumPy", "GeoPandas", "Shapely", "pyproj", "Rasterio",
    "Rtree", "libpysal", "affine", "xyzservices",
)
PRIVATE_PAYLOAD = "private metadata failure payload must not escape"


@pytest.fixture
def reporter():
    path = ROOT / "skills" / SKILLS[0] / "scripts" / "inspect_environment.py"
    spec = util.spec_from_file_location("metadata_reporter_under_test", path)
    module = util.module_from_spec(spec)
    # Execute the inspected helper without importlib writing into its package.
    # Keep the normal module globals so injected CLI/lookups exercise real code.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def record(present, state, version):
    return {"present": present, "state": state, "version": version}


def lookup_from(outcomes, calls):
    def lookup(name):
        calls.append(name)
        result = outcomes[name]
        if isinstance(result, Exception):
            raise result
        return result
    return lookup


def parse_text(text):
    """Decode the documented text representation without using its renderer."""
    first, *rows = text.splitlines()
    prefix = "Python: implementation="
    assert first.startswith(prefix)
    implementation, position = json.JSONDecoder().raw_decode(first[len(prefix):])
    remainder = first[len(prefix) + position:]
    assert remainder.startswith(" version=")
    result = {
        "python": {
            "implementation": implementation,
            "version": json.loads(remainder[len(" version="):]),
        },
        "distributions": {},
    }
    presence = {"true": True, "false": False, "unknown": None}
    for row in rows:
        matched = re.fullmatch(
            r"([^:]+): state=(\w+) present=(true|false|unknown) version=(.*)", row)
        assert matched is not None, row
        name, state, present, version = matched.groups()
        assert name not in result["distributions"]
        result["distributions"][name] = record(
            presence[present], state, json.loads(version))
    return result


def decode(output, as_json):
    return json.loads(output) if as_json else parse_text(output)


class TextValue:
    def __str__(self):
        return "vendor snapshot without a numeric version"


class BadTextValue:
    def __str__(self):
        raise ValueError(PRIVATE_PAYLOAD)


class InvalidTextValue:
    def __str__(self):
        return None


STATE_CASES = (
    pytest.param("  arbitrary release \"雪\" + local  ",
                 record(True, "available", "  arbitrary release \"雪\" + local  "),
                 id="printable-label-verbatim"),
    pytest.param(metadata.PackageNotFoundError("irrelevant diagnostic"),
                 record(False, "absent", None), id="absent"),
    pytest.param(None, record(True, "blank", None), id="none-is-blank"),
    pytest.param("", record(True, "blank", ""), id="empty-is-blank"),
    pytest.param(" \t\r\n", record(True, "blank", " \t\r\n"),
                 id="nonprintable-whitespace-is-blank"),
    pytest.param("release\nnext", record(True, "unprintable", None),
                 id="nonblank-control-character"),
    pytest.param("\x00", record(True, "unprintable", None), id="nul"),
    pytest.param(TextValue(), record(True, "available", str(TextValue())),
                 id="safe-string-conversion"),
    pytest.param(0, record(True, "available", "0"), id="falsey-nonstring"),
    pytest.param(BadTextValue(), record(True, "unprintable", None),
                 id="conversion-exception"),
    pytest.param(InvalidTextValue(), record(True, "unprintable", None),
                 id="invalid-conversion-result"),
    pytest.param(PermissionError(PRIVATE_PAYLOAD), record(None, "failed", None),
                 id="lookup-failure"),
)


@pytest.mark.parametrize("value,expected", STATE_CASES)
def test_metadata_states_preserve_observations(reporter, value, expected):
    calls = []
    report = reporter.collect_environment(version_lookup=lookup_from(
        {"Mesa": value, "NetworkX": "later successful observation"}, calls))
    assert calls == list(CORE)
    assert set(report) == {"python", "distributions"}
    assert set(report["python"]) == {"implementation", "version"}
    assert report["distributions"] == {
        "Mesa": expected,
        "NetworkX": record(True, "available", "later successful observation"),
    }


@pytest.mark.parametrize("geo", [False, True], ids=["core", "geographic"])
def test_selected_distributions_read_once_in_fixed_order(reporter, monkeypatch, geo):
    calls, python_calls = [], []

    def python_fact(name, value):
        def observe():
            python_calls.append(name)
            return value
        return observe

    monkeypatch.setattr(reporter.platform, "python_implementation",
                        python_fact("implementation", "Independent Python"))
    monkeypatch.setattr(reporter.platform, "python_version",
                        python_fact("version", "test interpreter label"))
    selected = CORE + (GEOGRAPHIC if geo else ())
    outcomes = {name: "reported-" + name for name in selected}
    report = reporter.collect_environment(
        geo=geo, version_lookup=lookup_from(outcomes, calls))
    assert calls == list(selected)
    assert list(report["distributions"]) == list(selected)
    assert python_calls == ["implementation", "version"]
    assert report["python"] == {
        "implementation": "Independent Python", "version": "test interpreter label"}
    assert report["distributions"] == {
        name: record(True, "available", "reported-" + name) for name in selected}


def test_lookup_default_is_resolved_at_each_call_and_api_is_keyword_only(
        reporter, monkeypatch):
    for label in ("first lookup", "replacement lookup"):
        calls = []
        monkeypatch.setattr(reporter.metadata, "version", lookup_from(
            dict.fromkeys(CORE, label), calls))
        report = reporter.collect_environment()
        assert calls == list(CORE)
        assert report["distributions"]["Mesa"]["version"] == label
    with pytest.raises(TypeError):
        reporter.collect_environment(True)


def mixed_outcomes():
    return {
        "Mesa": "  not a parsed version \"雪\"  ",
        "NetworkX": PermissionError(PRIVATE_PAYLOAD),
        "Mesa-Geo": metadata.PackageNotFoundError(PRIVATE_PAYLOAD),
        "NumPy": None,
        "GeoPandas": "",
        "Shapely": " \t\n",
        "pyproj": "line\nbreak",
        "Rasterio": BadTextValue(),
        "Rtree": 0,
        "libpysal": "successful after failures",
        "affine": TextValue(),
        "xyzservices": "last observation",
    }


def test_both_renderers_use_the_same_collected_facts_without_lookups(
        reporter, monkeypatch):
    calls = []
    report = reporter.collect_environment(
        geo=True, version_lookup=lookup_from(mixed_outcomes(), calls))
    saved_report = json.loads(json.dumps(report))

    def forbidden_lookup(name):
        pytest.fail("Rendering must not read metadata again: " + name)

    monkeypatch.setattr(reporter.metadata, "version", forbidden_lookup)
    assert parse_text(reporter.render_text(report)) == saved_report
    rendered_json = reporter.render_json(report)
    assert json.loads(rendered_json) == saved_report
    assert rendered_json == json.dumps(saved_report, indent=2, sort_keys=True)
    assert report == saved_report
    assert calls == list(CORE + GEOGRAPHIC)


@pytest.mark.parametrize("as_json", [False, True], ids=["text", "json"])
@pytest.mark.parametrize("value,expected", [
    pytest.param(metadata.PackageNotFoundError(), record(False, "absent", None),
                 id="all-absent"),
    pytest.param(None, record(True, "blank", None), id="all-none"),
    pytest.param("", record(True, "blank", ""), id="all-empty"),
    pytest.param("\t\n", record(True, "blank", "\t\n"), id="all-whitespace"),
    pytest.param(BadTextValue(), record(True, "unprintable", None),
                 id="all-unprintable"),
])
def test_complete_reports_exit_zero_even_without_available_versions(
        reporter, monkeypatch, capsys, as_json, value, expected):
    calls = []
    monkeypatch.setattr(reporter.metadata, "version", lookup_from(
        dict.fromkeys(CORE, value), calls))
    assert reporter.main(["--json"] if as_json else []) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert decode(captured.out, as_json)["distributions"] == dict.fromkeys(CORE, expected)
    assert calls == list(CORE)


@pytest.mark.parametrize("as_json", [False, True], ids=["text", "json"])
def test_failed_reads_emit_partial_report_and_private_safe_error(
        reporter, monkeypatch, capsys, as_json):
    calls = []
    monkeypatch.setattr(reporter.metadata, "version", lookup_from(mixed_outcomes(), calls))
    assert reporter.main(["--geo"] + (["--json"] if as_json else [])) == 2
    captured = capsys.readouterr()
    assert calls == list(CORE + GEOGRAPHIC)
    report = decode(captured.out, as_json)
    assert set(report["distributions"]) == set(CORE + GEOGRAPHIC)
    assert report["distributions"]["Mesa"] == record(
        True, "available", mixed_outcomes()["Mesa"])
    assert report["distributions"]["NetworkX"] == record(None, "failed", None)
    assert report["distributions"]["Mesa-Geo"] == record(False, "absent", None)
    assert report["distributions"]["xyzservices"] == record(
        True, "available", "last observation")
    assert "partial" in captured.err.lower()
    assert "failed" in captured.err.lower()
    assert len(captured.err.splitlines()) == 1
    assert PRIVATE_PAYLOAD not in captured.out + captured.err
    assert "traceback" not in captured.err.lower()


@pytest.mark.parametrize("as_json", [False, True], ids=["text", "json"])
@pytest.mark.parametrize("failure", ["collection", "rendering"])
def test_uncollectable_or_unrenderable_report_exits_two_without_payload(
        reporter, monkeypatch, capsys, as_json, failure):
    def fail(*args, **kwargs):
        raise RuntimeError(PRIVATE_PAYLOAD)

    if failure == "collection":
        monkeypatch.setattr(reporter.platform, "python_version", fail)
    else:
        monkeypatch.setattr(reporter.metadata, "version", lambda name: "observed")
        monkeypatch.setattr(reporter, "render_json" if as_json else "render_text", fail)
    assert reporter.main(["--json"] if as_json else []) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(captured.err.splitlines()) == 1
    assert "error" in captured.err.lower()
    assert PRIVATE_PAYLOAD not in captured.err
    assert "traceback" not in captured.err.lower()


def snapshot(root):
    result = {}
    for path in (root, *sorted(root.rglob("*"))):
        info = path.lstat()
        content = (os.readlink(path) if path.is_symlink() else
                   path.read_bytes() if stat.S_ISREG(info.st_mode) else None)
        result[path.relative_to(root)] = (info.st_mode, info.st_mtime_ns, content)
    return result


# The guard runs inside an isolated Python process. It records violations even
# if the reporter catches the resulting exception and tries to continue.
ISOLATED_GUARD = r'''
import importlib.metadata
import os
import runpy
import sys

script, forbidden_root, *arguments = sys.argv[1:]
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
assert all(not os.path.abspath(p).startswith(forbidden_root + os.sep) for p in sys.path)
violations = []
original_environment = os.environ


def deny(message):
    violations.append(message)
    raise RuntimeError(message)


class StandardLibraryOnly:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] not in sys.stdlib_module_names:
            deny('non-stdlib import: ' + fullname)


class NoEnvironment:
    def __getitem__(self, key):
        if sys._getframe(1).f_globals.get('__name__') in {'gettext', 'shutil'}:
            return original_environment[key]
        deny('environment access')
    def get(self, *args, **kwargs):
        # argparse legitimately reads locale and terminal settings via stdlib.
        if sys._getframe(1).f_globals.get('__name__') in {'gettext', 'shutil'}:
            return original_environment.get(*args, **kwargs)
        deny('environment access')
    def __iter__(self):
        deny('environment inventory')
    def keys(self):
        deny('environment inventory')
    def items(self):
        deny('environment inventory')
    def values(self):
        deny('environment inventory')
    def copy(self):
        deny('environment inventory')


def audit(event, args):
    if event == 'open':
        path, mode, flags = args
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            deny('file write')
        if isinstance(path, str) and os.path.abspath(path).startswith(forbidden_root + os.sep):
            deny('source checkout access')
    if event.startswith(('socket.', 'subprocess.', 'os.exec', 'os.spawn')):
        deny('network or process probe')
    if event in {
        'os.system', 'os.posix_spawn', 'os.remove', 'os.rename', 'os.rmdir',
        'os.mkdir', 'os.chmod', 'os.chown', 'os.truncate', 'os.utime',
        'os.link', 'os.symlink', 'os.putenv', 'os.unsetenv',
    }:
        deny('mutation or process probe')


def no_inventory(*args, **kwargs):
    deny('distribution inventory')


sys.meta_path.insert(0, StandardLibraryOnly())
os.environ = NoEnvironment()
importlib.metadata.distributions = no_inventory
importlib.metadata.packages_distributions = no_inventory
sys.addaudithook(audit)
sys.argv = [script, *arguments]
try:
    runpy.run_path(script, run_name='__main__')
except SystemExit as result:
    status = result.code
else:
    status = 0
assert violations == [], violations
raise SystemExit(status)
'''


@pytest.fixture(params=SKILLS)
def installed_reporter(request, tmp_path):
    assert not tmp_path.resolve().is_relative_to(ROOT.resolve())
    package = tmp_path / "installed" / request.param
    shutil.copytree(ROOT / "skills" / request.param, package)
    assert set(p.name for p in package.parent.iterdir()) == {request.param}
    working = tmp_path / "unrelated-working-directory"
    working.mkdir()
    (working / "model.py").write_text(
        "raise RuntimeError('user model code must not be imported')\n", encoding="utf-8")
    (working / "user-note.txt").write_text("Keep this note.\n", encoding="utf-8")
    script = package / "scripts" / "inspect_environment.py"
    assert script.is_file(), "An absent implementation fails QA."

    def run(*arguments, guarded=False):
        assert not list(package.rglob("__pycache__"))
        before = snapshot(tmp_path)
        command = [sys.executable, "-I", "-S", "-B"]
        if guarded:
            command += ["-c", ISOLATED_GUARD, str(script), str(ROOT)]
        else:
            command.append(str(script))
        command.extend(arguments)
        result = subprocess.run(command, cwd=working, capture_output=True, text=True,
                                check=False, timeout=10)
        assert snapshot(tmp_path) == before, "Reporter modified package or user files."
        assert not list(package.rglob("__pycache__"))
        assert "traceback" not in result.stderr.lower(), result.stderr
        return result
    return run


@pytest.mark.parametrize("as_json", [False, True], ids=["text", "json"])
@pytest.mark.parametrize("geo", [False, True], ids=["core", "geographic"])
def test_individually_installed_stdlib_cli_without_imports_probes_or_writes(
        installed_reporter, as_json, geo):
    arguments = (["--geo"] if geo else []) + (["--json"] if as_json else [])
    direct = installed_reporter(*arguments)
    guarded = installed_reporter(*arguments, guarded=True)
    assert (direct.returncode, direct.stderr) == (0, "")
    assert (guarded.returncode, guarded.stderr) == (0, "")
    assert guarded.stdout == direct.stdout
    report = decode(direct.stdout, as_json)
    assert set(report) == {"python", "distributions"}
    assert report["python"]["implementation"]
    assert report["python"]["version"]
    selected = CORE + (GEOGRAPHIC if geo else ())
    assert report["distributions"] == {
        name: record(False, "absent", None) for name in selected}


def test_individually_installed_cli_help(installed_reporter):
    result = installed_reporter("--help", guarded=True)
    assert (result.returncode, result.stderr) == (0, "")
    assert "--geo" in result.stdout and "--json" in result.stdout
    assert "metadata" in result.stdout.lower()


@pytest.mark.parametrize("arguments", [
    ("--unknown",), ("--ge",), ("--js",), ("model.py",), ("--geo=true",),
], ids=["unknown-option", "geo-abbreviation", "json-abbreviation", "positional", "flag-value"])
def test_individually_installed_cli_rejects_unsupported_usage(
        installed_reporter, arguments):
    result = installed_reporter(*arguments, guarded=True)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage:" in result.stderr.lower()


def test_vendored_reporters_are_identical():
    assert (ROOT / "skills" / SKILLS[0] / "scripts" / "inspect_environment.py").read_bytes() == (
        ROOT / "skills" / SKILLS[1] / "scripts" / "inspect_environment.py").read_bytes()
