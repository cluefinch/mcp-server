# Development

## Environment and checks

Cluefinch MCP requires Python 3.12.4 or newer. With uv installed:

```sh
uv python install 3.12
uv sync --locked
uv run ruff check mcp_search tests scripts
uv run ruff format --check mcp_search tests scripts
uv run pytest -q
uvx --from 'pyright==1.1.414' pyright --pythonpath .venv/bin/python mcp_search scripts
uv build
```

On Windows, use `.venv/Scripts/python.exe` when invoking Pyright manually.

CI runs the supported Python matrix on Ubuntu and Windows, repeats tests against `lowest-direct` dependency resolution, and runs the same pinned Pyright version. Do not disable inspections or type diagnostics globally merely to obtain a clean result.

The automated suite covers URL/IP policy, validated transport, decompression limits, text/link extraction, caches, source collection, Unicode coordinates, CJK ranking, document and link-list navigation actions, version mismatches, schemas, release metadata, DCO parsing, and real MCP stdio exchanges. Network-free fixtures belong in `tests/`; do not replace these tests with informal model self-reports.

For a live integration check, run:

```sh
uv run python scripts/smoke.py
```

This requires internet access and a running SearXNG. Optional `--query` and repeated `--url` arguments select inputs. Provider failures are surfaced; an unavailable required page fails the check.

## IDE inspection

Use the project's `.venv` as the Python interpreter. Exclude `.venv`, `dist`, caches, and local captures from source inspection. Missing-import diagnostics from an unrelated interpreter are environment problems, not evidence of broken project imports.

Spelling and optional style suggestions are distinct from type or runtime errors. The enforced Ruff rule set is intentionally high-signal; add new rule families only after probing their effect on this codebase.

## Evaluating agent usability

Use blind, task-oriented prompts, controlled documents, fresh sessions, and fixed model/client settings. Compare actual tool calls and answers, not a model's self-report of call counts.

Test text continuation, link-list continuation, excerpt expansion, changed retained text/navigation, and retained-tail boundaries. Control cache state separately from origin changes: version guards check retained server state and do not force a fresh origin download.

Capture what the client actually sends to the model/provider. An advertised output schema is not proof that the same structure reached the model. Separate result bytes, cumulative prompt tokens, uncached tokens, generated tokens, latency, and task correctness.

Single runs do not establish universal improvements. `scripts/measure_contract_size.py` measures repeatable synthetic JSON sizes, not model tokens or end-to-end compute cost.

Rich tool descriptions are intentional and model-facing. Evaluate changes to them behaviorally rather than shortening them solely because they consume context.

## Publishable-tree hygiene

Keep captures, session IDs, local URLs, model configuration, private reviews, commercial research, secrets, and internal audit material outside the publishable source tree. Public documentation should contain reusable instructions rather than internal transcripts.

`.gitignore` does not remove already tracked files. Inspect the GitHub source tree separately from wheel/sdist contents. Never publish `.env`, local SearXNG settings, IDE state, virtual environments, captures, caches, or internal reports. Preserve LICENSE, NOTICE, and third-party attributions.

See [Releasing](RELEASING.md) for the tag-based publication process and [Tool and retrieval reference](REFERENCE.md) for the runtime contract.
