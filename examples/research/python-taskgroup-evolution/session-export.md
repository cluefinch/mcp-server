# TaskGroup, gather, and ExceptionGroup

**Session ID:** ses_ed6f4ef2bffeqwMkuAUiG1ZzNm
**Run date:** 2026-10-11

---

## User

Investigate how Python’s structured concurrency model evolved around asyncio.TaskGroup.
Explain the behavioral differences between TaskGroup and asyncio.gather() when tasks fail or are cancelled, how ExceptionGroup fits into this model, and what design problem these changes were intended to solve.
Also determine when these features entered Python, and whether the current documentation reflects any behavioral changes introduced in later Python releases.
Support the answer with citations to public sources and clearly distinguish documented behavior from interpretation. 

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

The user is asking for a research task about Python's structured concurrency model around asyncio.TaskGroup: behavioral differences between TaskGroup and gather on failure/cancellation, how ExceptionGroup fits in, design problems, when these features were introduced (Python 3.11), whether current docs reflect later changes (e.g., 3.12/3.13 changes — e.g., TaskGroup cancellation behavior, `asyncio.TaskGroup` in 3.11; changes like "TaskGroup now cancels remaining tasks when one fails" was already there from the start… let me think).

Key facts I know:
- asyncio.TaskGroup and ExceptionGroup were added in Python 3.11 (PEP 654 for exception groups, PEP 697? no — TaskGroup is not a PEP; it's documented in the asyncio docs. Actually there was discussion on python-asyncio mailing list / GH issue bpo-46820 "Add asyncio.TaskGroup").
- ExceptionGroup: PEP 654, Python 3.11. `except*` syntax (PEP 654). BaseExceptionGroup, ExceptionGroup classes in builtins.
- TaskGroup behavior: when a task fails with an exception, the group cancels all remaining tasks and raises ExceptionGroup at the await point of `async with`. If the enclosing scope is cancelled, the group cancels all child tasks and propagates CancelledError (in 3.11, if the group itself was cancelled… there were changes: in Python 3.12? Let me recall).

Known behavioral differences between TaskGroup and gather:
- gather: by default does not cancel other tasks when one fails; returns results list with exception at failed position; `return_exceptions=True` collects exceptions as values. Cancellation of the gather future cancels all child tasks (in 3.8+? actually cancellation propagation to children was added in 3.8 — bpo-37658: "asyncio.gather() now propagates cancellation to its children"? Let me recall: in Python 3.8, `gather` started cancelling remaining futures when the gather itself is cancelled (bpo-32929? hmm). Actually: gh-80241 / bpo-45761? I remember "asyncio.gather() now cancels all remaining tasks if it is cancelled" — that was Python 3.8 (bpo-32929?). Let me verify with docs during research.)
- TaskGroup: on first failure, cancels siblings and raises ExceptionGroup containing all exceptions (including the original). If the task group's enclosing scope is cancelled, children are cancelled; if a child was already failing… in 3.11 there was a subtle bug/behavior: when the outer cancellation arrives while a child has failed, TaskGroup raised BaseExceptionGroup? There were changes in 3.12: "asyncio.TaskGroup now raises ExceptionGroup instead of BaseExceptionGroup"? Hmm.

Actually I recall specific changes:
- Python 3.12 changelog: "asyncio.TaskGroup" — hmm, not sure.
- Python 3.13: asyncio changes… TaskGroup? There was gh-105467? Not sure.

Let me think about what's documented in the current docs (docs.python.org/3/library/asyncio.html):

TaskGroup section says something like: "If a task fails with an exception, this exception is propagated to the code awaiting the task group… all other tasks are cancelled." And: "If the enclosing scope is cancelled, all remaining tasks are cancelled and CancelledError is raised." Also note about `except*`.

Also there's a documented change in 3.12? Let me recall What's New in Python 3.12 asyncio section:
- "asyncio.TaskGroup" — I don't think it was listed.
- Actually, What's New 3.12 has: "The asyncio module… `asyncio.timeout()` context manager added (3.11)".

Hmm, what about changes to TaskGroup in later versions? There were bug fixes: gh-98514? Let me think of known issues:
- bpo/gh issue: "TaskGroup does not cancel tasks when the enclosing scope is cancelled" — fixed in 3.12? I recall a change: "asyncio.TaskGroup now cancels remaining tasks if the task group itself is cancelled while waiting for its children to complete"?

Actually, I remember this specific documented behavior change: Python 3.12 What's New says nothing about TaskGroup; but there was gh-104698? Hmm.

Better approach: do actual research with Cluefinch tools. The task explicitly asks for citations from public sources and to distinguish documented behavior from interpretation, plus "whether current docs reflect behavioral changes introduced in later Python releases." So I should fetch:
1. https://docs.python.org/3/library/asyncio.html (TaskGroup section) — current docs.
2. What's New in 3.11 (PEP 654 exception groups, asyncio.TaskGroup).
3. PEP 654 (exception groups).
4. Possibly the original bpo-46820 / GH issue for TaskGroup design rationale ("design problem these changes were intended to solve" — structured concurrency: ensuring all spawned tasks are awaited/cancelled, avoiding orphaned tasks; gather's fire-and-forget semantics leak exceptions and don't cancel siblings).
5. What's New in 3.12/3.13 asyncio sections for TaskGroup-related changes (e.g., gh-104698? or "TaskGroup now…").

I recall a specific documented change: Python 3.13 What's New asyncio section mentions `asyncio.TaskGroup`? Hmm, not sure. There was a fix in 3.12: "Fixed a bug where TaskGroup would raise BaseExceptionGroup instead of ExceptionGroup when the group was cancelled while a child task had failed"? Not confident — need to verify with docs.

Actually! I now recall: there's a documented change in Python 3.12: "asyncio.TaskGroup" — no… let me think about gh-98514 "TaskGroup: cancel remaining tasks when the enclosing scope is cancelled". Hmm.

I also remember that in 3.11, if you cancelled the task containing a TaskGroup while a child had already failed, the behavior was to raise BaseExceptionGroup? And there's a note in current docs: "If the task group is cancelled… CancelledError is raised." Current docs (3.13/3.14) say something like:

"If any of the tasks fails with an exception, this exception is propagated to the code awaiting the task group. All other tasks are cancelled and their exceptions (if any) are added to the ExceptionGroup." Hmm, not exact wording; need to fetch.

Also current docs have a note about `except*` usage example.

And I recall there was an actual change in 3.12: gh-104698? Let me stop guessing and research.

Plan:
1. web_search for "asyncio.TaskGroup" docs, PEP 654, What's New 3.11 asyncio TaskGroup.
2. Fetch current asyncio.html TaskGroup section (use web_links or fetch with offset; the page is huge — better to search within it). Use research_collect with queries and URLs: docs.python.org/3/library/asyncio.html, docs.python.org/3/whatsnew/3.11.html, peps.python.org/pep-0654/, possibly gh issue bpo-46820 (github.com/python/cpython/issues/… actually bpo-46820 is "Add asyncio.TaskGroup" — migrated to GH as python/cpython#93741? hmm, not sure).
3. Check What's New 3.12 and 3.13 for TaskGroup changes: docs.python.org/3/whatsnew/3.12.html, /3.13.html.

Let me start with parallel searches/fetches. Use research_collect with multiple queries + explicit URLs to gather bounded evidence efficiently.

Queries:
- "asyncio.TaskGroup" site docs.python.org
- PEP 654 exception groups
- What's New in Python 3.11 asyncio TaskGroup ExceptionGroup
- TaskGroup cancellation behavior change 3.12 OR 3.13

URLs to include directly:
- https://docs.python.org/3/library/asyncio.html (huge; research_collect will extract BM25 passages around "TaskGroup")
- https://peps.python.org/pep-0654/
- https://docs.python.org/3/whatsnew/3.11.html

Then follow up with web_fetch on specific sections if needed, and check 3.12/3.13 whatsnew for TaskGroup mentions (grep via research_collect queries).

Let me do this in a few rounds:

Round 1 (parallel):
- research_collect(urls=[asyncio.html, peps.python.org/pep-0654/, docs.python.org/3/whatsnew/3.11.html], topic="asyncio.TaskGroup ExceptionGroup structured concurrency", max_sources=5) — but asyncio.html is huge; BM25 will pick passages about TaskGroup. Good.
- web_search("What's New in Python 3.12 asyncio TaskGroup") and ("TaskGroup cancelled enclosing scope behavior change 3.13").

Actually, research_collect with explicit URLs: "explicit URLs consume source budget first." With max_sources=5 and 3 URLs, remaining slots go to queries if I provide them. Let me include a few queries too for coverage of later-version changes.

Round 2: fetch specific sections (TaskGroup section in asyncio.html via web_fetch with offset — need to find the offset; research_collect excerpts give offsets). Also fetch whatsnew/3.12.html and 3.13.html TaskGroup mentions.

Let me also recall known documented change I'm fairly confident about now: Python 3.12 What's New asyncio section includes: "asyncio.TaskGroup" — hmm, no. Let me think… What's New in 3.12 asyncio changes include:
- `asyncio.to_thread` (that was 3.9)
- `asyncio.timeout()` (3.11)
- 3.12: "The asyncio module now uses the new event loop policy by default"? No, that's 3.8/3.10 deprecation of get_event_loop…

I really can't recall TaskGroup in 3.12 whatsnew. But there was a bug fix: gh-98514? "TaskGroup.__aexit__ should not swallow CancelledError"? Hmm.

Actually, I now recall something specific! In Python 3.11, when the enclosing scope of a TaskGroup is cancelled while a child task has already failed with an exception, the group raised `BaseExceptionGroup` (because it combined CancelledError + Exception). And there was a change in… hmm, or maybe not.

Another documented change I recall: Python 3.13 What's New asyncio section mentions "asyncio.TaskGroup" — no…

OK, another one I'm fairly confident about: gh-104698? No. Let me just research; the docs will tell me. Current asyncio.html TaskGroup doc text (from memory of reading it):

```
class asyncio.TaskGroup
A task group allows running multiple tasks concurrently while ensuring that all of them are completed before proceeding further... 

If a task fails with an exception, this exception is propagated to the code awaiting the task group. All other tasks are cancelled and their exceptions (if any) are added to the ExceptionGroup.

If the enclosing scope is cancelled, all remaining tasks are cancelled and CancelledError is raised.
```

Hmm wait — actually I think current docs say something like: "If a task fails with an exception, this exception is propagated… All other tasks are cancelled." And there's a note about `except*`.

And I recall the 3.12 changelog entry (What's New in Python 3.12 → asyncio): "asyncio.TaskGroup now cancels remaining tasks if the task group itself is cancelled while waiting for its children to complete"? Not sure.

There's also a documented change in 3.14? Today's date in this environment: October 2026, so Python 3.14 was released October 2025 (3.14 final). Current docs.python.org/3 = 3.14 (or dev 3.15?). What's New in 3.14 asyncio section — I don't know its contents; need to check.

Given the environment date is October 2026, "current documentation" = Python 3.14 docs (docs.python.org/3). Should check whatsnew for 3.12, 3.13, 3.14 for TaskGroup-related changes.

Known: gh-105467? Let me stop guessing and research.

Also "design problem these changes were intended to solve": structured concurrency — the problem with gather is that it doesn't enforce completion of all tasks (fire-and-forget), exceptions from one task don't cancel others, cancellation semantics are inconsistent; TaskGroup ensures: (1) all spawned tasks complete or are cancelled before leaving the `async with` block; (2) failures propagate as ExceptionGroup so callers can handle multiple exceptions with except*; (3) no orphaned tasks. This is discussed in the bpo-46820 issue and in PEP 654's motivation, plus Raymond Hettinger / Guido discussions. Also "TaskGroups" blog post? There was a famous discussion: "Structured concurrency in Python" — maybe a PyCon talk by… The design rationale is documented in the asyncio docs intro ("The task group allows running multiple tasks concurrently while ensuring that all of them are completed before proceeding further") and in PEP 654.

OK let me execute research now.

Round 1 (parallel calls):
1. cluefinch_research_collect with urls=[https://docs.python.org/3/library/asyncio.html, https://peps.python.org/pep-0654/, https://docs.python.org/3/whatsnew/3.11.html], queries=["asyncio.TaskGroup cancellation ExceptionGroup", "TaskGroup behavioral change 3.12 3.13 3.14"], topic="Python asyncio TaskGroup structured concurrency ExceptionGroup", max_sources=6? cap is 10; let me use 7 to leave room for query results. Hmm, explicit URLs take priority: 3 URLs consume 3 slots; remaining 4 go round-robin across queries. OK.

2. cluefinch_web_search("What's New in Python 3.12 asyncio TaskGroup")
3. cluefinch_web_search("asyncio.TaskGroup cancelled enclosing scope behavior change whatsnew")

Then Round 2: fetch specific sections based on offsets found (TaskGroup section in asyncio.html via web_fetch with offset — need to find the offset; research_collect excerpts give offsets). Also fetch whatsnew/3.12.html and 3.13.html TaskGroup mentions.

Let me start.


**Tool: cluefinch_research_collect**

**Input:**
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

**Output:**
```
{
  "query_variants": [
    "asyncio.TaskGroup cancellation ExceptionGroup behavior",
    "TaskGroup behavioral change whatsnew 3.12 3.13 3.14 asyncio"
  ],
  "sources": [
    {
      "title": "asyncio — Asynchronous I/O",
      "url": "https://docs.python.org/3/library/asyncio.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "Changed in version 3.12.5: (also 3.11.10, 3.10.15, 3.9.20, and 3.8.20) Emits audit events.",
          "start_char": 3046,
          "end_char": 3136,
          "heading": "`asyncio` — Asynchronous I/O[¶](https://docs.python.org#module-asyncio)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/library/asyncio.html",
              "start_offset": 3046,
              "max_chars": 3000,
              "expected_content_hash": "3aa847db18f3a7f1dc2a9259d95ce6678e2827ad057bf1bbedd0af487c5e93e4"
            }
          }
        },
        {
          "text": "Changed in version 3.13: Uses PyREPL if possible, in which case [`PYTHONSTARTUP`](https://docs.python.org/using/cmdline.html#envvar-PYTHONSTARTUP) is\nalso executed. Emits audit events.",
          "start_char": 3138,
          "end_char": 3322,
          "heading": "`asyncio` — Asynchronous I/O[¶](https://docs.python.org#module-asyncio)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/library/asyncio.html",
              "start_offset": 3138,
              "max_chars": 3000,
              "expected_content_hash": "3aa847db18f3a7f1dc2a9259d95ce6678e2827ad057bf1bbedd0af487c5e93e4"
            }
          }
        },
        {
          "text": "asyncio is often a perfect fit for IO-bound and high-level\n**structured** network code.",
          "start_char": 353,
          "end_char": 440,
          "heading": "`asyncio` — Asynchronous I/O[¶](https://docs.python.org#module-asyncio)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/library/asyncio.html",
              "start_offset": 353,
              "max_chars": 3000,
              "expected_content_hash": "3aa847db18f3a7f1dc2a9259d95ce6678e2827ad057bf1bbedd0af487c5e93e4"
            }
          }
        }
      ],
      "source_id": "src_eb33d36da592855b",
      "text_truncated": false,
      "content_hash": "3aa847db18f3a7f1dc2a9259d95ce6678e2827ad057bf1bbedd0af487c5e93e4"
    },
    {
      "title": "PEP 654 – Exception Groups and except* | peps.python.org",
      "url": "https://peps.python.org/pep-0654/",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "```\ntry:\n    async with asyncio.TaskGroup() as g:\n        g.create_task(task1); g.create_task(task2)\nexcept* KeyError:\n    # handling KeyError here is meaningless, there's\n    # no context to do anything with it but to log it.\n```\nWhen a program handles a collection of exceptions that were aggregated into\nan exception group, it would not typically attempt to recover from any\nparticular failed operation, but will rather use the types of the errors to\ndetermine how they should impact the",
          "start_char": 48974,
          "end_char": 49464,
          "heading": "PEP 654 – Exception Groups and except\\*",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://peps.python.org/pep-0654/",
              "start_offset": 48974,
              "max_chars": 3000,
              "expected_content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
            }
          }
        },
        {
          "text": "[Programming Without ‘except \\*’](https://peps.python.org#programming-without-except) section.) Implementing a better task spawning API in asyncio, inspired by Trio\nnurseries [\\[13\\]](https://peps.python.org#id31), was the main motivation for this PEP.  That work is currently\nblocked on Python not having native language level support for exception\ngroups.\n- **Multiple failures when retrying an operation.** The Python standard\nlibrary’s `socket.create_connection` function may attempt to connect",
          "start_char": 2595,
          "end_char": 3093,
          "heading": "PEP 654 – Exception Groups and except\\*",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://peps.python.org/pep-0654/",
              "start_offset": 2595,
              "max_chars": 3000,
              "expected_content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
            }
          }
        },
        {
          "text": "```\n>>> eg = ExceptionGroup(\n...     \"one\",\n...     [\n...         TypeError(1),\n...         ExceptionGroup(\n...             \"two\",\n...              [TypeError(2), ValueError(3)]\n...         ),\n...         ExceptionGroup(\n...              \"three\",\n...               [OSError(4)]\n...         )\n...     ]\n... )\n>>> import traceback\n>>> traceback.print_exception(eg)\n  | ExceptionGroup: one (3 sub-exceptions)\n  +-+---------------- 1 ----------------\n    | TypeError: 1\n    +---------------- 2",
          "start_char": 9695,
          "end_char": 10184,
          "heading": "PEP 654 – Exception Groups and except\\*",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://peps.python.org/pep-0654/",
              "start_offset": 9695,
              "max_chars": 3000,
              "expected_content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
            }
          }
        }
      ],
      "source_id": "src_d5e76c64a196fa9d",
      "text_truncated": false,
      "content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
    },
    {
      "title": "What’s New In Python 3.11",
      "url": "https://docs.python.org/3/whatsnew/3.11.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "primarily intended for internal use,\nnotably by [`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup).",
          "start_char": 21886,
          "end_char": 22017,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.11.html",
              "start_offset": 21886,
              "max_chars": 3000,
              "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
            }
          }
        },
        {
          "text": "- Added the [`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup) class,\nan [asynchronous context manager](https://docs.python.org/reference/datamodel.html#async-context-managers) holding a group of tasks that will wait for all of them upon exit.\nFor new code this is recommended over using [`create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.create_task) and [`gather()`](https://docs.python.org/library/asyncio-task.html#asyncio.gather)",
          "start_char": 18560,
          "end_char": 19051,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.11.html",
              "start_offset": 18560,
              "max_chars": 3000,
              "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
            }
          }
        },
        {
          "text": "[`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup).\n- Added the [`asyncio.StreamWriter.start_tls()`](https://docs.python.org/library/asyncio-stream.html#asyncio.StreamWriter.start_tls) method for\nupgrading existing stream-based connections to TLS.\n(Contributed by Ian Good in [bpo-34975](https://bugs.python.org/issue?@action=redirect&bpo=34975).)\n- Added raw datagram socket functions to the event loop:",
          "start_char": 20492,
          "end_char": 20929,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.11.html",
              "start_offset": 20492,
              "max_chars": 3000,
              "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
            }
          }
        }
      ],
      "source_id": "src_92b1f7451b43e174",
      "text_truncated": true,
      "content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
    }
  ],
  "gaps": [
    "query 'asyncio.TaskGroup cancellation ExceptionGroup behavior': unresponsive engines: brave, google, google cse, wikidata",
    "query 'asyncio.TaskGroup cancellation ExceptionGroup behavior': 0 results",
    "query 'TaskGroup behavioral change whatsnew 3.12 3.13 3.14 asyncio': unresponsive engines: brave, google, google cse, wikidata",
    "query 'TaskGroup behavioral change whatsnew 3.12 3.13 3.14 asyncio': 0 results",
    "https://docs.python.org/3/whatsnew/3.11.html: extracted text truncated by character limit"
  ]
}
```

**Tool: cluefinch_web_search**

**Input:**
```json
{
  "query": "What's New in Python 3.12 asyncio TaskGroup change",
  "max_results": 8
}
```

**Output:**
```
{
  "results": [],
  "unresponsive_engines": [
    "brave",
    "google",
    "google cse"
  ],
  "query_used": "What's New in Python 3.12 asyncio TaskGroup change",
  "cached": false
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

The search engine is mostly unresponsive (brave, google, google cse are all down). Only the wikipedia/wikidata engines might work. So I should rely on direct fetching of known URLs:

1. asyncio.html — need to find the TaskGroup section. The page is huge. research_collect only returned a few excerpts (BM25 picked weird passages). Better approach: use web_fetch with offsets, but I don't know where TaskGroup is located within the retained text. Alternative: fetch https://docs.python.org/3/library/asyncio-task.html — this is the asyncio task module page that contains the full documentation for TaskGroup! Yes, docs.python.org/3/library/asyncio-task.html has sections for "Task", "gather()", and "TaskGroup". Much smaller page.

2. PEP 654 — already fetched excerpts; might expand a bit more around motivation (offset ~2595) to get the exact wording of the design rationale.

3. whatsnew/3.11.html — got an excerpt about TaskGroup being added in 3.11 ("Added the TaskGroup class... For new code this is recommended over using create_task() and gather()"). Good. Also need the PEP 654 exception groups entry from whatsnew 3.11 (the "Exception Groups" section).

4. Check for later changes: fetch whatsnew/3.12.html, 3.13.html, 3.14.html and look for mentions of TaskGroup. These pages are large; use research_collect with urls + queries? The search engine is down so the query won't work, but explicit URLs will be fetched and BM25 will rank excerpts by topic — if I set the topic to "TaskGroup", it should surface TaskGroup-related passages within those pages. Let me try: research_collect(urls=[whatsnew/3.12.html, whatsnew/3.13.html, whatsnew/3.14.html], topic="asyncio.TaskGroup ExceptionGroup cancellation behavior change", max_sources=5). BM25 ranks excerpts by the topic; if there are no TaskGroup mentions, it'll return other asyncio-related stuff — I can check whether any excerpt mentions TaskGroup.

Also fetch asyncio-task.html directly with web_fetch (probably ~30-40k chars; the TaskGroup section is near the end). Fetch with max_chars=20000 and continue if needed. Actually, let me first preview to get a sense of size: fetch with max_chars=20000 from offset 0 — but I need the TaskGroup part which is at the tail. Hmm, web_fetch returns from start_offset; continuation gives next_start. The page might be ~50k chars retained. Let me just fetch and continue as needed.

Also, for gather's cancellation behavior: asyncio-task.html documents gather with a note like "Changed in version 3.8: ..."? Actually the documented change is: "If gather() is cancelled, all submitted awaitables that have not completed yet are also cancelled." — I think this was added in Python 3.8 (bpo-32929? or gh). Let me verify from the page text.

Also for TaskGroup's later changes: I recall a specific documented change in 3.12: "asyncio.TaskGroup" hmm. Anyway, let me check whatsnew pages via research_collect with topic ranking.

Round 2 (parallel):
- web_fetch https://docs.python.org/3/library/asyncio-task.html max_chars=20000 (start 0) — then continue to the tail if needed. Actually, to save context, I could fetch from a later offset... but I don't know the size. Let me just fetch with 20000 and see how it goes.
- research_collect(urls=[whatsnew/3.12.html, whatsnew/3.13.html, whatsnew/3.14.html], topic="asyncio TaskGroup ExceptionGroup cancellation", max_sources=5) — no queries (search is down anyway).

Wait: does docs.python.org/3 point to the latest stable version? As of October 2026, Python 3.14 was released in October 2025; 3.15 might be in beta (released October 2026?). Actually, Python 3.15's release is scheduled for October 2026 — today is October 11, 2026, so 3.15 might have just been released or be about to be! docs.python.org/3 typically points to the latest stable version (3.14 until 3.15 final). The asyncio.html I fetched has a "Changed in version 3.13" note and audit events for 3.12.5 — consistent with 3.14-era docs. Let me check what /3 points to... the page title is just "asyncio". I can verify by checking whatsnew/3.14.html existence, or fetching https://docs.python.org/3/about.html? Simpler: fetch https://docs.python.org/en/3.14/library/asyncio-task.html and compare hashes with /3 — if identical, then /3 == 3.14. That's a good verification step for "does the current documentation reflect later changes".

Let me run round 2 now.


Search engines are mostly down (only direct fetches work), so I'll go straight to the canonical docs pages.



**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "max_chars": 20000
}
```

**Output:**
```
{
  "title": "Coroutines and tasks",
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "content": "# Coroutines and tasks[¶](https://docs.python.org#coroutines-and-tasks)\n\nThis section outlines high-level asyncio APIs to work with coroutines and Tasks.\n\n**Source code:** [Lib/asyncio/coroutines.py](https://github.com/python/cpython/tree/3.15/Lib/asyncio/coroutines.py)\n\n[Coroutines](https://docs.python.org/glossary.html#term-coroutine) declared with the async/await syntax is the\npreferred way of writing asyncio applications.  For example, the following\nsnippet of code prints “hello”, waits 1 second,\nand then prints “world”:\n\n```\n>>> import asyncio\n>>> async def main():\n...     print('hello')\n...     await asyncio.sleep(1)\n...     print('world')\n>>> asyncio.run(main())\nhello\nworld\n```\nNote that simply calling a coroutine will not schedule it to be executed:\n\n```\n>>> main()\n<coroutine object main at 0x1053bb7c8>\n```\nTo actually run a coroutine, asyncio provides the following mechanisms:\n\n- The [`asyncio.run()`](https://docs.python.org/asyncio-runner.html#asyncio.run) function to run the top-level\nentry point “main()” function (see the above example.)\n- Awaiting on a coroutine.  The following snippet of code will\nprint “hello” after waiting for 1 second, and then print “world”\nafter waiting for *another* 2 seconds:\nimport asyncio import time async def say\\_after(delay, what): await asyncio.sleep(delay) print(what) async def main(): print(f\"started at {time.strftime('%X')}\") await say\\_after(1, 'hello') await say\\_after(2, 'world') print(f\"finished at {time.strftime('%X')}\") asyncio.run(main()) Expected output: started at 17:13:52 hello world finished at 17:13:55\n- The [`asyncio.create_task()`](https://docs.python.org#asyncio.create_task) function to run coroutines\nconcurrently as asyncio [`Tasks`](https://docs.python.org#asyncio.Task).\nLet’s modify the above example and run two `say_after` coroutines *concurrently*:\nasync def main(): task1 = asyncio.create\\_task( say\\_after(1, 'hello')) task2 = asyncio.create\\_task( say\\_after(2, 'world')) print(f\"started at {time.strftime('%X')}\") # Wait until both tasks are completed (should take # around 2 seconds.) await task1 await task2 print(f\"finished at {time.strftime('%X')}\") Note that expected output now shows that the snippet runs 1 second faster than before: started at 17:14:32 hello world finished at 17:14:34\n- The [`asyncio.TaskGroup`](https://docs.python.org#asyncio.TaskGroup) class provides a more modern\nalternative to [`create_task()`](https://docs.python.org#asyncio.create_task).\nUsing this API, the last example becomes:\nasync def main(): async with asyncio.TaskGroup() as tg: task1 = tg.create\\_task( say\\_after(1, 'hello')) task2 = tg.create\\_task( say\\_after(2, 'world')) print(f\"started at {time.strftime('%X')}\") # The await is implicit when the context manager exits. print(f\"finished at {time.strftime('%X')}\") The timing and output should be the same as for the previous version.\n\nWe say that an object is an **awaitable** object if it can be used\nin an [`await`](https://docs.python.org/reference/expressions.html#await) expression.  Many asyncio APIs are designed to\naccept awaitables.\n\nThere are three main types of *awaitable* objects:\n**coroutines**, **Tasks**, and **Futures**.\n\nCoroutines\n\nPython coroutines are *awaitables* and therefore can be awaited from\nother coroutines:\n\n```\nimport asyncio\nasync def nested():\n    return 42\nasync def main():\n    # Nothing happens if we just call \"nested()\".\n    # A coroutine object is created but not awaited,\n    # so it *won't run at all*.\n    nested()  # will raise a \"RuntimeWarning\".\n    # Let's do it differently now and await it:\n    print(await nested())  # will print \"42\".\nasyncio.run(main())\n```\nImportant\n\nIn this documentation the term “coroutine” can be used for two closely related concepts:\n\n- a *coroutine function*: an [`async def`](https://docs.python.org/reference/compound_stmts.html#async-def) function;\n- a *coroutine object*: an object returned by calling a *coroutine function*.\n\nTasks\n\n*Tasks* are used to schedule coroutines *concurrently*.\n\nWhen a coroutine is wrapped into a *Task* with functions like\n[`asyncio.create_task()`](https://docs.python.org#asyncio.create_task) the coroutine is automatically\nscheduled to run soon:\n\n```\nimport asyncio\nasync def nested():\n    return 42\nasync def main():\n    # Schedule nested() to run soon concurrently\n    # with \"main()\".\n    task = asyncio.create_task(nested())\n    # \"task\" can now be used to cancel \"nested()\", or\n    # can simply be awaited to wait until it is complete:\n    await task\nasyncio.run(main())\n```\nFutures\n\nA [`Future`](https://docs.python.org/asyncio-future.html#asyncio.Future) is a special **low-level** awaitable object that\nrepresents an **eventual result** of an asynchronous operation.\n\nWhen a Future object is *awaited* it means that the coroutine will\nwait until the Future is resolved in some other place.\n\nFuture objects in asyncio are needed to allow callback-based code to be used with async/await.\n\nNormally **there is no need** to create Future objects at the\napplication level code.\n\nFuture objects, sometimes exposed by libraries and some asyncio APIs, can be awaited:\n\n```\nasync def main():\n    await function_that_returns_a_future_object()\n    # this is also valid:\n    await asyncio.gather(\n        function_that_returns_a_future_object(),\n        some_python_coroutine()\n    )\n```\nA good example of a low-level function that returns a Future object\nis [`loop.run_in_executor()`](https://docs.python.org/asyncio-eventloop.html#asyncio.loop.run_in_executor).\n\n**Source code:** [Lib/asyncio/tasks.py](https://github.com/python/cpython/tree/3.15/Lib/asyncio/tasks.py)\n\n- \nasyncio.create\\_task(*coro*, *\\**, *name=None*, *context=None*, *eager\\_start=None*, *\\*\\*kwargs*)[¶](https://docs.python.org#asyncio.create_task)\n- Wrap the *coro* [coroutine](https://docs.python.org#coroutine) into a [`Task`](https://docs.python.org#asyncio.Task) and schedule its execution.  Return the Task object.\nThe full function signature is largely the same as that of the\n[`Task`](https://docs.python.org#asyncio.Task) constructor (or factory) - all of the keyword arguments to\nthis function are passed through to that interface.\nAn optional keyword-only *context* argument allows specifying a\ncustom [`contextvars.Context`](https://docs.python.org/contextvars.html#contextvars.Context) for the *coro* to run in.\nThe current context copy is created when no *context* is provided.\nAn optional keyword-only *eager\\_start* argument allows specifying\nif the task should execute eagerly during the call to create\\_task,\nor be scheduled later. If *eager\\_start* is not passed the mode set\nby [`loop.set_task_factory()`](https://docs.python.org/asyncio-eventloop.html#asyncio.loop.set_task_factory) will be used.\nThe task is executed in the loop returned by [`get_running_loop()`](https://docs.python.org/asyncio-eventloop.html#asyncio.get_running_loop), [`RuntimeError`](https://docs.python.org/builtins/exceptions.html#RuntimeError) is raised if there is no running loop in\ncurrent thread.\nNote [`asyncio.TaskGroup.create_task()`](https://docs.python.org#asyncio.TaskGroup.create_task) is a new alternative\nleveraging structural concurrency; it allows for waiting\nfor a group of related tasks with strong safety guarantees.\nImportant Save a reference to the result of this function, to avoid a task disappearing mid-execution. The event loop only keeps weak references to tasks. A task that isn’t referenced elsewhere may get garbage collected at any time, even before it’s done. For reliable “fire-and-forget” background tasks, gather them in a collection: background\\_tasks = set() for i in range(10): task = asyncio.create\\_task(some\\_coro(param=i)) # Add task to the set. This creates a strong reference. background\\_tasks.add(task) # To prevent keeping references to finished tasks forever, # make each task remove its own reference from the set after # completion: task.add\\_done\\_callback(background\\_tasks.discard) Note that this approach never awaits the tasks, so if a task\nfails, its exception is never retrieved and asyncio logs a\n“Task exception was never retrieved” message when the task is\ngarbage collected.  To avoid this, use [`asyncio.TaskGroup`](https://docs.python.org#asyncio.TaskGroup) which keeps a strong reference to each task, awaits them and\npropagates their exceptions:\nasync with asyncio.TaskGroup() as tg: for i in range(10): tg.create\\_task(some\\_coro(param=i)) Added in version 3.7. Changed in version 3.8: Added the *name* parameter.\nChanged in version 3.11: Added the *context* parameter.\nChanged in version 3.14: Added the *eager\\_start* parameter by passing on all *kwargs*.\n\nTasks can easily and safely be cancelled.\nWhen a task is cancelled, [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError) will be raised\nin the task at the next opportunity.\n\nIt is recommended that coroutines use `try/finally` blocks to robustly\nperform clean-up logic. In case [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError)\nis explicitly caught, it should generally be propagated when\nclean-up is complete. `asyncio.CancelledError` directly subclasses\n[`BaseException`](https://docs.python.org/builtins/exceptions.html#BaseException) so most code will not need to be aware of it.\n\nThe asyncio components that enable structured concurrency, like\n[`asyncio.TaskGroup`](https://docs.python.org#asyncio.TaskGroup) and [`asyncio.timeout()`](https://docs.python.org#asyncio.timeout),\nare implemented using cancellation internally and might misbehave if\na coroutine swallows [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError). Similarly, user code\nshould not generally call [`uncancel`](https://docs.python.org#asyncio.Task.uncancel).\nHowever, in cases when suppressing `asyncio.CancelledError` is\ntruly desired, it is necessary to also call `uncancel()` to completely\nremove the cancellation state.\n\nTask groups combine a task creation API with a convenient and reliable way to wait for all tasks in the group to finish.\n\n- *class* asyncio.TaskGroup[¶](https://docs.python.org#asyncio.TaskGroup)\n- An [asynchronous context manager](https://docs.python.org/reference/datamodel.html#async-context-managers) holding a group of tasks.\nTasks can be added to the group using [`create_task()`](https://docs.python.org#asyncio.create_task).\nAll tasks are awaited when the context manager exits.\nAdded in version 3.11. \n  - \ncreate\\_task(*coro*, *\\**, *name=None*, *context=None*, *eager\\_start=None*, *\\*\\*kwargs*)[¶](https://docs.python.org#asyncio.TaskGroup.create_task)\n  - Create a task in this task group.\nThe signature matches that of [`asyncio.create_task()`](https://docs.python.org#asyncio.create_task).\nIf the task group is inactive (e.g. not yet entered,\nalready finished, or in the process of shutting down),\nwe will close the given `coro` and raise [`RuntimeError`](https://docs.python.org/builtins/exceptions.html#RuntimeError).\nChanged in version 3.13: Close the given coroutine if the task group is not active.\n  - \ncancel()[¶](https://docs.python.org#asyncio.TaskGroup.cancel)\n  - Cancel the task group. This is a non-exceptional, early exit of the task group’s lifetime – useful once the group’s goal has been met or its services no longer needed. [`cancel()`](https://docs.python.org#asyncio.Task.cancel) will be called on any tasks in the group that\naren’t yet done, as well as the parent (body) of the group.  The task group\ncontext manager will exit *without* [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError) being raised.\nIf `cancel()` is called before entering the task group, the group will be\ncancelled upon entry.  This is useful for patterns where one piece of\ncode passes an unused [`asyncio.TaskGroup`](https://docs.python.org#asyncio.TaskGroup) instance to another in order to have\nthe ability to cancel anything run within the group.\n`cancel()` is idempotent and may be called after the task group has\nalready exited.\nSome ways to use `cancel()`:\n    - call it from the task group body based on some condition or event\n    - pass the task group instance to child tasks via [`create_task()`](https://docs.python.org#asyncio.create_task), allowing a child\ntask to conditionally cancel the entire group\n    - pass the task group instance or bound `cancel()` method to some other task *before* opening the task group, allowing remote cancellation\nAdded in version 3.15.\n\nExample:\n\n```\nasync def main():\n    async with asyncio.TaskGroup() as tg:\n        task1 = tg.create_task(some_coro(...))\n        task2 = tg.create_task(another_coro(...))\n    print(f\"Both tasks have completed now: {task1.result()}, {task2.result()}\")\n```\nThe `async with` statement will wait for all tasks in the group to finish.\nWhile waiting, new tasks may still be added to the group\n(for example, by passing `tg` into one of the coroutines\nand calling `tg.create_task()` in that coroutine).  There is also opportunity to\nrequest termination of the entire task group with `tg.cancel()`, based on some condition.\nOnce the last task has finished and the `async with` block is exited,\nno new tasks may be added to the group.\n\nThe first time any of the tasks belonging to the group fails\nwith an exception other than [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError),\nthe remaining tasks in the group are cancelled.\nNo further tasks can then be added to the group.\nAt this point, if the body of the `async with` statement is still active\n(i.e., [`__aexit__()`](https://docs.python.org/reference/datamodel.html#object.__aexit__) hasn’t been called yet),\nthe task directly containing the `async with` statement is also cancelled.\nThe resulting `asyncio.CancelledError` will interrupt an `await`,\nbut it will not bubble out of the containing `async with` statement.\n\nOnce all tasks have finished, if any tasks have failed\nwith an exception other than [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError),\nthose exceptions are combined in an\n[`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup) or [`BaseExceptionGroup`](https://docs.python.org/builtins/exceptions.html#BaseExceptionGroup)\n(as appropriate; see their documentation)\nwhich is then raised.\n\nTwo base exceptions are treated specially:\nIf any task fails with [`KeyboardInterrupt`](https://docs.python.org/builtins/exceptions.html#KeyboardInterrupt) or [`SystemExit`](https://docs.python.org/builtins/exceptions.html#SystemExit),\nthe task group still cancels the remaining tasks and waits for them,\nbut then the initial `KeyboardInterrupt` or `SystemExit`\nis re-raised instead of [`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup) or [`BaseExceptionGroup`](https://docs.python.org/builtins/exceptions.html#BaseExceptionGroup).\n\nIf the body of the `async with` statement exits with an exception\n(so [`__aexit__()`](https://docs.python.org/reference/datamodel.html#object.__aexit__) is called with an exception set),\nthis is treated the same as if one of the tasks failed:\nthe remaining tasks are cancelled and then waited for,\nand non-cancellation exceptions are grouped into an\nexception group and raised.\nThe exception passed into `__aexit__()`,\nunless it is [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError),\nis also included in the exception group.\nThe same special case is made for\n[`KeyboardInterrupt`](https://docs.python.org/builtins/exceptions.html#KeyboardInterrupt) and [`SystemExit`](https://docs.python.org/builtins/exceptions.html#SystemExit) as in the previous paragraph.\nThere is an additional special case made only for the body of the\n`async with`: if it raises [`GeneratorExit`](https://docs.python.org/builtins/exceptions.html#GeneratorExit) and none of the\nother tasks raise exceptions that would be reported, then the\n`GeneratorExit` is reraised.\n\nTask groups are careful not to mix up the internal cancellation used to\n“wake up” their [`__aexit__()`](https://docs.python.org/reference/datamodel.html#object.__aexit__) with cancellation requests\nfor the task in which they are running made by other parties.\nIn particular, when one task group is syntactically nested in another,\nand both experience an exception in one of their child tasks simultaneously,\nthe inner task group will process its exceptions, and then the outer task group\nwill receive another cancellation and process its own exceptions.\n\nIn the case where a task group is cancelled externally and also must\nraise an [`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup), it will call the parent task’s\n[`cancel()`](https://docs.python.org#asyncio.Task.cancel) method. This ensures that a\n[`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError) will be raised at the next\n[`await`](https://docs.python.org/reference/expressions.html#await), so the cancellation is not lost.\n\nTask groups preserve the cancellation count\nreported by [`asyncio.Task.cancelling()`](https://docs.python.org#asyncio.Task.cancelling).\n\nChanged in version 3.13: Improved handling of simultaneous internal and external cancellations and correct preservation of cancellation counts.\n\n- *async* asyncio.sleep(*delay*, *result=None*)[¶](https://docs.python.org#asyncio.sleep)\n- Block for *delay* seconds.\nIf *result* is provided, it is returned to the caller\nwhen the coroutine completes.\n`sleep()` always suspends the current task, allowing other tasks\nto run.\nSetting the delay to 0 provides an optimized path to allow other tasks to run. This can be used by long-running functions to avoid blocking the event loop for the full duration of the function call. Example of coroutine displaying the current date every second for 5 seconds: import asyncio import datetime as dt async def display\\_date(): loop = asyncio.get\\_running\\_loop() end\\_time = loop.time() + 5.0 while True: print(dt.datetime.now()) if (loop.time() + 1.0) >= end\\_time: break await asyncio.sleep(1) asyncio.run(display\\_date()) Changed in version 3.10: Removed the *loop* parameter.",
  "total_chars": 54084,
  "next_start": 18279,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/library/asyncio-task.html",
      "start_offset": 18279,
      "max_chars": 20000,
      "expected_content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
    }
  }
}
```

**Tool: cluefinch_research_collect**

**Input:**
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

**Output:**
```
{
  "query_variants": [],
  "sources": [
    {
      "title": "What’s New In Python 3.12",
      "url": "https://docs.python.org/3/whatsnew/3.12.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "[`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup) and raises one other exception, that exception is no longer wrapped in an `ExceptionGroup`. Also changed in version 3.11.4. (Contributed by Irit\nKatriel in [gh-103590](https://github.com/python/cpython/issues/103590).)\n- The Garbage Collector now runs only on the eval breaker mechanism of the\nPython bytecode evaluation loop instead of object allocations. The GC can\nalso run when",
          "start_char": 23416,
          "end_char": 23881,
          "heading": "Other Language Changes[¶](https://docs.python.org#other-language-changes)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.12.html",
              "start_offset": 23416,
              "max_chars": 3000,
              "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
            }
          }
        },
        {
          "text": "[`asyncio`](https://docs.python.org/library/asyncio.html#module-asyncio):\n  - The child watcher classes `asyncio.MultiLoopChildWatcher`, `asyncio.FastChildWatcher`, `asyncio.AbstractChildWatcher` and `asyncio.SafeChildWatcher` are deprecated and\nwill be removed in Python 3.14.\n(Contributed by Kumar Aditya in [gh-94597](https://github.com/python/cpython/issues/94597).)\n  - `asyncio.set_child_watcher()`, `asyncio.get_child_watcher()`, `asyncio.AbstractEventLoopPolicy.set_child_watcher()` and",
          "start_char": 60544,
          "end_char": 61038,
          "heading": "Deprecated[¶](https://docs.python.org#deprecated)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.12.html",
              "start_offset": 60544,
              "max_chars": 3000,
              "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
            }
          }
        },
        {
          "text": "[`asyncio`](https://docs.python.org/library/asyncio.html#module-asyncio):\n  - The child watcher classes `asyncio.MultiLoopChildWatcher`, `asyncio.FastChildWatcher`, `asyncio.AbstractChildWatcher` and `asyncio.SafeChildWatcher` are deprecated and\nwill be removed in Python 3.14.\n(Contributed by Kumar Aditya in [gh-94597](https://github.com/python/cpython/issues/94597).)\n  - `asyncio.set_child_watcher()`, `asyncio.get_child_watcher()`, `asyncio.AbstractEventLoopPolicy.set_child_watcher()` and",
          "start_char": 77516,
          "end_char": 78010,
          "heading": "Pending removal in Python 3.14[¶](https://docs.python.org#pending-removal-in-python-3-14)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.12.html",
              "start_offset": 77516,
              "max_chars": 3000,
              "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
            }
          }
        }
      ],
      "source_id": "src_d05666e0f9768783",
      "text_truncated": true,
      "content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
    },
    {
      "title": "What’s New In Python 3.13",
      "url": "https://docs.python.org/3/whatsnew/3.13.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "[`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup) when\nan external cancellation collides with an internal cancellation.\nFor example, when two task groups are nested\nand both experience an exception in a child task simultaneously,\nit was possible that the outer task group would hang,\nbecause its internal cancellation was swallowed by the inner task group.\nIn the case where a task group is cancelled externally\nand also must raise an",
          "start_char": 36983,
          "end_char": 37450,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.13.html",
              "start_offset": 36983,
              "max_chars": 3000,
              "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
            }
          }
        },
        {
          "text": "[`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup),\nit will now call the parent task’s [`cancel()`](https://docs.python.org/library/asyncio-task.html#asyncio.Task.cancel) method.\nThis ensures that a [`CancelledError`](https://docs.python.org/library/asyncio-exceptions.html#asyncio.CancelledError) will be raised\nat the next [`await`](https://docs.python.org/reference/expressions.html#await), so the cancellation is not lost.\nAn added benefit of these changes is",
          "start_char": 37451,
          "end_char": 37947,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.13.html",
              "start_offset": 37451,
              "max_chars": 3000,
              "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
            }
          }
        },
        {
          "text": "[`asyncio.TaskGroup.create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup.create_task).\n(Contributed by Thomas Grainger in [gh-128307](https://github.com/python/cpython/issues/128307).)",
          "start_char": 39822,
          "end_char": 40037,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.13.html",
              "start_offset": 39822,
              "max_chars": 3000,
              "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
            }
          }
        }
      ],
      "source_id": "src_e9820dbd7cc8f8e6",
      "text_truncated": true,
      "content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
    },
    {
      "title": "What’s new in Python 3.14",
      "url": "https://docs.python.org/3/whatsnew/3.14.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "```\n -m asyncio pstree 12345\n└── (T) Task-1\n    └──  main example.py:13\n        └──  TaskGroup.__aexit__ Lib/asyncio/taskgroups.py:72\n            └──  TaskGroup._aexit Lib/asyncio/taskgroups.py:121\n                ├── (T) Sundowning\n                │   └──  album example.py:8\n                │       └──  TaskGroup.__aexit__ Lib/asyncio/taskgroups.py:72\n                │           └──  TaskGroup._aexit Lib/asyncio/taskgroups.py:121\n                │               ├── (T) TNDNBTG",
          "start_char": 29998,
          "end_char": 30480,
          "heading": "Asyncio introspection capabilities[¶](https://docs.python.org#asyncio-introspection-capabilities)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.14.html",
              "start_offset": 29998,
              "max_chars": 3000,
              "expected_content_hash": "9b85a4c5c2c0f4ca431e6e9d36bffb18e6bb4480a892513398c10cb2203c72c3"
            }
          }
        },
        {
          "text": "argument of the factory,\nand `context` may be `None`.\nThis affects the following function and methods:\n[`asyncio.create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.create_task), [`asyncio.loop.create_task()`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.loop.create_task), [`asyncio.TaskGroup.create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup.create_task).\n(Contributed by Thomas Grainger in",
          "start_char": 49251,
          "end_char": 49717,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.14.html",
              "start_offset": 49251,
              "max_chars": 3000,
              "expected_content_hash": "9b85a4c5c2c0f4ca431e6e9d36bffb18e6bb4480a892513398c10cb2203c72c3"
            }
          }
        },
        {
          "text": "```\nimport asyncio\nasync def play_track(track):\n    await asyncio.sleep(5)\n    print(f'🎵 Finished: {track}')\nasync def play_album(name, tracks):\n    async with asyncio.TaskGroup() as tg:\n        for track in tracks:\n            tg.create_task(play_track(track), name=track)\nasync def main():\n    async with asyncio.TaskGroup() as tg:\n        tg.create_task(\n          play_album('Sundowning', ['TNDNBTG', 'Levitate']),\n          name='Sundowning')\n        tg.create_task(",
          "start_char": 27607,
          "end_char": 28078,
          "heading": "Asyncio introspection capabilities[¶](https://docs.python.org#asyncio-introspection-capabilities)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.14.html",
              "start_offset": 27607,
              "max_chars": 3000,
              "expected_content_hash": "9b85a4c5c2c0f4ca431e6e9d36bffb18e6bb4480a892513398c10cb2203c72c3"
            }
          }
        }
      ],
      "source_id": "src_009bfe70f430076c",
      "text_truncated": true,
      "content_hash": "9b85a4c5c2c0f4ca431e6e9d36bffb18e6bb4480a892513398c10cb2203c72c3"
    }
  ],
  "gaps": [
    "https://docs.python.org/3/whatsnew/3.12.html: extracted text truncated by character limit",
    "https://docs.python.org/3/whatsnew/3.13.html: extracted text truncated by character limit",
    "https://docs.python.org/3/whatsnew/3.14.html: extracted text truncated by character limit"
  ]
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

Excellent progress. Main findings so far:

1. **Current docs (asyncio-task.html, /3 = Python 3.15 dev version? — the source code link points to `github.com/python/cpython/tree/3.15/Lib/asyncio/tasks.py`!)** Interesting point: the "Source code" link references the 3.15 branch. So docs.python.org/3 currently points to Python 3.15 (dev version) — wait, but today is October 11, 2026… hmm, actually if /3 shows a source link for 3.15 and "Added in version 3.15" for TaskGroup.cancel(), then docs.python.org/3 = Python 3.15 (either just released or dev). Hmm wait — but the earlier asyncio.html fetch had "Changed in version 3.13: Uses PyREPL..." which is consistent with any recent version. The source link `tree/3.15` strongly suggests /3 currently points to 3.15. Actually, docs.python.org/3 usually points to the latest *stable* release; if it's showing a 3.15 branch link and "Added in version 3.15", then either 3.15 is stable (released October 2026 — plausible! Python 3.14 was released on October 7, 2025, so 3.15 should be around October 2026; today is October 11, 2026 → 3.15 may have just been released a few days ago) or /3 points to dev version. Either way: the current docs include features up through 3.15.

Wait, but I should double-check whether /3 = 3.14 or 3.15. The source link says tree/3.15 — that's decisive for which branch the docs were built from. So "current documentation" includes:
- TaskGroup.cancel() — Added in version 3.15 (new API!)
- create_task eager_start parameter — Changed in version 3.14
- TaskGroup.create_task closes coroutine when group is inactive — Changed in version 3.13
- Improved handling of concurrent internal/external cancellation + preservation of cancellation count — Changed in version 3.13

2. **TaskGroup documentation (current)**: full behavioral spec obtained from the fetch above:
   - "The first time any task belonging to a group fails with an exception other than CancelledError, the remaining tasks in the group are cancelled."
   - The containing task is also cancelled; that CancelledError does not leak out of async with.
   - Once all tasks complete, non-cancellation exceptions are combined into ExceptionGroup or BaseExceptionGroup and raised.
   - Special handling for KeyboardInterrupt/SystemExit: re-raised instead of a group.
   - Body exception → treated the same as task failure; included in the group (except CancelledError); GeneratorExit special case.
   - Nested groups: inner processes its own exceptions, outer receives another cancellation.
   - External cancellation + ExceptionGroup to raise → calls parent's cancel() so cancellation isn't lost.
   - Preserves Task.cancelling() count.

3. **What's New 3.13** (asyncio section): "Improved handling of concurrent internal and external cancellations in TaskGroup… when two task groups are nested and both experience an exception in a child task simultaneously, the outer task group could hang because its internal cancellation was swallowed by the inner task group." Plus: "In cases where a task group is externally cancelled and also needs to raise an ExceptionGroup, it now calls the parent task's cancel() method… An added benefit of these changes is…" (need the rest — probably "Task.cancelling() count is preserved"). Let me expand that excerpt.

4. **What's New 3.12**: found a language change: "If an ExceptionGroup contains only one exception, it is no longer wrapped in an ExceptionGroup" — wait, the excerpt says "[ExceptionGroup] and raises one other exception, that exception is no longer wrapped in an ExceptionGroup. Also changed in version 3.11.4." Hmm, this is about `except*`/raise behavior: "If a try block containing except* clauses raises an exception…"? Actually I recall gh-103590: "Fix except* to not wrap single exceptions" — the change is: when re-raising from within an except* handler? Let me expand that excerpt for exact wording. This is a documented behavioral change related to ExceptionGroup in 3.12 (backported to 3.11.4).

5. **What's New 3.14**: asyncio introspection (`python -m asyncio pstree`), task factory changes affecting create_task/TaskGroup.create_task (eager_start, context=None allowed). Need a bit more detail on the task factory change — "argument of the factory, and context may be None. This affects the following functions and methods: asyncio.create_task(), loop.create_task(), TaskGroup.create_task()." That's enough; can cite it as an API surface change in 3.14 (task factory).

6. **What's New 3.11**: "Added the TaskGroup class, an asynchronous context manager holding a group of tasks that will wait for all of them upon exit. For new code this is recommended over using create_task() and gather()." Also need the PEP 654 exception groups entry from whatsnew 3.11 (language section: "Exception Groups" — added ExceptionGroup, BaseExceptionGroup, except* syntax per PEP 654). Let me expand around offset ~20492 in whatsnew/3.11.html where I saw a mention of "[ExceptionGroup]." Actually the excerpt at 20492 was about StreamWriter.start_tls with an ExceptionGroup link — that's probably "Added asyncio.StreamWriter… (Contributed by …)" hmm, no. Let me expand around there to check context; also search for PEP 654 in whatsnew 3.11 language section.

7. **PEP 654**: motivation excerpt: "Implementing a better task spawning API in asyncio, inspired by Trio nurseries [13], was the main motivation for this PEP." — great citation for design problem. Also need the gather comparison from PEP 654? PEP 654 has a section on why exception groups are needed; also mentions `asyncio.gather` limitations? Let me expand around offset 2595 (motivation) to get more context, and maybe find where it discusses TaskGroup design.

8. **gather() documentation**: need the current gather docs for comparison: "If gather() is cancelled, all submitted awaitables that have not completed yet are also cancelled." — I saw the first 18279 chars of asyncio-task.html; the gather section comes after sleep(). Let me continue fetching from offset 18279 to get the gather() docs.

Also need: when did gather start cancelling children on cancellation? The current gather docs probably say "Changed in version 3.8: …"? Hmm, actually I recall bpo-32929 was fixed in 3.8: "asyncio.gather() now cancels all remaining futures if it is cancelled" — hmm wait, that might have been 3.8 (gh-75714?). Let me check the gather section text; there may be a version note. If not, I can cite the current documented behavior without historical detail, or quickly check whatsnew/3.8.html for "gather".

Also, the design problem: PEP 654 motivation (Trio nurseries) + TaskGroup docs intro ("Task groups combine task creation API with a convenient and reliable way to wait for all tasks in the group") + create_task note about fire-and-forget pitfalls ("This approach never awaits the tasks, so if a task fails, its exception is never retrieved… To avoid this, use asyncio.TaskGroup"). Also bpo-46820 (original TaskGroup issue) — search engines are down; can I fetch github.com/python/cpython/issues/93741? Hmm, what's the GH number for bpo-46820? The bpo→GH migration: bpo-46820 → python/cpython#… not sure. Maybe skip; PEP 654 + docs are enough as public sources. Actually, I could try fetching https://github.com/python/cpython/issues/93741 to check if it's the TaskGroup issue — risky guess. Better: search "bpo-46820" via web_search with wikipedia engine? Engines are down except maybe wikidata/wikipedia. Let me not chase this; PEP 654 explicitly names the asyncio task spawning API as its main motivation, and that's a solid citation for design rationale.

Round 3 (parallel):
- web_fetch continuation of asyncio-task.html from offset 18279 (get gather() docs).
- Expand whatsnew/3.13 excerpt at 36983 with max_chars 3000 (full TaskGroup change text) — actually the two excerpts are contiguous (36983–37450 and 37451–37947); fetch from 36983 with max_chars ~3200 to cover both.
- Expand whatsnew/3.12 excerpt at 23416 with max_chars 3000 (ExceptionGroup single exception change).
- Expand PEP 654 motivation around offset 2595 — fetch from ~2300 with max_chars 3000 to get the full "Motivation" bullet list.

That's 4 parallel calls. Then maybe one more round: whatsnew/3.11 language section for PEP 654 entry (search within page). The earlier research_collect on whatsnew/3.11.html returned an excerpt at 20492 mentioning ExceptionGroup — let me expand that too to see what it says (might be "Added asyncio.StreamWriter.start_tls()"… no wait, the text was "[ExceptionGroup]. - Added the asyncio.StreamWriter.start_tls() method…" so the line before is something like "Added support for exception groups …"? Hmm. Actually in whatsnew 3.11's asyncio section there's: "- The new TaskGroup class…" and also "- Added asyncio.timeout()"… the ExceptionGroup mention at ~20492 might be part of a bullet about `asyncio.gather`? Let me expand to check.)

Also, for "when did these features enter Python":
- ExceptionGroup/BaseExceptionGroup/except*: PEP 654 → Python 3.11 (whatsnew 3.11 language section).
- TaskGroup: Python 3.11 (whatsnew 3.11 asyncio section, "Added in version 3.11").

Let me also verify the exact wording of the PEP 654 entry in whatsnew 3.11 — expand around offset 20492 with a wider window (start ~19800, max_chars 3000).

Round 3 calls:
1. web_fetch asyncio-task.html start_offset=18279 max_chars=20000 expected_content_hash=9408… → gather section.
2. web_fetch whatsnew/3.13.html start_offset=36983 max_chars=3500 hash 147c…
3. web_fetch whatsnew/3.12.html start_offset=23416 max_chars=3000 hash 2f30…
4. web_fetch peps.python.org/pep-0654/ start_offset=2300 max_chars=3500 hash d667…
5. web_fetch whatsnew/3.11.html start_offset=19800 max_chars=3000 hash ec49…

All independent — run in parallel.


I've obtained the current TaskGroup specification (note: `/3` currently points to Python 3.15, and `TaskGroup.cancel()` is documented as "Added in version 3.15"). Next, I'll fetch the documentation for `gather()`, along with the exact wording of the changes in each release.



**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "start_offset": 18279,
  "max_chars": 20000,
  "expected_content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
}
```

**Output:**
```
{
  "error": "HTTP request failed: ReadError: ",
  "hint": "retry later or prefer another source"
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/whatsnew/3.13.html",
  "start_offset": 36983,
  "max_chars": 3500,
  "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
}
```

**Output:**
```
{
  "title": "What’s New In Python 3.13",
  "url": "https://docs.python.org/3/whatsnew/3.13.html",
  "content": "[`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup) when\nan external cancellation collides with an internal cancellation.\nFor example, when two task groups are nested\nand both experience an exception in a child task simultaneously,\nit was possible that the outer task group would hang,\nbecause its internal cancellation was swallowed by the inner task group.\nIn the case where a task group is cancelled externally\nand also must raise an [`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup),\nit will now call the parent task’s [`cancel()`](https://docs.python.org/library/asyncio-task.html#asyncio.Task.cancel) method.\nThis ensures that a [`CancelledError`](https://docs.python.org/library/asyncio-exceptions.html#asyncio.CancelledError) will be raised\nat the next [`await`](https://docs.python.org/reference/expressions.html#await), so the cancellation is not lost.\nAn added benefit of these changes is that task groups now preserve\nthe cancellation count ([`cancelling()`](https://docs.python.org/library/asyncio-task.html#asyncio.Task.cancelling)).\nIn order to handle some corner cases, [`uncancel()`](https://docs.python.org/library/asyncio-task.html#asyncio.Task.uncancel) may now\nreset the undocumented `_must_cancel` flag\nwhen the cancellation count reaches zero.\n(Inspired by an issue reported by Arthur Tacca in [gh-116720](https://github.com/python/cpython/issues/116720).)\n- When [`TaskGroup.create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup.create_task) is called on an inactive [`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup), the given coroutine will be closed (which\nprevents a [`RuntimeWarning`](https://docs.python.org/builtins/exceptions.html#RuntimeWarning) about the given coroutine being\nnever awaited).\n(Contributed by Arthur Tacca and Jason Zhang in [gh-115957](https://github.com/python/cpython/issues/115957).)\n- The function and methods named `create_task` have received a new `**kwargs` argument that is passed through to the task constructor.\nThis change was accidentally added in 3.13.3,\nand broke the API contract for custom task factories.\nSeveral third-party task factories implemented workarounds for this.\nIn 3.13.4 and later releases the old factory contract is honored\nonce again (until 3.14).\nTo keep the workarounds working, the extra `**kwargs` argument still\nallows passing additional keyword arguments to [`Task`](https://docs.python.org/library/asyncio-task.html#asyncio.Task) and to custom task factories.\nThis affects the following function and methods:\n[`asyncio.create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.create_task), [`asyncio.loop.create_task()`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.loop.create_task), [`asyncio.TaskGroup.create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup.create_task).\n(Contributed by Thomas Grainger in [gh-128307](https://github.com/python/cpython/issues/128307).)\n\n### base64[¶](https://docs.python.org#base64)",
  "total_chars": 100000,
  "next_start": 40084,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": true,
  "content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/whatsnew/3.13.html",
      "start_offset": 40084,
      "max_chars": 3500,
      "expected_content_hash": "147c9f467f7f3ef7fa5fd03734bb9b3048eee0c91cbf34f4b0530fef5a7c52ae"
    }
  }
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "start_offset": 23416,
  "max_chars": 3000,
  "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
}
```

**Output:**
```
{
  "title": "What’s New In Python 3.12",
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "content": "[`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup) and raises one other exception, that exception is no longer wrapped in an `ExceptionGroup`. Also changed in version 3.11.4. (Contributed by Irit\nKatriel in [gh-103590](https://github.com/python/cpython/issues/103590).)\n- The Garbage Collector now runs only on the eval breaker mechanism of the\nPython bytecode evaluation loop instead of object allocations. The GC can\nalso run when [`PyErr_CheckSignals()`](https://docs.python.org/c-api/exceptions.html#c.PyErr_CheckSignals) is called so C extensions that\nneed to run for a long time without executing any Python code also have a\nchance to execute the GC periodically. (Contributed by Pablo Galindo in [gh-97922](https://github.com/python/cpython/issues/97922).)\n- All builtin and extension callables expecting boolean parameters now accept\narguments of any type instead of just [`bool`](https://docs.python.org/builtins/functions.html#bool) and [`int`](https://docs.python.org/builtins/functions.html#int).\n(Contributed by Serhiy Storchaka in [gh-60203](https://github.com/python/cpython/issues/60203).)\n- [`memoryview`](https://docs.python.org/builtins/stdtypes.html#memoryview) now supports the half-float type (the “e” format code).\n(Contributed by Donghee Na and Antoine Pitrou in [gh-90751](https://github.com/python/cpython/issues/90751).)\n- [`slice`](https://docs.python.org/builtins/functions.html#slice) objects are now hashable, allowing them to be used as dict keys and\nset items. (Contributed by Will Bradshaw, Furkan Onder, and Raymond Hettinger in [gh-101264](https://github.com/python/cpython/issues/101264).)\n- [`sum()`](https://docs.python.org/builtins/functions.html#sum) now uses Neumaier summation to improve accuracy and commutativity\nwhen summing floats or mixed ints and floats.\n(Contributed by Raymond Hettinger in [gh-100425](https://github.com/python/cpython/issues/100425).)\n- [`ast.parse()`](https://docs.python.org/library/ast.html#ast.parse) now raises [`SyntaxError`](https://docs.python.org/builtins/exceptions.html#SyntaxError) instead of [`ValueError`](https://docs.python.org/builtins/exceptions.html#ValueError) when parsing source code containing null bytes. (Contributed by Pablo Galindo\nin [gh-96670](https://github.com/python/cpython/issues/96670).)\n- The extraction methods in [`tarfile`](https://docs.python.org/library/tarfile.html#module-tarfile), and [`shutil.unpack_archive()`](https://docs.python.org/library/shutil.html#shutil.unpack_archive),\nhave a new a *filter* argument that allows limiting tar features than may be\nsurprising or dangerous, such as creating files outside the destination\ndirectory.\nSee [tarfile extraction filters](https://docs.python.org/library/tarfile.html#tarfile-extraction-filter) for details.\nIn Python 3.14, the default will switch to `'data'`.\n(Contributed by Petr Viktorin in [**PEP 706**](https://peps.python.org/pep-0706/).)\n- [`types.MappingProxyType`](https://docs.python.org/libra",
  "total_chars": 100000,
  "next_start": 26416,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": true,
  "content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/whatsnew/3.12.html",
      "start_offset": 26416,
      "max_chars": 3000,
      "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
    }
  }
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://peps.python.org/pep-0654/",
  "start_offset": 2300,
  "max_chars": 3500,
  "expected_content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
}
```

**Output:**
```
{
  "title": "PEP 654 – Exception Groups and except* | peps.python.org",
  "url": "https://peps.python.org/pep-0654/",
  "content": "which are detailed in a design\ndocument for an improved version, `MultiError2` [\\[3\\]](https://peps.python.org#id21).\nThat document demonstrates how difficult it is to create an effective API\nfor reporting and handling multiple errors without the language changes we\nare proposing (see also the [Programming Without ‘except \\*’](https://peps.python.org#programming-without-except) section.) Implementing a better task spawning API in asyncio, inspired by Trio\nnurseries [\\[13\\]](https://peps.python.org#id31), was the main motivation for this PEP.  That work is currently\nblocked on Python not having native language level support for exception\ngroups.\n- **Multiple failures when retrying an operation.** The Python standard\nlibrary’s `socket.create_connection` function may attempt to connect to\ndifferent addresses, and if all attempts fail it needs to report that to the\nuser. It is an open issue how to aggregate these errors, particularly when\nthey are different (see issue 29980 [\\[4\\]](https://peps.python.org#id22).)\n- **Multiple user callbacks fail.** Python’s `atexit.register()` function\nallows users to register functions that are called on system exit. If any of\nthem raise exceptions, only the last one is reraised, but it would be better\nto reraise all of them together (see `atexit` documentation [\\[5\\]](https://peps.python.org#id23).)\nSimilarly, the pytest library allows users to register finalizers which\nare executed at teardown. If more than one of these finalizers raises an\nexception, only the first is reported to the user. This can be improved with `ExceptionGroups`, as explained in this issue by pytest developer Ran Benita\n(see pytest issue 8217 [\\[6\\]](https://peps.python.org#id24).)\n- **Multiple errors in a complex calculation.** The Hypothesis library performs\nautomatic bug reduction (simplifying code that demonstrates a bug). In the\nprocess it may find variations that generate different errors, and\n(optionally) reports all of them (see the Hypothesis documentation [\\[7\\]](https://peps.python.org#id25).)\nAn `ExceptionGroup` mechanism as we are proposing here can resolve some of\nthe difficulties with debugging that are mentioned in the link above, and\nwhich are due to the loss of context/cause information (communicated\nby Hypothesis Core Developer Zac Hatfield-Dodds).\n- **Errors in wrapper code.** The Python standard library’s `tempfile.TemporaryDirectory` context manager\nhad an issue where an exception raised during cleanup in `__exit__` effectively masked an exception that the user’s code raised inside the context\nmanager scope. While the user’s exception was chained as the context of the\ncleanup error, it was not caught by the user’s except clause\n(see issue 40857 [\\[8\\]](https://peps.python.org#id26).) The issue was resolved by making the cleanup code ignore errors, thus\nsidestepping the multiple exception problem. With the features we propose\nhere, it would be possible for `__exit__` to raise an `ExceptionGroup` containing its own errors along with the user’s errors, and this would allow\nthe user to catch their own exceptions by their types.",
  "total_chars": 55053,
  "next_start": 5405,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://peps.python.org/pep-0654/",
      "start_offset": 5405,
      "max_chars": 3500,
      "expected_content_hash": "d6670dba69a52e57ce3c03486efdb8cdd6660fd62c47c64bbd7932fee6ac3f20"
    }
  }
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/whatsnew/3.11.html",
  "start_offset": 19800,
  "max_chars": 3200,
  "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
}
```

**Output:**
```
{
  "title": "What’s New In Python 3.11",
  "url": "https://docs.python.org/3/whatsnew/3.11.html",
  "content": "drew Svetlov in [gh-91218](https://github.com/python/cpython/issues/91218).)\n- Added the [`Barrier`](https://docs.python.org/library/asyncio-sync.html#asyncio.Barrier) class to the synchronization\nprimitives in the asyncio library, and the related [`BrokenBarrierError`](https://docs.python.org/library/asyncio-sync.html#asyncio.BrokenBarrierError) exception.\n(Contributed by Yves Duprat and Andrew Svetlov in [gh-87518](https://github.com/python/cpython/issues/87518).)\n- Added keyword argument *all\\_errors* to [`asyncio.loop.create_connection()`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.loop.create_connection) so that multiple connection errors can be raised as an [`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup).\n- Added the [`asyncio.StreamWriter.start_tls()`](https://docs.python.org/library/asyncio-stream.html#asyncio.StreamWriter.start_tls) method for\nupgrading existing stream-based connections to TLS.\n(Contributed by Ian Good in [bpo-34975](https://bugs.python.org/issue?@action=redirect&bpo=34975).)\n- Added raw datagram socket functions to the event loop:\n[`sock_sendto()`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.loop.sock_sendto), [`sock_recvfrom()`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.loop.sock_recvfrom) and [`sock_recvfrom_into()`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.loop.sock_recvfrom_into).\nThese have implementations in [`SelectorEventLoop`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.SelectorEventLoop) and [`ProactorEventLoop`](https://docs.python.org/library/asyncio-eventloop.html#asyncio.ProactorEventLoop).\n(Contributed by Alex Grönholm in [bpo-46805](https://bugs.python.org/issue?@action=redirect&bpo=46805).)\n- Added [`cancelling()`](https://docs.python.org/library/asyncio-task.html#asyncio.Task.cancelling) and [`uncancel()`](https://docs.python.org/library/asyncio-task.html#asyncio.Task.uncancel) methods to [`Task`](https://docs.python.org/library/asyncio-task.html#asyncio.Task).\nThese are primarily intended for internal use,\nnotably by [`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup).\n\n### contextlib[¶](https://docs.python.org#contextlib)\n\n### dataclasses[¶](https://docs.python.org#dataclasses)\n\n### datetime[¶](https://docs.python.org#datetime)",
  "total_chars": 100000,
  "next_start": 22180,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": true,
  "content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/whatsnew/3.11.html",
      "start_offset": 22180,
      "max_chars": 3200,
      "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
    }
  }
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

Good. What I currently have on hand:

- **What's New in 3.13** (asyncio): Full text of the TaskGroup cancellation fix — "Improved handling of concurrent internal and external cancellations... nested task groups could hang because the outer group's internal cancellation was swallowed by the inner group; now, when a group is externally cancelled while needing to raise an ExceptionGroup, it calls the parent task's cancel() so that CancelledError isn't lost; as an additional benefit, task groups preserve the cancellation count (cancelling()); uncancel() may reset _must_cancel." Also: TaskGroup.create_task on an inactive group closes the coroutine (gh-115957). Plus a note about **kwargs for create_task.
- **What's New in 3.12**: The excerpt starts mid-sentence: "[ExceptionGroup] and raises one other exception, that exception is no longer wrapped in an ExceptionGroup. Also changed in version 3.11.4." — I need the first half of this sentence (it's about `except*` / raise inside a handler). Let me fetch a bit before offset 23416 to get the full bullet point. Probably: "If a try block with except* clauses... raises an exception that is not caught by any except* clause, and it contains only one exception..." Hmm. Actually I think this change (gh-103590) was about `raise` inside an `except*` handler? Let me fetch from around 22800 to get the full bullet point.
- **PEP 654 motivation**: "Implementing a better task spawning API in asyncio, inspired by Trio nurseries [13], was the main motivation for this PEP." — got it. Plus other use cases (socket.create_connection retries, atexit, pytest finalizers, tempfile masking).
- **What's New in 3.11**: Barrier, all_errors on create_connection → ExceptionGroup, cancelling()/uncancel() "primarily intended for internal use, notably by TaskGroup." I still want the exact bullet point about PEP 654 from the language section of whatsnew 3.11 ("Exception Groups" — added except*, ExceptionGroup, BaseExceptionGroup). Let me search within whatsnew/3.11.html: fetch around the "Language Changes" section. The page is large; in the earlier research_collect excerpt at offset ~20492 there was a mention of ExceptionGroup (that turned out to be all_errors on create_connection). The PEP 654 language entry should be near the top of whatsnew/3.11.html, under "Summary – Release Highlights" or "New Features → Language". Let me fetch from offset ~0 with max_chars 2000 and look for it... Actually, the release highlights section usually says something like: "Exception groups (PEP 654)..." Hmm, I'm not sure if it's in the highlights. The language changes section has a bullet point: "- Added support for exception groups (PEP 654): ... except* ..." Let me fetch from offset ~3000–8000 to find it. Or use research_collect with topic "exception groups PEP 654 except*" on that URL — BM25 should rank the relevant bullet point. That's cheaper: one call, max_sources=1... but explicit URLs consume budget; no problem.

- **gather() documentation**: The continuation fetch failed (ReadError). Retry needed. gather section: after sleep(), then "asyncio.gather(*aws, return_exceptions=False)". Let me retry the same fetch. If it fails again, try webfetch tool or a different offset.

Also, I want to check whether the current docs for gather() mention cancellation propagation and version notes (e.g., "Changed in version 3.8"?). Hmm — actually now I recall: bpo-32929? No... The change where "gather cancels children when cancelled" was gh-75714? Let me check the actual text of the docs; if there's no version note, I'll just describe the current documented behavior.

Also worth checking: does the current gather() doc mention TaskGroup as a recommended alternative? The intro to asyncio-task.html already says "The asyncio.TaskGroup class provides a more modern alternative to create_task()." And whatsnew 3.11 says "For new code this is recommended over using create_task() and gather()." Good.

Round 4 (parallel):
1. Retry web_fetch on asyncio-task.html from offset 18279, max_chars 20000 (gather section).
2. research_collect(urls=[whatsnew/3.11.html], topic="exception groups PEP 654 except* language changes", max_sources=1) — to find the PEP 654 bullet point in whatsnew 3.11. Hmm, but BM25 on a truncated page... The earlier fetch of this page was text_truncated=true (character limit). research_collect's extraction may be limited; still, it should rank excerpts by topic. Let me try.
3. web_fetch on whatsnew/3.12.html from offset 22700, max_chars 900 — to get the first half of the ExceptionGroup bullet point (the excerpt started mid-sentence at 23416; fetch a window before it).

Wait — for #3, I need to know where the bullet starts. The excerpt text at 23416 begins with "[ExceptionGroup] and raises one other exception..." so the sentence probably starts around ~23200–23350: "...If an except* clause catches an ExceptionGroup and raises one other exception, that exception is no longer wrapped in an ExceptionGroup." Hmm, something like that. Let me fetch from 22900 with max_chars 800 to capture the start of the bullet point.


**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "start_offset": 18279,
  "max_chars": 20000,
  "expected_content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
}
```

**Output:**
```
{
  "error": "HTTP request failed: ReadError: ",
  "hint": "retry later or prefer another source"
}
```

**Tool: cluefinch_research_collect**

**Input:**
```json
{
  "max_sources": 1,
  "topic": "exception groups PEP 654 except* language changes new features",
  "urls": [
    "https://docs.python.org/3/whatsnew/3.11.html"
  ]
}
```

**Output:**
```
{
  "query_variants": [],
  "sources": [
    {
      "title": "What’s New In Python 3.11",
      "url": "https://docs.python.org/3/whatsnew/3.11.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "handling interrupts is undesirable.\n- [`MAKE_CELL`](https://docs.python.org/library/dis.html#opcode-MAKE_CELL), to create [Cell Objects](https://docs.python.org/c-api/cell.html#cell-objects).\n- [`CHECK_EG_MATCH`](https://docs.python.org/library/dis.html#opcode-CHECK_EG_MATCH) and `PREP_RERAISE_STAR`,\nto handle the [new exception groups and except\\*](https://docs.python.org#whatsnew311-pep654) added in [**PEP 654**](https://peps.python.org/pep-0654/).\n-",
          "start_char": 70637,
          "end_char": 71093,
          "heading": "New opcodes[¶](https://docs.python.org#new-opcodes)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.11.html",
              "start_offset": 70637,
              "max_chars": 3000,
              "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
            }
          }
        },
        {
          "text": "[**PEP 654**](https://peps.python.org/pep-0654/) introduces language features that enable a program\nto raise and handle multiple unrelated exceptions simultaneously.\nThe builtin types [`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup) and [`BaseExceptionGroup`](https://docs.python.org/builtins/exceptions.html#BaseExceptionGroup)\nmake it possible to group exceptions and raise them together,\nand the new",
          "start_char": 5402,
          "end_char": 5839,
          "heading": "PEP 654: Exception Groups and `except*`[¶](https://docs.python.org#pep-654-exception-groups-and-except)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.11.html",
              "start_offset": 5402,
              "max_chars": 3000,
              "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
            }
          }
        },
        {
          "text": "[`except*`](https://docs.python.org/reference/compound_stmts.html#except-star) syntax generalizes\n[`except`](https://docs.python.org/reference/compound_stmts.html#except) to match subgroups of exception groups.",
          "start_char": 5840,
          "end_char": 6050,
          "heading": "PEP 654: Exception Groups and `except*`[¶](https://docs.python.org#pep-654-exception-groups-and-except)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.11.html",
              "start_offset": 5840,
              "max_chars": 3000,
              "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
            }
          }
        }
      ],
      "source_id": "src_92b1f7451b43e174",
      "text_truncated": true,
      "content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
    }
  ],
  "gaps": [
    "https://docs.python.org/3/whatsnew/3.11.html: extracted text truncated by character limit"
  ]
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "start_offset": 22900,
  "max_chars": 700,
  "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
}
```

**Output:**
```
{
  "title": "What’s New In Python 3.12",
  "url": "https://docs.python.org/3/whatsnew/3.12.html",
  "content": "ntributed by Nikita Sobolev in [gh-100581](https://github.com/python/cpython/issues/100581).)\n- Exceptions raised in a class or type’s `__set_name__` method are no longer\nwrapped by a [`RuntimeError`](https://docs.python.org/builtins/exceptions.html#RuntimeError). Context information is added to the\nexception as a [**PEP 678**](https://peps.python.org/pep-0678/) note. (Contributed by Irit Katriel in [gh-77757](https://github.com/python/cpython/issues/77757).)\n- When a `try-except*` construct handles the entire [`ExceptionGroup`](https://docs.python.org/builtins/exceptions.html#ExceptionGroup) and raises one other exception, that exception is no longer wrapped in an `ExceptionGroup`. Also cha",
  "total_chars": 100000,
  "next_start": 23600,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": true,
  "content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/whatsnew/3.12.html",
      "start_offset": 23600,
      "max_chars": 700,
      "expected_content_hash": "2f3029469d983ceb0cc850965481e2cde0dae5621160f479ccd333a2e1abd028"
    }
  }
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

With this, I've obtained the full text of the bullet point for 3.12: "When a `try-except*` construct handles an entire `ExceptionGroup` and raises one other exception, that exception is no longer wrapped in an `ExceptionGroup`. Also changed in version 3.11.4." (gh-103590).

And the PEP 654 section of whatsnew 3.11: "PEP 654 introduces language features that enable a program to raise and handle multiple unrelated exceptions simultaneously. The builtin types ExceptionGroup and BaseExceptionGroup make it possible to group exceptions and raise them together, and the new except* syntax generalizes except to match subgroups of exception groups."

Still missing: the current documentation for gather() (the continuation fetch failed twice with ReadError — probably a transient network issue). Let me retry once more. If cluefinch keeps failing, I can use the webfetch tool against https://docs.python.org/3/library/asyncio-task.html and grep locally... but webfetch returns markdown to my context; the page is about 54k characters of retained text — too big? The webfetch tool might summarize it. Better approach: retry cluefinch's web_fetch once more (the error was a ReadError, so "retry later").

Also, I want to double-check whether /3 points to 3.15 or 3.14. Evidence: the source link in asyncio-task.html says `tree/3.15/Lib/asyncio/tasks.py`, and TaskGroup.cancel() is documented as "Added in version 3.15". So docs.python.org/3 = Python 3.15 (dev or just-released). Given that today is October 11, 2026, Python 3.15 was probably released around October 7–8, 2026 (3.14 was released on October 7, 2025; the annual cadence suggests early-to-mid October 2026). I can quickly verify by fetching https://docs.python.org/3/about.html or checking whatsnew/3.15.html for a release date... Actually, an easier way: fetch https://www.python.org/downloads/ — it lists the latest version and date. Let me do that to pin down "current documentation" precisely.

Also, regarding TaskGroup.cancel() in 3.15 — I should check whatsnew/3.15.html for its description (a new API added after 3.14). This is a documented behavioral addition: an explicit non-exceptional early exit. Let me fetch the asyncio section of whatsnew/3.15.html via research_collect with topic "TaskGroup cancel".

Round 5 (parallel):
1. Retry web_fetch on asyncio-task.html from offset 18279, max_chars 20000 (gather).
2. research_collect(urls=[https://docs.python.org/3/whatsnew/3.15.html], topic="asyncio TaskGroup cancel new API", max_sources=1) — wait, does whatsnew/3.15.html exist? If /3 = 3.15 dev, it should exist (dev docs include the in-progress whatsnew). Let me try; if 404, I'll know /3 is something else... but the source link says 3.15, so it should exist.
3. web_fetch https://www.python.org/downloads/ max_chars=800 — to confirm the latest release version/date.

Let me run these three in parallel.


**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "start_offset": 18279,
  "max_chars": 20000,
  "expected_content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
}
```

**Output:**
```
{
  "title": "Coroutines and tasks",
  "url": "https://docs.python.org/3/library/asyncio-task.html",
  "content": "\n\n- *awaitable* asyncio.gather(*\\*aws*, *return\\_exceptions=False*)[¶](https://docs.python.org#asyncio.gather)\n- Run [awaitable objects](https://docs.python.org#asyncio-awaitables) in the *aws* sequence *concurrently*.\nIf any awaitable in *aws* is a coroutine, it is automatically\nscheduled as a Task.\nIf all awaitables are completed successfully, the result is an\naggregate list of returned values.  The order of result values\ncorresponds to the order of awaitables in *aws*.\nIf *return\\_exceptions* is `False` (default), the first\nraised exception is immediately propagated to the task that\nawaits on `gather()`.  Other awaitables in the *aws* sequence **won’t be cancelled** and will continue to run.\nIf *return\\_exceptions* is `True`, exceptions are treated the\nsame as successful results, and aggregated in the result list.\nIf `gather()` is *cancelled*, all submitted awaitables\n(that have not completed yet) are also *cancelled*.\nIf any Task or Future from the *aws* sequence is *cancelled*, it is\ntreated as if it raised [`CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError) – the `gather()` call is **not** cancelled in this case.  This is to prevent the\ncancellation of one submitted Task/Future to cause other\nTasks/Futures to be cancelled.\nNote A new alternative to create and run tasks concurrently and\nwait for their completion is [`asyncio.TaskGroup`](https://docs.python.org#asyncio.TaskGroup). *TaskGroup* provides stronger safety guarantees than *gather* for scheduling a nesting of subtasks:\nif a task (or a subtask, a task scheduled by a task)\nraises an exception, *TaskGroup* will, while *gather* will not,\ncancel the remaining scheduled tasks.\nExample: import asyncio async def factorial(name, number): f = 1 for i in range(2, number + 1): print(f\"Task {name}: Compute factorial({number}), currently i={i}...\") await asyncio.sleep(1) f \\*= i print(f\"Task {name}: factorial({number}) = {f}\") return f async def main(): # Schedule three calls \\*concurrently\\*: L = await asyncio.gather( factorial(\"A\", 2), factorial(\"B\", 3), factorial(\"C\", 4), ) print(L) asyncio.run(main()) # Expected output: # # Task A: Compute factorial(2), currently i=2... # Task B: Compute factorial(3), currently i=2... # Task C: Compute factorial(4), currently i=2... # Task A: factorial(2) = 2 # Task B: Compute factorial(3), currently i=3... # Task C: Compute factorial(4), currently i=3... # Task B: factorial(3) = 6 # Task C: Compute factorial(4), currently i=4... # Task C: factorial(4) = 24 # \\[2, 6, 24\\] Note If *return\\_exceptions* is false, cancelling gather() after it\nhas been marked done won’t cancel any submitted awaitables.\nFor instance, gather can be marked done after propagating an\nexception to the caller, therefore, calling `gather.cancel()` after catching an exception (raised by one of the awaitables) from\ngather won’t cancel any other awaitables.\nChanged in version 3.7: If the *gather* itself is cancelled, the cancellation is\npropagated regardless of *return\\_exceptions*.\nChanged in version 3.10: Removed the *loop* parameter.\nDeprecated since version 3.10: Deprecation warning is emitted if no positional arguments are provided or not all positional arguments are Future-like objects and there is no running event loop.\n\n- \nasyncio.eager\\_task\\_factory(*loop*, *coro*, *\\**, *name=None*, *context=None*)[¶](https://docs.python.org#asyncio.eager_task_factory)\n- A task factory for eager task execution. When using this factory (via [`loop.set_task_factory(asyncio.eager_task_factory)`](https://docs.python.org/asyncio-eventloop.html#asyncio.loop.set_task_factory)),\ncoroutines begin execution synchronously during [`Task`](https://docs.python.org#asyncio.Task) construction.\nTasks are only scheduled on the event loop if they block.\nThis can be a performance improvement as the overhead of loop scheduling\nis avoided for coroutines that complete synchronously.\nA common example where this is beneficial is coroutines which employ caching or memoization to avoid actual I/O when possible. Note Immediate execution of the coroutine is a semantic change. If the coroutine returns or raises, the task is never scheduled to the event loop. If the coroutine execution blocks, the task is scheduled to the event loop. This change may introduce behavior changes to existing applications. For example, the application’s task execution order is likely to change. Added in version 3.12.\n\n- \nasyncio.create\\_eager\\_task\\_factory(*custom\\_task\\_constructor*)[¶](https://docs.python.org#asyncio.create_eager_task_factory)\n- Create an eager task factory, similar to [`eager_task_factory()`](https://docs.python.org#asyncio.eager_task_factory),\nusing the provided *custom\\_task\\_constructor* when creating a new task instead\nof the default [`Task`](https://docs.python.org#asyncio.Task).\n*custom\\_task\\_constructor* must be a *callable* with the signature matching\nthe signature of [`Task.__init__`](https://docs.python.org#asyncio.Task).\nThe callable must return a [`asyncio.Task`](https://docs.python.org#asyncio.Task)-compatible object.\nThis function returns a *callable* intended to be used as a task factory of an\nevent loop via [`loop.set_task_factory(factory)`](https://docs.python.org/asyncio-eventloop.html#asyncio.loop.set_task_factory)).\nAdded in version 3.12.\n\n- *awaitable* asyncio.shield(*aw*)[¶](https://docs.python.org#asyncio.shield)\n- Protect an [awaitable object](https://docs.python.org#asyncio-awaitables) from being [`cancelled`](https://docs.python.org#asyncio.Task.cancel).\nIf *aw* is a coroutine it is automatically scheduled as a Task.\nThe statement: task = asyncio.create\\_task(something()) res = await shield(task) is equivalent to: res = await something() *except* that if the coroutine containing it is cancelled, the\nTask running in `something()` is not cancelled.  From the point\nof view of `something()`, the cancellation did not happen.\nAlthough its caller is still cancelled, so the “await” expression\nstill raises a [`CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError).\nIf `something()` is cancelled by other means (i.e. from within\nitself) that would also cancel `shield()`.\nIf it is desired to completely ignore cancellation (not recommended)\nthe `shield()` function should be combined with a try/except\nclause, as follows:\ntask = asyncio.create\\_task(something()) try: res = await shield(task) except CancelledError: res = None Important Save a reference to tasks passed to this function, to avoid a task disappearing mid-execution. The event loop only keeps weak references to tasks. A task that isn’t referenced elsewhere may get garbage collected at any time, even before it’s done. Changed in version 3.10: Removed the *loop* parameter.\nDeprecated since version 3.10: Deprecation warning is emitted if *aw* is not Future-like object\nand there is no running event loop.\n\n- \nasyncio.timeout(*delay*)[¶](https://docs.python.org#asyncio.timeout)\n- Return an [asynchronous context manager](https://docs.python.org/reference/datamodel.html#async-context-managers) that can be used to limit the amount of time spent waiting on\nsomething.\n*delay* can either be `None`, or a float/int number of\nseconds to wait. If *delay* is `None`, no time limit will\nbe applied; this can be useful if the delay is unknown when\nthe context manager is created.\nIn either case, the context manager can be rescheduled after\ncreation using [`Timeout.reschedule()`](https://docs.python.org#asyncio.Timeout.reschedule).\nExample: async def main(): async with asyncio.timeout(10): await long\\_running\\_task() If `long_running_task` takes more than 10 seconds to complete,\nthe context manager will cancel the current task and handle\nthe resulting [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError) internally, transforming it\ninto a [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError) which can be caught and handled.\nNote The [`asyncio.timeout()`](https://docs.python.org#asyncio.timeout) context manager is what transforms\nthe [`asyncio.CancelledError`](https://docs.python.org/asyncio-exceptions.html#asyncio.CancelledError) into a [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError),\nwhich means the `TimeoutError` can only be caught *outside* of the context manager.\nExample of catching [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError):\nasync def main(): try: async with asyncio.timeout(10): await long\\_running\\_task() except TimeoutError: print(\"The long operation timed out, but we've handled it.\") print(\"This statement will run regardless.\") The context manager produced by [`asyncio.timeout()`](https://docs.python.org#asyncio.timeout) can be\nrescheduled to a different deadline and inspected.\n  - *class* asyncio.Timeout(*when*)[¶](https://docs.python.org#asyncio.Timeout)\n  - An [asynchronous context manager](https://docs.python.org/reference/datamodel.html#async-context-managers) for cancelling overdue coroutines.\nPrefer using [`asyncio.timeout()`](https://docs.python.org#asyncio.timeout) or [`asyncio.timeout_at()`](https://docs.python.org#asyncio.timeout_at) rather than instantiating `Timeout` directly.\n`when` should be an absolute time at which the context should time out,\nas measured by the event loop’s clock:\n    - If `when` is `None`, the timeout will never trigger.\n    - If `when < loop.time()`, the timeout will trigger on the next\niteration of the event loop.\nExample: async def main(): try: # We do not know the timeout when starting, so we pass \\`\\`None\\`\\`. async with asyncio.timeout(None) as cm: # We know the timeout now, so we reschedule it. new\\_deadline = get\\_running\\_loop().time() + 10 cm.reschedule(new\\_deadline) await long\\_running\\_task() except TimeoutError: pass if cm.expired(): print(\"Looks like we haven't finished on time.\") Timeout context managers can be safely nested. Added in version 3.11.\n\n- \nasyncio.timeout\\_at(*when*)[¶](https://docs.python.org#asyncio.timeout_at)\n- Similar to [`asyncio.timeout()`](https://docs.python.org#asyncio.timeout), except *when* is the absolute time\nto stop waiting, or `None`.\nExample: async def main(): loop = get\\_running\\_loop() deadline = loop.time() + 20 try: async with asyncio.timeout\\_at(deadline): await long\\_running\\_task() except TimeoutError: print(\"The long operation timed out, but we've handled it.\") print(\"This statement will run regardless.\") Added in version 3.11.\n\n- *async* asyncio.wait\\_for(*aw*, *timeout*)[¶](https://docs.python.org#asyncio.wait_for)\n- Wait for the *aw* [awaitable](https://docs.python.org#asyncio-awaitables) to complete with a timeout.\n*timeout* can either be `None` or a float or int number of seconds\nto wait for.  If *timeout* is `None`, block until the future\ncompletes.\nIf a timeout occurs, it cancels *aw* and raises [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError).\nTo prevent *aw* from being cancelled, wrap it in [`shield()`](https://docs.python.org#asyncio.shield).\nThe function will wait until the future is actually cancelled,\nso the total wait time may exceed the *timeout*. If an exception\nhappens during cancellation, it is propagated.\nIf the wait is cancelled, the future *aw* is also cancelled.\nExample: async def eternity(): # Sleep for one hour await asyncio.sleep(3600) print('yay!') async def main(): # Wait for at most 1 second try: await asyncio.wait\\_for(eternity(), timeout=1.0) except TimeoutError: print('timeout!') asyncio.run(main()) # Expected output: # # timeout! Changed in version 3.7: When *aw* is cancelled due to a timeout, `wait_for` waits\nfor *aw* to be cancelled.  Previously, it raised [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError) immediately.\nChanged in version 3.10: Removed the *loop* parameter.\n\n- *async* asyncio.wait(*aws*, *\\**, *timeout=None*, *return\\_when=ALL\\_COMPLETED*)[¶](https://docs.python.org#asyncio.wait)\n- Run [`Future`](https://docs.python.org/asyncio-future.html#asyncio.Future) and [`Task`](https://docs.python.org#asyncio.Task) instances in the *aws* iterable concurrently and block until the condition specified\nby *return\\_when*.\nThe *aws* iterable must not be empty.\nReturns two sets of Tasks/Futures: `(done, pending)`.\nUsage: done, pending = await asyncio.wait(aws) *timeout* (a float or int), if specified, can be used to control\nthe maximum number of seconds to wait before returning.\nNote that this function does not raise [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError).\nFutures or Tasks that aren’t done when the timeout occurs are simply\nreturned in the second set.\n*return\\_when* indicates when this function should return.  It must\nbe one of the following constants:\nConstant Description \n  - \nasyncio.FIRST\\_COMPLETED[¶](https://docs.python.org#asyncio.FIRST_COMPLETED)\nThe function will return when any future finishes or is cancelled. \n  - \nasyncio.FIRST\\_EXCEPTION[¶](https://docs.python.org#asyncio.FIRST_EXCEPTION)\nThe function will return when any future finishes by raising an\nexception. If no future raises an exception\nthen it is equivalent to [`ALL_COMPLETED`](https://docs.python.org#asyncio.ALL_COMPLETED).\n  - \nasyncio.ALL\\_COMPLETED[¶](https://docs.python.org#asyncio.ALL_COMPLETED)\nThe function will return when all futures finish or are cancelled. Unlike [`wait_for()`](https://docs.python.org#asyncio.wait_for), `wait()` does not cancel the\nfutures when a timeout occurs.\nIf `wait()` is cancelled, the futures in *aws* are not cancelled\nand continue to run.\nChanged in version 3.10: Removed the *loop* parameter.\nChanged in version 3.11: Passing coroutine objects to `wait()` directly is forbidden.\nChanged in version 3.12: Added support for generators yielding tasks.\n\n- \nasyncio.as\\_completed(*aws*, *\\**, *timeout=None*)[¶](https://docs.python.org#asyncio.as_completed)\n- Run [awaitable objects](https://docs.python.org#asyncio-awaitables) in the *aws* iterable\nconcurrently. The returned object can be iterated to obtain the results\nof the awaitables as they finish.\nThe object returned by `as_completed()` can be iterated as an [asynchronous iterator](https://docs.python.org/glossary.html#term-asynchronous-iterator) or a plain [iterator](https://docs.python.org/glossary.html#term-iterator). When asynchronous\niteration is used, the originally-supplied awaitables are yielded if they\nare tasks or futures. This makes it easy to correlate previously-scheduled\ntasks with their results. Example:\nipv4\\_connect = create\\_task(open\\_connection(\"127.0.0.1\", 80)) ipv6\\_connect = create\\_task(open\\_connection(\"::1\", 80)) tasks = \\[ipv4\\_connect, ipv6\\_connect\\] async for earliest\\_connect in as\\_completed(tasks): # earliest\\_connect is done. The result can be obtained by # awaiting it or calling earliest\\_connect.result() reader, writer = await earliest\\_connect if earliest\\_connect is ipv6\\_connect: print(\"IPv6 connection established.\") else: print(\"IPv4 connection established.\") During asynchronous iteration, implicitly-created tasks will be yielded for supplied awaitables that aren’t tasks or futures. When used as a plain iterator, each iteration yields a new coroutine that returns the result or raises the exception of the next completed awaitable. This pattern is compatible with Python versions older than 3.13: ipv4\\_connect = create\\_task(open\\_connection(\"127.0.0.1\", 80)) ipv6\\_connect = create\\_task(open\\_connection(\"::1\", 80)) tasks = \\[ipv4\\_connect, ipv6\\_connect\\] for next\\_connect in as\\_completed(tasks): # next\\_connect is not one of the original task objects. It must be # awaited to obtain the result value or raise the exception of the # awaitable that finishes next. reader, writer = await next\\_connect A [`TimeoutError`](https://docs.python.org/builtins/exceptions.html#TimeoutError) is raised if the timeout occurs before all awaitables\nare done. This is raised by the `async for` loop during asynchronous\niteration or by the coroutines yielded during plain iteration.\n`as_completed()` does not cancel the tasks running the supplied\nawaitables: if a timeout occurs or the iteration is cancelled, the\nremaining tasks continue to run.\nChanged in version 3.10: Removed the *loop* parameter.\nDeprecated since version 3.10: Deprecation warning is emitted if not all awaitable objects in the *aws* iterable are Future-like objects and there is no running event loop.\nChanged in version 3.12: Added support for generators yielding tasks.\n\n- *async* asyncio.to\\_thread(*func*, */*, *\\*args*, *\\*\\*kwargs*)[¶](https://docs.python.org#asyncio.to_thread)\n- Asynchronously run function *func* in a separate thread.\nAny \\*args and \\*\\*kwargs supplied for this function are directly passed\nto *func*. Also, the current [`contextvars.Context`](https://docs.python.org/contextvars.html#contextvars.Context) is propagated,\nallowing context variables from the event loop thread to be accessed in the\nseparate thread.\nReturn a coroutine that can be awaited to get the eventual result of *func*.\nThis coroutine function is primarily intended to be used for executing IO-bound functions/methods that would otherwise block the event loop if they were run in the main thread. For example: def blocking\\_io(): print(f\"start blocking\\_io at {time.strftime('%X')}\") # Note that time.sleep() can be replaced with any blocking # IO-bound operation, such as file operations. time.sleep(1) print(f\"blocking\\_io complete at {time.strftime('%X')}\") async def main(): print(f\"started main at {time.strftime('%X')}\") await asyncio.gather( asyncio.to\\_thread(blocking\\_io), asyncio.sleep(1)) print(f\"finished main at {time.strftime('%X')}\") asyncio.run(main()) # Expected output: # # started main at 19:50:53 # start blocking\\_io at 19:50:53 # blocking\\_io complete at 19:50:54 # finished main at 19:50:54 Directly calling `blocking_io()` in any coroutine would block the event loop\nfor its duration, resulting in an additional 1 second of run time. Instead,\nby using `asyncio.to_thread()`, we can run it in a separate thread without\nblocking the event loop.\nNote Due to the [GIL](https://docs.python.org/glossary.html#term-GIL), `asyncio.to_thread()` can typically only be used\nto make IO-bound functions non-blocking. However, for extension modules\nthat release the GIL or alternative Python implementations that don’t\nhave one, `asyncio.to_thread()` can also be used for CPU-bound functions.\nAdded in version 3.9.",
  "total_chars": 54084,
  "next_start": 36754,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/library/asyncio-task.html",
      "start_offset": 36754,
      "max_chars": 20000,
      "expected_content_hash": "940818f7fdaeb73f5ec058f096478fa978bf81f939fefd7778e9f8b627b2a18b"
    }
  }
}
```

**Tool: cluefinch_research_collect**

**Input:**
```json
{
  "max_sources": 1,
  "topic": "asyncio TaskGroup cancel new API changes",
  "urls": [
    "https://docs.python.org/3/whatsnew/3.15.html"
  ]
}
```

**Output:**
```
{
  "query_variants": [],
  "sources": [
    {
      "title": "What’s new in Python 3.15",
      "url": "https://docs.python.org/3/whatsnew/3.15.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "- Added [`TaskGroup.cancel`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup.cancel) to allow early\ntermination of a task group, for instance, when the goal of the tasks has\nbeen achieved or their services are no longer needed.\nPreviously this would involve unintuitive boilerplate such as an extra task\nraising a custom exception which is then suppressed as it exits the task group.\n(Contributed by John Belmonte in [gh-127214](https://github.com/python/cpython/issues/127214).)",
          "start_char": 45222,
          "end_char": 45721,
          "heading": "asyncio[¶](https://docs.python.org#asyncio)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.15.html",
              "start_offset": 45222,
              "max_chars": 3000,
              "expected_content_hash": "cc48a7d1ce80c0d2ee4887766af8bc404b94e010f14c6703cdf00db20d74ff55"
            }
          }
        },
        {
          "text": "- [**PEP 782**](https://peps.python.org/pep-0782/): [A new PyBytesWriter C API to create a Python bytes object](https://docs.python.org#whatsnew315-pybyteswriter)\n- [**PEP 788**](https://peps.python.org/pep-0788/): [Protection against finalization in the C API](https://docs.python.org#whatsnew315-c-api-interpreter-finalization)\n- [**PEP 803**](https://peps.python.org/pep-0803/), [**820**](https://peps.python.org/pep-0820/), [**793**](https://peps.python.org/pep-0793/): [Stable ABI for",
          "start_char": 2309,
          "end_char": 2798,
          "heading": "Summary – Release highlights[¶](https://docs.python.org#summary-release-highlights)",
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.15.html",
              "start_offset": 2309,
              "max_chars": 3000,
              "expected_content_hash": "cc48a7d1ce80c0d2ee4887766af8bc404b94e010f14c6703cdf00db20d74ff55"
            }
          }
        },
        {
          "text": "The library changes include a new\n[profiling package](https://docs.python.org#whatsnew315-profiling-package) with\n[Tachyon](https://docs.python.org#whatsnew315-sampling-profiler),\na high-frequency statistical sampling profiler,\n[more color](https://docs.python.org#whatsnew315-more-color) in command-line output,\nas well as the usual deprecations and removals,\nand improvements in user-friendliness and correctness.",
          "start_char": 1065,
          "end_char": 1480,
          "heading": "Summary – Release highlights[¶](https://docs.python.org#summary-release-highlights)",
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://docs.python.org/3/whatsnew/3.15.html",
              "start_offset": 1065,
              "max_chars": 3000,
              "expected_content_hash": "cc48a7d1ce80c0d2ee4887766af8bc404b94e010f14c6703cdf00db20d74ff55"
            }
          }
        }
      ],
      "source_id": "src_e9517672d49f2226",
      "text_truncated": true,
      "content_hash": "cc48a7d1ce80c0d2ee4887766af8bc404b94e010f14c6703cdf00db20d74ff55"
    }
  ],
  "gaps": [
    "https://docs.python.org/3/whatsnew/3.15.html: extracted text truncated by character limit"
  ]
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.python.org/downloads/",
  "max_chars": 900
}
```

**Output:**
```
{
  "title": "Download Python",
  "url": "https://www.python.org/downloads/",
  "content": "## Active Python releases\n\n## Looking for a specific release?\n\nPython releases by version number:\n\n1. [Python 3.15.0](https://www.python.org/downloads/release/python-3150/) Oct. 9, 2026 [Release notes](https://docs.python.org/release/3.15.0/whatsnew/changelog.html)\n2. [Python 3.14.8](https://www.python.org/downloads/release/python-3148/) Sept. 30, 2026 [Release notes](https://docs.python.org/release/3.14.8/whatsnew/changelog.html)\n3. [Python 3.14.7](https://www.python.org/downloads/release/python-3147/) Aug. 5, 2026 [Release notes](https://docs.python.org/release/3.14.7/whatsnew/changelog.html)\n4. [Python 3.14.6](https://www.python.org/downloads/release/python-3146/) June 10, 2026 [Release notes](https://docs.python.org/release/3.14.6/whatsnew/changelog.html)\n5. [Python 3.14.5](https://www.python.org/downloads/release/python-3145/) May 10, 2026 [Release notes](https://docs.python.org/rel",
  "total_chars": 50362,
  "next_start": 900,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "c8171aad8e9d225d3d0bf9079bd79df69537d8e697f12570d72e7d7624536962",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://www.python.org/downloads/",
      "start_offset": 900,
      "max_chars": 900,
      "expected_content_hash": "c8171aad8e9d225d3d0bf9079bd79df69537d8e697f12570d72e7d7624536962"
    }
  }
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

Now I have everything I need:

**Confirmed facts:**

1. **Current documentation = Python 3.15**: python.org/downloads shows "Python 3.15.0 — Oct. 9, 2026" as the latest release (today is October 11, 2026). docs.python.org/3 points to 3.15 (source links reference tree/3.15; TaskGroup.cancel() is documented as "Added in version 3.15").

2. **When features were introduced:**
   - PEP 654 (ExceptionGroup, BaseExceptionGroup, except*): Python 3.11 — whatsnew/3.11.html section "PEP 654: Exception Groups and except*".
   - asyncio.TaskGroup: Python 3.11 — whatsnew/3.11.html asyncio section: "Added the TaskGroup class, an asynchronous context manager holding a group of tasks that will wait for all of them upon exit. For new code this is recommended over using create_task() and gather()."
   - Related 3.11 additions: Task.cancelling()/uncancel() "primarily intended for internal use, notably by TaskGroup"; asyncio.timeout(); the all_errors keyword argument on loop.create_connection raises ExceptionGroup.

3. **Behavioral differences between TaskGroup vs gather (documented in current docs):**
   - gather (asyncio-task.html): "If return_exceptions is False (default), the first raised exception is immediately propagated to the task that awaits on gather(). Other awaitables in the aws sequence won't be cancelled and will continue to run." / "If return_exceptions is True, exceptions are treated the same as successful results, and aggregated in the result list." / "If gather() is cancelled, all submitted awaitables (that have not completed yet) are also cancelled." / "If any Task or Future from the aws sequence is cancelled, it is treated as if it raised CancelledError – the gather() call is not cancelled in this case."
   - Note on gather: "A new alternative to create and run tasks concurrently... is asyncio.TaskGroup. TaskGroup provides stronger safety guarantees than gather for scheduling a nesting of subtasks: if a task (or a subtask, a task scheduled by a task) raises an exception, TaskGroup will, while gather will not, cancel the remaining scheduled tasks."
   - Note on gather: "If return_exceptions is false, cancelling gather() after it has been marked done won't cancel any submitted awaitables. For instance, gather can be marked done after propagating an exception to the caller..."
   - Version note for gather: "Changed in version 3.7: If the gather itself is cancelled, the cancellation is propagated regardless of return_exceptions." — interesting! So propagation of gather's own cancellation to children was documented as a change in 3.7 (bpo-32929? whatever). Good — this is a documented historical note.
   - TaskGroup: on first non-CancelledError failure → cancel remaining tasks; no new tasks can be added; the containing task is also cancelled (that CancelledError does not leak out of async with); after all complete, exceptions are combined into ExceptionGroup or BaseExceptionGroup and raised; KeyboardInterrupt/SystemExit special case (re-raised directly); body exception treated as a failure and included in the group (except for CancelledError); GeneratorExit special case; nested groups process sequentially; external cancellation + pending ExceptionGroup → parent's cancel() is called so cancellation isn't lost; preserves Task.cancelling() count.

4. **Role of ExceptionGroup:** PEP 654 — "introduces language features that enable a program to raise and handle multiple unrelated exceptions simultaneously"; builtins ExceptionGroup/BaseExceptionGroup + except* syntax generalizes except to match subgroups. TaskGroup raises these groups; except* is the natural way to handle them (PEP 654 shows an asyncio.TaskGroup example with except*). PEP 654 motivation: "Implementing a better task spawning API in asyncio, inspired by Trio nurseries [13], was the main motivation for this PEP."

5. **Design problem:**
   - PEP 654: difficulty of reporting/handling multiple errors without language support (MultiError2 design doc); asyncio's task-spawning API inspired by Trio nurseries as the primary motivation; other use cases (socket.create_connection retries, atexit, pytest finalizers, tempfile masking).
   - Docs: create_task note — fire-and-forget tasks are never awaited → "if a task fails, its exception is never retrieved and asyncio logs a 'Task exception was never retrieved' message... To avoid this, use asyncio.TaskGroup which keeps a strong reference to each task, awaits them and propagates their exceptions."
   - gather's note: TaskGroup provides stronger safety guarantees for nested subtasks.
   - Interpretation (mine): structured concurrency = scope-based lifetime guarantee; all spawned work completes or is cancelled before the scope exits; failures are aggregated rather than lost or orphaned.

6. **Later behavioral changes reflected in current docs:**
   - 3.12: "When a try-except* construct handles the entire ExceptionGroup and raises one other exception, that exception is no longer wrapped in an ExceptionGroup." (gh-103590; also changed in 3.11.4). This is a language-level change to except*/ExceptionGroup handling — reflected in current docs? The reference docs for except* probably reflect this now. I haven't verified the reference page, but whatsnew documents it.
   - 3.13: TaskGroup cancellation fixes (gh-116720): improved handling of concurrent internal/external cancellations; nested groups no longer hang when both fail simultaneously; external cancel + ExceptionGroup → parent's cancel() so CancelledError isn't lost; preserves cancelling() count; uncancel() may reset _must_cancel. Also TaskGroup.create_task on an inactive group closes the coroutine (gh-115957). Current asyncio-task.html has "Changed in version 3.13: Improved handling of simultaneous internal and external cancellations and correct preservation of cancellation counts." — yes, confirmed in the fetched text.
   - 3.14: task factory changes — create_task/TaskGroup.create_task accept **kwargs passed to the task constructor; eager_start parameter (docs say "Changed in version 3.14: Added the eager_start parameter by passing on all kwargs"); context may be None. Also asyncio introspection (python -m asyncio pstree) shows TaskGroup frames — minor.
   - 3.15: new API TaskGroup.cancel() (gh-127214): "non-exceptional, early exit of the task group's lifetime"; cancels unfinished tasks and the parent body; exits without raising CancelledError; idempotent; can be called before entering. This is a documented addition in current docs ("Added in version 3.15").

So the answer to "does current documentation reflect behavioral changes introduced in later Python releases": yes — current (3.15) docs include:
- Changed-in-3.13 notes on TaskGroup (cancellation handling, create_task closing coroutines),
- Changed-in-3.14 note on eager_start/kwargs for create_task,
- Added-in-3.15 TaskGroup.cancel(),
and the 3.12 except* change is reflected in language semantics (documented in whatsnew 3.12; also backported to 3.11.4).

One caveat: I should double-check whether the "Changed in version 3.13" note on TaskGroup was present in the 3.11/3.12 docs — obviously it wasn't (it documents a change that happened later); the question is whether current docs reflect later changes, and they do, as shown by these version notes.

Do I need to verify the except* reference page for the 3.12 change? The whatsnew entry is sufficient evidence of the documented change; I can cite it without fetching the reference page. That's fine.

Another possible check: PEP 654 status (Accepted, Python-3.11). The top of the PEP says "Status: Final" / "Python-Version: 3.11". I haven't fetched that part but it's standard; whatsnew 3.11 confirms implementation in 3.11. That's enough.

Also worth noting: TaskGroup itself is not a PEP — it was added via bpo-46820 (I don't have the issue number verified from sources I fetched, so I shouldn't cite an unverified issue number). The whatsnew 3.11 entry for TaskGroup didn't show a contributor/issue in my excerpt (it was cut off at "For new code this is recommended over using create_task() and gather()" — truncated: true; the full bullet probably ends with "(Contributed by ... in bpo-46820.)"). I could expand to get the issue number. Let me do one more small fetch of whatsnew/3.11.html at offset 18560, max_chars ~700 to capture the end of that bullet (contributor + issue). That would strengthen the citation for "when introduced".

Also, I might want to verify the exact wording of the TaskGroup bullet in whatsnew 3.11 — already have most of it: "Added the TaskGroup class, an asynchronous context manager holding a group of tasks that will wait for all of them upon exit. For new code this is recommended over using create_task() and gather()."

Let me do one final fetch to get the tail of that bullet (issue number), then write the answer.


One last detail — the issue reference on the 3.11 TaskGroup entry:



**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://docs.python.org/3/whatsnew/3.11.html",
  "start_offset": 18560,
  "max_chars": 900,
  "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
}
```

**Output:**
```
{
  "title": "What’s New In Python 3.11",
  "url": "https://docs.python.org/3/whatsnew/3.11.html",
  "content": "- Added the [`TaskGroup`](https://docs.python.org/library/asyncio-task.html#asyncio.TaskGroup) class,\nan [asynchronous context manager](https://docs.python.org/reference/datamodel.html#async-context-managers) holding a group of tasks that will wait for all of them upon exit.\nFor new code this is recommended over using [`create_task()`](https://docs.python.org/library/asyncio-task.html#asyncio.create_task) and [`gather()`](https://docs.python.org/library/asyncio-task.html#asyncio.gather) directly.\n(Contributed by Yury Selivanov and others in [gh-90908](https://github.com/python/cpython/issues/90908).)\n- Added [`timeout()`](https://docs.python.org/library/asyncio-task.html#asyncio.timeout), an asynchronous context manager for\nsetting a timeout on asynchronous operations. For new code this is\nrecommended over using [`wait_for()`](https://docs.python.org/library/asyncio-task.html#asyncio.wai",
  "total_chars": 100000,
  "next_start": 19460,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": true,
  "content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://docs.python.org/3/whatsnew/3.11.html",
      "start_offset": 19460,
      "max_chars": 900,
      "expected_content_hash": "ec49c4a2ce6931156337d4ca28eae43bb9721998263f7e6bd8bbbe990b66c5ec"
    }
  }
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

TaskGroup was contributed by Yury Selivanov and others in gh-90908 (this is the GH issue number, not bpo-46820 — good thing I checked. Cite gh-90908).

Now everything's in place. Let me structure the final answer:

Structure:
1. Timeline / when introduced
2. Design problem (documented rationale + my interpretation)
3. TaskGroup vs gather on failure/cancellation (table or bullet points, all documented)
4. Role of ExceptionGroup
5. Later changes reflected in current docs (3.12 except*, 3.13 cancellation fix, 3.14 task factory/eager_start, 3.15 cancel())
6. Sources

Keep it organized but reasonably concise. The user asked a detailed research question so a longer answer is warranted — the "under 4 lines" guidance yields to explicit requests for detail/citations. Use markdown with citations (URLs). Distinguish documented vs interpreted.

Key documented facts with sources:

**When introduced:**
- PEP 654 exception groups + except*: Python 3.11 (whatsnew/3.11.html "PEP 654: Exception Groups and except*": "introduces language features that enable a program to raise and handle multiple unrelated exceptions simultaneously"; builtins ExceptionGroup/BaseExceptionGroup; except* generalizes except).
- asyncio.TaskGroup: Python 3.11 (whatsnew/3.11.html: "Added the TaskGroup class... For new code this is recommended over using create_task() and gather() directly. (Contributed by Yury Selivanov and others in gh-90908.)")
- Related 3.11: Task.cancelling()/uncancel() "primarily intended for internal use, notably by TaskGroup"; asyncio.timeout(); loop.create_connection(all_errors=...) raises ExceptionGroup.

**Design problem:**
- PEP 654 (documented): "Implementing a better task spawning API in asyncio, inspired by Trio nurseries [13], was the main motivation for this PEP." Also: MultiError2 design doc shows how hard it is to report/handle multiple errors without language changes; other use cases (socket.create_connection retries, atexit callbacks, pytest finalizers, tempfile cleanup masking).
- Docs (documented): create_task note — fire-and-forget tasks are never awaited → "if a task fails, its exception is never retrieved and asyncio logs a 'Task exception was never retrieved' message... To avoid this, use asyncio.TaskGroup which keeps a strong reference to each task, awaits them and propagates their exceptions."
- gather docs (documented): TaskGroup note — "provides stronger safety guarantees than gather for scheduling a nesting of subtasks: if a task (or a subtask...) raises an exception, TaskGroup will, while gather will not, cancel the remaining scheduled tasks."
- Interpretation (mine): structured concurrency = scope-based lifetime guarantee; no orphaned tasks; failures aggregated rather than lost.

**Behavioral differences (all from current docs):**

gather:
- return_exceptions=False (default): first exception propagates immediately to awaiting task; other awaitables are not cancelled and keep running.
- return_exceptions=True: exceptions collected as results in the list.
- If gather() itself is cancelled → all incomplete submitted awaitables are also cancelled (documented change since 3.7).
- Cancellation of one child does not cancel gather or its siblings ("treated as if it raised CancelledError – the gather() call is not cancelled").
- Caveat: cancelling gather after it's already done (e.g., after propagating an exception) doesn't cancel anything.

TaskGroup:
- First non-CancelledError failure → remaining tasks are cancelled; no new tasks can be added; containing task also cancelled (that CancelledError does not leak out of async with).
- After all complete, non-cancellation exceptions combined into ExceptionGroup or BaseExceptionGroup and raised at the await point.
- KeyboardInterrupt/SystemExit: re-raised directly instead of a group.
- Body exception → treated as failure; included in group (except CancelledError); GeneratorExit special case.
- Nested groups: inner processes its own exceptions first, then outer receives cancellation and processes its own.
- External cancellation + pending ExceptionGroup → parent task's cancel() is called so cancellation isn't lost.
- Preserves Task.cancelling() count.

**Role of ExceptionGroup:** language-level container (PEP 654) that lets multiple unrelated exceptions be raised/handled together; except* matches subgroups by type; TaskGroup is the primary asyncio producer of these groups; PEP 654's own examples use TaskGroup + except*. BaseExceptionGroup for mixed BaseException/Exception.

**Later changes reflected in current docs (docs.python.org/3 = Python 3.15, released Oct 9, 2026 per python.org/downloads):**
- 3.12: try-except* handling the whole ExceptionGroup and raising one other exception → no longer wrapped in an ExceptionGroup (gh-103590; also backported to 3.11.4). Language-level change to except*/ExceptionGroup semantics.
- 3.13: TaskGroup cancellation fixes (gh-116720): concurrent internal/external cancellations handled correctly — previously nested groups could hang when both failed simultaneously because the outer group's internal cancellation was swallowed by the inner; now, if a group is externally cancelled while it must raise an ExceptionGroup, it calls parent task's cancel() so CancelledError isn't lost; cancelling() count preserved. Also TaskGroup.create_task on inactive group closes coroutine (gh-115957). Current docs carry "Changed in version 3.13" notes for both.
- 3.14: create_task/TaskGroup.create_task accept **kwargs passed to task constructor; eager_start parameter added ("Changed in version 3.14"); context may be None (task factory contract, gh-128307).
- 3.15: new TaskGroup.cancel() API (gh-127214) — non-exceptional early exit; cancels unfinished tasks and parent body; exits without raising CancelledError; idempotent; can be called before entering group. Documented as "Added in version 3.15."

So: yes, current docs reflect later changes via version notes and new API entries; the core failure/cancellation semantics documented for TaskGroup are stable since 3.11 except for the 3.13 corner-case fixes (hang on nested simultaneous failures, lost external cancellation) — those were bug fixes to edge cases rather than a redesign of the model.

Caveats: search engines were mostly unresponsive during research; relied on direct fetches from docs.python.org, peps.python.org, python.org. All claims verified against fetched text.

Format: headings + bullets, cite URLs inline. Distinguish "documented" vs "interpretation" explicitly — mark interpretation sections clearly. Length: this is a detailed research answer so it can be long but keep it tight.


# Python's structured concurrency around `asyncio.TaskGroup`

## When the features landed

| Feature | Version | Source |
|---|---|---|
| `ExceptionGroup`, `BaseExceptionGroup`, `except*` (PEP 654) | **3.11** | [What's New in 3.11, "PEP 654: Exception Groups and except\*"](https://docs.python.org/3/whatsnew/3.11.html): "introduces language features that enable a program to raise and handle multiple unrelated exceptions simultaneously" |
| `asyncio.TaskGroup` | **3.11** | [What's New in 3.11, asyncio](https://docs.python.org/3/whatsnew/3.11.html): "Added the TaskGroup class… For new code this is recommended over using create_task() and gather() directly" (Yury Selivanov et al., [gh-90908](https://github.com/python/cpython/issues/90908)) |
| Supporting 3.11 pieces | 3.11 | `Task.cancelling()`/`uncancel()` — documented as "primarily intended for internal use, notably by TaskGroup"; `asyncio.timeout()`; `loop.create_connection(all_errors=…)` raising an `ExceptionGroup` ([What's New in 3.11](https://docs.python.org/3/whatsnew/3.11.html)) |

## The design problem these changes solve

**Documented rationale:**
- PEP 654 states directly: "Implementing a better task spawning API in asyncio, inspired by Trio nurseries, was the main motivation for this PEP" — i.e., exception groups were built *because* asyncio needed them ([PEP 654, Motivation](https://peps.python.org/pep-0654/)). The same section notes that prior design attempts (e.g. `MultiError2`) showed "how difficult it is to create an effective API for reporting and handling multiple errors without the language changes."
- The asyncio docs document the failure mode TaskGroup fixes: fire-and-forget tasks created with bare `create_task()` are never awaited, so "if a task fails, its exception is never retrieved and asyncio logs a 'Task exception was never retrieved' message… To avoid this, use asyncio.TaskGroup which keeps a strong reference to each task, awaits them and propagates their exceptions" ([asyncio-task docs](https://docs.python.org/3/library/asyncio-task.html)).
- The `gather()` entry itself now carries a note: "TaskGroup provides stronger safety guarantees than gather for scheduling a nesting of subtasks: if a task (or a subtask, a task scheduled by a task) raises an exception, TaskGroup will, while gather will not, cancel the remaining scheduled tasks."

**Interpretation (mine):** the problem is that pre-3.11 asyncio had no *scope* for concurrent work. `create_task` + manual awaits leaves lifetime management to the programmer: orphaned tasks keep running after a failure, their exceptions are silently lost, and cancellation of one task doesn't coordinate with its siblings. TaskGroup makes concurrency scope-based (like Trio's nursery): everything spawned inside an `async with` block is guaranteed to have completed or been cancelled before the block exits, and all failures surface together at that single exit point.

## Behavioral differences: failure and cancellation

All of the following is **documented** in the current [asyncio-task docs](https://docs.python.org/3/library/asyncio-task.html):

| Scenario | `gather()` | `TaskGroup` |
|---|---|---|
| One task raises (default settings) | First exception propagates immediately to the awaiting task; **other awaitables are not cancelled and keep running** | Remaining tasks **are cancelled**; no new tasks can be added; the containing task is also cancelled, but that internal `CancelledError` does not bubble out of the `async with` |
| Where exceptions surface | Single exception (or, with `return_exceptions=True`, all exceptions collected as list values) | After all tasks finish, non-cancellation exceptions are combined into an **`ExceptionGroup`** (or `BaseExceptionGroup`) and raised at the group's exit point |
| Cancellation of one child | Treated as if it raised `CancelledError`; the `gather()` call itself is *not* cancelled, siblings unaffected | A child cancelling normally doesn't trigger failure; only non-`CancelledError` exceptions do |
| The whole operation is cancelled externally | All not-yet-completed submitted awaitables are also cancelled (documented since 3.7) | Remaining tasks cancelled; if the group must *also* raise an `ExceptionGroup`, it calls the parent task's `cancel()` so "the cancellation is not lost" |
| Exception raised in the body/scope itself | N/A (no scope concept) | Treated as a task failure: siblings cancelled, and the exception is included in the resulting group (unless it's `CancelledError`) |

Additional documented TaskGroup specifics: `KeyboardInterrupt`/`SystemExit` from a child are re-raised directly instead of being grouped; nested groups process exceptions inner-first so an outer group isn't starved; task groups "preserve the cancellation count reported by `Task.cancelling()`."

## How ExceptionGroup fits in

- **Documented:** PEP 654 adds the builtin container types and the `except*` syntax, which "generalizes except to match subgroups of exception groups" ([What's New in 3.11](https://docs.python.org/3/whatsnew/3.11.html)). TaskGroup is the primary asyncio *producer* of these groups: it aggregates every non-cancellation failure from its children into one group at scope exit, and `except*` is the matching consumer — PEP 654's own examples pair `async with asyncio.TaskGroup()` with `except* KeyError`.
- **Interpretation:** this closes a loop that was previously impossible: without a language-level multi-exception type, a task group either had to pick one "winner" exception (losing the rest) or invent an ad-hoc wrapper class that `except` clauses couldn't pattern-match on. With PEP 654 + TaskGroup, "N independent subtasks failed" is a first-class, catchable-by-type outcome.

## Do current docs reflect later behavioral changes? Yes

Current documentation ([docs.python.org/3](https://docs.python.org/3/library/asyncio-task.html)) now points to **Python 3.15** (released Oct 9, 2026 per [python.org/downloads](https://www.python.org/downloads/)), and it carries version notes for every post-3.11 change:

- **3.12 — `except*` semantics:** "When a try-except\* construct handles the entire ExceptionGroup and raises one other exception, that exception is no longer wrapped in an ExceptionGroup" ([What's New in 3.12](https://docs.python.org/3/whatsnew/3.12.html), gh-103590; also backported to 3.11.4).
- **3.13 — TaskGroup cancellation corner cases** (gh-116720, [What's New in 3.13](https://docs.python.org/3/whatsnew/3.13.html)): previously, when two nested task groups both had a child fail simultaneously, "the outer task group would hang, because its internal cancellation was swallowed by the inner task group." Now simultaneous internal+external cancellations are handled correctly, an externally-cancelled group that must raise an `ExceptionGroup` calls the parent's `cancel()` so the `CancelledError` isn't lost, and `cancelling()` counts are preserved. The current TaskGroup entry carries "Changed in version 3.13: Improved handling of simultaneous internal and external cancellations…". Also 3.13: `TaskGroup.create_task()` on an inactive group now closes the coroutine (gh-115957).
- **3.14 — task factory surface:** `create_task`/`TaskGroup.create_task` gained `**kwargs` passthrough and the `eager_start` parameter ("Changed in version 3.14"), with `context=None` allowed for custom factories (gh-128307).
- **3.15 — new API:** `TaskGroup.cancel()` ([What's New in 3.15](https://docs.python.org/3/whatsnew/3.15.html), gh-127214) — a "non-exceptional, early exit of the task group's lifetime" that cancels unfinished tasks and the body but exits *without* raising `CancelledError`; documented as "Added in version 3.15."

**Interpretation:** none of these changed the core model (fail-fast sibling cancellation + grouped exceptions at scope exit); they fixed edge cases (lost/hung cancellations), tightened language semantics around re-raising from `except*`, and added an explicit early-exit API. So code written against 3.11's documented TaskGroup contract behaves identically in current Python except for the 3.13 corner-case fixes — which are bug fixes, not breaking changes.

## Sources
- [asyncio "Coroutines and tasks" (current, 3.15)](https://docs.python.org/3/library/asyncio-task.html) — TaskGroup spec, gather() semantics
- [PEP 654 – Exception Groups and except\*](https://peps.python.org/pep-0654/) — motivation, design rationale
- [What's New in Python 3.11](https://docs.python.org/3/whatsnew/3.11.html) · [3.12](https://docs.python.org/3/whatsnew/3.12.html) · [3.13](https://docs.python.org/3/whatsnew/3.13.html) · [3.15](https://docs.python.org/3/whatsnew/3.15.html)
- [python.org/downloads](https://www.python.org/downloads/) — 3.15.0 release date

Caveat: search engines were largely unresponsive during this research, so all claims above come from direct fetches of the official docs, PEP, and python.org; I did not consult third-party commentary.

---

