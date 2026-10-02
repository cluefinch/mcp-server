# Contributing to Cluefinch MCP

Submit reproducible bugs and focused feature proposals through the repository issue forms, and code changes through pull requests. Read [SUPPORT.md](SUPPORT.md) for support scope and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating.

## Licensing and DCO

By intentionally submitting an original contribution for inclusion in this project, you agree to license it under Apache-2.0 as provided in section 5 of LICENSE. Copyright remains with the respective copyright holders; this is not a copyright assignment or a promise of exclusive rights.

Every contributed commit must carry a Developer Certificate of Origin 1.1 sign-off matching that commit's author identity:

```text
Signed-off-by: Your Name <your-email@example.com>
```

Use `git commit -s` only if you can truthfully make that certification. Do not sign for another contributor. Sign-off details become part of public Git history. Pull requests are checked automatically for matching DCO sign-offs.

## Before submitting

Run the standard checks:

```sh
uv python install 3.12
uv sync --locked
uv run ruff check mcp_search tests scripts
uv run ruff format --check mcp_search tests scripts
uv run pytest -q
uvx --from 'pyright==1.1.414' pyright --pythonpath .venv/bin/python mcp_search scripts
```

Add regression tests for behavior changes, especially security boundaries, MCP schemas, retrieval coordinates, release metadata, and compatibility behavior. Keep changes focused; avoid combining unrelated refactors with contract changes.

Tool descriptions are part of the model-facing interface. Changes to them should be justified with behavioral evaluation rather than token-count reduction alone.

## Third-party material

Identify copied or adapted material, its exact upstream revision, license, and existing notices in the pull request. Obtain any necessary employer or client authorization before submitting. Do not remove third-party attributions.

Disclose material AI assistance and known source matches. AI generation does not establish ownership or remove third-party licensing obligations.

Do not copy SearXNG code into this Apache-licensed core. Propose SearXNG patches in a separately identified component under the applicable upstream license and review distribution/network-source obligations. New dependencies and embedded assets require license review, including transitive and binary contents when redistributed.

## Sensitive information

Do not commit or post credentials, `.env` files, private URLs, captures, session IDs, internal audit material, private model configuration, or sensitive retrieved content.

Report vulnerabilities through [SECURITY.md](SECURITY.md), not a public issue. Ordinary usage questions and reproducible defects should follow [SUPPORT.md](SUPPORT.md).
