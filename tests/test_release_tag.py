from pathlib import Path

import pytest

from scripts.check_release_tag import ReleaseTagError, validate_release_tag


def _project(tmp_path: Path, version: str = "0.1.4") -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        f'[project]\nname = "cluefinch"\nversion = "{version}"\n', encoding="utf-8"
    )
    return path


def test_release_tag_must_match_project_version(tmp_path):
    project = _project(tmp_path)

    assert validate_release_tag("v0.1.4", project) == "0.1.4"

    with pytest.raises(ReleaseTagError, match=r"expected 'v0\.1\.4'"):
        validate_release_tag("v0.1.3", project)


@pytest.mark.parametrize(
    "tag", ["", " v0.1.4", "v0.1.4 ", "refs/tags/v0.1.4", "tags\\v0.1.4"]
)
def test_release_tag_rejects_ambiguous_ref_forms(tmp_path, tag):
    with pytest.raises(ReleaseTagError):
        validate_release_tag(tag, _project(tmp_path))
