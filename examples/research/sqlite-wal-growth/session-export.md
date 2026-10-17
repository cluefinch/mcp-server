# SQLite WAL growth and checkpointing

**Session ID:** ses_ed602284affeR9j4bYB708osp6
**Run date:** 2026-10-11

---

## User

Investigate why an SQLite database running in WAL mode can develop a large WAL file even while reads and writes continue to succeed.
Explain what role long-lived read transactions can play, how checkpointing interacts with readers and writers, and under what conditions the WAL can be reused or truncated.
Compare the practical behavior of the available checkpoint modes and determine what an application can do when the WAL keeps growing.
Also identify any important limitations or edge cases that affect the conclusions.
Support the answer with citations to public sources and clearly distinguish documented behavior from interpretation. 

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

The user is asking for a research task about SQLite's WAL mode: why the WAL file grows large even while reads/writes continue, the role of long-lived read transactions, checkpointing interactions with readers/writers, conditions under which the WAL can be reused/truncated, comparison of checkpoint modes (PASSIVE, FULL, RESTART, TRUNCATE), what applications can do when the WAL keeps growing, limitations/edge cases. With citations to public sources, distinguishing documented behavior from interpretation.

This is a substantial research task. I should use Cluefinch MCP tools: web_search for discovery, then fetch primary sources (SQLite docs: wal.html, c3full.html, pragma page, lang_c3ref.html). Key primary sources:
- https://www.sqlite.org/wal.html — WAL mode documentation
- https://www.sqlite.org/pragma.html#pragma_wal_checkpoint — checkpoint modes
- https://www.sqlite.org/c3ref/wal_autocheckpoint.html
- Possibly the "WAL file" section of wal.html, and discussion of hot journals.

Plan:
1. Search for SQLite WAL documentation (I know the URLs but should verify/fetch).
2. Fetch https://www.sqlite.org/wal.html — read relevant sections on checkpointing, readers, writers, WAL reuse/truncation.
3. Fetch the pragma_wal_checkpoint section of https://www.sqlite.org/pragma.html.
4. Possibly fetch c3ref for sqlite3_wal_checkpoint and wal_autocheckpoint.

Let's start with research_collect using known URLs plus a few queries to pick up additional sources (e.g., SQLite forum threads on WAL growth, long-lived readers blocking checkpoints). Actually, per AGENTS.md: use known strong URLs directly; add search only for missing evidence. I know the primary docs well enough to fetch them directly. But I should verify content with actual fetches rather than memory.

Let me plan the evidence needs:
1. Why WAL grows even while reads/writes succeed — checkpointing is what truncates/reuses the WAL; if checkpoints can't complete (e.g., a long-lived reader holding an old snapshot), the WAL keeps growing. Also, auto-checkpoint default of 1000 pages only runs when a writer commits and no readers are blocking... actually, PASSIVE checkpoints don't block; they stop at frames that active readers need.
2. Role of long-lived read transactions: in WAL mode, readers hold a snapshot (the "read mark"); the WAL cannot be truncated/reused past the oldest reader's read mark. A checkpoint can only overwrite frames not needed by any active reader... actually, for PASSIVE checkpoints: it copies as many frames as possible without blocking; stops if a frame is needed by an active reader. FULL waits for readers to finish (blocks until no readers), then truncates? Let me recall the documented behavior from pragma.html:

From SQLite's docs (pragma_wal_checkpoint):
- "The wal_checkpoint pragma attempts to checkpoint dirty pages in the WAL back into the main database file."
- Modes: PASSIVE, FULL, RESTART, TRUNCATE.
- PASSIVE: "This mode of operation never blocks or causes client connections to execute a rollback. It does as much of the job as possible while allowing continued database activity then stops."
- FULL: "This mode waits until all other database connections have completed or rolled back their transactions and/or checkpoints. Then it checkpoints all dirty frames into the main database file... A full checkpoint is guaranteed to succeed if no other connection starts a read transaction before the checkpoint completes..." Actually, let me recall precisely:

From https://www.sqlite.org/pragma.html#pragma_wal_checkpoint:
- PASSIVE — "This mode of operation never blocks or causes client connections to execute a rollback. It does as much of the job as possible while allowing continued database activity then stops."
- FULL — "This mode waits until all other database connections have completed or rolled back their transactions and/or checkpoints. Then it checkpoints all dirty frames into the main database file... A full checkpoint is guaranteed to succeed if no other connection starts a read transaction before the checkpoint completes, even if there are concurrent writes..." Hmm, I need the exact wording. Let me fetch it.

- RESTART — "This mode works just like FULL except that after checkpointing, it additionally resets the WAL so that it starts from offset zero in the file... A restart checkpoint is guaranteed to succeed if no other connection starts a read transaction before the checkpoint completes..."
- TRUNCATE — "This mode works just like RESTART except that after resetting the WAL, it truncates the WAL file to zero bytes in size."

Also from wal.html:
- "The WAL file grows as needed... The WAL file is reused rather than recreated on each transaction commit. When a checkpoint occurs, the WAL file can be truncated or reset..."
- Key section: "A read-transaction that has been active for a long time prevents the WAL from being truncated." Something like: "If there are no active readers, then the WAL file can be truncated to zero bytes... If there is an active reader, the WAL cannot be truncated past the point needed by the oldest reader."

Also relevant: sqlite3_wal_autocheckpoint (default 1000 pages) — auto-checkpoint runs a PASSIVE checkpoint when the WAL reaches N frames. And "the automatic checkpointing mechanism only operates if there is an active writer" — actually, auto-checkpoints are triggered on commit by a connection that has write access... let me verify: from c3ref/wal_autocheckpoint.html: "By default, SQLite automatically checkpoints the WAL every 1000 pages. ... The automatic checkpointing mechanism only operates when the database is in WAL mode and there is an active writer..." Hmm, I recall it being something like: auto-checkpoint runs after a commit on a connection that has write access to the database... let me fetch to verify.

Also edge cases/limitations:
- Hot journal / recovery at startup; if a process crashes, WAL recovery happens on next open.
- The WAL file cannot be truncated while any reader is active (PASSIVE stops early).
- A long-lived read transaction (e.g., an uncommitted SELECT held by an application, or a connection left open with BEGIN DEFERRED... actually in WAL mode, readers hold the snapshot from when they started reading; even idle connections? No — only connections that have begun a read transaction and not committed/rolled back. A connection that has executed a query but hasn't closed it (e.g., an unfinalized prepared statement holding rows) keeps the read mark.)
- Also: "If a reader is active, checkpoints can still proceed up to the oldest reader's snapshot" — PASSIVE copies frames up to just before the first frame needed by any active reader.
- The WAL file size grows in page-size units; max WAL size... there's no hard limit other than disk space (and 2^31 pages? Actually, is there a documented maximum WAL size of about 4GB? Hmm — I recall "the WAL file can grow to at most..." Let me check: wal.html says something like "The WAL file grows as needed. ... The maximum size of the WAL file is limited by...". I don't remember exactly; need to verify.)
- Also, checkpointing requires write access (a connection with write permission); a read-only connection cannot checkpoint.
- Also, if the database is on NFS or other network filesystems, WAL mode has limitations (file locking).
- Also: "A checkpoint can only be performed by a connection that has write access to the database file." And "If the main database file is read-only, checkpoints are not possible" — actually, in WAL mode with a read-only main DB... there's a documented case: if the main db file is read-only but the -wal and -shm files are writable, readers can still work (the "read-only WAL" scenario).
- Also edge cases: busy timeout; FULL/RESTART/TRUNCATE checkpoints block waiting for readers to finish — with a long-lived reader, they wait until busy_timeout expires and return SQLITE_BUSY. This is important: an application calling wal_checkpoint(TRUNCATE) while a long-lived reader exists will get BUSY after the timeout rather than truncating.
- Also: "The WAL file can only be truncated when no readers are active" — TRUNCATE mode requires that there be no active readers at checkpoint time (otherwise it fails with busy? or does it wait?). Let me verify exact semantics from docs.

Also, why the WAL grows even while reads/writes continue: because checkpoints may not run (auto-checkpoint only runs on commit by a writer connection; if writes are rare... but the user says writes continue). More precisely: auto-checkpoint is PASSIVE and stops at frames needed by active readers; so with long-lived readers, each auto-checkpoint can only advance up to the oldest reader's snapshot, and the WAL keeps growing. Also, if all connections are read-only (no writer), no checkpoint runs at all... but writes continue in this scenario.

Another subtle point: a PASSIVE checkpoint "does as much of the job as possible" — it copies frames that no active reader needs. So with long-lived readers holding old snapshots, the WAL grows unboundedly until those readers finish. This is the core answer.

Also worth noting: sqlite3_wal_checkpoint returns (busy, log, checkpointed) values; busy=1 means a full/restart/truncate checkpoint couldn't complete because of active readers... actually, per c3ref/wal_checkpoint.html: "The return value is an array of three integers: {SQLITE_BUSY, ...}" — the first element is 0 on success or SQLITE_BUSY if the checkpoint could not complete (for FULL/RESTART/TRUNCATE when readers are present and busy timeout expires). The second is the number of frames in the WAL log, the third is the number of frames checkpointed.

Also: "A connection that has write access can perform a checkpoint... A read-only connection cannot." And auto-checkpoint: from c3ref/wal_autocheckpoint.html — "The automatic checkpointing mechanism only operates when there is an active writer..." Hmm, I need to verify exact wording. Let me fetch it.

Also relevant edge cases:
- The -shm file and locking; if the process crashes while holding a read mark... recovery handles it.
- "WAL reuse": after a RESTART checkpoint, the WAL starts from offset zero again (the file is reused). After TRUNCATE, the file is truncated to 0 bytes and grows again. Without a restart/truncate checkpoint, the WAL keeps being written at increasing offsets? Actually no — in normal operation, when a checkpoint completes fully (all frames copied), the WAL can be reset... let me recall wal.html: "When a checkpoint occurs, the WAL file is either truncated or reused..." Hmm.

From wal.html (I'll verify by fetching):
- Section "WAL File": "The WAL file grows as needed to accommodate new transactions. ... The WAL file is not deleted when the last connection closes; it remains on disk... If a checkpoint has occurred and there are no active readers, the WAL file can be truncated to zero bytes."

Actually, I recall this specific documented statement: "If there are no active read-transactions, then the WAL file can be truncated to zero bytes. Otherwise, the WAL file is retained..." Something like that. And: "The WAL file is reused rather than recreated on each transaction commit" — hmm, not exactly; let me fetch and quote precisely.

Also from wal.html's checkpoint section:
- "A checkpoint operation copies pages from the WAL into the main database file."
- "If there are no active readers, a checkpoint can truncate the WAL to zero bytes..."
- Also: "The automatic checkpointing mechanism... every 1000 pages by default (sqlite3_wal_autocheckpoint)."

Also important documented behavior about long-lived readers: from wal.html's "Readers and Writers" section? There's a statement like: "A read-transaction that has been active for a long time prevents the WAL file from being truncated." I think there's something in wal.html along those lines. Let me fetch to verify.

Also, SQLite forum threads (sqlite.org/forum) on "WAL file keeps growing" — good secondary sources. E.g., forum thread about long-lived readers blocking checkpoints. Could search for that.

Plan of tool calls:
1. research_collect with urls=[wal.html, pragma.html] and queries like ["SQLite WAL file grows large checkpoint", "sqlite wal_checkpoint TRUNCATE long-lived reader"] to get excerpts from both primary docs plus possibly forum threads. Actually, research_collect fetches pages and extracts BM25 passages — good for getting targeted excerpts without reading the whole page. But I want precise wording; can expand excerpts with web_fetch using excerpt.expand.arguments.

Better approach:
- Fetch https://www.sqlite.org/wal.html (it's a longish page but manageable, maybe ~15k chars). Use web_fetch with max_chars 20000 and continue if needed.
- Fetch the pragma_wal_checkpoint section of https://www.sqlite.org/pragma.html — this page is huge; better to use research_collect with queries targeting "wal_checkpoint" on that URL, or fetch with a large offset... I don't know the offset. Use research_collect(urls=[pragma.html], queries=["PRAGMA wal_checkpoint modes PASSIVE FULL RESTART TRUNCATE"]) to get targeted excerpts, then expand as needed.
- Fetch https://www.sqlite.org/c3ref/wal_autocheckpoint.html (small page).
- Possibly fetch https://www.sqlite.org/c3ref/wal_checkpoint.html (small page).
- Search for forum threads on WAL growth with long-lived readers for secondary corroboration: web_search "sqlite forum WAL file grows large long-lived reader checkpoint".

Let me batch the independent calls. First round:
1. cluefinch_web_fetch wal.html max_chars 20000 (start 0).
2. cluefinch_research_collect urls=[pragma.html, c3ref/wal_autocheckpoint.html, c3ref/wal_checkpoint.html] queries=["wal_checkpoint PASSIVE FULL RESTART TRUNCATE", "automatic checkpointing WAL every 1000 pages"] max_sources=5.
3. cluefinch_web_search query="sqlite forum WAL file keeps growing long-lived reader checkpoint" (for secondary sources).

Then follow up based on results: expand excerpts, fetch forum threads if useful.

Let me think about what the final answer should contain (structure):
1. Why the WAL grows even while reads/writes succeed — mechanism: commits append frames to the WAL; only checkpoints move frames back into the main DB and allow the WAL to be reset/truncated. Checkpoints are opportunistic (auto-checkpoint is PASSIVE, runs on commit by a writer connection) and can make no progress if active readers hold old snapshots. So reads/writes continue fine while the WAL grows — growth doesn't block anything; it's just uncheckpointed data + frames retained for readers.
2. Role of long-lived read transactions: in WAL mode, each reader holds a snapshot (read mark) from when its transaction began; the WAL cannot be truncated/reused past the oldest active reader's read mark; PASSIVE checkpoints stop at that point. Long-lived readers = unbounded growth until they finish. Examples: an application holding an open cursor/prepared statement across long operations, a connection left in a transaction, a monitoring query.
3. Checkpointing interactions with readers/writers: checkpoint requires write access; copies frames to main DB; PASSIVE never blocks and stops at the oldest reader's need; FULL waits for all readers to finish (blocks up to busy timeout), then checkpoints everything; RESTART = FULL + reset WAL to offset zero (reuse); TRUNCATE = RESTART + truncate file to 0 bytes. Writers: a checkpoint can run concurrently with writers? In WAL mode, only one writer at a time; a checkpoint by another connection... hmm — actually, can a checkpoint run while a write transaction is active on another connection? I think checkpoints are done as part of the commit process or via explicit pragma; if another connection holds the write lock (in a write transaction), the checkpoint waits for it. Let me verify from docs: "A full checkpoint is guaranteed to succeed if no other connection starts a read transaction before the checkpoint completes, even if there are concurrent writes." — I think that's in the FULL description. So concurrent writers are OK; readers are the problem.
4. Conditions under which WAL can be reused/truncated: when no active readers (and no write transaction holding frames?), the WAL can be reset to offset zero (RESTART) or truncated to 0 bytes (TRUNCATE). Also, after a full checkpoint with no readers, SQLite automatically... hmm — does it auto-truncate? I don't think so; without TRUNCATE mode, the file stays at its high-water mark and is reused. Actually wait: there's documented behavior that "when a checkpoint completes and there are no active readers, the WAL file can be truncated to zero bytes" — but does SQLite do this automatically on every full checkpoint? I don't think so; only TRUNCATE mode truncates. But hmm, actually I recall from wal.html: "If there are no active read-transactions, then the WAL file is truncated to zero bytes after a checkpoint." Let me verify carefully by fetching — this matters for accuracy.

Let me try to recall the actual text of wal.html (from memory of the page):
- Section "WAL File": "The WAL file grows as needed... The WAL file is not deleted when the last connection closes; it remains on disk..." Hmm, actually I think there's a statement: "When the last connection to a database in WAL mode closes, the WAL and SHM files are deleted" — no wait, that's for rollback journal? Let me recall: in WAL mode, if the last connection closes cleanly, SQLite deletes the -wal and -shm files (if it can). Yes! I'm fairly confident: "If the last connection to a database in WAL mode closes normally, then the WAL file and SHM file are deleted." Hmm, but there's also the case where they're retained for hot journal recovery... actually no — if the last connection closes cleanly, the WAL is checkpointed (if possible) and the -wal/-shm files are removed. If a process crashes, on next open the WAL is recovered. I think wal.html says: "When the last connection to a database in WAL mode closes, SQLite attempts to delete the WAL file and SHM file." Something like that. Need to verify by fetching.

- Also from wal.html: "The WAL file can be reused... When a checkpoint occurs, if there are no active readers, the WAL file is reset so that it starts again at offset zero" — hmm.

OK, enough guessing; let me fetch and quote precisely.

5. Comparison of practical behavior of checkpoint modes (table):
- PASSIVE: non-blocking, best-effort, stops at oldest reader's need; used by auto-checkpoint; returns busy=0 even if partial? Actually, for PASSIVE, the return value is... per c3ref/wal_checkpoint.html: "If a passive checkpoint succeeds, it returns {0, N, M}..." Hmm — I think PASSIVE always returns 0 in the first element (never busy) since it doesn't wait. Let me verify.
- FULL: blocks waiting for readers to finish; if readers don't finish within busy_timeout → SQLITE_BUSY; on success, all frames are checkpointed but the WAL file is not truncated/reset? Wait — does FULL reset the WAL offset? I think RESTART resets and FULL does not... hmm, actually let me recall from pragma.html:

"FULL: This mode of operation waits until all other database connections have completed or rolled back their transactions and/or checkpoints. Then it checkpoints all dirty frames into the main database file. A full checkpoint is guaranteed to succeed if no other connection starts a read transaction before the checkpoint completes, even if there are concurrent writes." — I don't think FULL resets the WAL offset; RESTART does: "This mode works just like FULL except that after checkpointing, it additionally resets the WAL so that it starts from offset zero in the file. A restart checkpoint is guaranteed to succeed if no other connection starts a read transaction before the checkpoint completes..."

"TRUNCATE: This mode works just like RESTART except that after resetting the WAL, it truncates the WAL file to zero bytes in size."

So the practical difference between FULL and RESTART: both fully checkpoint; RESTART additionally resets the write offset so subsequent writes start from frame 1 (file is reused from the beginning); TRUNCATE also shrinks the file on disk. Without RESTART/TRUNCATE, after a full checkpoint the WAL keeps its size and new frames are appended at increasing offsets? Hmm — actually no: I think even without an explicit restart, when a full checkpoint completes with no readers, SQLite automatically resets the WAL to start from offset zero... let me check wal.html for "restart".

From memory of wal.html's "Checkpointing" section:
- "A checkpoint operation copies pages from the WAL into the main database file. ... If there are no active read-transactions, then a checkpoint can also truncate the WAL file to zero bytes." Hmm.

And I recall this specific documented statement in wal.html: "The WAL file is reused rather than recreated on each transaction commit. When a checkpoint occurs and there are no active readers, the WAL file is reset so that it starts again at offset zero..." Not sure. Let me fetch.

Actually — now I remember more precisely from wal.html (the "WAL File" section):
"The WAL file grows as needed to accommodate new transactions... The WAL file is not deleted when the last connection closes; it remains on disk and can be reused by subsequent connections." Hmm, no...

OK let me just fetch. Also there's a documented statement about maximum WAL size: I think wal.html says something like "The maximum size of the WAL file is limited to..." — hmm, maybe not. There might be a limit related to 2^31 pages? Not sure if documented. Let me check by fetching; if not documented, don't claim it (or note as undocumented).

6. What applications can do when the WAL keeps growing:
- Identify and eliminate long-lived read transactions (close cursors promptly, finalize prepared statements, commit/rollback idle connections; use busy_timeout appropriately).
- Use PRAGMA wal_checkpoint(TRUNCATE) at quiet times (e.g., end of batch job, maintenance window) — requires no active readers to succeed.
- Increase/decrease auto-checkpoint size (sqlite3_wal_autocheckpoint / PRAGMA wal_autocheckpoint=N); note that it only helps if checkpoints can make progress; default 1000 pages.
- Ensure at least one connection has write access for checkpointing (read-only connections cannot checkpoint).
- Monitor with PRAGMA wal_checkpoint(PASSIVE) return values or sqlite3_wal_checkpoint to detect when readers are blocking (busy flag / log vs checkpointed counts).
- If the WAL is huge and you can't stop readers: restart the application/processes holding long-lived reads; as a last resort, close all connections (which triggers recovery/checkpoint on reopen) — note that closing the last connection deletes -wal/-shm.
- Also: keep the database file writable; checkpoints write to the main DB.

7. Limitations/edge cases:
- FULL/RESTART/TRUNCATE block up to busy_timeout and return SQLITE_BUSY if readers persist (they don't force readers out).
- PASSIVE never blocks but may make zero progress — auto-checkpoint silently does nothing while a reader is active; the WAL grows.
- Checkpoints require write access to the main database file; read-only connections cannot checkpoint. If the main DB file is read-only, checkpoints are impossible (though reads can still proceed via the WAL).
- A connection that has begun a read transaction but is idle still holds its snapshot — "long-lived" doesn't mean actively reading; an unfinalized statement or an open transaction counts.
- The oldest reader determines how far the WAL can be truncated/reset, not the newest.
- Concurrent writers don't prevent FULL/RESTART/TRUNCATE from succeeding (per docs), but a checkpoint waits for the write lock... hmm — actually, if another connection is in the middle of a write transaction, does the checkpoint wait? I think so: "waits until all other database connections have completed or rolled back their transactions" — that includes write transactions. So writers also block FULL checkpoints (they must complete/rollback first). But the guarantee statement says it succeeds even with concurrent writes as long as no new readers start... slightly contradictory; let me fetch exact wording and quote carefully.
- NFS/network filesystem caveats for WAL mode in general (documented on wal.html: "WAL mode requires shared memory and file locking... not supported on some network filesystems").
- Hot journal recovery after crash: if a process dies, the next connection to open recovers the WAL; a large WAL means longer recovery time.
- The -shm file must be writable; permissions issues can prevent checkpointing (e.g., read-only directory).
- Also edge case: "If a database is in WAL mode and all connections are closed... the WAL file may remain if it couldn't be deleted" — e.g., on some platforms/filesystems.
- Another documented subtlety: auto-checkpoint only runs when a connection commits a write transaction (i.e., triggered by writers). If writes stop, no more auto-checkpoints run even if readers finish... actually, I think the docs say "The automatic checkpointing mechanism only operates when there is an active writer" — hmm, or does it operate on any commit? Let me verify from c3ref/wal_autocheckpoint.html.

Also worth noting: PRAGMA journal_size_limit (added in 3.7.x?) — truncates the WAL to a specified size after checkpoints... actually, journal_size_limit applies to rollback journals; for WAL mode, "PRAGMA journal_size_limit" also limits the WAL file size? Let me recall: from pragma.html's journal_size_limit: "In WAL mode, this pragma sets the maximum size of the WAL file..." Hmm — I think in WAL mode, after a checkpoint, if the WAL is larger than the limit, it's truncated to that size. Yes! I'm fairly confident: "If the database is in WAL mode, then the journal_size_limit pragma limits the size of the WAL file." Something like: after each checkpoint, SQLite truncates the WAL to at most journal_size_limit bytes (if possible). This is a practical tool for applications. Let me verify by fetching the pragma page section.

OK. Time to execute. First batch (independent):
1. web_fetch https://www.sqlite.org/wal.html max_chars=20000 start 0.
2. research_collect urls=["https://www.sqlite.org/pragma.html", "https://www.sqlite.org/c3ref/wal_autocheckpoint.html", "https://www.sqlite.org/c3ref/wal_checkpoint.html"] queries=["PRAGMA wal_checkpoint PASSIVE FULL RESTART TRUNCATE modes", "wal_autocheckpoint automatic checkpointing 1000 pages", "journal_size_limit WAL mode truncate"] max_sources=5.
3. web_search "sqlite forum WAL file grows large long-lived reader blocking checkpoint" max_results=8.

Then follow up: expand excerpts as needed, fetch forum threads if useful.

Let me also consider fetching https://www.sqlite.org/lang_vacuum.html — no, not relevant. The "hot journal" section of wal.html is covered by the same page.

After gathering evidence, write a structured answer with citations (URLs + section names), clearly marking documented vs interpreted. Keep it organized but reasonably concise; this is a research question so a longer answer is justified ("unless user asks for detail" — the user explicitly asked for a detailed investigation with citations, so a thorough response is appropriate).

Let me execute the first batch now.


**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.sqlite.org/wal.html",
  "max_chars": 20000
}
```

**Output:**
```
{
  "title": "Write-Ahead Logging",
  "url": "https://www.sqlite.org/wal.html",
  "content": "The default method by which SQLite implements\n[atomic commit and rollback](https://www.sqlite.org/atomiccommit.html) is a [rollback journal](https://www.sqlite.org/lockingv3.html#rollback).\nBeginning with [version 3.7.0](https://www.sqlite.org/releaselog/3_7_0.html) (2010-07-21), a new \"Write-Ahead Log\" option\n(hereafter referred to as \"WAL\") is available.\n\nThere are advantages and disadvantages to using WAL instead of a rollback journal. Advantages include:\n\nBut there are also disadvantages:\n\nThe traditional rollback journal works by writing a copy of the\noriginal unchanged database content into a separate rollback journal file\nand then writing changes directly into the database file.  In the\nevent of a crash or [ROLLBACK](https://www.sqlite.org/lang_transaction.html), the original content contained in the\nrollback journal is played back into the database file to\nrevert the database file to its original state.  The [COMMIT](https://www.sqlite.org/lang_transaction.html) occurs\nwhen the rollback journal is deleted.\n\nThe WAL approach inverts this.  The original content is preserved\nin the database file and the changes are appended into a separate\nWAL file.  A [COMMIT](https://www.sqlite.org/lang_transaction.html) occurs when a special record indicating a commit\nis appended to the WAL.  Thus a COMMIT can happen without ever writing\nto the original database, which allows readers to continue operating\nfrom the original unaltered database while changes are simultaneously being\ncommitted into the WAL.  Multiple transactions can be appended to the\nend of a single WAL file.\n\nOf course, one wants to eventually transfer all the transactions that\nare appended in the WAL file back into the original database.  Moving\nthe WAL file transactions back into the database is called a\n\"*checkpoint*\".\n\n\nAnother way to think about the difference between rollback and write-ahead log is that in the rollback-journal approach, there are two primitive operations, reading and writing, whereas with a write-ahead log there are now three primitive operations: reading, writing, and checkpointing.\n\nBy default, SQLite does a checkpoint automatically when the WAL file\nreaches a threshold size of 1000 pages.  (The\n[SQLITE\\_DEFAULT\\_WAL\\_AUTOCHECKPOINT](https://www.sqlite.org/compile.html#default_wal_autocheckpoint) compile-time option can be used to\nspecify a different default.) Applications using WAL do\nnot have to do anything in order for these checkpoints to occur.  \nBut if they want to, applications can adjust the automatic checkpoint\nthreshold.  Or they can turn off the automatic checkpoints and run \ncheckpoints during idle moments or in a separate thread or process.\n\nWhen a read operation begins on a WAL-mode database, it first remembers the location of the last valid commit record in the WAL. Call this point the \"end mark\". Because the WAL can be growing and adding new commit records while various readers connect to the database, each reader can potentially have its own end mark. But for any particular reader, the end mark is unchanged for the duration of the transaction, thus ensuring that a single read transaction only sees the database content as it existed at a single point in time.\n\nWhen a reader needs a page of content, it first checks the WAL to see if that page appears there, and if so it pulls in the last copy of the page that occurs in the WAL prior to the reader's end mark. If no copy of the page exists in the WAL prior to the reader's end mark, then the page is read from the original database file. Readers can exist in separate processes, so to avoid forcing every reader to scan the entire WAL looking for pages (the WAL file can grow to multiple megabytes, depending on how often checkpoints are run), a data structure called the \"wal-index\" is maintained in shared memory which helps readers locate pages in the WAL quickly and with a minimum of I/O. The wal-index greatly improves the performance of readers, but the use of shared memory means that all readers must exist on the same machine. This is why the write-ahead log implementation will not work on a network filesystem.\n\nWriters merely append new content to the end of the WAL file. Because writers do nothing that would interfere with the actions of readers, writers and readers can run at the same time. However, since there is only one WAL file, there can only be one writer at a time.\n\nA checkpoint operation takes content from the WAL file and transfers it back into the original database file. A checkpoint can run concurrently with readers, however the checkpoint must stop when it reaches a page in the WAL that is past the end mark of any current reader. The checkpoint has to stop at that point because otherwise it might overwrite part of the database file that the reader is actively using. The checkpoint remembers (in the wal-index) how far it got and will resume transferring content from the WAL to the database from where it left off on the next invocation.\n\nThus a long-running read transaction can prevent a checkpointer from making progress. But presumably every read transaction will eventually end and the checkpointer will be able to continue.\n\nWhenever a write operation occurs, the writer checks how much progress the checkpointer has made, and if the entire WAL has been transferred into the database and synced and if no readers are making use of the WAL, then the writer will rewind the WAL back to the beginning and start putting new transactions at the beginning of the WAL. This mechanism prevents a WAL file from growing without bound.\n\nWrite transactions are very fast since they only involve writing\nthe content once (versus twice for rollback-journal transactions)\nand because the writes are all sequential.  Further, syncing the\ncontent to the disk is not required, as long as the application is\nwilling to sacrifice durability following a power loss or hard reboot.\n(Writers sync the WAL on every transaction commit if\n[PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) is set to FULL but omit this sync if\n[PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) is set to NORMAL.)\n\nOn the other hand, read performance deteriorates as the WAL file grows in size since each reader must check the WAL file for the content and the time needed to check the WAL file is proportional to the size of the WAL file. The wal-index helps find content in the WAL file much faster, but performance still falls off with increasing WAL file size. Hence, to maintain good read performance it is important to keep the WAL file size down by running checkpoints at regular intervals.\n\nCheckpointing does require sync operations in order to avoid the possibility of database corruption following a power loss or hard reboot. The WAL must be synced to persistent storage prior to moving content from the WAL into the database and the database file must be synced prior to resetting the WAL. Checkpoint also requires more seeking. The checkpointer makes an effort to do as many sequential page writes to the database as it can (the pages are transferred from WAL to database in ascending order) but even then there will typically be many seek operations interspersed among the page writes. These factors combine to make checkpoints slower than write transactions.\n\nThe default strategy is to allow successive write transactions to\ngrow the WAL until the WAL becomes about 1000 pages in size, then to\nrun a checkpoint operation for each subsequent COMMIT until the WAL\nis reset to be smaller than 1000 pages.  By default, the checkpoint will be\nrun automatically by the same thread that does the COMMIT that pushes\nthe WAL over its size limit.  This has the effect of causing most\nCOMMIT operations to be very fast but an occasional COMMIT (those that trigger\na checkpoint) to be much slower.  If that effect is undesirable, then\nthe application can disable automatic checkpointing and run the\nperiodic checkpoints in a separate thread, or separate process.\n(Links to commands and interfaces to accomplish this are\n[shown below](https://www.sqlite.org#how_to_checkpoint).)\n\nNote that with [PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) set to NORMAL, the checkpoint\nis the only operation to issue an I/O barrier or sync operation\n(fsync() on unix or FlushFileBuffers() on windows).  If an application\ntherefore runs checkpoint in a separate thread or process, the main\nthread or process that is doing database queries and updates will never\nblock on a sync operation.  This helps to prevent \"latch-up\" in applications\nrunning on a busy disk drive.  The downside to\nthis configuration is that transactions are no longer durable and\nmight rollback following a power failure or hard reset.\n\nNotice too that there is a tradeoff between average read performance and average write performance. To maximize the read performance, one wants to keep the WAL as small as possible and hence run checkpoints frequently, perhaps as often as every COMMIT. To maximize write performance, one wants to amortize the cost of each checkpoint over as many writes as possible, meaning that one wants to run checkpoints infrequently and let the WAL grow as large as possible before each checkpoint. The decision of how often to run checkpoints may therefore vary from one application to another depending on the relative read and write performance requirements of the application. The default strategy is to run a checkpoint once the WAL reaches 1000 pages and this strategy seems to work well in test applications on workstations, but other strategies might work better on different platforms or for different workloads.\n\nAn SQLite database connection defaults to \n[journal\\_mode=DELETE](https://www.sqlite.org/pragma.html#pragma_journal_mode).  To convert to WAL mode, use the\nfollowing pragma:\n\nPRAGMA journal\\_mode=WAL;\n\nThe journal\\_mode pragma returns a string which is the new journal mode.\nOn success, the pragma will return the string \"`wal`\".  If \nthe conversion to WAL could not be completed (for example, if the [VFS](https://www.sqlite.org/vfs.html)\ndoes not support the necessary shared-memory primitives) then the\njournaling mode will be unchanged and the string returned from the\nprimitive will be the prior journaling mode (for example \"`delete`\").\n\nBy default, SQLite will automatically checkpoint whenever a [COMMIT](https://www.sqlite.org/lang_transaction.html)\noccurs that causes the WAL file to be 1000 pages or more in size, or when the \nlast database connection on a database file closes.  The default \nconfiguration is intended to work well for most applications.\nBut programs that want more control can force a checkpoint\nusing the [wal\\_checkpoint pragma](https://www.sqlite.org/pragma.html#pragma_wal_checkpoint) or by calling the\n[sqlite3\\_wal\\_checkpoint()](https://www.sqlite.org/c3ref/wal_checkpoint.html) C interface.  The automatic checkpoint\nthreshold can be changed or automatic checkpointing can be completely\ndisabled using the [wal\\_autocheckpoint pragma](https://www.sqlite.org/pragma.html#pragma_wal_autocheckpoint) or by calling the\n[sqlite3\\_wal\\_autocheckpoint()](https://www.sqlite.org/c3ref/wal_autocheckpoint.html) C interface.  A program can also \nuse [sqlite3\\_wal\\_hook()](https://www.sqlite.org/c3ref/wal_hook.html) to register a callback to be invoked whenever\nany transaction commits to the WAL.  This callback can then invoke\n[sqlite3\\_wal\\_checkpoint()](https://www.sqlite.org/c3ref/wal_checkpoint.html) or [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) based on whatever\ncriteria it thinks is appropriate.  (The automatic checkpoint mechanism\nis implemented as a simple wrapper around [sqlite3\\_wal\\_hook()](https://www.sqlite.org/c3ref/wal_hook.html).)\n\nAn application can initiate a checkpoint using any writable database\nconnection on the database simply by invoking\n[sqlite3\\_wal\\_checkpoint()](https://www.sqlite.org/c3ref/wal_checkpoint.html) or [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html).\nThere are three subtypes of checkpoints that vary in their aggressiveness:\nPASSIVE, FULL, and RESTART.  The default checkpoint style is PASSIVE, which\ndoes as much work as it can without interfering with other database\nconnections, and which might not run to completion if there are\nconcurrent readers or writers.\nAll checkpoints initiated by [sqlite3\\_wal\\_checkpoint()](https://www.sqlite.org/c3ref/wal_checkpoint.html) and\nby the automatic checkpoint mechanism are PASSIVE.  FULL and RESTART\ncheckpoints try harder to run the checkpoint to completion and can only\nbe initiated by a call to [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html).  See the\n[sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) documentation for additional information\non FULL and RESET checkpoints.\n\nUnlike the other journaling modes, \n[PRAGMA journal\\_mode=WAL](https://www.sqlite.org/pragma.html#pragma_journal_mode) is\npersistent.  If a process sets WAL mode, then closes and reopens the\ndatabase, the database will come back in WAL mode.  In contrast, if\na process sets (for example) PRAGMA journal\\_mode=TRUNCATE and then closes and\nreopens the database will come back up in the default rollback mode of\nDELETE rather than the previous TRUNCATE setting.\n\nThe persistence of WAL mode means that applications can be converted\nto using SQLite in WAL mode without making any changes to the application\nitself.  One has merely to run \"`PRAGMA journal_mode=WAL;`\" on the\ndatabase file(s) using the [command-line shell](https://www.sqlite.org/cli.html) or other utility, then\nrestart the application.\n\nThe WAL journal mode will be set on all connections to the same database file if it is set on any one connection.\n\nWhile a [database connection](https://www.sqlite.org/c3ref/sqlite3.html) is open on a WAL-mode database, SQLite\nmaintains an extra journal file called a \"Write Ahead Log\" or \"WAL File\".\nThe name of this file on disk is usually the name of the database file\nwith an extra \"`-wal`\" suffix, though different naming rules may\napply if SQLite is compiled with [SQLITE\\_ENABLE\\_8\\_3\\_NAMES](https://www.sqlite.org/compile.html#enable_8_3_names).\n\nThe WAL file exists for as long as any [database connection](https://www.sqlite.org/c3ref/sqlite3.html) has the\ndatabase open.  Usually, the WAL file is deleted automatically when the\nlast connection to the database closes.  However, if the last process to\nhave the database open exits without cleanly\nshutting down the database connection, or if the \n[SQLITE\\_FCNTL\\_PERSIST\\_WAL](https://www.sqlite.org/c3ref/c_fcntl_begin_atomic_write.html#sqlitefcntlpersistwal) [file control](https://www.sqlite.org/c3ref/file_control.html) is used, then the WAL file\nmight be retained on disk after all connections to the database have\nbeen closed.  The WAL file is part of the persistent state of the\ndatabase and should be kept with the database if the database is copied\nor moved.  If a database file is separated from its WAL file, then\ntransactions that were previously committed to the database might be lost,\nor the database file might become corrupted.\nThe only safe way to remove a WAL file is\nto open the database file using one of the [sqlite3\\_open()](https://www.sqlite.org/c3ref/open.html) interfaces\nthen immediately close the database using [sqlite3\\_close()](https://www.sqlite.org/c3ref/close.html).\n\nThe [WAL file format](https://www.sqlite.org/fileformat2.html#walformat) is precisely defined and is cross-platform.\n\nOlder versions of SQLite could not read a WAL-mode database that was\nread-only.  In other words, write access was required in order to read a\nWAL-mode database.  This constraint was relaxed beginning with\nSQLite [version 3.22.0](https://www.sqlite.org/releaselog/3_22_0.html) (2018-01-22).\n\nOn newer versions of SQLite, a WAL-mode database on read-only media, or a WAL-mode database that lacks write permission, can still be read as long as one or more of the following conditions are met:\n\nEven though it is possible to open a read-only WAL-mode database,\nit is good practice to convert the database to \n[PRAGMA journal\\_mode=DELETE](https://www.sqlite.org/pragma.html#pragma_journal_mode) prior to burning an\nSQLite database image onto read-only media.\n\nIn normal cases, new content is appended to the WAL file until the\nWAL file accumulates about 1000 pages (and is thus about 4MB \nin size) at which point a checkpoint is automatically run and the WAL file\nis recycled.  The checkpoint does not normally truncate the WAL file\n(unless the [journal\\_size\\_limit pragma](https://www.sqlite.org/pragma.html#pragma_journal_size_limit) is set).  Instead, it merely\ncauses SQLite to start overwriting the WAL file from the beginning.\nThis is done because it is normally faster to overwrite an existing file\nthan to append.  When the last connection to a database closes, that\nconnection does one last checkpoint and then deletes the WAL and its\nassociated shared-memory file, to clean up the disk.\n\nSo in the vast majority of cases, applications need not worry about the WAL file at all. SQLite will automatically take care of it. But it is possible to get SQLite into a state where the WAL file will grow without bound, causing excess disk space usage and slow query speeds. The following bullets enumerate some of the ways that this can happen and how to avoid them.\n\n**Disabling the automatic checkpoint mechanism.**\nIn its default configuration, SQLite will checkpoint the WAL file at the\nconclusion of any transaction when the WAL file is more than 1000 pages\nlong.  However, compile-time and run-time options exist that can disable\nor defer this automatic checkpoint.  If an application disables the\nautomatic checkpoint, then there is nothing to prevent the WAL file\nfrom growing excessively.\n\n**Checkpoint starvation.**\nA checkpoint is only able to run to completion, and reset the WAL file,\nif there are no other database connections using the WAL file.  If another\nconnection has a read transaction open,\nthen the checkpoint cannot reset the WAL file because\ndoing so might delete content out from under the reader.\nThe checkpoint will do as much work as it can without upsetting the\nreader, but it cannot run to completion.\nThe checkpoint will start up again where it left off after the next\nwrite transaction.  This repeats until some checkpoint is able to complete.\n\nHowever, if a database has many concurrent overlapping readers and there is always at least one active reader, then no checkpoints will be able to complete and hence the WAL file will grow without bound.\n\nThis scenario can be avoided by ensuring that there are \"reader gaps\":\ntimes when no processes are reading from the \ndatabase and that checkpoints are attempted during those times.\nIn applications with many concurrent readers, one might also consider \nrunning manual checkpoints with the [SQLITE\\_CHECKPOINT\\_RESTART](https://www.sqlite.org/c3ref/c_checkpoint_full.html) or\n[SQLITE\\_CHECKPOINT\\_TRUNCATE](https://www.sqlite.org/c3ref/c_checkpoint_full.html) option which will ensure that the checkpoint\nruns to completion before returning.  The disadvantage of using\n[SQLITE\\_CHECKPOINT\\_RESTART](https://www.sqlite.org/c3ref/c_checkpoint_full.html) and [SQLITE\\_CHECKPOINT\\_TRUNCATE](https://www.sqlite.org/c3ref/c_checkpoint_full.html) is that\nreaders might block while the checkpoint is running.\n\n**Very large write transactions.**\nA checkpoint can only complete when no other transactions are running, \nwhich means the WAL file cannot be reset in the middle of a write\ntransaction.  So a large change to a large database\nmight result in a large WAL file.  The WAL file will be checkpointed\nonce the write transaction completes (assuming there are no other readers\nblocking it) but in the meantime, the file can grow very big.",
  "total_chars": 30929,
  "next_start": 19949,
  "truncated": true,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "5e84ac63b99e78226b7f0c473726d33a62a2eb40501b739c5657e1d1a7da50c7",
  "continuation": {
    "tool": "web_fetch",
    "arguments": {
      "url": "https://www.sqlite.org/wal.html",
      "start_offset": 19949,
      "max_chars": 20000,
      "expected_content_hash": "5e84ac63b99e78226b7f0c473726d33a62a2eb40501b739c5657e1d1a7da50c7"
    }
  }
}
```

**Tool: cluefinch_research_collect**

**Input:**
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

**Output:**
```
{
  "query_variants": [
    "PRAGMA wal_checkpoint PASSIVE FULL RESTART TRUNCATE modes behavior readers",
    "wal_autocheckpoint automatic checkpointing every 1000 pages writer",
    "journal_size_limit WAL mode truncate size of WAL file"
  ],
  "sources": [
    {
      "title": "PRAGMA Statements",
      "url": "https://www.sqlite.org/pragma.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "**PRAGMA** *schema.***wal\\_checkpoint(TRUNCATE);**",
          "start_char": 88094,
          "end_char": 88144,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/pragma.html",
              "start_offset": 88094,
              "max_chars": 3000,
              "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
            }
          }
        },
        {
          "text": "**PRAGMA** *schema.***wal\\_checkpoint(PASSIVE);**",
          "start_char": 87944,
          "end_char": 87993,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/pragma.html",
              "start_offset": 87944,
              "max_chars": 3000,
              "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
            }
          }
        },
        {
          "text": "**PRAGMA** *schema.***wal\\_checkpoint(RESTART);**",
          "start_char": 88043,
          "end_char": 88092,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/pragma.html",
              "start_offset": 88043,
              "max_chars": 3000,
              "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
            }
          }
        }
      ],
      "source_id": "src_f8124ebf5d1023e1",
      "text_truncated": false,
      "content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
    },
    {
      "title": "Configure an auto-checkpoint",
      "url": "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "Every new [database connection](https://www.sqlite.org/c3ref/sqlite3.html) defaults to having the auto-checkpoint\nenabled with a threshold of 1000 or [SQLITE\\_DEFAULT\\_WAL\\_AUTOCHECKPOINT](https://www.sqlite.org/compile.html#default_wal_autocheckpoint)\npages.",
          "start_char": 1210,
          "end_char": 1469,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
              "start_offset": 1210,
              "max_chars": 3000,
              "expected_content_hash": "5de63a4aaeff9c7f062ef791867ee255fb46f2fe36f11f9389768660eb18cd0e"
            }
          }
        },
        {
          "text": "The [wal\\_autocheckpoint pragma](https://www.sqlite.org/pragma.html#pragma_wal_autocheckpoint) can be used to invoke this interface\nfrom SQL.",
          "start_char": 958,
          "end_char": 1099,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
              "start_offset": 958,
              "max_chars": 3000,
              "expected_content_hash": "5de63a4aaeff9c7f062ef791867ee255fb46f2fe36f11f9389768660eb18cd0e"
            }
          }
        },
        {
          "text": "The [sqlite3\\_wal\\_autocheckpoint(D,N)](https://www.sqlite.org/c3ref/wal_autocheckpoint.html) is a wrapper around\n[sqlite3\\_wal\\_hook()](https://www.sqlite.org/c3ref/wal_hook.html) that causes any database on [database connection](https://www.sqlite.org/c3ref/sqlite3.html) D\nto automatically [checkpoint](https://www.sqlite.org/wal.html#ckpt)\nafter committing a transaction if there are N or\nmore frames in the [write-ahead log](https://www.sqlite.org/wal.html) file.  Passing zero or\na negative",
          "start_char": 56,
          "end_char": 552,
          "heading": null,
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
              "start_offset": 56,
              "max_chars": 3000,
              "expected_content_hash": "5de63a4aaeff9c7f062ef791867ee255fb46f2fe36f11f9389768660eb18cd0e"
            }
          }
        }
      ],
      "source_id": "src_beccea90b39075e4",
      "text_truncated": false,
      "content_hash": "5de63a4aaeff9c7f062ef791867ee255fb46f2fe36f11f9389768660eb18cd0e"
    },
    {
      "title": "Checkpoint a database",
      "url": "https://www.sqlite.org/c3ref/wal_checkpoint.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "In brief, sqlite3\\_wal\\_checkpoint(D,X) causes the content in the\n[write-ahead log](https://www.sqlite.org/wal.html) for database X on [database connection](https://www.sqlite.org/c3ref/sqlite3.html) D to be\ntransferred into the database file and for the write-ahead log to\nbe reset.  See the [checkpointing](https://www.sqlite.org/wal.html#ckpt) documentation for addition\ninformation.",
          "start_char": 292,
          "end_char": 678,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/c3ref/wal_checkpoint.html",
              "start_offset": 292,
              "max_chars": 3000,
              "expected_content_hash": "c40f9bef0e8bb6c484143377d0b45bb7c9c7127d4b9b9f5fe11c620161834b7c"
            }
          }
        },
        {
          "text": "This interface used to be the only way to cause a checkpoint to\noccur.  But then the newer and more powerful [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)\ninterface was added.  This interface is retained for backwards\ncompatibility and as a convenience for applications that need to manually\nstart a callback but which do not need the full power (and corresponding\ncomplication) of",
          "start_char": 680,
          "end_char": 1101,
          "heading": null,
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/c3ref/wal_checkpoint.html",
              "start_offset": 680,
              "max_chars": 3000,
              "expected_content_hash": "c40f9bef0e8bb6c484143377d0b45bb7c9c7127d4b9b9f5fe11c620161834b7c"
            }
          }
        }
      ],
      "source_id": "src_b189f766b2f0f613",
      "text_truncated": false,
      "content_hash": "c40f9bef0e8bb6c484143377d0b45bb7c9c7127d4b9b9f5fe11c620161834b7c"
    }
  ],
  "gaps": [
    "query 'PRAGMA wal_checkpoint PASSIVE FULL RESTART TRUNCATE modes behavior readers': unresponsive engines: brave, google, google cse",
    "query 'PRAGMA wal_checkpoint PASSIVE FULL RESTART TRUNCATE modes behavior readers': 0 results",
    "query 'wal_autocheckpoint automatic checkpointing every 1000 pages writer': unresponsive engines: brave, google, google cse, wikidata",
    "query 'wal_autocheckpoint automatic checkpointing every 1000 pages writer': 0 results",
    "query 'journal_size_limit WAL mode truncate size of WAL file': unresponsive engines: brave, google, google cse",
    "query 'journal_size_limit WAL mode truncate size of WAL file': 0 results"
  ]
}
```

**Tool: cluefinch_web_search**

**Input:**
```json
{
  "query": "sqlite forum WAL file keeps growing long-lived reader blocking checkpoint",
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
  "query_used": "sqlite forum WAL file keeps growing long-lived reader blocking checkpoint",
  "cached": false
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

Good progress. The first fetch of wal.html gave me most of the important content (30929 chars total, fetched up to 19949). Let's continue fetching the rest of wal.html (from offset 19949) — it probably contains sections on "how to checkpoint", hot journals, and so on.

The research_collect against pragma.html only returned small excerpts (just the syntax lines for PRAGMA wal_checkpoint(...)). I need the full description text of each mode. The excerpt at start_char 87944 is just a syntax line. Let's fetch around that region of pragma.html with web_fetch — say, from about 87500 to 92000 (max_chars 20000) to capture the full description text for PASSIVE/FULL/RESTART/TRUNCATE.

Also, I need the journal_size_limit section of pragma.html too. Let's search for it — either fetch a larger window or use research_collect with a different query. The BM25 excerpts didn't include journal_size_limit. Let's fetch pragma.html around wal_checkpoint (offset ~87000-91000) and separately look for the location of journal_size_limit. I don't know its offset. Options: web_fetch can't search within a page. research_collect with query "journal_size_limit" against that URL should rank excerpts containing it. The earlier collect had 3 queries, but only returned excerpts from pragma.html matching wal_checkpoint (the other two queries matched the c3ref pages). Let's run another research_collect with urls=[pragma.html] and queries=["journal_size_limit WAL mode", "wal_autocheckpoint pragma threshold"].

Also, fetch the full text of c3ref/wal_autocheckpoint.html (small page) — expand the excerpt at offset 56 with max_chars 3000 to get the whole thing. And also c3ref/wal_checkpoint_v2.html for the FULL/RESTART/TRUNCATE semantics and return values. Let's fetch that page too: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — small, so web_fetch with max_chars 10000 should be enough.

Also, the search engine is mostly unresponsive (brave/google are down; only wikipedia/wikidata seem to work?). The forum thread search returned 0 results. I could try a different query or use the wikipedia engine… actually, for secondary sources, sqlite.org/forum threads would be ideal. Let's try web_search with engines=["wikipedia"]? That won't find forum threads. Try research_collect with queries about WAL growth — but the search engines are unresponsive (brave, google, google cse all down). Only wikidata/wikipedia might work. Hmm. The gaps show "unresponsive engines: brave, google, google cse" and 0 results. So web-based discovery is limited right now. I can try fetching known forum thread URLs directly if I know them — but I shouldn't guess URLs.

Alternative secondary sources: the SQLite docs themselves are the primary source, which is ideal here (documented behavior). For "practical behavior", the docs' own guidance section ("It is possible to get SQLite into a state where the WAL file will grow without bound...") covers it well. I could also try fetching https://www.sqlite.org/faq.html — there's an FAQ entry about WAL mode! The FAQ has questions like "Why does my database file in WAL mode have -wal and -shm files?" or "How do I checkpoint?". Let me check: sqlite.org/faq.html has a section on WAL. Yes, the FAQ includes Q&A about WAL (e.g., "What is the difference between..."). Let's fetch faq.html with research_collect using queries about WAL growth/checkpointing.

Plan for next batch (independent):
1. web_fetch wal.html continuation start_offset=19949 max_chars=20000 (with hash).
2. web_fetch pragma.html start_offset ~87300 max_chars 20000 — need to capture the full text of the wal_checkpoint section. The syntax line is at 87944; the description probably follows after all four syntax lines (PASSIVE at 87944, RESTART at 88043, TRUNCATE at 88094). So the descriptive prose starts around ~88150. Let's fetch from 87600 with max_chars 20000 to be safe (covers syntax + description + probably the start of the next section).
3. web_fetch c3ref/wal_checkpoint_v2.html max_chars 12000.
4. research_collect urls=[https://www.sqlite.org/faq.html, https://www.sqlite.org/c3ref/wal_autocheckpoint.html] queries=["WAL file grow without bound checkpoint", "journal_size_limit WAL"] — hmm, journal_size_limit is in pragma.html; let's include pragma.html again with that query: urls=[pragma.html, faq.html], queries=["journal_size_limit maximum size of the WAL file", "FAQ WAL mode -wal -shm files"].

Wait — for pragma.html I already have content_hash ce51e8... from research_collect. web_fetch without expected_content_hash is fine (unguarded read).

Let's run these four in parallel.


I've obtained most of the primary documentation on wal.html. Next, I'll fetch the remaining portion of that page, along with the detailed descriptions of each checkpoint mode and the related C API pages.



**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.sqlite.org/wal.html",
  "start_offset": 19949,
  "max_chars": 20000,
  "expected_content_hash": "5e84ac63b99e78226b7f0c473726d33a62a2eb40501b739c5657e1d1a7da50c7"
}
```

**Output:**
```
{
  "title": "Write-Ahead Logging",
  "url": "https://www.sqlite.org/wal.html",
  "content": "\n\nAs of SQLite [version 3.11.0](https://www.sqlite.org/releaselog/3_11_0.html) (2016-02-15), \nthe WAL file for a single transaction\nshould be proportional in size to the transaction itself.  Pages that\nare changed by the transaction should only be written into the WAL file\nonce.  However, with older versions of SQLite, the same page might be\nwritten into the WAL file multiple times if the transaction grows larger\nthan the page cache.\n\nThe [wal-index](https://www.sqlite.org/walformat.html#shm) is implemented using an ordinary file that is\nmmapped for robustness.  Early (pre-release) implementations of WAL mode\nstored the wal-index in volatile shared-memory, such as files created in\n/dev/shm on Linux or /tmp on other unix systems.  The problem\nwith that approach is that processes with a different root directory\n(changed via [chroot](http://en.wikipedia.org/wiki/Chroot))\nwill see different files and hence use different shared memory areas,\nleading to database corruption.  Other methods for creating nameless\nshared memory blocks are not portable across the various flavors of\nunix.  And we could not find any method to create nameless shared\nmemory blocks on windows.  The only way we have found to guarantee\nthat all processes accessing the same database file use the same shared\nmemory is to create the shared memory by mmapping a file in the same\ndirectory as the database itself.\n\nUsing an ordinary disk file to provide shared memory has the disadvantage that it might actually do unnecessary disk I/O by writing the shared memory to disk. However, the developers do not think this is a major concern since the wal-index rarely exceeds 32 KiB in size and is never synced. Furthermore, the wal-index backing file is deleted when the last database connection disconnects, which often prevents any real disk I/O from ever happening.\n\nSpecialized applications for which the default implementation of\nshared memory is unacceptable can devise alternative methods via a\ncustom [VFS](https://www.sqlite.org/vfs.html).  \nFor example, if it is known that a particular database\nwill only be accessed by threads within a single process, the wal-index\ncan be implemented using heap memory instead of true shared memory.\n\nBeginning in SQLite [version 3.7.4](https://www.sqlite.org/releaselog/3_7_4.html) (2010-12-07), \nWAL databases can be created, read, and\nwritten even if shared memory is unavailable as long as the\n[locking\\_mode](https://www.sqlite.org/pragma.html#pragma_locking_mode) is set to EXCLUSIVE before the first attempted access.\nIn other words, a process can interact with\na WAL database without using shared memory if that\nprocess is guaranteed to be the only process accessing the database.\nThis feature allows WAL databases to be created, read, and written\nby legacy [VFSes](https://www.sqlite.org/vfs.html) that lack the \"version 2\" shared-memory\nmethods xShmMap, xShmLock, xShmBarrier, and xShmUnmap on the\n[sqlite3\\_io\\_methods](https://www.sqlite.org/c3ref/io_methods.html) object.\n\nIf [EXCLUSIVE locking mode](https://www.sqlite.org/pragma.html#pragma_locking_mode)\nis set prior to the first WAL-mode \ndatabase access, then SQLite never attempts to call any of the\nshared-memory methods and hence no shared-memory\nwal-index is ever created.\nIn that case, the database connection remains in EXCLUSIVE mode\nas long as the journal mode is WAL; attempts to change the locking\nmode using \"`PRAGMA locking_mode=NORMAL;`\" are no-ops.\nThe only way to change out of EXCLUSIVE locking mode is to first\nchange out of WAL journal mode.\n\nIf NORMAL locking mode is in effect for the first WAL-mode database access, then the shared-memory wal-index is created. This means that the underlying VFS must support the \"version 2\" shared-memory. If the VFS does not support shared-memory methods, then the attempt to open a database that is already in WAL mode, or the attempt to convert a database into WAL mode, will fail. As long as exactly one connection is using a shared-memory wal-index, the locking mode can be changed freely between NORMAL and EXCLUSIVE. It is only when the shared-memory wal-index is omitted, when the locking mode is EXCLUSIVE prior to the first WAL-mode database access, that the locking mode is stuck in EXCLUSIVE.\n\nThe [second advantage of WAL-mode](https://www.sqlite.org/wal.html#advantages) is that\nwriters do not block readers and readers do not block writers.\nThis is <u>mostly</u> true.\nBut there are some obscure cases where a query against a WAL-mode\ndatabase can return [SQLITE\\_BUSY](https://www.sqlite.org/rescode.html#busy), so applications should be prepared\nfor that happenstance.\n\nCases where a query against a WAL-mode database can return [SQLITE\\_BUSY](https://www.sqlite.org/rescode.html#busy)\ninclude the following:\n\nIf another database connection has the database mode open\nin [exclusive locking mode](https://www.sqlite.org/pragma.html#pragma_locking_mode) then all queries against the\ndatabase will return [SQLITE\\_BUSY](https://www.sqlite.org/rescode.html#busy).  Both Chrome and Firefox open their\ndatabase files in exclusive locking mode, so attempts to read Chrome or\nFirefox databases while the applications are running will run into this\nproblem, for example.\n\nWhen the last connection to a particular database is closing,\nthat connection will acquire an exclusive lock for a short time while\nit cleans up the WAL and shared-memory files.  If a separate attempt\nis made to open and query the database while the first connection is\nstill in the middle of its cleanup process, the second connection\nmight get an [SQLITE\\_BUSY](https://www.sqlite.org/rescode.html#busy) error.\n\nIf the last connection to a database crashed, then the first new\nconnection to open the database will start a recovery process.  An\nexclusive lock is held during recovery.  So if a third database connection\ntries to jump in and query while the second connection is running recovery,\nthe third connection will get an [SQLITE\\_BUSY](https://www.sqlite.org/rescode.html#busy) error.\n\nThe database file format is unchanged for WAL mode.  However, the\nWAL file and the [wal-index](https://www.sqlite.org/walformat.html#shm) are new concepts and so older versions of \nSQLite will not know\nhow to recover a crashed SQLite database that was operating in WAL mode\nwhen the crash occurred.\nTo prevent older versions of SQLite (prior to version 3.7.0, 2010-07-22)\nfrom trying to recover\na WAL-mode database (and making matters worse) the database file format\nversion numbers (bytes 18 and 19 in the [database header](https://www.sqlite.org/fileformat2.html#database_header))\nare increased from 1 to 2 in WAL mode.\nThus, if an older version of SQLite attempts to connect to an SQLite\ndatabase that is operating in WAL mode, it will report an error along\nthe lines of \"file is encrypted or is not a database\".\n\nOne can explicitly change out of WAL mode using a pragma such as this:\n\nPRAGMA journal\\_mode=DELETE;\n\nDeliberately changing out of WAL mode changes the database file format version numbers back to 1 so that older versions of SQLite can once again access the database file.\n\nOn 2026-03-03, one of the SQLite developers (Dan) found and fixed a bug that could, in rare cases, lead to database corruption. We call this the \"WAL-reset bug\". Key points:\n\nThe bug is likely present in all version of SQLite from\n3.7.0 (2010-07-21) through 3.51.2 (2026-01-09).  It is\nfixed in version 3.51.3 (2026-03-13) and later.  Backports of the fix\nare available for some earlier releases:\n[3.44.6](https://sqlite.org/src/info/863c171b76cd36e0) and\n[3.50.7](https://sqlite.org/src/info/c7facf7ac58d2cda).\n\nThe bug only affects databases in WAL mode when there are two or more database connections open on the same file, in separate threads or processes, and when those two connections attempt to write or checkpoint at the same instant.\n\nThe bug is a data race with tight timing constraints and that requires an unusual usage pattern. It is unlikely to occur in common use. The developers were unable to reproduce the bug organically and had to add special testing logic to SQLite that deliberately triggers the circumstances of the the bug in order to verify that the issue has been fixed.\n\nThis is what happens:\n\nOne connection does a [checkpoint](https://www.sqlite.org/wal.html#ckpt).  This first checkpoint must be\ncomplete.  In other words, the checkpoint must successfully copy all\ncontent from the WAL file back into the database and leave the WAL file\nin a state where it can potentially be reset.\n\nShortly after the first checkpoint completes, a second checkpoint is started.\n\nWhile the second checkpoint from step 2 is starting up, another database connection commits a transaction that resets the WAL file and writes new content into the beginning of the WAL file.\n\nDue to a data race, the second checkpoint from step 2 does not realize that the WAL file has been reset by the transaction commit in step 3. The second checkpoint leaves a field in the header of the WAL-Index set incorrectly. That field indicates that part of the WAL file has already been checkpointed, when in fact it has not been.\n\nAdditional transactions are committed to increase the number of pages in the WAL file to be more than were present for the first checkpoint from step 1.\n\nLater when a third checkpoint occurs, the third checkpoint skips all or part of the transaction that was written in step 3. Thus parts of the transaction from step 3 never reach the database file, and the database file goes corrupt.\n\nIn order for this bug to happen, many details must align at just\nthe right moment.  So much so that the SQLite developers were unable\nto reproduce the bug organically in the lab.  The only way the developers\nhave been able to cause the malfunction was to modify the SQLite sources\nto invoke a callback controlled by [sqlite3\\_test\\_control()](https://www.sqlite.org/c3ref/test_control.html)\nthat enables a test program or script to trigger the write transaction \nof step 3 at just the right moment during the second checkpoint.\nWithout that code hack, the problem has never been observed during \ndevelopment and testing.\n\n**UPDATE: 2026-08-24 →**  Phil Eaton has devised\na reproducer that does not involve using the special testing code hack.\nSee [Another look at SQLite's WAL-Reset bug](https://theconsensus.dev/p/2026/08/23/another-look-at-sqlite-wal-reset.html)\nfor details.\n\nThis bug, though rare, does have serious consequences, and so application developers should upgrade to a version of SQLite that fixes the problem. However, this is not an emergency. Based on available telemetry, the occurrence rate of this problem in the wild appears to be less than or equal to the expected occurrence rate of SSD malfunctions and/or cosmic-ray hits. So even if you are running an unpatched version of SQLite, and unless you are doing something really unusual, you are unlikely to ever encounter this problem.\n\n*This page was last updated on 2026-08-25 19:42:39Z*",
  "total_chars": 30929,
  "next_start": null,
  "truncated": false,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "5e84ac63b99e78226b7f0c473726d33a62a2eb40501b739c5657e1d1a7da50c7",
  "continuation": null
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.sqlite.org/pragma.html",
  "start_offset": 87400,
  "max_chars": 16000
}
```

**Output:**
```
{
  "title": "PRAGMA Statements",
  "url": "https://www.sqlite.org/pragma.html",
  "content": "e auto-checkpoint size to zero or a negative value\n    turns auto-checkpointing off.\n\nThis pragma is a wrapper around the\n    [sqlite3\\_wal\\_autocheckpoint()](https://www.sqlite.org/c3ref/wal_autocheckpoint.html) C interface.\n    All automatic checkpoints are [PASSIVE](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html).\n\nAutocheckpointing is enabled by default with an interval\n    of 1000 or [SQLITE\\_DEFAULT\\_WAL\\_AUTOCHECKPOINT](https://www.sqlite.org/compile.html#default_wal_autocheckpoint).\n\n**PRAGMA** *schema.***wal\\_checkpoint;**\n\n**PRAGMA** *schema.***wal\\_checkpoint(PASSIVE);**\n\n**PRAGMA** *schema.***wal\\_checkpoint(FULL);**\n\n**PRAGMA** *schema.***wal\\_checkpoint(RESTART);**\n\n**PRAGMA** *schema.***wal\\_checkpoint(TRUNCATE);**\n\n**PRAGMA** *schema.***wal\\_checkpoint(NOOP);**\n\nIf the [write-ahead log](https://www.sqlite.org/wal.html) is enabled (via the [journal\\_mode pragma](https://www.sqlite.org/pragma.html#pragma_journal_mode)),\n    this pragma causes a [checkpoint](https://www.sqlite.org/wal.html#ckpt) operation to run on database\n    *database*, or on all attached databases if *database*\n    is omitted.  If [write-ahead log](https://www.sqlite.org/wal.html) mode is disabled, this pragma is a\n    harmless no-op.\n\nInvoking this\n    pragma without an argument is equivalent to calling the\n    [sqlite3\\_wal\\_checkpoint()](https://www.sqlite.org/c3ref/wal_checkpoint.html) C interface.\n\nThe wal\\_checkpoint pragma returns a single row with three\n    integer columns.  The first column is usually 0 but will be\n    1 if a RESTART or FULL or TRUNCATE checkpoint was blocked from completing,\n    for example because another thread or process was actively\n    using the database.  In other words, the first column is 0 if the\n    equivalent call to [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) would have returned\n    [SQLITE\\_OK](https://www.sqlite.org/rescode.html#ok) or 1 if the equivalent call would have returned [SQLITE\\_BUSY](https://www.sqlite.org/rescode.html#busy).\n    The second column is the number of modified pages that have been\n    written to the write-ahead log file.\n    The third column is the number of pages in the write-ahead log file\n    that have been successfully moved back into the database file at\n    the conclusion of the checkpoint.\n   The second and third column are -1 if there is no\n    write-ahead log, for example if this pragma is invoked on a database\n    connection that is not in [WAL mode](https://www.sqlite.org/wal.html).\n\n**PRAGMA writable\\_schema  =** *boolean***;**\n\n**PRAGMA writable\\_schema = RESET**\n\nWhen this pragma is on, and the [SQLITE\\_DBCONFIG\\_DEFENSIVE](https://www.sqlite.org/c3ref/c_dbconfig_defensive.html#sqlitedbconfigdefensive) flag\n    is off, then the [sqlite\\_schema](https://www.sqlite.org/schematab.html) table\n    can be changed using ordinary [UPDATE](https://www.sqlite.org/lang_update.html), [INSERT](https://www.sqlite.org/lang_insert.html), and [DELETE](https://www.sqlite.org/lang_delete.html)\n    statements.  If the argument is \"RESET\" then schema writing is\n    disabled (as with \"PRAGMA writable\\_schema=OFF\") and, in addition, the\n    schema is reloaded.  **Warning:**\n    misuse of this pragma can easily result in\n    a [corrupt database file](https://www.sqlite.org/howtocorrupt.html#cfgerr).\n\n*This page was last updated on 2026-10-04 10:38:19Z*",
  "total_chars": 90797,
  "next_start": null,
  "truncated": false,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a",
  "continuation": null
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.sqlite.org/c3ref/wal_checkpoint_v2.html",
  "max_chars": 14000
}
```

**Output:**
```
{
  "title": "Checkpoint a database",
  "url": "https://www.sqlite.org/c3ref/wal_checkpoint_v2.html",
  "content": "int sqlite3\\_wal\\_checkpoint\\_v2( sqlite3 \\*db, /\\* Database handle \\*/ const char \\*zDb, /\\* Name of attached database (or NULL) \\*/ int eMode, /\\* SQLITE\\_CHECKPOINT\\_\\* value \\*/ int \\*pnLog, /\\* OUT: Size of WAL log in frames \\*/ int \\*pnCkpt /\\* OUT: Total number of frames checkpointed \\*/ );\n\nThe sqlite3\\_wal\\_checkpoint\\_v2(D,X,M,L,C) interface runs a checkpoint\noperation on database X of [database connection](https://www.sqlite.org/c3ref/sqlite3.html) D in mode M.  Status\ninformation is written back into integers pointed to by L and C.\nThe M parameter must be a valid [checkpoint mode](https://www.sqlite.org/c3ref/c_checkpoint_full.html):\n\nIf pnLog is not NULL, then \\*pnLog is set to the total number of frames in\nthe log file or to -1 if the checkpoint could not run because\nof an error or because the database is not in [WAL mode](https://www.sqlite.org/wal.html). If pnCkpt is not\nNULL,then \\*pnCkpt is set to the total number of checkpointed frames in the\nlog file (including any that were already checkpointed before the function\nwas called) or to -1 if the checkpoint could not run due to an error or\nbecause the database is not in WAL mode. Note that upon successful\ncompletion of an SQLITE\\_CHECKPOINT\\_TRUNCATE, the log file will have been\ntruncated to zero bytes and so both \\*pnLog and \\*pnCkpt will be set to zero.\n\nAll calls obtain an exclusive \"checkpoint\" lock on the database file. If any other process is running a checkpoint operation at the same time, the lock cannot be obtained and SQLITE\\_BUSY is returned. Even if there is a busy-handler configured, it will not be invoked in this case.\n\nThe SQLITE\\_CHECKPOINT\\_FULL, RESTART and TRUNCATE modes also obtain the exclusive \"writer\" lock on the database file. If the writer lock cannot be obtained immediately, and a busy-handler is configured, it is invoked and the writer lock retried until either the busy-handler returns 0 or the lock is successfully obtained. The busy-handler is also invoked while waiting for database readers as described above. If the busy-handler returns 0 before the writer lock is obtained or while waiting for database readers, the checkpoint operation proceeds from that point in the same way as SQLITE\\_CHECKPOINT\\_PASSIVE - checkpointing as many frames as possible without blocking any further. SQLITE\\_BUSY is returned in this case.\n\nIf parameter zDb is NULL or points to a zero length string, then the\nspecified operation is attempted on all WAL databases [attached](https://www.sqlite.org/lang_attach.html) to\n[database connection](https://www.sqlite.org/c3ref/sqlite3.html) db.  In this case the\nvalues written to output parameters \\*pnLog and \\*pnCkpt are undefined. If\nan SQLITE\\_BUSY error is encountered when processing one or more of the\nattached WAL databases, the operation is still attempted on any remaining\nattached databases and SQLITE\\_BUSY is returned at the end. If any other\nerror occurs while processing an attached database, processing is abandoned\nand the error code is returned to the caller immediately. If no error\n(SQLITE\\_BUSY or otherwise) is encountered while processing the attached\ndatabases, SQLITE\\_OK is returned.\n\nIf database zDb is the name of an attached database that is not in WAL mode, SQLITE\\_OK is returned and both \\*pnLog and \\*pnCkpt set to -1. If zDb is not NULL (or a zero length string) and is not the name of any attached database, SQLITE\\_ERROR is returned to the caller.\n\nUnless it returns SQLITE\\_MISUSE,\nthe sqlite3\\_wal\\_checkpoint\\_v2() interface\nsets the error information that is queried by\n[sqlite3\\_errcode()](https://www.sqlite.org/c3ref/errcode.html) and [sqlite3\\_errmsg()](https://www.sqlite.org/c3ref/errcode.html).\n\nThe [PRAGMA wal\\_checkpoint](https://www.sqlite.org/pragma.html#pragma_wal_checkpoint) command can be used to invoke this interface\nfrom SQL.",
  "total_chars": 3840,
  "next_start": null,
  "truncated": false,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "63f63615a17003571b966dee9a93324e351f433bbe9c67131596fd1b5822cec1",
  "continuation": null
}
```

**Tool: cluefinch_research_collect**

**Input:**
```json
{
  "urls": [
    "https://www.sqlite.org/pragma.html",
    "https://www.sqlite.org/faq.html"
  ],
  "queries": [
    "journal_size_limit maximum size of the WAL file truncate after checkpoint",
    "WAL mode -wal -shm files grow checkpoint FAQ"
  ],
  "max_sources": 4
}
```

**Output:**
```
{
  "query_variants": [
    "journal_size_limit maximum size of the WAL file truncate after checkpoint",
    "WAL mode -wal -shm files grow checkpoint FAQ"
  ],
  "sources": [
    {
      "title": "PRAGMA Statements",
      "url": "https://www.sqlite.org/pragma.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "In [WAL](https://www.sqlite.org/wal.html) mode when synchronous is NORMAL (1), the WAL file is\n    synchronized before each [checkpoint](https://www.sqlite.org/wal.html#ckpt) and the database file is\n    synchronized after each completed [checkpoint](https://www.sqlite.org/wal.html#ckpt) and the WAL file\n    header is synchronized when a WAL file begins to be reused after\n    a checkpoint, but no sync operations occur during most transactions.\n    With synchronous=FULL in WAL mode, an",
          "start_char": 74802,
          "end_char": 75291,
          "heading": null,
          "truncated": true,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/pragma.html",
              "start_offset": 74802,
              "max_chars": 3000,
              "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
            }
          }
        },
        {
          "text": "The journal\\_size\\_limit pragma may be used to limit the size of rollback-journal and WAL files left in the file-system after transactions or checkpoints. Each time a transaction is committed or a WAL file resets, SQLite compares the size of the rollback journal file or WAL file left in the file-system to the size limit set by this pragma and if the journal or WAL file is larger it is truncated to the limit.",
          "start_char": 45286,
          "end_char": 45697,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/pragma.html",
              "start_offset": 45286,
              "max_chars": 3000,
              "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
            }
          }
        },
        {
          "text": "Similarly, in [WAL mode](https://www.sqlite.org/wal.html), the write-ahead log file is not truncated\n  following a [checkpoint](https://www.sqlite.org/wal.html#ckpt).  Instead, SQLite reuses the existing file\n  for subsequent WAL entries since overwriting is faster than appending.",
          "start_char": 45003,
          "end_char": 45284,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/pragma.html",
              "start_offset": 45003,
              "max_chars": 3000,
              "expected_content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
            }
          }
        }
      ],
      "source_id": "src_f8124ebf5d1023e1",
      "text_truncated": false,
      "content_hash": "ce51e8df1f6bdeeabe4045af1755f62f76b30e8b71b086a5cd000cb7b285266a"
    },
    {
      "title": "SQLite Frequently Asked Questions",
      "url": "https://www.sqlite.org/faq.html",
      "snippet": "",
      "source_type": "unknown",
      "excerpts": [
        {
          "text": "**(9) What is the maximum size of a VARCHAR in SQLite?**",
          "start_char": 10613,
          "end_char": 10669,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/faq.html",
              "start_offset": 10613,
              "max_chars": 3000,
              "expected_content_hash": "8044482cfa592526b15bae40185c0608c727c80b1e54fd2ba7356e9e61ebbc89"
            }
          }
        },
        {
          "text": "SQLite is threadsafe because it uses mutexes to serialize\n  access to common data structures.  However, the work of acquiring and\n  releasing these mutexes will slow SQLite down slightly.  Hence, if you\n  do not need SQLite to be threadsafe, you should disable the mutexes\n  for maximum performance.  See the [threading mode](https://www.sqlite.org/threadsafe.html) documentation for\n  additional information.",
          "start_char": 7518,
          "end_char": 7927,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/faq.html",
              "start_offset": 7518,
              "max_chars": 3000,
              "expected_content_hash": "8044482cfa592526b15bae40185c0608c727c80b1e54fd2ba7356e9e61ebbc89"
            }
          }
        },
        {
          "text": "If you delete a lot of data and want to shrink the database file,\n  run the [VACUUM](https://www.sqlite.org/lang_vacuum.html) command.\n  VACUUM will reconstruct\n  the database from scratch.  This will leave the database with an empty\n  free-list and a file that is minimal in size.  Note, however, that the\n  VACUUM can take some time to run and it can use up to twice\n  as much temporary disk space as the original file while it is running.",
          "start_char": 12256,
          "end_char": 12697,
          "heading": null,
          "truncated": false,
          "expand": {
            "tool": "web_fetch",
            "arguments": {
              "url": "https://www.sqlite.org/faq.html",
              "start_offset": 12256,
              "max_chars": 3000,
              "expected_content_hash": "8044482cfa592526b15bae40185c0608c727c80b1e54fd2ba7356e9e61ebbc89"
            }
          }
        }
      ],
      "source_id": "src_4f753dfe60be8239",
      "text_truncated": false,
      "content_hash": "8044482cfa592526b15bae40185c0608c727c80b1e54fd2ba7356e9e61ebbc89"
    }
  ],
  "gaps": [
    "query 'journal_size_limit maximum size of the WAL file truncate after checkpoint': unresponsive engines: brave, google, google cse",
    "query 'journal_size_limit maximum size of the WAL file truncate after checkpoint': 0 results",
    "query 'WAL mode -wal -shm files grow checkpoint FAQ': unresponsive engines: brave, google, google cse",
    "query 'WAL mode -wal -shm files grow checkpoint FAQ': 0 results"
  ]
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

Excellent. Now I have the following lined up:

1. wal.html (full text):
- Checkpoint definition; automatic checkpoints at 1000 pages by default.
- End mark concept: readers remember the position of the last valid commit record; end mark is fixed for the duration of a transaction.
- "A checkpoint can run concurrently with readers, but it must stop when it reaches a page in the WAL that is past any current reader's end mark."
- "Therefore, long-running read transactions can prevent the checkpointer from making progress."
- "Whenever a write operation occurs, the writer checks how far the checkpointer has progressed, and if the entire WAL has been transferred to the database and synced, and no readers are using the WAL, then the writer rewinds the WAL back to the beginning... This mechanism prevents unbounded growth of the WAL file."
- Read performance degrades as the WAL grows.
- Default strategy: grow up to 1000 pages, checkpoint on each subsequent COMMIT until it shrinks below 1000 pages; auto-checkpoint runs in the same thread that does the COMMIT.
- Checkpoints require sync operations (WAL synced before moving content, DB file synced before resetting WAL).
- "In normal cases, new content is appended to the WAL file until about 1000 pages (~4MB) accumulate, at which point a checkpoint runs automatically and the WAL file is recycled. The checkpoint does not normally truncate the WAL file (unless the journal_size_limit pragma is set). Instead, it simply causes SQLite to start overwriting from the beginning of the WAL file."
- "When the last connection to the database closes, that connection performs one final checkpoint and then deletes the WAL file and its associated shared memory file."
- Section on unbounded growth: disabling auto-checkpoint; **checkpoint starvation** — "A checkpoint can only run to completion and reset the WAL file if no other database connections are using the WAL file. If another connection has a read transaction open, the checkpoint cannot reset the WAL file... The checkpoint does as much work as it can without disturbing readers, but cannot complete. After the next write transaction, the checkpoint resumes from where it left off. This repeats until some checkpoint is able to complete. However, if there are many concurrent overlapping readers on a database and at least one reader is always active, no checkpoint will be able to complete, and the WAL file will grow without bound." Mitigations: "reader gaps"; manual checkpoints with SQLITE_CHECKPOINT_RESTART or TRUNCATE "guarantee that the checkpoint runs to completion before returning. The downside... readers may block while the checkpoint is running."
- **Very large write transactions**: "A checkpoint can only complete when no other transaction is in progress, which means the WAL file cannot be reset in the middle of a write transaction."
- WAL file lifecycle: exists as long as any connection has it open; normally deleted when the last connection closes; may remain if the process exits without clean shutdown or with SQLITE_FCNTL_PERSIST_WAL. "The only safe way to delete a WAL file is to open the database... and then immediately close it."
- Read-only WAL databases (3.22+).
- Busy cases: exclusive lock mode, cleanup by last connection, recovery after crash.
- WAL reset bug (3.7.0–3.51.2, fixed in 3.51.3) — a data race between concurrent checkpoints and commits that reset the WAL; relevant edge case for applications running manual checkpoints concurrently with writers! This is an important limitation/edge case to mention: run sqlite3_wal_checkpoint_v2(FULL/RESTART/TRUNCATE) from multiple connections while writes are happening → rare corruption bug in versions before 3.51.3.
- Also, the "how to checkpoint" section — I saw a link reference but didn't see the actual list of commands (the page has a "How To Checkpoint" section with links: PRAGMA wal_checkpoint, sqlite3_wal_checkpoint, etc.). The first fetch ended at 19949 in the middle of the "Very large write transactions" bullet; the continuation started from there and covered the rest. Wait — did I miss the content between ~15000-19949? No: the first fetch returned chars 0..19949 (max_chars 20000, total 30929). The second fetch was from 19949 to the end. So I have the full page. But wait — did the first chunk include the "How To Checkpoint" section? It ended with "...the file can grow very large." (end of the Very large write transactions bullet). Hmm, actually the first chunk's content ended at "Very large write transactions... in the meantime, the file can grow very large." And the second chunk started from "\n\nAs of SQLite version 3.11.0..." — so between them there might be a section I missed? No — the chunks are contiguous: 0-19949 and 19949-end. The first chunk ended with "the file can grow very large." and the second started from "\n\nAs of SQLite version 3.11.0". So there's no gap. But where is the "How To Checkpoint" section? It must be somewhere in the middle... Actually, looking at the first fetch: it included "...(links to commands and interfaces for doing this are shown below.)" — so the how-to-checkpoint list appears later on the page. Hmm, but I don't see it in either chunk. Let me re-verify: the second chunk covered wal-index shared memory details, EXCLUSIVE locking mode, busy cases, file format version, WAL reset bug. The "How To Checkpoint" section with a bulleted list of interfaces... maybe it's between 19949 and where the second chunk started? No, contiguous.

Wait, actually — I might have misread; the first fetch was max_chars=20000 starting from 0 → returned chars [0, 19949)? It said next_start: 19949, total_chars 30929. The second fetch started at 19949 and went to the end (next_start null). So I have all 30929 characters. The "How To Checkpoint" section — hmm, maybe it's in a part of the first chunk that I skimmed over. Looking back at the first chunk: after "...(links to commands and interfaces for doing this are shown below.)", the text continues with "Note that with PRAGMA synchronous set to NORMAL..." then tradeoffs, then journal_mode=WAL pragma section, WAL file naming/lifecycle, read-only media, recycling paragraph, unbounded growth bullets. I don't see an explicit "How To Checkpoint" heading list in what was returned... maybe it's rendered as a definition list and the text extraction merged it. Not important — I have enough material: PRAGMA wal_checkpoint (all modes), sqlite3_wal_checkpoint(), sqlite3_wal_checkpoint_v2() with FULL/RESTART/TRUNCATE, wal_autocheckpoint pragma, journal_size_limit.

Hmm wait, actually there's one thing missing: the first chunk said "There are three subtypes of checkpoints that vary in their aggressiveness: PASSIVE, FULL, and RESTART." — this is from the older text on wal.html (TRUNCATE was added later; the c3ref page has four modes). No problem.

2. pragma.html:
- End of wal_autocheckpoint section: "Setting auto-checkpoint size to zero or a negative value disables auto-checkpointing... All automatic checkpoints are PASSIVE. Autocheckpointing is enabled by default with an interval of 1000 pages."
- Full text of the wal_checkpoint pragma: syntax (no argument, PASSIVE, FULL, RESTART, TRUNCATE, NOOP); "If WAL mode is disabled, this pragma is a harmless no-op"; return value row: first column is 0 or 1 if RESTART/FULL/TRUNCATE was blocked from completing (e.g., another thread/process actively using the DB) — i.e., equivalent to SQLITE_OK vs SQLITE_BUSY; second = number of modified pages written to WAL; third = number of pages successfully moved back. -1 if no WAL.
- journal_size_limit: "The journal_size_limit pragma can be used to limit the size of rollback journal and WAL files left in the filesystem after a transaction or checkpoint. Each time a transaction is committed, or when the WAL file resets, SQLite compares the size of the rollback journal file or WAL file left in the filesystem against the size limit set by this pragma, and if the journal or WAL file is larger, it is truncated to that limit."
- Also: "Similarly, in WAL mode, the write-ahead log file is not truncated after a checkpoint. Instead, SQLite reuses the existing file for subsequent WAL entries because overwriting is faster than appending." (This is from the rollback journal section context — actually this excerpt at 45003 seems to be inside the journal_size_limit section explaining why journals aren't truncated.)
- synchronous NORMAL in WAL: "The WAL file is synced before each checkpoint, and the database file is synced after each completed checkpoint, and the WAL file header is synced when the WAL file begins to be reused after a checkpoint."

3. c3ref/wal_checkpoint_v2.html (full text):
- Signature; pnLog/pnCkpt semantics; "On successful completion of SQLITE_CHECKPOINT_TRUNCATE, the log file will have been truncated to zero bytes and both *pnLog and *pnCkpt set to zero."
- "All calls acquire an exclusive 'checkpoint' lock on the database file. If another process is running a checkpoint operation at the same time, the lock cannot be acquired and SQLITE_BUSY is returned. Even if a busy handler is configured, it will not be invoked in this case." — Important edge case: two concurrent checkpoints → immediate BUSY with no retry!
- "SQLITE_CHECKPOINT_FULL, RESTART, TRUNCATE modes also acquire an exclusive 'writer' lock... If the writer lock cannot be acquired immediately and a busy handler is configured, it is invoked and the writer lock retried until either the busy handler returns 0 or the lock is successfully acquired. The busy handler is also invoked while waiting for database readers as described above." — "as described above" refers to the mode descriptions on c_checkpoint_full.html (the constants page), which I haven't fetched yet! The per-mode behavior ("If a reader is active...") is documented at https://www.sqlite.org/c3ref/c_checkpoint_full.html. I should fetch that page for the exact FULL/RESTART/TRUNCATE semantics: e.g., "SQLITE_CHECKPOINT_FULL: ... waits until all other database connections have completed or rolled back their transactions and/or checkpoints..." Let me fetch it.

4. c3ref/wal_autocheckpoint.html — got an excerpt; I want the full text (small page, ~1500 chars). The excerpt at offset 56 was truncated at 552 chars: "sqlite3_wal_autocheckpoint(D,N) is a wrapper around sqlite3_wal_hook() that causes any database on database connection D to automatically checkpoint after committing a transaction if there are N or more frames in the write-ahead log file. Passing zero or a negative..." — I need the rest (what happens with 0/negative, and probably "The automatic checkpointing mechanism only operates when..."). Let me fetch the full page.

Also, the FAQ didn't yield WAL-specific excerpts (BM25 matched unrelated questions). The FAQ has a WAL section ("What is the difference between..." hmm). Not important; I have enough primary material. But one more useful source: the "hot journal" / recovery part of wal.html — already covered in the busy cases (recovery after crash holds an exclusive lock).

Also, for completeness on "conditions under which the WAL can be reused or truncated":
- Reuse (reset to offset zero): happens when a checkpoint completes fully AND no readers are using the WAL — per wal.html: "Whenever a write operation occurs, the writer checks how far the checkpointer has progressed, and if the entire WAL has been transferred to the database and synced, and no readers are using the WAL, then the writer rewinds the WAL back to the beginning." So reset is done by the next writer after a complete checkpoint. Also RESTART mode explicitly resets.
- Truncation: TRUNCATE mode truncates to zero bytes; journal_size_limit truncates on commit/WAL reset if larger than limit; deletion when last connection closes (after final checkpoint).

Now, remaining fetches:
1. https://www.sqlite.org/c3ref/c_checkpoint_full.html — per-mode constant descriptions (SQLITE_CHECKPOINT_PASSIVE/FULL/RESTART/TRUNCATE). Small page.
2. Full text of https://www.sqlite.org/c3ref/wal_autocheckpoint.html (~1500 chars; fetch with max_chars 4000).

Both are small and independent — run in parallel. Then I'll have everything I need to write the answer.

Should I also try a secondary source (forum thread)? The search engine is unresponsive (brave/google down), so discovery via search isn't working right now; only wikipedia/wikidata engines might respond, but they won't help for forum threads. Per AGENTS.md: don't keep retrying blocked sources when sufficient alternatives exist. Primary documentation is the best source here — documented behavior is exactly what's being asked for. I'll note that the search engine was partially unresponsive (gap) and that all citations are from official SQLite docs, which is appropriate since the question asks about documented behavior.

Let me do these last two fetches.


I've obtained most of the primary documentation. Two small pages remain: the per-mode checkpoint constant descriptions, and the full text of `wal_autocheckpoint`.



**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.sqlite.org/c3ref/c_checkpoint_full.html",
  "max_chars": 8000
}
```

**Output:**
```
{
  "title": "Checkpoint Mode Values",
  "url": "https://www.sqlite.org/c3ref/c_checkpoint_full.html",
  "content": "#define SQLITE\\_CHECKPOINT\\_NOOP -1 /\\* Do no work at all \\*/ #define SQLITE\\_CHECKPOINT\\_PASSIVE 0 /\\* Do as much as possible w/o blocking \\*/ #define SQLITE\\_CHECKPOINT\\_FULL 1 /\\* Wait for writers, then checkpoint \\*/ #define SQLITE\\_CHECKPOINT\\_RESTART 2 /\\* Like FULL but wait for readers \\*/ #define SQLITE\\_CHECKPOINT\\_TRUNCATE 3 /\\* Like RESTART but also truncate WAL \\*/\n\nThese constants define all valid values for the \"checkpoint mode\" passed\nas the third parameter to the [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) interface.\nSee the [sqlite3\\_wal\\_checkpoint\\_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) documentation for details on the\nmeaning of each of these checkpoint modes.",
  "total_chars": 750,
  "next_start": null,
  "truncated": false,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "40ede9604e4bc44a6128c5ba65c62692781bd16b104162134d19bf22c19fc357",
  "continuation": null
}
```

**Tool: cluefinch_web_fetch**

**Input:**
```json
{
  "url": "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
  "max_chars": 4000
}
```

**Output:**
```
{
  "title": "Configure an auto-checkpoint",
  "url": "https://www.sqlite.org/c3ref/wal_autocheckpoint.html",
  "content": "int sqlite3\\_wal\\_autocheckpoint(sqlite3 \\*db, int N);\n\nThe [sqlite3\\_wal\\_autocheckpoint(D,N)](https://www.sqlite.org/c3ref/wal_autocheckpoint.html) is a wrapper around\n[sqlite3\\_wal\\_hook()](https://www.sqlite.org/c3ref/wal_hook.html) that causes any database on [database connection](https://www.sqlite.org/c3ref/sqlite3.html) D\nto automatically [checkpoint](https://www.sqlite.org/wal.html#ckpt)\nafter committing a transaction if there are N or\nmore frames in the [write-ahead log](https://www.sqlite.org/wal.html) file.  Passing zero or\na negative value as the N parameter disables automatic\ncheckpoints entirely.\n\nThe callback registered by this function replaces any existing callback\nregistered using [sqlite3\\_wal\\_hook()](https://www.sqlite.org/c3ref/wal_hook.html).  Likewise, registering a callback\nusing [sqlite3\\_wal\\_hook()](https://www.sqlite.org/c3ref/wal_hook.html) disables the automatic checkpoint mechanism\nconfigured by this function.\n\nThe [wal\\_autocheckpoint pragma](https://www.sqlite.org/pragma.html#pragma_wal_autocheckpoint) can be used to invoke this interface\nfrom SQL.\n\nCheckpoints initiated by this mechanism are\n[PASSIVE](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html).\n\nEvery new [database connection](https://www.sqlite.org/c3ref/sqlite3.html) defaults to having the auto-checkpoint\nenabled with a threshold of 1000 or [SQLITE\\_DEFAULT\\_WAL\\_AUTOCHECKPOINT](https://www.sqlite.org/compile.html#default_wal_autocheckpoint)\npages.\n\nThe use of this interface is only necessary if the default setting is found to be suboptimal for a particular application.",
  "total_chars": 1593,
  "next_start": null,
  "truncated": false,
  "cache_hit": false,
  "source_type": "unknown",
  "text_truncated": false,
  "content_hash": "5de63a4aaeff9c7f062ef791867ee255fb46f2fe36f11f9389768660eb18cd0e",
  "continuation": null
}
```

---

## Assistant (Build · Qwen3.8 27B UD IQ4_XS)

_Thinking:_

The c_checkpoint_full.html page only has comments on the constants: PASSIVE = "do as much as possible without blocking," FULL = "wait for writers, then checkpoint," RESTART = "same as FULL but also wait for readers," TRUNCATE = "same as RESTART but also truncate the WAL." Interesting — so according to these constant comments, FULL waits for *writers* and RESTART additionally waits for *readers*. This is a subtle point: does FULL not wait for readers? Hmm. But wal.html says that checkpoints must stop at pages beyond any reader's end mark (that applies to all modes). And the pragma page says the first column becomes 1 "if a RESTART or FULL or TRUNCATE checkpoint was blocked from completing, e.g., because another thread or process was actively using the database."

So what does "blocked" mean for FULL? Let me think about the documented semantics:
- PASSIVE: copies as many frames as possible without blocking; stops at the oldest reader's end mark. Never waits.
- FULL: acquires the writer lock (waits for writers via busy handler), checkpoints all dirty frames… but what about readers? The constant comment says "wait for writers, then checkpoint" — and RESTART is "same as FULL but also wait for readers." So FULL does not wait for readers; it checkpoints everything up to where readers allow? Hmm, that seems odd. Let me think about the actual behavior:

From SQLite source knowledge (wal.c): in sqlite3WalCheckpoint, mode PASSIVE → checkpoint frames up to mxFrame allowed by readers (no waiting). FULL/RESTART/TRUNCATE → first acquire the write lock; then for RESTART/TRUNCATE, wait for all readers to finish (via busy handler) so that the WAL can be reset/truncated. For FULL… hmm, actually I recall: FULL checkpoints as many frames as possible after acquiring the writer lock — but if a reader is active, it stops at the reader's end mark and returns SQLITE_BUSY? Or does it complete the copy of all frames (since copying frames to the DB file doesn't conflict with readers — wait no, it does conflict: "the checkpoint must stop when it reaches a page in the WAL that is beyond any current reader's end mark. The checkpoint has to stop at that point because otherwise it might overwrite part of the database file that the reader is actively using."

Hmm wait, why would copying frames past a reader's end mark overwrite something the reader is using? Because if the reader needs an older version of page X (from before its end mark), and the checkpoint copies a newer version of page X into the main DB… no wait — the checkpoint only copies pages that are *not* needed by any reader. If a frame at position F in the WAL is beyond reader R's end mark, then R does not use that frame; but R might need an older copy of the same page from before its end mark, which lives either in an earlier part of the WAL or in the main DB file. If we overwrite the main DB page with a newer version, and R needs the old version from the main DB (because no pre-end-mark copy exists in the WAL), then R would see corrupted data. So the checkpoint must stop at the first frame beyond any reader's end mark — because past that point, pages may have older versions still needed by readers living in the main DB file.

So even FULL cannot copy frames past the oldest active reader's end mark. The difference between FULL and RESTART per the constant comments: FULL waits for writers (acquires writer lock) then checkpoints as much as it can; RESTART additionally waits for readers to finish so that the WAL can be reset (rewound to offset zero). TRUNCATE = RESTART + truncate file to 0 bytes.

Hmm, but wait — is that right? Let me reconsider: if FULL doesn't wait for readers and stops at the reader's end mark, then with a long-lived reader present, FULL returns SQLITE_BUSY (blocked from completing) after checkpointing what it can. The pragma page says column 1 = 1 "if a RESTART or FULL or TRUNCATE checkpoint was blocked from completing, e.g., because another thread or process was actively using the database." Consistent: with an active reader, FULL is "blocked from completing" → busy=1.

And wal.html's guidance on unbounded growth says to use SQLITE_CHECKPOINT_RESTART or TRUNCATE "to ensure that the checkpoint runs to completion before returning. The downside of using RESTART and TRUNCATE is that readers may be blocked while the checkpoint is running." — consistent: RESTART/TRUNCATE wait for readers (blocking them), FULL does not wait for readers.

Hmm, but actually I want to double-check whether FULL waits for readers or not. Let me look at the actual SQLite source behavior… From wal.c (sqlite3WalCheckpoint):
- If mode == PASSIVE: no waiting; checkpoint up to mxFrame = min of reader end marks.
- Otherwise (FULL/RESTART/TRUNCATE): acquire write lock (with busy handler). Then if mode >= RESTART: wait for readers to finish? Actually I recall the code: "if( eMode>=SQLITE_CHECKPOINT_RESTART ){ ... wait for all readers to go away ... }" Hmm. And for FULL, after acquiring the writer lock, it checkpoints up to mxFrame (which may be limited by readers) and returns SQLITE_BUSY if not everything was checkpointed?

Actually from the source (3.x wal.c):
```
  /* If this is a RESTART or TRUNCATE checkpoint, then wait for all
  ** readers to finish... */
```
Hmm, I don't remember exactly. But the constant comments are authoritative documentation: FULL = "wait for writers, then checkpoint"; RESTART = "same as FULL but also wait for readers." So per docs: FULL waits only for writers; RESTART/TRUNCATE wait for both writers and readers.

But hmm — one more consideration: if a reader is active, can FULL even complete the copy of all frames? No (it stops at the reader's end mark). So with an active long-lived reader:
- PASSIVE: partial progress, returns OK (busy=0), WAL not reset.
- FULL: acquires writer lock, copies up to reader's end mark, cannot complete → returns SQLITE_BUSY (pragma column 1 = 1). WAL not reset.
- RESTART/TRUNCATE: waits for readers via busy handler; if readers finish within the timeout → full checkpoint + reset (+ truncate) → OK. If readers persist past busy_timeout → degrades to PASSIVE-like behavior ("the checkpoint operation proceeds from that point in the same way as SQLITE_CHECKPOINT_PASSIVE - checkpointing as many frames as possible without blocking any further. SQLITE_BUSY is returned") per wal_checkpoint_v2.html.

This last quote is a gem: "If the busy handler returns 0 before the writer lock is acquired, or while waiting for database readers, the checkpoint operation proceeds from that point in the same way as SQLITE_CHECKPOINT_PASSIVE - checkpointing as many frames as possible without blocking any further. SQLITE_BUSY is returned in this case."

So RESTART/TRUNCATE with a persistent reader: waits up to busy_timeout, then does partial passive work and returns BUSY. Readers are "blocked" only during the wait (they aren't actually blocked — readers continue; rather, the checkpoint waits for them). The wal.html phrasing "readers may be blocked while the checkpoint is running" — hmm, how would readers be blocked? A RESTART checkpoint holds the writer lock… readers don't need the writer lock. Hmm, maybe it means that once the checkpoint completes and resets the WAL, new readers are fine; existing readers were waiting to finish. Actually I think "readers may be blocked" is loose phrasing — or does a TRUNCATE checkpoint block *new* readers? No… let me not over-interpret; I'll quote wal.html's statement as documented guidance and note that the mechanism per c3ref is that the checkpoint waits for active readers (via busy handler) rather than blocking reader queries. Actually wait — hmm, there might be a real sense in which readers are blocked: while a RESTART/TRUNCATE checkpoint holds the exclusive writer lock… no, readers don't need it.

Hmm, let me reconsider: maybe "readers may be blocked" refers to this: for the checkpoint to reset/truncate the WAL, all readers must have finished; if an application's reader is in a long transaction, the *checkpoint* blocks (waits) — from the reader's perspective nothing is blocked. I'll present it as documented wording and add my interpretation that what waits is the checkpoint, not the reader queries.

OK — do I need more evidence? Let me check coverage against the question:

1. "Why can a WAL-mode SQLite database develop a large WAL file even while reads and writes continue to succeed?"
   - Documented: commits append frames; only checkpoints move content back; auto-checkpoint is PASSIVE (stops at oldest reader's end mark); checkpoint starvation with always-active readers → unbounded growth; very large write transactions; disabled auto-checkpoint. Reads/writes are unaffected because WAL mode allows concurrent reads and writes — growth doesn't block anything, it just accumulates. Also documented: read performance degrades as the WAL grows (wal-index helps but still).
   ✓ Covered by wal.html quotes.

2. "What role can long-lived read transactions play?"
   - Documented: end mark is fixed for the duration of a transaction; checkpoint must stop at pages beyond any reader's end mark; "long-running read transactions can prevent the checkpointer from making progress"; writer only rewinds WAL if no readers are using it. So a long-lived reader pins the oldest frames → WAL cannot be reset/truncated past that point → growth.
   ✓ Covered.

3. "How does checkpointing interact with readers and writers?"
   - Documented: checkpoints run concurrently with readers but stop at end marks; remember progress in wal-index, resume on next invocation (triggered by next write transaction); FULL/RESTART/TRUNCATE acquire writer lock (wait for active writers via busy handler); RESTART/TRUNCATE also wait for readers; all checkpoint calls take an exclusive "checkpoint" lock — concurrent checkpoints → immediate SQLITE_BUSY with no busy-handler retry.
   ✓ Covered.

4. "Under what conditions can the WAL be reused or truncated?"
   - Reuse/reset: after a complete checkpoint (all frames copied + synced) and no readers using the WAL, the next writer rewinds the WAL to offset zero; RESTART mode explicitly resets; TRUNCATE additionally truncates file to 0 bytes. journal_size_limit truncates on commit/WAL reset if larger than limit. Last connection closing: final checkpoint + delete -wal/-shm (unless unclean shutdown or PERSIST_WAL).
   ✓ Covered by wal.html ("In normal cases... recycled... start overwriting from the beginning"), pragma's journal_size_limit, c3ref TRUNCATE note.

5. "Compare practical behavior of available checkpoint modes" — PASSIVE/FULL/RESTART/TRUNCATE (+ NOOP):
   - PASSIVE: no blocking; partial progress allowed; used by auto-checkpoint and bare PRAGMA wal_checkpoint; returns OK even if partial (pragma column 1 = 0? hmm — is that documented? The pragma page says column 1 "is usually 0 but will be 1 if a RESTART or FULL or TRUNCATE checkpoint was blocked from completing" — so PASSIVE never sets it to 1. Good, documented.)
   - FULL: waits for writers (writer lock via busy handler), checkpoints as much as possible; with active readers cannot complete → SQLITE_BUSY; does not reset WAL (per constant comment distinction).
   - RESTART: same + wait for readers; on success resets WAL to offset zero (file reused from start); if readers persist past timeout → degrades to passive partial work, returns BUSY.
   - TRUNCATE: same as RESTART + truncate file to 0 bytes; on success pnLog=pnCkpt=0.
   - NOOP: does nothing (returns log/ckpt counts).
   ✓ Covered by constant comments + wal_checkpoint_v2.html + pragma page.

6. "What can an application do if the WAL keeps growing?"
   - Documented guidance from wal.html: ensure "reader gaps"; run manual checkpoints with RESTART/TRUNCATE during those windows; don't disable auto-checkpointing; keep transactions small (very large write transactions); adjust threshold via wal_autocheckpoint; journal_size_limit to cap file size on disk; close long-lived read transactions promptly (interpretation/application of documented mechanism — the docs say checkpoint starvation is caused by open read transactions, so eliminating them is the fix; I'll mark this as interpretation grounded in documented cause).
   - Also: monitor via pragma return values / sqlite3_wal_checkpoint_v2 output (log vs ckpt frame counts) to detect blocking.
   - Last resort: close all connections (last connection does final checkpoint and deletes WAL file); "the only safe way to delete a WAL file is to open the database... then immediately close it."
   ✓ Covered.

7. "Important limitations or edge cases":
   - FULL/RESTART/TRUNCATE return SQLITE_BUSY if readers/writers persist past busy_timeout; they degrade to passive partial work (documented).
   - Concurrent checkpoints: exclusive checkpoint lock, immediate BUSY with no busy-handler retry (documented) — so don't run manual checkpoints from multiple connections simultaneously.
   - WAL-reset bug: versions 3.7.0–3.51.2, data race between concurrent checkpoints and commits that reset the WAL → rare corruption; fixed in 3.51.3 (and backported to 3.44.6/3.50.7). Relevant if an app runs manual checkpoints from a separate thread/process while writers commit.
   - Checkpoints require sync I/O (WAL synced before copy, DB file synced before reset) → slower than writes; with synchronous=NORMAL the checkpoint is the only operation that does fsync — implications for durability and "latch-up" if run in main thread.
   - Read performance degrades as WAL grows (wal-index mitigates but still).
   - WAL mode requires shared memory on same machine → not usable over network filesystems; EXCLUSIVE locking_mode workaround for single-process.
   - Read-only connections cannot checkpoint? Hmm — is that documented anywhere I fetched? wal.html says "an application can initiate a checkpoint using any writable database connection" — yes! That's in the first chunk: "An application can initiate a checkpoint using any writable database connection on the database simply by invoking sqlite3_wal_checkpoint()..." So checkpoints require a *writable* connection. ✓ Documented.
   - WAL file lifecycle edge cases: may remain after unclean shutdown; PERSIST_WAL; only safe deletion is open+close.
   - Older SQLite (<3.7) can't read WAL-mode DBs (format version 2).
   - Busy cases for readers (exclusive lock mode, cleanup by last connection, recovery after crash holds exclusive lock → third connection gets BUSY).
   - Auto-checkpoint only fires "after committing a transaction" on that connection — i.e., triggered by writers; if no writes happen, no auto-checkpoint runs. Documented: "automatically checkpoint after committing a transaction if there are N or more frames." So in a read-only workload with an existing large WAL… hmm, actually the last-connection-close also checkpoints ("or when the last database connection on a database file closes"). Also note: auto-checkpoint is per-connection setting (each new connection defaults to 1000).
   - Another subtle documented point: "The checkpoint will start up again where it left off after the next write transaction." — so progress resumes only when writes happen. In a read-only workload with no writers, a stalled checkpoint won't resume until a write occurs (or an explicit checkpoint is run). This is a good edge case for "reads and writes continue" — well, in our scenario writes do continue.
   - Also: the 1000-page threshold ≈ 4MB at default page size; WAL grows to ~4MB before auto-checkpoint kicks in (documented "about 4MB").

I think I have everything I need. One more consideration — the question says "even while reads and writes continue to succeed." Key insight: nothing about a large WAL causes read/write failures; it's purely a checkpointing issue. Documented support: readers/writers run concurrently by design; growth is due to checkpoints not completing (starvation) or not running (disabled, no writers). Also very large write transactions temporarily grow the WAL even with healthy checkpointing.

Citation plan (URLs):
- https://www.sqlite.org/wal.html — main WAL doc (end mark, checkpoint stop rule, long-running reader quote, writer rewind mechanism, default 1000-page strategy, recycling/no-truncate behavior, unbounded growth bullets: disabled auto-checkpoint / checkpoint starvation / very large write transactions, WAL file lifecycle and safe deletion, read-only media, busy cases, WAL-reset bug).
- https://www.sqlite.org/pragma.html — wal_checkpoint pragma (modes including NOOP, return value semantics), wal_autocheckpoint pragma (PASSIVE only, default 1000, disable with 0/negative), journal_size_limit (truncate on commit/WAL reset), synchronous NORMAL in WAL.
- https://www.sqlite.org/c3ref/wal_checkpoint_v2.html — locks (exclusive checkpoint lock → immediate BUSY; writer lock + busy handler for FULL/RESTART/TRUNCATE; degradation to passive behavior when busy handler returns 0; TRUNCATE zeroes file and counters).
- https://www.sqlite.org/c3ref/c_checkpoint_full.html — constant comments defining mode semantics.
- https://www.sqlite.org/c3ref/wal_autocheckpoint.html — auto-checkpoint wrapper, PASSIVE only, default threshold, disable with 0/negative.

Distinguishing documented vs interpretation: I'll mark most claims as documented (with citations) and clearly flag interpretive parts: e.g., "a long-lived reader is the usual suspect" (inference from documented starvation mechanism), practical recommendations like "close cursors promptly / commit idle transactions" (application of documented cause; docs don't enumerate app-level fixes beyond reader gaps and RESTART/TRUNCATE checkpoints), and the note that what waits during RESTART is the checkpoint, not reader queries.

Also disclose: search engines were partially unresponsive during research (brave/google down) so I relied on direct fetches of official documentation — which are primary sources anyway; no independent secondary corroboration was obtained (and none needed for documented behavior).

OK let me write the final answer now. It should be thorough but organized. The user asked a multi-part research question with citations — a longer structured response is appropriate here (the "under 4 lines" guidance yields to explicit request for detailed investigation; still, I'll keep it tight and avoid fluff).

Structure:
1. Short summary of the mechanism (why WAL grows while reads/writes succeed)
2. Role of long-lived read transactions
3. Checkpointing vs readers/writers
4. When WAL is reused/truncated
5. Comparison table of checkpoint modes
6. What an application can do
7. Limitations and edge cases
8. Sources + note on documented vs interpretation

Use headings, keep quotes short with citations. Mark [documented] / (interpretation) inline or via a legend. Let me draft it.

Key quotes to use (short):
- "A checkpoint can run concurrently with readers, however the checkpoint must stop when it reaches a page in the WAL that is past the end mark of any current reader." (wal.html)
- "Thus a long-running read transaction can prevent a checkpointer from making progress." (wal.html)
- "if the entire WAL has been transferred into the database and synced and if no readers are making use of the WAL, then the writer will rewind the WAL back to the beginning" (wal.html)
- "if a database has many concurrent overlapping readers and there is always at least one active reader, then no checkpoints will be able to complete and hence the WAL file will grow without bound." (wal.html)
- "The checkpoint does not normally truncate the WAL file (unless the journal_size_limit pragma is set). Instead, it merely causes SQLite to start overwriting the WAL file from the beginning." (wal.html)
- "A checkpoint can only complete when no other transactions are running" — actually the exact quote: "A checkpoint can only complete when no other transactions are running, which means the WAL file cannot be reset in the middle of a write transaction." (wal.html, very large write transactions bullet)
- Constant comments: PASSIVE "Do as much as possible w/o blocking"; FULL "Wait for writers, then checkpoint"; RESTART "Like FULL but wait for readers"; TRUNCATE "Like RESTART but also truncate WAL" (c_checkpoint_full.html)
- wal_checkpoint_v2: "If the busy-handler returns 0 before the writer lock is obtained or while waiting for database readers, the checkpoint operation proceeds from that point in the same way as SQLITE_CHECKPOINT_PASSIVE... SQLITE_BUSY is returned."
- "All calls obtain an exclusive 'checkpoint' lock... If any other process is running a checkpoint operation at the same time, the lock cannot be obtained and SQLITE_BUSY is returned. Even if there is a busy-handler configured, it will not be invoked in this case."
- journal_size_limit: "Each time a transaction is committed or a WAL file resets, SQLite compares the size of ... WAL file left in the file-system to the size limit... and if the journal or WAL file is larger it is truncated to the limit." (pragma.html)
- wal_autocheckpoint: "automatically checkpoint after committing a transaction if there are N or more frames"; "Checkpoints initiated by this mechanism are PASSIVE."; default 1000.
- pragma wal_checkpoint return values: column 1 = 1 "if a RESTART or FULL or TRUNCATE checkpoint was blocked from completing, for example because another thread or process was actively using the database."
- WAL file lifecycle: "Usually, the WAL file is deleted automatically when the last connection to the database closes... The only safe way to remove a WAL file is to open the database file ... then immediately close it." (wal.html)
- "An application can initiate a checkpoint using any writable database connection" (wal.html)
- Read performance: "read performance deteriorates as the WAL file grows in size" (wal.html)
- WAL-reset bug summary (wal.html).
- synchronous NORMAL: "the checkpoint is the only operation to issue an I/O barrier or sync operation" (wal.html); pragma's synchronous section.

Mode comparison table:

| Mode | Waits for writers? | Waits for readers? | Resets WAL offset? | Truncates file? | Returns BUSY if blocked? |
- PASSIVE: no / no / only if complete and no readers (writer rewinds) / no / never (column 1 stays 0; partial OK)
- FULL: yes (busy handler) / no / no / no / yes, if not fully checkpointed (e.g., active reader)
- RESTART: yes / yes (busy handler) / yes / no / yes, degrades to passive partial work
- TRUNCATE: yes / yes / yes / yes (to 0 bytes) / same as RESTART

Hmm wait — does FULL reset the WAL offset on success? If FULL completes with no readers present… if there are no readers and all frames are checkpointed, then the next writer will rewind anyway. But does FULL itself reset? Per constant comments, only RESTART "waits for readers" to enable reset; I believe in the source, FULL mode checkpoints up to mxFrame (limited by readers) — with no readers present, it checkpoints everything and… hmm, actually let me think about wal.c:

```c
  if( eMode==SQLITE_CHECKPOINT_PASSIVE ){
    ...
  }else{
    /* Acquire write lock */
    ...
    if( eMode>=SQLITE_CHECKPOINT_RESTART ){
      /* Wait for readers to finish */
      while( pWal->nReadLock>0 && busyHandler ) ...
    }
  }
```

Hmm, I don't really remember whether FULL resets. The documented distinction (constant comments) is: RESTART = "Like FULL but wait for readers." If FULL could reset the WAL when no readers are present, then waiting for readers in RESTART would be pointless — so the reasonable reading is: FULL does not reset the WAL; it only guarantees a full copy of all frames to the DB file (waiting for writers so that the set of dirty pages is stable). The actual rewind/reset happens either via RESTART/TRUNCATE or naturally by the next writer after a complete checkpoint. I'll state this as documented distinction and flag the "FULL does not reset" part as inference from the constant comments' wording (the docs don't explicitly say "FULL does not reset"). Actually — to be safe, I'll phrase it: "The documented difference between FULL and RESTART is that RESTART additionally waits for readers; only a checkpoint that runs with no active readers can reset/rewind the WAL" — grounded in both the constant comments and wal.html's writer-rewind mechanism.

One more check on my claim "auto-checkpoint only fires after committing a transaction [by that connection]": documented quote: "causes any database on database connection D to automatically checkpoint after committing a transaction if there are N or more frames." So it's triggered by commits on the connection with autocheckpoint enabled. If all connections have writes disabled… well, in our scenario writes continue so no issue. Edge case worth noting: if write traffic stops, auto-checkpoint also stops (no commit to trigger it) — a WAL left large will stay large until a writer commits or an explicit checkpoint runs. This is documented by the trigger mechanism ("after committing a transaction"). I'll mark as inference from documented trigger semantics… actually it's fairly direct: the mechanism only fires on commit. I'll present it with citation and note that it follows directly from the documented trigger.

Also worth noting: "By default, SQLite will automatically checkpoint whenever a COMMIT occurs that causes the WAL file to be 1000 pages or more in size, or when the last database connection on a database file closes." (wal.html) — good quote covering both triggers.

Length: this is a detailed research answer; I'll aim for ~600-900 words with table and citations. The system prompt says to be concise but the user explicitly asked for a full investigation with citations — depth is justified. Keep it as tight as possible while complete.


All evidence gathered from official SQLite documentation (primary sources). Search engines were partially unresponsive during research (brave/google down), so I relied on direct fetches of sqlite.org pages — appropriate here since the question asks about documented behavior. No independent secondary corroboration was obtained; everything below is either quoted/documented or explicitly flagged as interpretation.

# Why a WAL-mode SQLite database can develop a large WAL file while reads and writes keep succeeding

## 1. The core mechanism: growth is a checkpointing problem, not an I/O problem

In WAL mode, commits append frames to the `-wal` file; readers read from the main DB plus the WAL up to their own snapshot point ("end mark"), and writers never block readers or vice versa ([wal.html](https://www.sqlite.org/wal.html)). The only operation that moves content back into the main database is a **checkpoint**, and by design:

> "A checkpoint can run concurrently with readers, however the checkpoint must stop when it reaches a page in the WAL that is past the end mark of any current reader." — [wal.html](https://www.sqlite.org/wal.html)

So nothing about a large WAL makes reads or writes fail — the file simply accumulates frames faster than checkpoints can retire them. Documented causes of unbounded growth ([wal.html, "grow without bound" section](https://www.sqlite.org/wal.html)):

- **Checkpoint starvation** (the main one): "if a database has many concurrent overlapping readers and there is always at least one active reader, then no checkpoints will be able to complete and hence the WAL file will grow without bound."
- **Disabled automatic checkpointing**: auto-checkpoint can be turned off via `PRAGMA wal_autocheckpoint=0` / `sqlite3_wal_autocheckpoint(D,0)` ([c3ref/wal_autocheckpoint.html](https://www.sqlite.org/c3ref/wal_autocheckpoint.html)); then "there is nothing to prevent the WAL file from growing excessively."
- **Very large write transactions**: "A checkpoint can only complete when no other transactions are running, which means the WAL file cannot be reset in the middle of a write transaction. So a large change to a large database might result in a large WAL file."

Note also that auto-checkpointing is *triggered by commits*: it fires "after committing a transaction if there are N or more frames" (default N=1000 pages, ~4MB) ([c3ref/wal_autocheckpoint.html](https://www.sqlite.org/c3ref/wal_autocheckpoint.html), [wal.html](https://www.sqlite.org/wal.html)). It therefore only runs while writes happen; if write traffic stops, so do auto-checkpoints (inference from the documented trigger).

## 2. Role of long-lived read transactions

Each reader "first remembers the location of the last valid commit record in the WAL" — its end mark — which is fixed for the duration of its transaction ([wal.html](https://www.sqlite.org/wal.html)). Consequences, all documented:

- A checkpoint must stop at any page past **any** current reader's end mark, because overwriting those main-DB pages could destroy older versions the reader still needs.
- "Thus a long-running read transaction can prevent a checkpointer from making progress." ([wal.html](https://www.sqlite.org/wal.html))
- The WAL is only rewound to its beginning when "the entire WAL has been transferred into the database and synced **and if no readers are making use of the WAL**" — done by the next writer. A single long-lived reader pins the oldest frames indefinitely; it is the *oldest* active reader that bounds how far the WAL can be reset, not the newest (interpretation from the documented "any current reader" rule).

Practically (interpretation): a "long-lived read transaction" includes idle connections with an open transaction or unfinalized statement/cursor — anything holding a snapshot. The docs' own remedy is to create "reader gaps": times when no process is reading, and attempt checkpoints during those windows ([wal.html](https://www.sqlite.org/wal.html)).

## 3. How checkpointing interacts with readers and writers

Documented behavior:

- Checkpoints run concurrently with readers but stop at reader end marks; they record progress in the wal-index and "will resume transferring content from the WAL to the database from where it left off on the next invocation" — which, for auto-checkpoint, happens after the **next write transaction** ([wal.html](https://www.sqlite.org/wal.html)).
- Checkpoints require a **writable** connection: "An application can initiate a checkpoint using any writable database connection" ([wal.html](https://www.sqlite.org/wal.html)). Read-only connections cannot checkpoint.
- `SQLITE_CHECKPOINT_FULL/RESTART/TRUNCATE` also obtain the exclusive **writer lock**, retried via the busy-handler; if the busy-handler gives up, "the checkpoint operation proceeds from that point in the same way as SQLITE_CHECKPOINT_PASSIVE — checkpointing as many frames as possible without blocking any further. SQLITE_BUSY is returned" ([c3ref/wal_checkpoint_v2.html](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)).
- **Every** checkpoint call takes an exclusive "checkpoint" lock; if another process is already checkpointing, `SQLITE_BUSY` is returned immediately and the busy-handler is *not* invoked ([c3ref/wal_checkpoint_v2.html](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)).
- Checkpoints are sync-heavy: the WAL must be synced before copying content out and the DB file synced before resetting the WAL; with `synchronous=NORMAL` "the checkpoint is the only operation to issue an I/O barrier" ([wal.html](https://www.sqlite.org/wal.html), [pragma.html](https://www.sqlite.org/pragma.html)).

## 4. When can the WAL be reused or truncated?

- **Reused (reset to offset zero):** after a *complete* checkpoint with no active readers, the next writer rewinds the WAL to the beginning; normal operation "recycles" the file — "The checkpoint does not normally truncate the WAL file... Instead, it merely causes SQLite to start overwriting the WAL file from the beginning," because overwriting is faster than appending ([wal.html](https://www.sqlite.org/wal.html), [pragma.html](https://www.sqlite.org/pragma.html)). `RESTART`/`TRUNCATE` checkpoints force this reset explicitly.
- **Truncated on disk:** only by (a) `SQLITE_CHECKPOINT_TRUNCATE`, which "truncates the WAL file to zero bytes" ([c3ref/wal_checkpoint_v2.html](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)), or (b) `PRAGMA journal_size_limit=N`: "Each time a transaction is committed or a WAL file resets, SQLite compares the size of... the WAL file left in the file-system to the size limit... and if... larger it is truncated to the limit" ([pragma.html](https://www.sqlite.org/pragma.html)).
- **Deleted:** when the last connection closes cleanly (it does one final checkpoint first); otherwise it may persist after an unclean exit or with `SQLITE_FCNTL_PERSIST_WAL`. "The only safe way to remove a WAL file is to open the database... then immediately close it" ([wal.html](https://www.sqlite.org/wal.html)).

## 5. Checkpoint modes compared (practical behavior)

Mode semantics per [c3ref/c_checkpoint_full.html](https://www.sqlite.org/c3ref/c_checkpoint_full.html): PASSIVE = "Do as much as possible w/o blocking"; FULL = "Wait for writers, then checkpoint"; RESTART = "Like FULL but wait for readers"; TRUNCATE = "Like RESTART but also truncate WAL".

| | Waits for writers | Waits for readers | Resets WAL offset | Shrinks file on disk | Failure behavior with persistent readers |
|---|---|---|---|---|---|
| **PASSIVE** (default; all auto-checkpoints) | no | no | only if fully complete & no readers (next writer rewinds) | no | never blocks; silently makes partial or zero progress; pragma col 1 stays 0 ([pragma.html](https://www.sqlite.org/pragma.html)) |
| **FULL** | yes (busy-handler) | no | no (documented distinction vs RESTART is the reader wait) | no | returns `SQLITE_BUSY` if it can't complete, e.g. active reader; pragma col 1 = 1 ([pragma.html](https://www.sqlite.org/pragma.html)) |
| **RESTART** | yes | yes (busy-handler) | yes — WAL starts again at offset zero | no | waits up to busy-timeout, then degrades to passive partial work and returns `SQLITE_BUSY` ([c3ref/wal_checkpoint_v2.html](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)) |
| **TRUNCATE** | yes | yes | yes | yes — file truncated to 0 bytes (counters report 0) | same as RESTART |

(`NOOP` does no work and just reports frame counts.) The docs' guidance for a growing WAL is exactly this: "one might also consider running manual checkpoints with the SQLITE_CHECKPOINT_RESTART or SQLITE_CHECKPOINT_TRUNCATE option which will ensure that the checkpoint runs to completion before returning. The disadvantage... is that readers might block while the checkpoint is running" ([wal.html](https://www.sqlite.org/wal.html)). Interpretation: what actually waits is the *checkpoint* (via busy-handler) for active readers to finish; reader queries themselves are not blocked by the wait, but a RESTART/TRUNCATE cannot succeed at all while any read transaction persists.

## 6. What an application can do when the WAL keeps growing

Documented levers:

1. **Eliminate long-lived read transactions** — create "reader gaps" and checkpoint during them ([wal.html](https://www.sqlite.org/wal.html)). (App-level specifics like closing cursors promptly are interpretation, but the cause is documented.)
2. **Run explicit `PRAGMA wal_checkpoint(RESTART|TRUNCATE)`** at quiet moments; use TRUNCATE if on-disk size matters. Check the returned row: col 1 = 1 means a RESTART/FULL/TRUNCATE was blocked (e.g., by an active reader); cols 2–3 give frames in WAL vs frames checkpointed, so you can *detect* starvation ([pragma.html](https://www.sqlite.org/pragma.html)).
3. **Don't disable auto-checkpointing**; tune the threshold with `PRAGMA wal_autocheckpoint=N` (all auto-checkpoints are PASSIVE) ([c3ref/wal_autocheckpoint.html](https://www.sqlite.org/c3ref/wal_autocheckpoint.html), [pragma.html](https://www.sqlite.org/pragma.html)).
4. **Cap on-disk size** with `PRAGMA journal_size_limit=N` — truncates the WAL to N bytes after commits/resets ([pragma.html](https://www.sqlite.org/pragma.html)). Note this only helps once a reset is actually possible, i.e., no active readers (interpretation from the documented "or a WAL file resets" trigger).
5. **Keep write transactions small** — huge single transactions transiently bloat the WAL even with healthy checkpointing ([wal.html](https://www.sqlite.org/wal.html)).
6. **Ensure at least one writable connection exists** for checkpointing; consider running checkpoints in a separate thread/process (especially with `synchronous=NORMAL`, where checkpoints are the only fsync point) ([wal.html](https://www.sqlite.org/wal.html)).
7. **Last resort:** close all connections — the last closing connection does a final checkpoint and deletes `-wal`/`-shm`; that open+close is "the only safe way to remove a WAL file" ([wal.html](https://www.sqlite.org/wal.html)).

## 7. Important limitations and edge cases

- **Busy, not forced:** FULL/RESTART/TRUNCATE never kill readers; past `busy_timeout` they degrade to passive partial work and return `SQLITE_BUSY` ([c3ref/wal_checkpoint_v2.html](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)). A persistent reader means the WAL keeps growing regardless of how often you checkpoint.
- **Concurrent checkpoints collide:** two simultaneous checkpointers → immediate `SQLITE_BUSY`, busy-handler not invoked ([c3ref/wal_checkpoint_v2.html](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html)). Don't run manual checkpoints from multiple connections/threads at once — which matters because of the next item.
- **WAL-reset bug (corruption):** in SQLite 3.7.0–3.51.2, a data race between concurrent checkpoints and a commit that resets the WAL could corrupt the database; fixed in 3.51.3 with backports to 3.44.6/3.50.7 ([wal.html](https://www.sqlite.org/wal.html)). If you run background checkpoint threads alongside writers, upgrade.
- **Read performance degrades as the WAL grows** — the wal-index mitigates but "performance still falls off with increasing WAL file size," so a large WAL is not just a disk-space problem ([wal.html](https://www.sqlite.org/wal.html)).
- **Checkpoints need write access and sync I/O:** read-only connections can't checkpoint; checkpoints are slower than writes (syncs + seeks) ([wal.html](https://www.sqlite.org/wal.html), [pragma.html](https://www.sqlite.org/pragma.html)).
- **WAL mode requires shared memory on one machine** — it "will not work on a network filesystem" (single-process `locking_mode=EXCLUSIVE` is the documented workaround) ([wal.html](https://www.sqlite.org/wal.html)).
- **File lifecycle edge cases:** `-wal`/`-shm` may survive unclean shutdowns or `SQLITE_FCNTL_PERSIST_WAL`; a WAL separated from its DB file risks lost commits/corruption; pre-3.7 SQLite can't even open a WAL-mode database (format version bumped to 2) ([wal.html](https://www.sqlite.org/wal.html)).
- **Reader-side BUSY cases:** exclusive locking mode, the last connection's cleanup lock, and post-crash recovery (which holds an exclusive lock) can make queries return `SQLITE_BUSY` even though "readers do not block writers" is mostly true ([wal.html](https://www.sqlite.org/wal.html)).
- **Stalled checkpoints resume only on writes:** a passive checkpoint that stopped at a reader's end mark resumes "after the next write transaction" — in a read-only workload it won't retry until something writes or an explicit checkpoint runs ([wal.html](https://www.sqlite.org/wal.html)).

## Sources

All from official SQLite documentation (fetched 2026-10-11):
- [Write-Ahead Logging (wal.html)](https://www.sqlite.org/wal.html) — end marks, checkpoint stop rule, writer rewind, default 1000-page strategy, recycling behavior, unbounded-growth causes and remedies, WAL file lifecycle, busy cases, WAL-reset bug.
- [PRAGMA Statements (pragma.html)](https://www.sqlite.org/pragma.html) — `wal_checkpoint` modes incl. NOOP and return-value semantics; `wal_autocheckpoint`; `journal_size_limit`; `synchronous=NORMAL` in WAL mode.
- [sqlite3_wal_checkpoint_v2()](https://www.sqlite.org/c3ref/wal_checkpoint_v2.html) — checkpoint/writer locks, busy-handler degradation to passive behavior, TRUNCATE zeroing the file.
- [Checkpoint Mode Values (c_checkpoint_full.html)](https://www.sqlite.org/c3ref/c_checkpoint_full.html) — per-mode constant definitions.
- [sqlite3_wal_autocheckpoint()](https://www.sqlite.org/c3ref/wal_autocheckpoint.html) — auto-checkpoint trigger, PASSIVE-only, default threshold, disabling.

Everything quoted above is documented behavior; items marked "interpretation" are inferences from those mechanisms (e.g., that closing idle cursors/transactions fixes starvation, that FULL does not reset the WAL offset, and what exactly waits during a RESTART checkpoint).

---

