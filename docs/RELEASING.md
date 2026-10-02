# Releasing Cluefinch MCP

This repository publishes the PyPI distribution `cluefinch`; the Python package remains `mcp_search`, and the console entrypoint is `cluefinch`.

Releases are immutable-tag driven. The release workflow does not publish an arbitrary default-branch checkout.

## Release checklist

1. Prepare the intended version in `pyproject.toml`, `mcp_search/__init__.py`, `uv.lock`, `CHANGELOG.md`, `README.md`, and `server.json`.
2. Confirm the README Registry marker exactly matches `server.json.name`.
3. Run the full `Checks` workflow on the exact release commit. It must pass the supported OS/Python matrix, lower-bound dependency check, Ruff, tests, build, and Pyright.
4. Review the source tree for secrets and internal-only material. `.gitignore` does not remove files that are already tracked.
5. Ensure the repository is public before publishing a version whose metadata links to this repository.
6. Confirm GitHub security/publication settings required for the release are enabled, including the PyPI `pypi` environment and Trusted Publisher.
7. Create the version tag `vX.Y.Z` on the reviewed commit. The tag must match `pyproject.toml` exactly.
8. Run **Publish to PyPI** and supply that existing tag.
9. Verify the resulting PyPI project page, wheel, sdist, provenance/attestation, and GitHub Release.
10. Publish the same version to the official MCP Registry and verify discovery.

Do not reuse a released version number or uploaded distribution filename.

## Local verification

Use the project-pinned uv version and Python 3.12.4 explicitly for this shell session. Verify the actual interpreter before continuing:

```sh
export UV_PYTHON=3.12.4
uv python install 3.12.4
uv sync --locked
uv run python -c "import sys; print(sys.version); sys.exit(sys.version_info[:3] != (3, 12, 4))" || exit 1
uv run ruff check mcp_search tests scripts
uv run ruff format --check mcp_search tests scripts
uv run pytest -q
uvx --from 'pyright==1.1.414' pyright --pythonpath .venv/bin/python mcp_search scripts
uv build --out-dir release-dist
uv run python scripts/check_release.py release-dist
uvx --from 'twine==7.0.0' twine check --strict release-dist/*
```

Install the built wheel into a fresh environment and run `scripts/smoke_installed.py` with that environment path. The smoke test exercises both the `cluefinch` console script and `python -m mcp_search` through MCP stdio outside the source checkout.

Archive validation checks the public-file allowlist, required package/build files, metadata, dependency requirements, console entry points, and the sdist build configuration against the checkout. Run it in the synced development environment, which includes `packaging`. It complements, but does not replace, installation/smoke checks or a source-tree secret review.

## GitHub release workflow

The `Publish to PyPI` workflow takes an existing version tag such as `v0.1.4`.

The workflow first validates that the requested tag is exactly `v<project.version>`. The prepare job resolves the explicit tag ref to a commit SHA and exports it. Every verification/build job checks out that SHA and verifies HEAD instead of resolving the tag again. Publication depends on the full supported matrix rather than a single release-only runner.

The build job creates and validates the wheel and sdist, performs installed-package smoke checks, and uploads the reviewed artifacts under a name containing the prepared SHA. A separate PyPI job downloads those same artifacts and uses Trusted Publishing/OIDC. Only the publishing job receives `id-token: write` and uses the `pypi` GitHub Environment.

Before PyPI publication and again before creating the GitHub Release, the workflow checks that the tag still identifies the prepared commit. A moved/deleted tag or API failure stops that step. After successful PyPI publication, the workflow creates a GitHub Release for the same tag and attaches the same distribution artifacts. A failure at this later step does not undo a completed PyPI publication.

The tag check and publication are not atomic. Repository/tag protection is an operational GitHub setting rather than a file in the release artifact. Public release setup should protect `v*` tags from unreviewed movement/deletion where the repository plan permits it.

## Trusted Publishing

The PyPI Trusted Publisher should identify:

- owner: `cluefinch`
- repository: `mcp-server`
- workflow: `release.yml`
- environment: `pypi`

No long-lived PyPI API token is required. A required reviewer on the `pypi` environment can add a human publication gate.

## Official MCP Registry

Cluefinch MCP's canonical Registry server name is:

```text
io.github.cluefinch/mcp
```

The root `server.json`, README marker, package version, and PyPI version must agree. Before Registry publication, validate the manifest with the official publisher CLI.

A typical sequence after PyPI publication is:

```sh
mcp-publisher login github
mcp-publisher validate
mcp-publisher publish
```

Registry publication follows PyPI because Registry ownership verification for a PyPI package checks the package metadata/README marker. After publication, query the production Registry for `io.github.cluefinch/mcp` and confirm the expected version is discoverable.

Before publishing, validate `server.json` and follow the current official MCP Registry publisher documentation.

See [Development](DEVELOPMENT.md) and the repository [SECURITY.md](../SECURITY.md) for adjacent policy.
