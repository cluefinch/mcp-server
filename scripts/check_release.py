"""Validate release metadata and allowlisted archive contents without extraction."""

import ast
import sys
import tarfile
import tomllib
import zipfile
from collections import Counter
from configparser import ConfigParser
from configparser import Error as ConfigError
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

from packaging.requirements import InvalidRequirement, Requirement


class ReleaseValidationError(RuntimeError):
    """Raised when a release artifact violates the publication contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseValidationError(message)


def _requirements(values: list[str]) -> Counter[Requirement]:
    """Compare PEP 508 requirements without resolving or installing packages."""
    try:
        return Counter(Requirement(value) for value in values)
    except InvalidRequirement as exc:
        raise ReleaseValidationError(f"Invalid dependency requirement: {exc}") from exc


def _required_files(names: set[str], required: set[str], artifact: str) -> None:
    missing = required - names
    _require(not missing, f"Missing {artifact} files: {', '.join(sorted(missing))}")


def _entry_points(raw: str, expected: dict[str, str]) -> None:
    parsed = ConfigParser(interpolation=None)
    parsed.optionxform = lambda optionstr: optionstr
    try:
        parsed.read_string(raw)
    except ConfigError as exc:
        raise ReleaseValidationError(f"Invalid wheel entry points: {exc}") from exc
    _require(
        not parsed.defaults()
        and parsed.sections() == ["console_scripts"]
        and dict(parsed["console_scripts"]) == expected,
        "Wheel console scripts differ from pyproject.toml",
    )


def main(directory: Path) -> None:
    configuration = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = configuration["project"]
    version = project["version"]
    _require(project["name"] == "cluefinch", "Unexpected project name")
    tree = ast.parse(Path("mcp_search/__init__.py").read_text(encoding="utf-8"))
    versions = [
        ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "__version__" for t in n.targets)
    ]
    _require(versions == [version], "Package version does not match pyproject.toml")
    wheel = directory / f"cluefinch-{version}-py3-none-any.whl"
    sdist = directory / f"cluefinch-{version}.tar.gz"
    # uv creates this marker beside (not inside) the distributions.
    files = {p for p in directory.iterdir() if p.name != ".gitignore"}
    _require(files == {wheel, sdist}, "Unexpected release files")
    info = f"cluefinch-{version}.dist-info"
    package_sources = {path.as_posix() for path in Path("mcp_search").rglob("*.py")}
    _required_files(
        package_sources,
        {"mcp_search/__init__.py", "mcp_search/__main__.py", "mcp_search/server.py"},
        "checkout",
    )
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        _require(len(names) == len(set(names)), "Duplicate wheel paths")
        _required_files(
            set(names),
            package_sources
            | {
                f"{info}/{name}"
                for name in ("METADATA", "WHEEL", "RECORD", "entry_points.txt")
            }
            | {f"{info}/licenses/{name}" for name in project["license-files"]},
            "wheel",
        )
        for name in names:
            path = PurePosixPath(name)
            _require(
                not path.is_absolute() and ".." not in path.parts and "\\" not in name,
                f"Unsafe wheel path: {name}",
            )
            _require(archive.getinfo(name).file_size < 5 * 1024 * 1024, name)
            _require(name.startswith(("mcp_search/", info + "/")), name)
            if name.startswith("mcp_search/"):
                _require(
                    name.endswith(".py") and len(PurePosixPath(name).parts) == 2, name
                )
        metadata = archive.read(info + "/METADATA")
        entrypoints = archive.read(info + "/entry_points.txt").decode()
        _entry_points(entrypoints, project["scripts"])
    allowed = {
        ".gitignore",
        "pyproject.toml",
        "uv.lock",
        "server.json",
        "README.md",
        "CHANGELOG.md",
        "ROADMAP.md",
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SUPPORT.md",
        "SECURITY.md",
        "AGENTS.md",
        "PKG-INFO",
        "examples/searxng/README.md",
        "examples/searxng/compose.yaml",
        "examples/searxng/settings.yml",
        "docs/DEVELOPMENT.md",
        "docs/REFERENCE.md",
        "docs/RELEASING.md",
        "docs/SEARXNG_COMPLIANCE.md",
    }
    with tarfile.open(sdist) as archive:
        source_names: set[str] = set()
        source_files: set[str] = set()
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            _require(
                member.name not in source_names, f"Duplicate sdist path: {member.name}"
            )
            source_names.add(member.name)
            _require(
                bool(path.parts) and path.parts[0] == f"cluefinch-{version}",
                member.name,
            )
            _require(
                ".." not in path.parts
                and not path.is_absolute()
                and "\\" not in member.name,
                f"Unsafe sdist path: {member.name}",
            )
            if member.isdir():
                continue
            _require(member.isfile(), member.name)
            _require(member.size < 5 * 1024 * 1024, member.name)
            relative = str(PurePosixPath(*path.parts[1:]))
            source_files.add(relative)
            _require(
                relative in allowed
                or (
                    len(path.parts) > 1
                    and path.parts[1] in {"mcp_search", "tests", "scripts"}
                    and relative.endswith(".py")
                    and "__pycache__" not in path.parts
                ),
                relative,
            )
        _required_files(
            source_files,
            package_sources
            | {"pyproject.toml", "README.md", "PKG-INFO"}
            | set(project["license-files"]),
            "sdist",
        )
        project_file = archive.extractfile(f"cluefinch-{version}/pyproject.toml")
        if project_file is None:
            raise ReleaseValidationError("Missing sdist build configuration")
        with project_file:
            source_configuration = tomllib.loads(project_file.read().decode("utf-8"))
        _require(
            source_configuration == configuration,
            "Sdist pyproject.toml differs from checkout",
        )
        metadata_file = archive.extractfile(f"cluefinch-{version}/PKG-INFO")
        if metadata_file is None:
            raise ReleaseValidationError("Missing sdist metadata")
        with metadata_file:
            source_metadata = metadata_file.read()
    for raw in (metadata, source_metadata):
        parsed = BytesParser().parsebytes(raw)
        _require(parsed["Name"] == "cluefinch", "Unexpected package name")
        _require(parsed["Version"] == version, "Unexpected package version")
        _require(
            parsed["Requires-Python"] == project["requires-python"],
            "Requires-Python differs from pyproject.toml",
        )
        _require(
            parsed["License-Expression"] == "Apache-2.0",
            "Unexpected license expression",
        )
        _require(
            parsed["Description-Content-Type"] == "text/markdown",
            "Unexpected description content type",
        )
        _require(
            _requirements(parsed.get_all("Requires-Dist", []))
            == _requirements(project["dependencies"]),
            "Dependency metadata differs from pyproject.toml",
        )
        _require(
            "<!-- mcp-name: io.github.cluefinch/mcp -->" in str(parsed.get_payload()),
            "Missing MCP Registry ownership marker from package description",
        )
    for artifact in (wheel, sdist):
        print(f"PASS: {artifact.name} ({artifact.stat().st_size} bytes)")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
