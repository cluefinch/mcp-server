# Tool and retrieval reference

This document records the detailed behavior of Cluefinch MCP's public retrieval contract. The README is the product and onboarding overview; this file is the technical reference for agents, client integrators, and contributors.

## MCP response contract

The server exposes typed input and output schemas. Successful structured payloads are returned both as JSON text content and MCP `structuredContent` with the same object shape. Expected tool failures return `error` and `hint` instead of success fields.

Tool descriptions are intentionally detailed and model-facing. They are part of the interface presented to an agent, not merely human documentation.

## `web_search`

`web_search` sends a query to the configured SearXNG JSON API. It supports:

- `query`
- `max_results`
- `engines`
- `language`
- `safe_search`
- `domain`
- `exclude_domains`

Search result URLs are conservatively normalized for deduplication. Search pagination is not implemented; `max_results` controls the returned result count. Domain operators depend on external search-engine support. A candidate can be passed to `web_fetch` for reading, to `web_links` for source navigation, or to `research_collect` as an explicit URL.

`unresponsive_engines` reports engines that SearXNG identified as unavailable. A successful search response with an empty list does not establish that the topic has no relevant sources.

Search requests are serialized. The process waits five seconds after each SearXNG request completes, including failed requests, before starting the next uncached search by default. Concurrent identical searches share the cache/lock path rather than issuing duplicate requests.

## `web_fetch`

`web_fetch` accepts an HTTP(S) URL and returns a Markdown slice of retained extracted text.

`start_offset` is an input specifying the starting Unicode-character offset, clamped to the retained text length. It is not a response field.

Important response fields include:

- `url`: final URL after redirects.
- `title`: extracted and length-bounded title.
- `content`: literal slice of retained extracted text.
- `next_start`: next offset when more retained text remains.
- `truncated`: whether more retained text remains after this slice.
- `text_truncated`: whether extraction exceeded the server's retained-text ceiling and a tail was discarded.
- `total_chars`: retained extracted-text length.
- `content_hash`: SHA-256 of the entire retained extracted text.
- `cache_hit`: whether the page came from the process-local fetch cache.
- `continuation`: optional ready-to-call action for the next slice.

Offsets count Python Unicode characters, not bytes and not UTF-16 code units.

### Continuation and version guards

A continuation action contains `{tool, arguments}` with the final URL, the exact next offset, the effective reading budget, and `expected_content_hash`. Creating an action makes no additional network request.

`continuation: null` means the retained text has ended. Manual continuation is also available by calling `web_fetch` with `start_offset=response.next_start`.

If `expected_content_hash` is provided and the currently retained text differs, the tool returns `content_changed` and does not return a stale-coordinate slice. Reacquire the source without the old hash before selecting new coordinates.

A matching hash is **not an origin-freshness guarantee**. Cached retained text can still match even if the origin changed after it was cached. The hash identifies the retained extraction version used for coordinate safety; it is not a remote validator.

### Extraction

Cluefinch accepts HTML/XHTML. Trafilatura performs the primary Markdown extraction with links and tables enabled, images and comments excluded, and the final redirected URL supplied as the base for resolving document links. Very small primary extractions fall back to stripped Beautiful Soup text.

The server does not render JavaScript. Readable-text adequacy is determined before the retained-text ceiling is applied. Low-text HTML is still retained as a shared processed page so `web_links` can use its ordinary anchors. `web_fetch` returns an expected insufficient-text error for such a page, and `research_collect` records a corresponding gap. This is a routing hint rather than proof that JavaScript is the reason readable content was unavailable.

The server does not parse PDFs or authenticated/private pages.

## `web_links`

`web_links` exposes bounded HTTP(S) navigation discovered from a fetched HTML page. It uses the same SSRF-protected download, redirect handling, processed-page cache and single-flight path as `web_fetch`, but link discovery and readable-text adequacy are independent: a short table-of-contents page can be useful to `web_links` even when `web_fetch` rejects it as too little readable text.

Important fields and arguments include:

- `url`: final fetched page URL.
- `same_origin`: optional filter; `true` keeps links with the same scheme, normalized hostname and effective port, `false` keeps cross-origin links, and `null` keeps both.
- `start_index` / `next_start_index`: zero-based positions in the retained list after origin filtering.
- `max_links`: response budget, 50 by default and at most 100.
- `links_hash`: SHA-256 version of the entire retained ordered link list before filtering or pagination.
- `links_truncated`: whether otherwise admissible navigation data was lost to page-level scan/count/byte/URL limits.
- `continuation`: ready-to-call `web_links` action carrying the next index, current filter, response budget and `expected_links_hash`.

Filtering happens before pagination. A `links_changed` result means the retained navigation list no longer matches the continuation version, so the old index is not used.

Each link contains a bounded best-effort `label`, resolved URL, `rel` tokens, fragment, `same_origin` and `same_document`. Labels are derived deterministically from anchor descendant text, then `aria-label`, `title`, image `alt`, or an empty string; CSS visibility is not evaluated. Duplicate URLs including the fragment retain their first position, can acquire a later non-empty label, and merge bounded unique `rel` tokens.

Relative links use the first `<base href>` in the parsed page if it resolves to an admissible URL within the URL limit; otherwise they use the final fetched URL, without trying later base elements. Origin and same-document comparisons remain anchored to the final fetched document URL.

Navigation identity uses HTTPX URL serialization after the existing scheme/hostname/port normalization. Unicode and corresponding percent-encoded components therefore share identity where HTTPX serializes them identically. Query ordering and encoded reserved characters are preserved: `%2F` is not decoded into `/`. Fragments remain part of link identity and are excluded only for same-document comparison. `same_document=true` does not imply that Cluefinch maps that HTML fragment to coordinates in extracted Markdown.

Discovery does not follow links, perform DNS lookups for their destinations, or claim that they are safe or reachable. It performs only local parsing and normalization and rejects unsupported schemes, credentials and malformed forms. A selected link receives the full existing SSRF validation only when it is subsequently fetched.

The server retains at most 512 links per page, scans at most 4096 anchor elements, and bounds retained navigation data to 128 KiB of compact UTF-8 JSON-equivalent payload. URLs use the same 8192-character ceiling accepted by the other retrieval tools. These are fixed safety ceilings rather than crawler controls.

### Agent interpretation rules

`web_links` is most useful after a strong source has already been identified but the correct internal page is not yet known. Prefer it over another search when the desired chapter, appendix, next page, reference, or related document is plausibly exposed by the current page.

A returned URL is navigation data, not evidence that the destination exists, is reachable, is safe to fetch, or belongs to the same organization. `same_origin` is a technical origin comparison, not a “same site” or ownership assertion. Cross-origin links can be valuable primary sources and should not be hidden by default.

`links_truncated` and `continuation` describe different conditions. A continuation means additional retained links are available. `links_truncated=true` means some otherwise admissible navigation data was not retained because a hard page-level resource ceiling was reached; continuation cannot recover that lost data.

`links_hash` is independent from `content_hash`. Use `expected_links_hash` only to protect link-list indices. Use `expected_content_hash` only to protect retained-text coordinates. Neither hash forces an origin refresh or proves that the remote page has not changed since the cache entry was created.

## `research_collect`

`research_collect` accepts:

- explicit `urls`
- search `queries`
- an optional `topic` used for excerpt ranking
- `max_sources`
- optional search settings

`topic` alone does not initiate a search.

Explicit URLs are attempted first. If they fill `max_sources`, no search request is made. Remaining candidate slots are shared round-robin between query variants. `max_sources` limits attempted candidates; it does not guarantee that many successful sources.

Explicit URLs and the final candidate selection are deduplicated by exact URL string before fetching, so an invalid credential-bearing explicit URL does not suppress a later valid variant through cache-key normalization. Search results and each query's candidate pool also use conservative URL normalization for deduplication before fetching; this is not safety validation. Selected URLs undergo fetch validation, and successful sources are deduplicated by normalized final URL after redirects.

The server does not invent replacement queries or replacement sources when candidates fail.

### Sources

A source includes a stable `source_id`, final URL, bounded title/metadata, the retained `content_hash`, and literal excerpts.

`source_id` is `src_` plus the first 16 hexadecimal characters of the normalized final URL's SHA-256. It is stable across calls and restarts for that normalized URL, but it is not a document-version identifier.

`source_type` is a domain-based category, not a credibility score. Unrecognized domains are `unknown`.

### Excerpts and expansion

Excerpts are literal slices satisfying:

```text
excerpt.text == retained_text[excerpt.start_char:excerpt.end_char]
```

Long material is split into bounded passages and ranked with BM25. When there is no positive match, leading eligible passages are returned rather than generated summaries.

Latin/whitespace-delimited words use ordinary tokenization. CJK runs use deterministic overlapping bigrams; this improves substring relevance without claiming language-specific morphological segmentation. There is no lemmatization or semantic embedding model.

`heading` is local context, not a complete document outline.

An excerpt expansion action starts at the excerpt's `start_char`, includes the source `content_hash`, and uses a bounded default expansion budget. It can be adjusted by the client while preserving the hash guard.

### Gaps

Collection `gaps` report provider failures, blocked or unreadable sources, final-URL duplicates, and other bounded failure reasons. Empty gaps do not prove topic completeness. The agent remains responsible for deciding whether evidence is sufficient.

## Network and SSRF policy

Outbound fetching accepts only HTTP(S). It rejects URL credentials, malformed/scoped hosts, localhost names, private/local/reserved/shared/multicast addresses, unsafe mapped or transition addresses, and mixed safe/unsafe DNS answers.

Validation is repeated for redirects and immediately before the TCP connection. The transport connects to a validated numeric IP while preserving the original hostname for HTTP `Host`, TLS SNI, and certificate verification. Environment proxy inheritance is disabled.

Alternate numeric IPv4 host forms are resolved through the same DNS/IP policy rather than treated as implicitly public.

The fetcher requests gzip or identity encoding. Content length is bounded before/while reading, decompressed output is bounded, and incomplete or concatenated gzip members are rejected.

These controls are SSRF defenses. They do not filter prompt injection or establish that retrieved content is trustworthy.

## Fetch concurrency and extraction resources

Page downloads use a global concurrency limit and a per-host start-to-start interval. Requests to the same hostname do not overlap. Redirect transitions pass through the same limiter.

Concurrent identical page fetches share one in-flight retrieval after URL validation, including concurrent `web_fetch` and `web_links` calls for the same canonical page. Text and link extraction run in the bounded dedicated processing pool so parser work cannot consume an unbounded share of the event loop's default executor.

`DOWNLOAD_TIMEOUT` bounds the shared download operation, including limiter/semaphore waits, redirect validation and response reading. Initial URL validation before cache lookup and text/link extraction (including the extraction-slot wait) are outside this timeout. It is not an end-to-end tool deadline or a hard parser-thread deadline.

## Caches

Fetch and search caches are in-memory, per-process TTL/LRU caches. They do not persist across MCP server restarts and are not shared between processes.

Fetch cache keys use conservative URL normalization. Query parameter ordering is preserved because changing it could change URL semantics. Credentials and fragments do not become part of cache identity.

A cache hit avoids another HTTP request and the corresponding rate-limit wait. Page URL validation still happens before cache lookup and can involve DNS lookups.

## Configuration reference

All variables below are prefixed with `MCP_SEARCH_` when supplied to the MCP process.

| Setting | Default | Meaning |
| --- | ---: | --- |
| `SEARXNG_URL` | `http://127.0.0.1:8081` | SearXNG JSON endpoint |
| `ENGINES` | `google,google cse,brave,wikipedia,wikidata` | Allowed explicit engine subset advertised by Cluefinch; omitting `engines` uses the SearXNG instance defaults |
| `UA` | `Cluefinch/<version> (+https://github.com/cluefinch/mcp-server)` | Page-fetch User-Agent |
| `MAX_RESULTS` | `20` | Maximum search results |
| `MAX_SOURCES` | `10` | Maximum collection source attempts |
| `MAX_QUERIES` | `10` | Maximum collection query variants |
| `MAX_FETCH_CHARS` | `20,000` | Maximum characters returned by one page slice |
| `MAX_TEXT_CHARS` | `100,000` | Maximum retained extracted characters per page |
| `EXPAND_CHARS` | `3,000` | Default excerpt expansion budget |
| `MIN_EXTRACTED_CHARS` | `100` | Low-text extraction heuristic |
| `MAX_RESPONSE_BYTES` | `5,242,880` | Maximum decoded response bytes |
| `MAX_REDIRECTS` | `5` | Maximum redirect hops |
| `DOWNLOAD_TIMEOUT` | `60` seconds | Shared download timeout, including limiter waits and redirects; excludes initial validation and extraction |
| `EXTRACT_CONCURRENCY` | `2` | Maximum concurrent extraction jobs |
| `FETCH_CONCURRENCY` | `3` | Maximum concurrent page HTTP transitions across hosts |
| `HOST_INTERVAL` | `5` seconds | Minimum request-start spacing per hostname |
| `SEARCH_INTERVAL` | `5` seconds | Pause after each SearXNG request |
| `FETCH_TTL` | `600` seconds | Fetch-cache TTL |
| `SEARCH_TTL` | `300` seconds | Search-cache TTL |
| `CACHE_ENTRIES` | `500` | Maximum entries in each process-local cache |

Numeric deployment settings must be positive and finite where applicable. Restart the MCP process after changing settings.

`MCP_SEARCH_UA` changes only Cluefinch's page-download identity; it does not change SearXNG's own requests to upstream search engines.

The intervals above reduce request frequency but do not guarantee that a site will accept requests. Cluefinch does not currently enforce `robots.txt` or `Retry-After` and does not automatically retry failed downloads. Operators remain responsible for applicable provider/site policies.

## Input and metadata bounds

Tool schemas impose maximum lengths and item counts before unbounded input can enter retrieval work. Untrusted descriptive metadata such as titles, snippets, headings, engine names, errors, hints, and gaps is truncated to explicit limits before being returned.

Literal excerpt text and its offsets are not silently rewritten to satisfy metadata limits. The 8192-character URL ceiling applies to both the supplied string and HTTPX's serialized URL, including the fragment: it bounds a reusable MCP argument, not only the HTTP request-target. It is checked before fetch-cache lookup and at redirect transitions; discovered links use the same accounting. Oversized fetch URLs are rejected rather than truncated into a different destination, and oversized discovered links are omitted with `links_truncated=true`.

## Unsupported capabilities

Current scope does not include:

- JavaScript/browser rendering
- PDF extraction
- authenticated sessions
- CAPTCHA or paywall bypass
- arbitrary browser automation
- vector/embedding search
- autonomous query planning or evidence synthesis
- hosted SaaS or REST API
- telemetry

For product-level context and installation, return to the [README](../README.md).
