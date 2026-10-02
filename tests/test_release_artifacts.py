import io
import tarfile
import tomllib
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.check_release import ReleaseValidationError, main


@dataclass
class Artifacts:
    directory: Path
    version: str
    wheel: dict[str, bytes]
    sdist: dict[str, bytes]

    @property
    def info(self):
        return f"cluefinch-{self.version}.dist-info"

    def write(self):
        with zipfile.ZipFile(
            self.directory / f"cluefinch-{self.version}-py3-none-any.whl", "w"
        ) as archive:
            for name, content in self.wheel.items():
                archive.writestr(name, content)
        with tarfile.open(
            self.directory / f"cluefinch-{self.version}.tar.gz", "w:gz"
        ) as archive:
            for name, content in self.sdist.items():
                member = tarfile.TarInfo(f"cluefinch-{self.version}/{name}")
                member.size = len(content)
                archive.addfile(member, io.BytesIO(content))


@pytest.fixture
def artifacts(tmp_path):
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    version = project["version"]
    info = f"cluefinch-{version}.dist-info"
    metadata = (
        f"Metadata-Version: 2.4\nName: cluefinch\nVersion: {version}\n"
        f"Requires-Python: {project['requires-python']}\n"
        "License-Expression: Apache-2.0\nDescription-Content-Type: text/markdown\n"
        + "".join(f"Requires-Dist: {req}\n" for req in project["dependencies"])
        + "\n<!-- mcp-name: io.github.cluefinch/mcp -->\n"
    ).encode()
    package = {
        path.as_posix(): path.read_bytes() for path in Path("mcp_search").rglob("*.py")
    }
    wheel = {
        **package,
        f"{info}/METADATA": metadata,
        f"{info}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{info}/RECORD": b"",
        f"{info}/entry_points.txt": b"[console_scripts]\ncluefinch = mcp_search.server:main\n",
        **{
            f"{info}/licenses/{name}": Path(name).read_bytes()
            for name in project["license-files"]
        },
    }
    sdist = {
        **package,
        "PKG-INFO": metadata,
        **{
            name: Path(name).read_bytes()
            for name in ["pyproject.toml", "README.md", *project["license-files"]]
        },
    }
    return Artifacts(tmp_path, version, wheel, sdist)


def test_accepts_required_artifact_contract(artifacts):
    artifacts.write()
    main(artifacts.directory)


def test_rejects_status_file_in_sdist(artifacts):
    artifacts.sdist["STATUS.md"] = b"internal release state"
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match=r"STATUS\.md"):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_rejects_metadata_only_artifact(artifacts, kind):
    if kind == "wheel":
        artifacts.wheel = {
            name: data
            for name, data in artifacts.wheel.items()
            if not name.startswith("mcp_search/") or name == "mcp_search/__main__.py"
        }
    else:
        artifacts.sdist = {"PKG-INFO": artifacts.sdist["PKG-INFO"]}
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match=f"Missing {kind} files"):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize(
    "name",
    ["mcp_search/__init__.py", "mcp_search/server.py", "mcp_search/navigation.py"],
)
def test_rejects_missing_package_module(artifacts, kind, name):
    del getattr(artifacts, kind)[name]
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match=r"Missing .* files"):
        main(artifacts.directory)


@pytest.mark.parametrize("name", ["pyproject.toml", "README.md", "LICENSE", "PKG-INFO"])
def test_rejects_missing_sdist_build_or_metadata_file(artifacts, name):
    del artifacts.sdist[name]
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match="Missing sdist files"):
        main(artifacts.directory)


@pytest.mark.parametrize(
    "name", ["METADATA", "WHEEL", "RECORD", "entry_points.txt", "licenses/LICENSE"]
)
def test_rejects_missing_wheel_contract_file(artifacts, name):
    del artifacts.wheel[f"{artifacts.info}/{name}"]
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match="Missing wheel files"):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize(
    "replacement",
    [
        b"unrelated-package>=0.27,<1",
        b"httpx>=0.28,<1",
        b"httpx[http2]>=0.27,<1",
        b'httpx>=0.27,<1; python_version < "3.13"',
        b"httpx @ https://example.com/pkg.whl",
        b"httpx???",
    ],
)
def test_rejects_changed_dependency_with_same_count(artifacts, kind, replacement):
    entries = getattr(artifacts, kind)
    name = f"{artifacts.info}/METADATA" if kind == "wheel" else "PKG-INFO"
    entries[name] = entries[name].replace(b"httpx>=0.27,<1", replacement)
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match=r"[Dd]ependency"):
        main(artifacts.directory)


def test_accepts_equivalent_dependency_spelling_and_order(artifacts):
    name = f"{artifacts.info}/METADATA"
    lines = artifacts.wheel[name].splitlines(keepends=True)
    requirements = [line for line in lines if line.startswith(b"Requires-Dist:")]
    metadata = b"".join(
        line for line in lines if not line.startswith(b"Requires-Dist:")
    )
    headers, body = metadata.split(b"\n\n", 1)
    artifacts.wheel[name] = (
        headers + b"\n" + b"".join(reversed(requirements)) + b"\n" + body
    ).replace(b"rank-bm25>=0.2.2,<0.3", b"Rank_BM25 (<0.3, >=0.2.2)")
    artifacts.write()
    main(artifacts.directory)


@pytest.mark.parametrize(
    "entrypoints",
    [
        b"[console_scripts]\nother = mcp_search.server:main\n# cluefinch = mcp_search.server:main\n",
        b"[console_scripts]\ncluefinch = mcp_search.server:wrong\n",
        b"[console_scripts]\ncluefinch = mcp_search.server:main\nextra = mcp_search.server:main\n",
        b"[console_scripts]\ncluefinch = mcp_search.server:main\ncluefinch = mcp_search.server:wrong\n",
    ],
)
def test_rejects_wrong_or_ambiguous_console_scripts(artifacts, entrypoints):
    artifacts.wheel[f"{artifacts.info}/entry_points.txt"] = entrypoints
    artifacts.write()
    with pytest.raises(
        ReleaseValidationError, match=r"[Ee]ntry points|console scripts"
    ):
        main(artifacts.directory)


def test_rejects_different_sdist_build_configuration(artifacts):
    artifacts.sdist["pyproject.toml"] = artifacts.sdist["pyproject.toml"].replace(
        b"hatchling.build", b"other.build"
    )
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match=r"pyproject\.toml differs"):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_rejects_unsafe_archive_path(artifacts, kind):
    name = (
        f"{artifacts.info}/../escape" if kind == "wheel" else "mcp_search/../escape.py"
    )
    getattr(artifacts, kind)[name] = b"unexpected"
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match="Unsafe"):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_rejects_dependency_omission_or_duplication(artifacts, kind, change):
    entries = getattr(artifacts, kind)
    name = f"{artifacts.info}/METADATA" if kind == "wheel" else "PKG-INFO"
    line = b"Requires-Dist: httpx>=0.27,<1\n"
    entries[name] = entries[name].replace(
        line, b"" if change == "missing" else line * 2
    )
    artifacts.write()
    with pytest.raises(ReleaseValidationError, match="Dependency metadata"):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("Name", "other"),
        ("Version", "0.0.0"),
        ("Requires-Python", ">=3.11"),
        ("License-Expression", "MIT"),
        ("Description-Content-Type", "text/plain"),
    ],
)
def test_rejects_inconsistent_metadata(artifacts, kind, field, value):
    entries = getattr(artifacts, kind)
    name = f"{artifacts.info}/METADATA" if kind == "wheel" else "PKG-INFO"
    entries[name] = b"".join(
        f"{field}: {value}\n".encode()
        if line.startswith(f"{field}:".encode())
        else line
        for line in entries[name].splitlines(keepends=True)
    )
    artifacts.write()
    with pytest.raises(ReleaseValidationError):
        main(artifacts.directory)


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_rejects_duplicate_archive_member(artifacts, kind):
    artifacts.write()
    if kind == "wheel":
        path = artifacts.directory / f"cluefinch-{artifacts.version}-py3-none-any.whl"
        with zipfile.ZipFile(path, "a") as archive:
            with pytest.warns(UserWarning, match="Duplicate name"):
                archive.writestr("mcp_search/__init__.py", b"duplicate")
    else:
        path = artifacts.directory / f"cluefinch-{artifacts.version}.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for name, data in [*artifacts.sdist.items(), ("PKG-INFO", b"duplicate")]:
                member = tarfile.TarInfo(f"cluefinch-{artifacts.version}/{name}")
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
    with pytest.raises(ReleaseValidationError, match="Duplicate"):
        main(artifacts.directory)
