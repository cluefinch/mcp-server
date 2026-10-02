# Third-party components

Apache-2.0 applies to original Cluefinch MCP code. Dependencies,
separately obtained services, and retrieved website content keep their own terms.
This file is an informational index, not a replacement for upstream license texts.

## Distribution scope

The project wheel contains the `mcp_search` package and metadata. The source
archive additionally contains selected development files and a SearXNG Compose
example. Neither artifact is intended to contain SearXNG, Python itself, or
third-party dependency code. The package manager obtains dependencies separately.
Always inspect the actual release artifacts before publishing.

## Direct Python dependencies

The following versions were inspected in the local environment on 2026-09-13;
they are not pins imposed on downstream installations. `uv.lock` records the
development resolution; package installations can resolve different versions.

| Component      | Inspected version   | Declared license  | Upstream                                           |
|----------------|---------------------|-------------------|----------------------------------------------------|
| mcp            | 1.30.0              | MIT               | https://github.com/modelcontextprotocol/python-sdk |
| httpx          | 0.28.1              | BSD-3-Clause      | https://github.com/encode/httpx                    |
| httpcore       | 1.0.9               | BSD-3-Clause      | https://github.com/encode/httpcore                 |
| trafilatura    | 2.2.0               | Apache-2.0        | https://github.com/adbar/trafilatura               |
| beautifulsoup4 | 4.15.0              | MIT               | https://www.crummy.com/software/BeautifulSoup/     |
| rank-bm25      | 0.2.2               | Apache-2.0        | https://github.com/dorianbrown/rank_bm25           |
| pydantic       | 2.13.5              | MIT               | https://github.com/pydantic/pydantic               |

## Dependencies requiring particular attention when bundled

- `certifi` 2026.7.22 declares MPL-2.0. Preserve notices and provide the required
  source availability information if redistributing it.
- `tld` 0.13.2, reached through `trafilatura` and `courlan`, offers a choice of
  MPL-1.1, GPL-2.0, or LGPL-2.1 in its license notice. The intended route for a
  future project-managed redistribution is MPL-1.1; comply with that license,
  including covered source and notices. This does not relicense it to Apache-2.0.
- `numpy`, `lxml`, `cryptography`, and platform-specific runtimes may include
  additional native code, data and license notices. The top-level package license
  is not a complete inventory of a frozen executable or container.
- `regex` declares Apache-2.0 AND CNRI-Python; `tzdata`, Babel, and public suffix
  data may also carry data-specific notices. Preserve the actual installed files.

A bundled installer, wheelhouse, executable, container, or mirror needs a new
inventory of the exact shipped files and complete applicable license texts,
copyright notices, and source provision. This index alone does not satisfy that
work. Development tools are not automatically shipped with the core.

## SearXNG

The Compose example retrieves `searxng/searxng` from its upstream registry.
SearXNG is not relicensed by this project. Its upstream
[LICENSE](https://github.com/searxng/searxng/blob/master/LICENSE) contains GNU
Affero General Public License version 3. Preserve all applicable upstream notices
and verify version options and exceptions against the exact revision supplied.
The moving `master` link is an identification link, not a verified source offer
for any particular image. See [SearXNG compliance](docs/SEARXNG_COMPLIANCE.md).

## Retrieved content and names

Search results and fetched pages are not licensed under Apache-2.0 merely because
this program returns them. Site terms, copyright, database rights and personal
data obligations require their own assessment for the intended use. References
to other projects identify compatibility; they do not imply sponsorship or grant
trademark rights. Any paid support is provided by the contracting provider on
its own behalf, not on behalf of upstream contributors.
