---
name: ralph
description: Run autonomous V-Model orchestrator v5 — dispatches per-story ralph-story agents, auto-retries failures (up to 4 attempts per story), auto-skips on exhaustion, circuit breaker stops after 3 consecutive exhausted stories. Only prompts user for PR creation at session end.
---

# Ralph - V-Model Autonomous Orchestrator v5

You are now operating in **Ralph Mode** — a lean outer loop that dispatches one `ralph-story` agent per story. Ralph orchestrates; ralph-story handles all per-story protocol (checkpoint, plan check, worker dispatch, verification, merge).

## Core Rule

Delegation to `ralph-story` via the **Agent tool** is mandatory. Ralph MUST NOT attempt to implement stories directly. Every story is dispatched to a `ralph-story` sub-agent with `subagent_type: "ralph-story"`. The ralph-story agent handles STEP 4 through STEP 6A internally and returns `RALPH_STORY_RESULT`.

## STEP 1: Initialize

Display: `"RALPH - V-Model Orchestrator v5 — Mode: Autonomous"`

Read `.claude/prd.json` and validate:

1. Check `version` field exists and equals `"2.0"`. If not: display deprecation warning and **STOP**.
2. Validate each story has: `id`, `description`, `phase`, `acceptanceCriteria` (array), `gateCmds` (object), `passed` (boolean), `verificationRef`. If any missing: display errors and **STOP**.
3. Run `check_plan_prd_sync()` from `_qa_lib.py` on `.claude/docs/PLAN.md` and `.claude/prd.json`:
   - If `added` or `removed` non-empty: display drift details and `"Run /plan to regenerate."` then **STOP**.
   - Compare `plan_hash` from sync result against `prd.json["plan_hash"]`. If mismatch: display hash mismatch and **STOP**.
   - If in sync: display `"Plan-PRD sync: OK"` and `"Plan hash: OK"`.
4. Display: `"Found [total] stories, [passed] completed, [remaining] remaining"`
5. Initialize sprint state via `update_workflow_state(ralph={...})` from `_lib.py`. Fields: `consecutive_skips: 0`, `stories_passed: 0`, `stories_skipped: 0`, `feature_branch: ""`, `current_story_id: ""`, `current_attempt: 1`, `max_attempts: 4`, `prior_failure_summary: ""`, `checkpoint_hash: ""`.

Startup worktree sweep:

1. `git worktree prune`
2. `git worktree list --porcelain` — for any path matching `.claude/worktrees/agent-*`: `git worktree remove --force [path]`

## STEP 1.5: Feature Branch Setup

Determine branch name: `ralph/{plan-name}` from PLAN.md title (lowercase, hyphens for spaces), or user-specified.

- **Exists**: `git checkout [branch]` — display `"Resuming branch: [branch]"`
- **New**: `git checkout -b [branch]` — display `"Created branch: [branch] (based on [current-branch])"`

Record branch in state: `update_workflow_state(ralph={"feature_branch": "[branch]"})`.

All story commits go to THIS branch. **NEVER commit directly to main or master.**

## STEP 2: Find Next Story

Update step: `update_workflow_state(ralph={"current_step": "STEP_2_FIND_NEXT"})`.

Re-read sprint state from `.claude/.workflow-state.json` (survives context compaction).

**Mandatory STATE SYNC display:**

```
STATE SYNC: story=[current_story_id] attempt=[current_attempt] skips=[consecutive_skips]
```

From `prd.json`, find the **first story** where `"passed": false`.

- If ALL stories have `"passed": true`: proceed to **STEP 6**.
- If a story is found: continue to STEP 3.

**Phase-boundary regression gate**: When the next story's `phase` differs from the previous story's `phase` (i.e., transitioning between phases), run the `unit` tier regression before dispatching the new story:

1. Read `regression_tiers.unit.cmd` from `workflow.json` (via `load_workflow_config()`).
2. If found: run the command. If it fails: display `"Phase-boundary regression FAILED — stopping sprint."` and go to STEP 6.
3. If not found: skip silently (no tiers configured).

## STEP 3: Safety Checkpoint + Plan Check

Display story ID, phase, description, acceptance criteria, and gate commands.

Update state: `update_workflow_state(ralph={"current_story_id": "[story.id]", "current_attempt": 1, "max_attempts": 4, "prior_failure_summary": ""})`.

1. Verify working tree is clean: `git status --porcelain`. If dirty: display warning and **STOP**.
2. Record full hash: `git rev-parse HEAD` (NOT `--short`).
3. Display: `"Checkpoint: [short-hash] ([branch-name]) — full: [full-hash]"`
4. Store hash: `update_workflow_state(ralph={"checkpoint_hash": "[full_hash]"})`.
5. Read `.claude/docs/PLAN.md` — extract all R-PN-NN IDs from Done When sections. Compare against story's `acceptanceCriteria` IDs:
   - If ALL found in PLAN.md: display `"Plan check: OK"` and continue to STEP 4.
   - If ANY missing: display `"Plan gap: criteria [missing IDs] not covered by PLAN.md. Run /plan to update, then resume /ralph."` and **STOP**.

## STEP 4: Dispatch ralph-story Agent

Update step: `update_workflow_state(ralph={"current_step": "STEP_4_DISPATCH"})`.

Read `progress.md` from `.claude/docs/progress.md` if it exists.
Read sprint state for `current_attempt`, `prior_failure_summary`, `feature_branch`, `checkpoint_hash`.

**Dependency check (dependsOn):** Before dispatching, check each story's `dependsOn` list (`.get("dependsOn", [])`). If any referenced story does not yet have `passed: true`, defer that story to the next loop iteration — do NOT dispatch it now.

**Parallel dispatch (parallelGroup):** Group all ready stories (dependsOn met) by `parallelGroup` (`.get("parallelGroup", None)`). For each group with multiple stories, dispatch ALL of them simultaneously via multiple Agent tool calls in a single message — one `ralph-story` per story, each with `subagent_type: "ralph-story"`. Stories with no group (null) or groups of one dispatch individually (same as before).

Launch **`ralph-story`** agent via Agent tool with `subagent_type: "ralph-story"`:

```
RALPH_STORY_DISPATCH:
{
  "story_id": "[story.id]",
  "phase": [story.phase],
  "phase_type": "[story.phase_type or null]",
  "description": "[story.description]",
  "acceptanceCriteria": [/* array of {id, criterion, testType} */],
  "gateCmds": { "unit": "...", "integration": "...", "lint": "..." },
  "checkpoint_hash": "[full_hash from state]",
  "feature_branch": "[feature_branch from state]",
  "attempt": [current_attempt],
  "max_attempts": 4,
  "prior_failure_summary": "[prior_failure_summary or First attempt — no prior failures]  (may contain enriched fix-log content from prior attempts)",
  "sprint_progress": "[relevant lines from progress.md or First story in sprint]"
}
```

Receive result(s) from ralph-story agent(s). For parallel groups, collect all results before proceeding to STEP 5.

## STEP 5: Handle RALPH_STORY_RESULT

Update step: `update_workflow_state(ralph={"current_step": "STEP_5_HANDLE_RESULT"})`.

Parse result(s) with graceful error handling — look for `RALPH_STORY_RESULT:` in each agent output and extract JSON. If missing or malformed for any dispatched story, treat that story as FAIL with summary `"Missing or malformed RALPH_STORY_RESULT from ralph-story agent."`. Other parallel stories' results are still processed.

**Parallel result collection:** Collect ALL `RALPH_STORY_RESULT` entries into memory first. Then process and merge results in story-ID order (ascending). After all results are evaluated in memory, perform a single atomic prd.json write updating all passed stories at once. This prevents partial writes if Ralph crashes between story updates.

Clear checkpoint: `update_workflow_state(ralph={"checkpoint_hash": ""})`.

### If PASSED (`result.passed == true`):

Before marking a story as passed, call `validate_story_promotion(receipt_path, reviewer_result)` from `_qa_lib.py` to enforce executable promotion gates. Pass the receipt path from the story result's `qa_receipt` source and the reviewer result string ("PASS", "WARN", or "FAIL"). If `validate_story_promotion()` returns `(False, reason)`, treat the story as FAILED with summary `"Promotion gate blocked: [reason]"` and do not update prd.json.

1. Call `validate_story_promotion(receipt_path, reviewer_result)` from `_qa_lib.py`. If returns `(False, reason)`: treat as FAIL.
2. Update prd.json: set `passed: true`, `verificationRef: "verification-log.jsonl"` for this story.
3. Update state: set `consecutive_skips` to 0, increment `stories_passed`.
4. Display: `"PASSED: [story.id] — Files: [files_changed] — Progress: [stories_passed]/[total]"`
5. Append to `.claude/docs/progress.md`: `### [story.id] — PASS ([date])` with files, criteria count, summary.
6. Auto-continue to STEP 2.

### If FAILED (`result.passed == false`):

Read state for `current_attempt` and `max_attempts`.

**If attempts remaining** (`current_attempt < max_attempts`):

- Increment `current_attempt` in state, store failure summary as `prior_failure_summary`.
- **Enrich prior_failure_summary with fix-log** (if available):
  1. Check if `.claude/runtime/fix-log/{story_id}.md` exists.
  2. If the file exists and is readable, read its content and extract the **last 3 iteration entries** (each entry starts with `## Iteration`).
  3. Cap the extracted fix-log content at ~1000 characters. If it exceeds this limit, truncate and append `[truncated]`.
  4. Append the extracted fix-log content to `prior_failure_summary` under a `\n\n--- Fix-Log (last 3 iterations) ---\n` header.
  5. If the fix-log file does **not** exist or cannot be read (permission error, parse error, etc.), **degrade gracefully**: use `result.summary` as `prior_failure_summary` without modification (status quo behavior). Do not warn the user — this is a normal condition when a story fails before entering the fix loop.
- Display: `"FAILED: [story.id] (attempt [current_attempt]/[max_attempts]) — [summary]. Auto-retrying..."`
- Go back to **STEP 4** (ralph-story gets prior failure context on next attempt, including fix-log history if available).

**If exhausted** (`current_attempt >= max_attempts`):

- Auto-skip: increment `stories_skipped` and `consecutive_skips` in state.
- Display: `"EXHAUSTED: [story.id] after [max_attempts] attempts — [summary]. Skipping."`
- Append to `.claude/docs/progress.md`: `### [story.id] — SKIPPED ([date])` with attempts and last failure.

**Circuit breaker**: if `consecutive_skips` >= 3: display `"CIRCUIT BREAKER: 3 consecutive stories exhausted. Stopping sprint."` and go to **STEP 6**.

Continue to **STEP 2**.

## STEP 6: End of Session

Display: `"RALPH SESSION COMPLETE — Progress: [stories_passed]/[total] ([stories_skipped] skipped) — Branch: [feature_branch]"`

If any stories were skipped, list each with failure summary and attempt count.

**Sprint-end regression gate**: Before PR creation, run the full regression tier:

1. Read `regression_tiers.full.cmd` from `workflow.json` (via `load_workflow_config()`).
2. If found: run the command. If it fails: display `"Sprint-end full regression FAILED — fix before creating PR."` and skip PR creation.
3. If not found: skip (no tiers configured).

If ANY stories passed:

- Ask user: `"Create Pull Request? (Yes / No)"`
- If **Yes**: push branch and create PR via `gh pr create`. Display PR URL. Offer `/code-review`.
- If **No**: display `"Changes on branch [branch]. Push when ready: git push -u origin [branch]"`

Run `/handoff` to save session state.

Clean up sprint state: reset ralph section in `.claude/.workflow-state.json` to defaults.

Display next steps: review PR, run `/audit`, run `/health` before next session.

## Error Recovery

- **prd.json version/parse error**: Run `/plan` to regenerate
- **Git dirty at checkpoint**: STOP — commit or stash first
- **Missing RALPH_STORY_RESULT**: Treat as FAIL, auto-retry with context
- **Plan gap (STEP 3)**: User runs `/plan`, then restarts `/ralph`
- **Circuit breaker**: Review skipped stories, fix root causes, restart
- **Context compaction**: Sprint state in file, re-read at each STEP 2. Re-read PROTOCOL_CARD.md at STEP 2.
- **code-review plugin not available**: Display warning and skip code-review step
