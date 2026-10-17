# Research Examples

These examples show how AI agents use Cluefinch MCP to investigate real questions. They focus on the decisions agents make during research: which sources to consult, how deeply to read them, and how to adapt their approach as new information or constraints emerge.

- [SQLite WAL growth and checkpointing](./sqlite-wal-growth/) — An investigation into why SQLite WAL files can keep growing and how checkpointing affects their behavior.
- [Python TaskGroup: Tracing API Evolution Across Releases](./python-taskgroup-evolution/) — An investigation into the evolution of Python's structured concurrency model, including task failures, cancellation, and changes across releases.

Each example contains a `README.md` describing selected interactions from the research session, a `session-export.md` with the full normalized trace, and a `metadata.yaml` recording the environment and integrity information. The complete exports preserve the original tool responses and final answers; normalization is limited to the changes documented in each example's metadata.

Cluefinch provides research primitives; the agent researches.
