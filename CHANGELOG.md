# Changelog

Notable changes to Cluefinch MCP are recorded here.

## 0.1.4 — Unreleased

### Added

- `web_links` for navigating links exposed by fetched HTML pages, including bounded pagination and version checks.

### Improved

- Improved excerpt ranking for Chinese, Japanese, and Korean text.
- Page extraction now ignores HTML comments and resolves extracted links against the final redirected URL.
- Concurrent requests for the same page now share a single in-flight fetch.
- `research_collect` avoids unnecessary searches when explicit URLs already fill the source budget.

### Fixed

- Reserved IPv6 destinations are now rejected by the SSRF policy.
- Invalid explicit URLs no longer suppress later valid candidates that resolve to the same destination.

## 0.1.3

Initial published Cluefinch distribution with SearXNG search, SSRF-safe HTML retrieval, literal BM25 research excerpts, continuation/expansion actions, and MCP stdio entrypoints.
