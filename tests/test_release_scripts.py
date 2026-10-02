from ast import Assert, parse, walk
from pathlib import Path

RELEASE_GATE_SCRIPTS = [
    Path("scripts/check_release.py"),
    Path("scripts/smoke_installed.py"),
]


def test_release_gate_scripts_do_not_use_assert():
    for path in RELEASE_GATE_SCRIPTS:
        tree = parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert not any(isinstance(node, Assert) for node in walk(tree)), path


def test_installed_smoke_has_no_hard_coded_project_version():
    text = Path("scripts/smoke_installed.py").read_text(encoding="utf-8")
    project_text = Path("pyproject.toml").read_text(encoding="utf-8")

    for line in project_text.splitlines():
        if line.startswith("version = "):
            version = line.split("=", 1)[1].strip().strip('"')
            break
    else:
        raise AssertionError("project version not found")

    assert version not in text
