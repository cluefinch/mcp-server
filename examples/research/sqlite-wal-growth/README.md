# SQLite WAL growth and checkpointing

This example demonstrates a fairly complex research scenario in which the agent had to use different reading strategies to suit the characteristics of each source.

## Prompt

> Investigate why an SQLite database running in WAL mode can develop a large WAL file even while reads and writes continue to succeed.
>
> Explain what role long-lived read transactions can play, how checkpointing interacts with readers and writers, and under what conditions the WAL can be reused or truncated.
>
> Compare the practical behavior of the available checkpoint modes and determine what an application can do when the WAL keeps growing.
>
> Also identify any important limitations or edge cases that affect the conclusions.
>
> Support the answer with citations to public sources and clearly distinguish documented behavior from interpretation.

## Research walkthrough

The agent broke the original question into several related areas: how WAL works, how active read transactions affect checkpointing, how the checkpoint modes differ, and where practical recommendations have limitations. Each area called for a different level of detail from the documentation.

To establish the underlying mechanism, the agent already knew about SQLite's official [Write-Ahead Logging](https://www.sqlite.org/wal.html) documentation. Rather than searching for a URL it already had, it opened the page directly with `web_fetch`.

**From the session — the first `cluefinch_web_fetch` call:**

```json
{
  "url": "https://www.sqlite.org/wal.html",
  "max_chars": 20000
}
```

The first excerpt explained how a read transaction establishes its view of the WAL at an `end mark`, and why a checkpoint cannot always advance beyond that point. This gave the agent the basis for explaining *checkpoint starvation*: reads and writes continue to succeed while the WAL keeps growing.

The same document described other circumstances that can affect WAL size, including disabled automatic checkpoints and large write transactions. The agent therefore did not limit the investigation to a single suspected cause.

The general mechanism was now clear, but a practical answer required more specific documentation: the syntax of `PRAGMA wal_checkpoint`, automatic checkpointing, and the behavior of the C API.

One relevant source was [`pragma.html`](https://www.sqlite.org/pragma.html), a large reference page that would be inefficient to read from beginning to end just to locate a particular section.

The agent therefore chose a different approach: it passed several known URLs and search queries covering the remaining questions to `research_collect`, so it could locate relevant passages before reading them in full.

**From the session — a `cluefinch_research_collect` call:**

```json
{
  "urls": [
    "https://www.sqlite.org/pragma.html",
    "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
    "https://www.sqlite.org/c3ref/wal_checkpoint.html"
  ],
  "queries": [
    "PRAGMA wal_checkpoint PASSIVE FULL RESTART TRUNCATE modes behavior readers",
    "wal_autocheckpoint automatic checkpointing every 1000 pages writer",
    "journal_size_limit WAL mode truncate size of WAL file"
  ],
  "max_sources": 5
}
```

Cluefinch returned relevant excerpts from all three documents supplied by URL. Each excerpt came with its source, text, position within the extracted document, and arguments for a follow-up `web_fetch` call.

For example, the agent immediately received the location of the `wal_checkpoint` section within the much larger `pragma.html` page:

**From the `research_collect` response (only fields relevant to this example are shown):**

```json
{
  "text": "**PRAGMA** *schema.***wal\\_checkpoint(PASSIVE);**",
  "start_char": 87944,
  "end_char": 87993,
  "expand": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://www.sqlite.org/pragma.html",
      "start_offset": 87944,
      "max_chars": 3000,
      "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
    }
  }
}
```

The agent now knew where to find the relevant section and could retrieve it with surrounding context, without reading the reference from the beginning.

Meanwhile, the search queries submitted through `research_collect` returned no search results. The tool reported unresponsive search engines in its `gaps` field, even though all three documents supplied by explicit URL had been retrieved successfully. The agent also tried `web_search` to find discussions of the issue on the SQLite forum.

**From the session — the `cluefinch_web_search` request:**

```json
{
  "query": "sqlite forum WAL file keeps growing long-lived reader blocking checkpoint",
  "max_results": 8
}
```

**Response (limited to diagnostic fields):**

```json
{
  "results": [],
  "unresponsive_engines": ["brave", "google", "google cse"]
}
```

The `unresponsive_engines` field made it possible to distinguish search engines failing to respond from a search that simply found no relevant material. This let the agent recognize a limitation of the discovery stage without mistakenly concluding that suitable sources did not exist.

It adjusted its approach and continued working with SQLite's official documentation through direct retrieval and excerpt collection. The agent made no further standalone `web_search` calls.

The two documents required different reading approaches. The agent continued reading `wal.html` sequentially; for `pragma.html`, the offsets it had already identified allowed it to jump directly to the relevant section.

The initial `web_fetch` of `wal.html` had returned a 20,000-character excerpt along with the following metadata:

```json
{
  "total_chars": 30929,
  "next_start": 19949,
  "truncated": true,
  "content_hash": "5e84ac63b99e78226b7f0c473726d33a62a2eb40501b739c5657e1d1a7da50c7"
}
```

Knowing that it had not yet read the entire document, the agent continued from the supplied offset.

**From the session — the next `cluefinch_web_fetch` call:**

```json
{
  "url": "https://www.sqlite.org/wal.html",
  "start_offset": 19949,
  "max_chars": 20000,
  "expected_content_hash": "5e84ac63b99e78226b7f0c473726d33a62a2eb40501b739c5657e1d1a7da50c7"
}
```

`next_start` provided the continuation point, while `expected_content_hash` tied the follow-up request to the same version of the extracted document. There was no need to retrieve the beginning of the page again.

The continuation covered further WAL limitations, locking behavior, and a section on the *WAL-reset* bug — an important version-sensitive edge case that the agent included in its investigation.

For `pragma.html`, by contrast, `research_collect` had already located the `wal_checkpoint` section near offset `87944` in a document containing **90,797 characters**. Rather than use the suggested `expand` arguments verbatim, the agent moved the starting offset slightly earlier to capture a broader passage.

**From the session — a targeted `cluefinch_web_fetch` call:**

```json
{
  "url": "https://www.sqlite.org/pragma.html",
  "start_offset": 87400,
  "max_chars": 16000
}
```

That gave the agent the descriptions of `wal_autocheckpoint`, the `PRAGMA wal_checkpoint(...)` variants, and their return values — exactly the information needed for the next part of the investigation.

Notably, **the characteristics of the sources made different reading approaches necessary**, and the agent chose the most effective one for each:

- For `wal.html`, it read sequentially with continuation requests because the explanation was spread across the page.
- For `pragma.html`, it first located relevant passages with `research_collect` and then read the specific section with `web_fetch`, because the information it needed was confined to one part of a large reference document.

By this point, the agent had established the general mechanism behind WAL growth. More detailed questions remained: how the checkpoint modes differ in practice, when a WAL can be reused or truncated, what happens when checkpoints contend with writers, and how to interpret `SQLITE_BUSY`.

The agent moved from SQLite's overview documentation to more specialized references.

It first opened the [`sqlite3_wal_checkpoint_v2()`](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) page directly. The URL was already known, so there was no need for another search:

```json
{
  "url": "https://www.sqlite.org/c3ref/wal_checkpoint_v2.html",
  "max_chars": 14000
}
```

This page clarified how checkpoint locks, writer locks, and the busy handler interact. The agent then made another `research_collect` call to look for details about `journal_size_limit` and other constraints, obtaining a relevant passage from `pragma.html`.

After that, it fetched the [Checkpoint Mode Values](https://www.sqlite.org/c3ref/c_checkpoint_full.html) and [`sqlite3_wal_autocheckpoint()`](https://www.sqlite.org/c3ref/wal_autocheckpoint.html) references directly. These supplied further definitions of the checkpoint modes, conditions for truncating the WAL, and details of automatic checkpoints, which run in `PASSIVE` mode and are triggered by default at a threshold of 1,000 pages (unless SQLite was built with a different default).

Once it had gathered the necessary material, the agent produced its answer to the original prompt. It connected long-lived read transactions to stalled checkpoint progress, compared the checkpoint modes and practical ways to manage WAL size, identified limitations, and cited official sources. It also distinguished documented behavior from its own interpretations.

## Why this example is included

This example demonstrates how an agent can **deliberately change its reading strategy** as an investigation unfolds. At each stage, it identified what it needed to establish, took the characteristics of the source into account, and independently chose the most effective way to obtain the relevant information.

It also shows **Cluefinch's architecture in action**: the model makes the decisions, while the MCP server provides the research primitives the model needs to carry out its chosen strategy.

The example further illustrates how Cluefinch's diagnostic information helps an agent adapt its research strategy. When the search engines stopped responding, the agent could identify the nature of the problem and continue working with the primary sources it could still access.

The excerpts above are selected from a real session. The complete sequence of calls, tool responses, and intermediate reasoning is preserved in [`session-export.md`](./session-export.md).

---

## Run details

| Parameter | Value |
| --- | --- |
| Date | October 11, 2026 |
| Model | `Qwen3.8 27B UD IQ4_XS` (`Qwen3.8-27B-GGUF:UD-IQ4_XS`) |
| Quantization | `UD-IQ4_XS` |
| Runtime | Unsloth `0.1.900-beta` |
| Agent/client | OpenCode `1.19.0` (`Build` mode) |
| Cluefinch | `0.1.4`, commit `14383fb015576244889ea86c3e6815ad67196d8a` |
| Agent instructions | [`AGENTS.md`](https://github.com/cluefinch/mcp-server/blob/14383fb015576244889ea86c3e6815ad67196d8a/AGENTS.md), unmodified |
| Tools used | `web_fetch` (6), `research_collect` (2), `web_search` (1) |

### Limitations of the result

The final answer contains an error in its interpretation of the `FULL` checkpoint mode. The original answer is preserved without edits in the full session export. This run demonstrates the agent's research workflow with source material; it was not a load test of SQLite.

## Session integrity

- **Session export:** normalized
- **Final answer:** unedited
- **Tool outputs:** unedited
- **Redactions:** none
- **Normalizations:** per-turn elapsed timing was removed from assistant headings; the original Created/Updated timestamps were replaced with a single run date

No failed retrievals, model corrections, contradictory intermediate hypotheses, or inconvenient parts of the research process were removed.

## Files

- [`session-export.md`](./session-export.md) — normalized full session export
- [`metadata.yaml`](./metadata.yaml) — machine-readable setup and integrity metadata
- [`AGENTS.md` at the Cluefinch commit used for the run](https://github.com/cluefinch/mcp-server/blob/14383fb015576244889ea86c3e6815ad67196d8a/AGENTS.md)

Cluefinch provides research primitives; the agent researches.
