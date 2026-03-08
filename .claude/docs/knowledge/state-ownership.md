# State Ownership Contract

This document is the canonical reference for which layer owns which mutable state
file, what mutation rules apply, and how each field behaves under context-budget
degradation. The runtime chain is Ralph (orchestrator) -> ralph-story (story agent)
-> ralph-worker (worker sub-agent). Framing this chain as a **runtime reliability
concern** -- not an API support concern -- is deliberate: the primary failure modes
are context-budget exhaustion, state handoff fidelity loss, and audit gaps, not
interface mismatches.

See also: `.claude/hooks/_lib.py` `DEFAULT_WORKFLOW_STATE` for the authoritative
Python defaults; `.claude/docs/ARCHITECTURE.md` Data Flow section for the owner
layer table.

---

## State Files and Owners

| File | Owner Layer | Mutation Rules |
| ---- | ----------- | -------------- |
| `.claude/.workflow-state.json` | Hooks + Ralph orchestrator | Hooks write `needs_verify` and `stop_block_count` via `write_marker` / `clear_marker`. Ralph orchestrator writes the `ralph` subsection (story progress, checkpoint hash, current step). ralph-story and ralph-worker NEVER write this file directly. Atomic writes via `write_atomic()` with retry on `PermissionError`. |
| `.claude/prd.json` | Ralph orchestrator (outer loop only) | Ralph marks `passed: true` per story after a verified merge. ralph-story and ralph-worker read it but never write it. |
| `.claude/docs/verification-log.jsonl` | ralph-story agent | Appended once per story attempt (PASS or FAIL). ralph-worker does not write it. Append-only; never truncated by workflow code. |
| `.claude/docs/progress.md` | Ralph orchestrator | Appended after each story result. Gitignored -- not present in worktrees. ralph-story receives progress context embedded in the dispatch prompt. |
| `.claude/receipts/` (QA receipts) | ralph-story agent | Written by `qa_runner.py` during story verification. One receipt per story attempt. ralph-worker returns the receipt object in `RALPH_WORKER_RESULT`; ralph-story writes it to disk. |
| `.claude/hooks/_lib.py` `DEFAULT_WORKFLOW_STATE` | Source -- hooks team | Defines schema defaults. Changing this dict changes what `read_workflow_state()` returns for missing keys. Any new field must be added here and documented in this file. |
| `.claude/runtime/fix-log/{story_id}.md` | ralph-story agent | Append-only during fix loop iterations within a story attempt. Each iteration appends a structured entry (failing steps, changes made, files touched, outcome). Deleted on successful QA pass (cleanup). Created with `mkdir -p` on first write. File is gitignored under `.claude/runtime/`. Non-fatal if read/write fails (degrades to status quo). |

### Fields Within `.workflow-state.json`

| Field | Owner | Mutation Event |
| ----- | ----- | -------------- |
| `needs_verify` | `post_format.py` hook (set), `post_bash_capture.py` hook (clear) | Set when a code file is edited; cleared when tests pass. |
| `stop_block_count` | `stop_verify_gate.py` hook | Incremented each time Stop is blocked; reset to 0 when marker is cleared. |
| `ralph.consecutive_skips` | Ralph orchestrator | Incremented on story skip; reset to 0 on story pass. |
| `ralph.stories_passed` | Ralph orchestrator | Incremented after successful story merge. |
| `ralph.stories_skipped` | Ralph orchestrator | Incremented after max_attempts exhausted. |
| `ralph.feature_branch` | Ralph orchestrator (STEP 1.5) | Set once at sprint start; never changed mid-sprint. |
| `ralph.current_story_id` | Ralph orchestrator (STEP 2-3) | Updated before each story dispatch. |
| `ralph.current_attempt` | Ralph orchestrator (STEP 4) | Incremented on each dispatch; reset to 0 at story start. |
| `ralph.max_attempts` | Ralph orchestrator (STEP 1) | Set from prd.json at sprint start; not mutated after. |
| `ralph.prior_failure_summary` | Ralph orchestrator (STEP 5) | Written after a FAIL result; cleared after a PASS. |
| `ralph.current_step` | Ralph orchestrator | Tracks orchestrator position (e.g., "STEP 4") for compaction recovery. |
| `ralph.checkpoint_hash` | Ralph orchestrator (STEP 4 pre-dispatch) | Full git hash written before story dispatch; used for `git reset --hard` on merge conflict. |

---

## Single-Writer Invariants

1. **One writer per field**: Each field in `.workflow-state.json` has exactly one
   owner layer. No two agents write the same field. Violations cause race conditions
   and silent state corruption.

2. **Hooks write lifecycle flags**: `needs_verify` and `stop_block_count` belong to
   the hook layer exclusively. Ralph orchestrator reads but never writes them.

3. **Ralph orchestrator owns the `ralph` subsection**: Only the outer Ralph loop
   (`ralph.md` / `ralph` SKILL.md) writes the `ralph` dict. ralph-story and
   ralph-worker are consumers, not writers, of this section.

4. **ralph-story appends verification-log.jsonl**: ralph-worker returns a
   `qa_receipt` in its result JSON. ralph-story writes the receipt to disk and
   appends one entry to `verification-log.jsonl`. The outer loop does not duplicate
   this write.

5. **prd.json is write-once per story**: Only the Ralph outer loop marks
   `passed: true` after a verified merge. No retry path writes `passed` back to
   `false`.

6. **Atomic writes are mandatory**: All writes to `.workflow-state.json` MUST use
   `write_atomic()` or `write_workflow_state()` from `_lib.py`. Direct `open()`
   writes bypass the retry-on-PermissionError guard and the tmp-file swap, creating
   partial-write risk on Windows.

---

## Context-Budget Degradation

The Ralph -> story -> worker chain is a **nested agent invocation**. Each layer
consumes context tokens. When context approaches the budget limit, the agent may
be compacted (context window reset). The following rules define what each layer
must re-read on recovery.

### Ralph Orchestrator (outer loop)

- On compaction: reads `.workflow-state.json` `ralph.current_step` to determine
  where to resume.
- Re-reads `prd.json` to find the next unfinished story.
- Does NOT rely on in-memory state surviving compaction. Every field it needs is
  persisted before dispatch.
- `ralph.checkpoint_hash` is written to state before dispatching ralph-story so
  the outer loop can find it after compaction (even though the dispatch prompt
  also embeds it for ralph-story).

### ralph-story agent (per-story)

- Receives all required state as **pass-by-value in the dispatch prompt**
  (`checkpoint_hash`, `feature_branch`, `acceptanceCriteria`, etc.).
- Does NOT read `.workflow-state.json` for story-execution decisions. The dispatch
  prompt is the authoritative source.
- On compaction within a story run: re-reads PLAN.md and the dispatch prompt
  context. Cannot recover mid-merge -- treats partial state as FAIL.
- **Fix-log as compaction recovery mechanism**: During the inner fix loop,
  ralph-story appends each iteration to `.claude/runtime/fix-log/{story_id}.md`.
  On compaction, the agent re-reads this file to recover what was already tried,
  avoiding redundant fix attempts. This is the primary compaction-resilience
  mechanism for the ralph-story fix loop. The fix-log is deleted on successful
  QA pass; if the story fails, its content is embedded in the `summary` field
  of RALPH_STORY_RESULT for inclusion in `prior_failure_summary` on retry.

### ralph-worker sub-agent (per-story implementation)

- Receives all context via the worker dispatch prompt.
- Writes no state files. Returns `RALPH_WORKER_RESULT` JSON in its output.
- On compaction: re-reads PLAN.md, acceptance criteria from prompt, and runs
  gate commands to assess current state. TDD loop provides natural recovery
  checkpoints (tests either pass or they do not).

### Degradation Failure Modes

| Failure Mode | Detection | Recovery |
| ------------ | --------- | -------- |
| Ralph compacted mid-sprint | `ralph.current_step` stale | Re-read state, re-derive next story from prd.json |
| ralph-story compacted mid-merge | Merge branch in dirty state | Return FAIL, outer loop resets to `checkpoint_hash` |
| Worker compacted mid-implementation | Tests still fail | Worker re-reads criteria, re-runs TDD loop |
| State file corrupt after crash | `read_workflow_state()` returns default | Safe -- defaults allow clean restart |

---

## State Handoff Fidelity

The Ralph -> story -> worker chain passes state in two ways.

### Pass-by-Value (embedded in dispatch prompt)

These fields are copied into the dispatch prompt text. They are authoritative at
call time and do NOT require the sub-agent to read a file:

| Field | Passed From | Passed To |
| ----- | ----------- | --------- |
| `checkpoint_hash` | Ralph outer loop | ralph-story dispatch prompt |
| `feature_branch` | Ralph outer loop | ralph-story dispatch prompt |
| `story_id` | prd.json | ralph-story dispatch prompt |
| `acceptanceCriteria` | prd.json | ralph-story dispatch prompt, then worker |
| `gateCmds` | prd.json | ralph-story dispatch prompt, then worker |
| `attempt` | Ralph outer loop counter | ralph-story dispatch prompt |
| `prior_failure_summary` | Ralph outer loop | ralph-story dispatch prompt, then worker |
| `sprint_progress` | progress.md content | ralph-story dispatch prompt, then worker |

**Critical invariant**: ralph-story reads `checkpoint_hash` from the dispatch
prompt -- NOT from `.workflow-state.json`. The dispatch prompt is the authoritative
source because the state file may be stale if another story ran concurrently or if
the file was not flushed before dispatch.

### Pass-by-Reference (read from file by sub-agent)

These items are too large to embed in the prompt or change frequently enough that
the sub-agent must read the current version:

| Resource | Read By | File Location |
| -------- | ------- | ------------- |
| PLAN.md | ralph-story (plan check), ralph-worker (implementation guide) | `.claude/docs/PLAN.md` |
| prd.json | ralph-story (criteria IDs), ralph-worker (acceptance criteria) | `.claude/prd.json` |
| workflow.json | ralph-worker (gate commands fallback) | `.claude/workflow.json` |

### Fidelity Failure Modes

| Failure | Consequence | Mitigation |
| ------- | ----------- | ---------- |
| `checkpoint_hash` read from stale state file | `git reset --hard` to wrong commit | Always read from dispatch prompt |
| Worker result JSON malformed | Story treated as FAIL | ralph-story uses fallback qa_receipt schema |
| `sprint_progress` stale (progress.md not flushed) | Worker has stale context | Non-blocking -- worker only uses it for informational context |

---

## Auditability Requirements

Each layer must produce enough output that `/audit` can reconstruct the sprint
state without reading runtime-only files.

### Ralph Orchestrator

- Writes one entry to `verification-log.jsonl` per story (via ralph-story).
- Updates `prd.json` `passed` flag -- audit can reconstruct sprint progress from
  prd.json alone.
- Writes `ralph.current_step` to state so `/audit` can detect interrupted sprints.

### ralph-story

- Returns `RALPH_STORY_RESULT` JSON as the last output, containing:
  - `passed`, `summary`, `files_changed`, `attempt`, `story_id`
  - `qa_receipt` (full 12-step QA receipt from `qa_runner.py`)
  - `prod_violations_checked` flag
- Appends one JSONL entry to `verification-log.jsonl` with story metadata.
- The qa_receipt must contain `criteria_verified` listing all acceptance criteria
  IDs, enabling `/audit Section 4` to verify full traceability.

### ralph-worker

- Returns `RALPH_WORKER_RESULT` JSON containing:
  - `passed`, `summary`, `files_changed`, `worktree_branch`
  - `qa_receipt` with all 12 QA steps
- Does NOT write to any persistent file. All audit data flows through ralph-story.

### Audit Reconstruction Path

```
/audit Section 4
    reads verification-log.jsonl (append-only, one entry per story)
        contains story_id, passed, qa_receipt.criteria_verified
    reads prd.json (passed flags per story)
    cross-references PLAN.md R-PN-NN IDs
    -> full traceability: requirement -> story -> test -> verification
```

### Minimum Auditability Invariants

1. Every story attempt (pass or fail) produces one `verification-log.jsonl` entry.
2. Every entry contains the story acceptance criteria IDs in `criteria_verified`.
3. `prd.json` `passed` is updated atomically after a verified merge (never before).
4. QA receipts contain `overall_result` and all 12 step results.
5. No state mutation happens between the last gate command pass and the merge --
   the merge itself is the commit of record.
