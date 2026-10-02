# Roadmap

Cluefinch MCP 0.1.4 focuses the project around one stable boundary: the MCP server supplies bounded retrieval and research-navigation capabilities; the external agent decides what to investigate, what evidence matters, and what conclusions to draw.

Future candidates require separate design, compatibility, and security review:

- Lower-cost navigation actions without losing self-contained arguments or coordinate safety.
- More structured collection-gap reporting without implying topic completeness.
- An explicit origin-freshness policy distinct from retained-text version consistency.
- Additional document metadata and search pagination.
- Behavioral evaluation across multiple MCP clients/models for tool-description and contract changes.
- Additional deterministic multilingual ranking improvements beyond current CJK bigrams.

These are candidates, not release commitments. Do not rename existing fields, weaken network security, or add automatic research decisions as incidental cleanup.

Agent usability should be evaluated with controlled tasks and actual client payloads. No universal reduction in tool calls, context, latency, or model compute is promised.

See [Development](docs/DEVELOPMENT.md), [Technical reference](docs/REFERENCE.md), and [Releasing](docs/RELEASING.md).
