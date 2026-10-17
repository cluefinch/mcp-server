# Python TaskGroup: Tracing API Evolution Across Releases

This example demonstrates a research scenario in which the agent compared documentation across several Python releases, located relevant passages in large documents, and expanded specific sections to verify the details.

## Prompt

> Investigate how Python’s structured concurrency model evolved around asyncio.TaskGroup.
>
> Explain the behavioral differences between TaskGroup and asyncio.gather() when tasks fail or are cancelled, how ExceptionGroup fits into this model, and what design problem these changes were intended to solve.
>
> Also determine when these features entered Python, and whether the current documentation reflects any behavioral changes introduced in later Python releases.
>
> Support the answer with citations to public sources and clearly distinguish documented behavior from interpretation.

## 1. The Origins of TaskGroup and the Need for ExceptionGroup

The question called for more than a comparison of the current behavior of `asyncio.TaskGroup` and `asyncio.gather()`. The agent also needed to establish why Python introduced a new approach to concurrent task management. It began with several official sources: the general `asyncio` documentation, [PEP 654](https://peps.python.org/pep-0654/), and [What's New in Python 3.11](https://docs.python.org/3/whatsnew/3.11.html). In a single `research_collect` call, it supplied both known URLs and search queries targeting subsequent changes in behavior.

**From the session — the first `cluefinch_research_collect` call:**

```json
{
  "urls": [
    "https://docs.python.org/3/library/asyncio.html",
    "https://peps.python.org/pep-0654/",
    "https://docs.python.org/3/whatsnew/3.11.html"
  ],
  "queries": [
    "asyncio.TaskGroup cancellation ExceptionGroup behavior",
    "TaskGroup behavioral change whatsnew 3.12 3.13 3.14 asyncio"
  ],
  "topic": "Python asyncio TaskGroup structured concurrency and ExceptionGroup (PEP 654)",
  "max_sources": 7
}
```

The tool returned excerpts from all three documents supplied by URL. The PEP 654 excerpts included the motivation for handling multiple exceptions, while the Python 3.11 release notes contained the announcement of `TaskGroup`. The response also provided the positions of the excerpts within their respective documents, making it possible to read further where needed.

**From the `research_collect` response (selected sources, offsets, and diagnostic fields only):**

```json
{
  "sources": [
    {
      "url": "https://peps.python.org/pep-0654/",
      "excerpts": [
        {
          "start_char": 2595,
          "end_char": 3093
        }
      ]
    },
    {
      "url": "https://docs.python.org/3/whatsnew/3.11.html",
      "excerpts": [
        {
          "start_char": 18560,
          "end_char": 19051
        }
      ]
    }
  ],
  "gaps": [
    "query 'asyncio.TaskGroup cancellation ExceptionGroup behavior': unresponsive engines: brave, google, google cse, wikidata",
    "query 'asyncio.TaskGroup cancellation ExceptionGroup behavior': 0 results"
  ]
}
```

Search engines did not respond. A separate `web_search` attempt also returned an empty `results` array and reported `unresponsive_engines`. The agent saw that direct retrieval from known URLs was still working and continued with official primary sources rather than repeatedly attempting searches.

## 2. From the General asyncio Page to Task-Specific Documentation

The initial excerpts from the general [`asyncio.html`](https://docs.python.org/3/library/asyncio.html) page were not specific enough to compare task failures and cancellation: some were version notes unrelated to `TaskGroup` itself. The agent chose a more relevant source, the [Coroutines and tasks](https://docs.python.org/3/library/asyncio-task.html) reference, which documents both APIs.

**From the session — a direct `cluefinch_web_fetch` call:**

```json
{
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "max_chars": 20000
}
```

The retrieved section described `TaskGroup`, how it cancels other tasks when one fails, how exceptions are grouped, and how its behavior has changed across Python releases. It also covered `TaskGroup.cancel()`, a new API introduced in Python 3.15.

The page was longer than the requested excerpt. Along with the content, `web_fetch` returned the information needed to continue reading:

```json
{
  "total_chars": 54084,
  "next_start": 18279,
  "truncated": true,
  "content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
}
```

The agent had obtained the `TaskGroup` semantics it needed at this stage, but the `gather()` documentation lay beyond the portion retrieved. The `next_start` value provided a way to continue reading the same document, with `expected_content_hash` available to check that the subsequent request referred to the same extracted version. The agent returned to that continuation later.

## 3. Tracking Changes Across Releases: Find First, Then Read Further

The current API reference alone could not establish which behaviors had changed in later releases. The agent therefore turned to the historical What's New pages for Python 3.12, 3.13, and 3.14. Rather than reading these lengthy release notes from beginning to end, it supplied their URLs and a focused topic to `research_collect`.

**From the session — a `cluefinch_research_collect` call:**

```json
{
  "urls": [
    "https://docs.python.org/3/whatsnew/3.12.html",
    "https://docs.python.org/3/whatsnew/3.13.html",
    "https://docs.python.org/3/whatsnew/3.14.html"
  ],
  "topic": "asyncio TaskGroup ExceptionGroup cancellation behavior change",
  "max_sources": 5
}
```

One result pointed to a passage in What's New for Python 3.13 about simultaneous external and internal cancellation in `TaskGroup`. The tool returned not just the excerpt, but its location within the document and arguments for retrieving the surrounding context.

**From the `research_collect` response (one excerpt; other fields and sources omitted):**

```json
{
  "url": "https://docs.python.org/3/whatsnew/3.13.html",
  "excerpts": [
    {
      "text": "[`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup) when\nan external cancellation collides with an internal cancellation.\nFor example, when two task groups are nested\nand both experience an exception in a child task simultaneously,\nit was possible that the outer task group would hang,\nbecause its internal cancellation was swallowed by the inner task group.\nIn the case where a task group is cancelled externally\nand also must raise an",
      "start_char": 36983,
      "end_char": 37450,
      "expand": {
        "tool": "web_fetch",
        "arguments": {
          "url": "https://docs.python.org/3/whatsnew/3.13.html",
          "start_offset": 36983,
          "max_chars": 3000,
          "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
        }
      }
    }
  ]
}
```

The agent needed to expand this passage with `web_fetch` to read the full explanation of nested task groups and the preservation of cancellation counts. It used the `start_offset` and `expected_content_hash` from the preceding Cluefinch response:

```json
{
  "url": "https://docs.python.org/3/whatsnew/3.13.html",
  "start_offset": 36983,
  "max_chars": 3500,
  "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
}
```

The expanded passage explained how, under the earlier behavior, an inner task group could swallow the outer group’s internal cancellation. This gave the agent concrete evidence of a behavioral fix in Python 3.13, rather than merely an indication that the API had changed in that release.

For the other releases, `research_collect` also found relevant passages and reported `gaps` indicating that the extracted page text had been truncated at a character limit. The excerpts therefore served as entry points for more targeted reading, not as evidence that the entire change history had been exhaustively examined.

## 4. Recovering the Full Context of an Excerpt

Not every retrieved excerpt was sufficient to establish a precise conclusion. One passage from [What's New in Python 3.12](https://docs.python.org/3/whatsnew/3.12.html), concerning `ExceptionGroup` behavior, began in the middle of a sentence. The agent first opened the located passage using `web_fetch`:

```json
{
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "start_offset": 23416,
  "max_chars": 3000,
  "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
}
```

The text confirmed that a change had been made, but without the beginning of the sentence, the exact condition under which an exception would no longer be wrapped in an `ExceptionGroup` remained unclear.

The next clarification concerned the design rationale itself. The agent used `web_fetch` to read a specific section of [PEP 654](https://peps.python.org/pep-0654/) identified in its first `research_collect` call. That section described the difficulties of representing multiple exceptions and explained how the problem was connected to a task-spawning API inspired by **Trio nurseries**.

```json
{
  "url": "https://peps.python.org/pep-0654/",
  "start_offset": 2300,
  "max_chars": 3500,
  "expected_content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
}
```

To establish when `ExceptionGroup` and `except*` entered the language, the agent later returned to [What's New in Python 3.11](https://docs.python.org/3/whatsnew/3.11.html). After directly reading another section of that page, it used `research_collect` again, this time with a single known URL and a more specific topic:

```json
{
  "max_sources": 1,
  "topic": "exception groups PEP 654 except* language changes new features",
  "urls": [
    "https://docs.python.org/3/whatsnew/3.11.html"
  ]
}
```

The tool located the section titled **PEP 654: Exception Groups and `except*`**, rather than the more general references to `TaskGroup` elsewhere in the release notes.

Finally, the agent returned to the incomplete sentence in the Python 3.12 release notes. This time, it requested **a small section starting slightly before the previously identified position** to capture the missing beginning.

**From the session — a targeted `cluefinch_web_fetch` call:**

```json
{
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "start_offset": 22900,
  "max_chars": 700,
  "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
}
```

The response supplied the missing condition: the change applies when a `try-except*` construct handles an entire `ExceptionGroup` and then raises another exception. A request for just 700 characters was enough to recover the meaning; the agent did not need to start reading the page from the beginning.

## 5. Resuming a Read and Verifying the Current Python Version

While working through the release notes, the agent still needed the `gather()` specification for a direct comparison with `TaskGroup`. Two attempts to continue reading [`asyncio-task.html`](https://docs.python.org/3/library/asyncio-task.html) failed with `ReadError`. Both used the same position in the document, and neither returned the requested content.

**From one unsuccessful `web_fetch` response:**

```json
{
  "error": "HTTP request failed: ReadError: ",
  "hint": "retry later or prefer another source"
}
```

The agent continued pursuing the comparison. Later, it retried the same targeted request, retaining the original `start_offset` and `expected_content_hash`:

```json
{
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "start_offset": 18279,
  "max_chars": 20000,
  "expected_content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
}
```

This time, `web_fetch` returned the `gather()` section: how it behaves when one task fails, how `return_exceptions` works, how cancellation of `gather()` propagates to its child tasks, and why cancellation of an individual child does not cancel the others. The successful continuation remained tied to the original extracted version of the document:

```json
{
  "total_chars": 54084,
  "next_start": 36754,
  "truncated": true,
  "content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
}
```

One question remained: which Python release did the **current** documentation actually describe? The API reference retrieved earlier already linked to source code on the `3.15` branch and documented `TaskGroup.cancel()` as a Python 3.15 addition. Rather than assuming that the documentation still covered the previous stable release, the agent checked this explicitly.

It first used `research_collect` to find the announcement of the new `TaskGroup.cancel()` method in [What's New in Python 3.15](https://docs.python.org/3/whatsnew/3.15.html). Then it opened the [official Python downloads page](https://www.python.org/downloads/) directly with `web_fetch`:

```json
{
  "url": "https://www.python.org/downloads/",
  "max_chars": 900
}
```

The response listed `Python 3.15.0`, released on **October 9, 2026**. That allowed the agent to relate the current documentation to a specific release as of the investigation date, October 11, 2026.

For its final verification, the agent made another targeted `web_fetch` call to What's New in Python 3.11, returning to the passage documenting the original introduction of `TaskGroup` and the recommendation to use it in new code instead of directly combining `create_task()` and `gather()`.

## 6. Completing the Investigation

The agent then answered the original question, comparing the documented behavior of `TaskGroup` and `gather()`, the role of `ExceptionGroup`, the design motivation behind PEP 654, and the changes described in the Python 3.12–3.15 documentation. It explicitly distinguished conclusions it regarded as interpretation and cited the official sources it had examined.

What matters here is the progression of the research: the agent moved from initial excerpts to the appropriate API reference, then to selective reading of release notes, targeted recovery of missing context, and verification of the current release. At each step, it determined how much to read and whether another source was needed based on the evidence still missing.

## Why This Example Is Included in the Collection

This example demonstrates how the agent independently developed a research strategy for tracing an API's evolution across Python releases. To understand not only `TaskGroup`'s current behavior, but also why it was introduced and how it changed over time, the agent drew on sources serving different purposes: the original PEP, historical release notes, and the current API reference. It chose which sources to consult and the most effective way to read each one based on what still needed to be verified.

This also shows **Cluefinch's architecture in action**: the model made the research decisions—what to consult, how deeply to read, and what to verify next—while Cluefinch provided the tools to carry them out efficiently. When search engines failed to respond, the agent continued with known primary sources. When the current API reference mentioned changes introduced in Python 3.15, the agent extended the investigation to verify which release the documentation described.

The excerpts above are selected from a real session. The [full session export](./session-export.md) preserves the complete sequence of tool calls and responses, including retries and the agent's intermediate reasoning.

---

## Run Details

| Parameter | Value |
| --- | --- |
| Date | October 11, 2026 |
| Model | `Qwen3.8 27B UD IQ4_XS` (`Qwen3.8-27B-GGUF:UD-IQ4_XS`) |
| Quantization | `UD-IQ4_XS` |
| Runtime | Unsloth `0.1.900-beta` |
| Agent/client | OpenCode `1.19.0` (`Build` mode) |
| Cluefinch | `0.1.4`, commit `14383fb015576244889ea86c3e6815ad67196d8a` |
| Agent instructions | [`AGENTS.md`](https://github.com/cluefinch/mcp-server/blob/14383fb015576244889ea86c3e6815ad67196d8a/AGENTS.md), unmodified |
| Model settings | context length `65536`, KV cache `q4_0`, speculative decoding `MTP`; other settings in `metadata.yaml` |
| Tools used | `research_collect` (4), `web_fetch` (11), `web_search` (1) |

### Limitations of the Result

The search engines did not respond, so the investigation relied on official materials retrieved from known URLs. For several large pages, the tool reported that extracted text had been truncated at the character limit. The behavior of `TaskGroup` and `gather()` was examined through documentation, without running experimental Python code; the final answer's conclusions about compatibility across versions were the agent's interpretation, not the result of testing.

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
