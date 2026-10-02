## Summary

Describe what changes and why.

## Validation

- [ ] `uv sync --locked`
- [ ] `uv run ruff check mcp_search tests scripts`
- [ ] `uv run ruff format --check mcp_search tests scripts`
- [ ] `uv run pytest -q`
- [ ] Relevant security/contract behavior is covered by regression tests.

## Public contract

- [ ] Tool descriptions/schemas, documented behavior, and compatibility boundaries were reviewed if affected.
- [ ] No secrets, private URLs, captures, local configuration, or internal-only material are included.

## DCO

Every commit in this pull request must carry a matching Developer Certificate of Origin sign-off. Use `git commit -s` when creating commits; amend/rebase commits that are missing a sign-off.
