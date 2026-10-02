"""Validate that a requested release tag names the project version."""

import sys
import tomllib
from pathlib import Path


class ReleaseTagError(RuntimeError):
    """Raised when a release tag does not match project metadata."""


def validate_release_tag(tag: str, project_file: Path = Path("pyproject.toml")) -> str:
    """Return the project version when ``tag`` is exactly ``v<version>``."""
    if not tag or tag != tag.strip():
        raise ReleaseTagError(
            "Release tag must be a non-empty value without surrounding whitespace"
        )
    if "/" in tag or "\\" in tag:
        raise ReleaseTagError("Release tag must be a simple tag name, not a ref path")

    project = tomllib.loads(project_file.read_text(encoding="utf-8"))["project"]
    version = str(project["version"])
    expected = f"v{version}"

    if tag != expected:
        raise ReleaseTagError(
            f"Release tag {tag!r} does not match project version {version!r}; expected {expected!r}"
        )

    return version


def main() -> None:
    if len(sys.argv) != 2:
        raise ReleaseTagError("Usage: check_release_tag.py vX.Y.Z")
    version = validate_release_tag(sys.argv[1])
    print(f"PASS: release tag v{version} matches pyproject.toml")


if __name__ == "__main__":
    main()
