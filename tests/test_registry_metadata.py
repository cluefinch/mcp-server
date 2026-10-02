import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_NAME = "io.github.cluefinch/mcp"
REGISTRY_MARKER = f"<!-- mcp-name: {REGISTRY_NAME} -->"


def test_registry_metadata_matches_project_release_contract():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert server["$schema"] == (
        "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
    )
    assert server["name"] == REGISTRY_NAME
    assert len(server["description"]) <= 100
    assert server["version"] == project["version"]
    assert server["repository"] == {
        "url": "https://github.com/cluefinch/mcp-server",
        "source": "github",
    }

    packages = server["packages"]
    assert len(packages) == 1
    package = packages[0]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == project["name"] == "cluefinch"
    assert package["version"] == project["version"]
    assert package["transport"] == {"type": "stdio"}

    assert readme.count(REGISTRY_MARKER) == 1
