---
name: plan
description: Create/update .claude/docs/PLAN.md for the requested feature.
agent: architect
context: fork
argument-hint: "[feature description]"
---

## Procedure (follow every step in order — do not skip any step)

### 1. Load Context

Read these files (all mandatory — if a file is missing, note it):

- `CLAUDE.md` — project rules and constraints
- `WORKFLOW.md` — usage guide, command reference, step-by-step tutorials
- `PROJECT_BRIEF.md` — tech stack, dependencies, constraints
- `.claude/docs/ARCHITECTURE.md` — system design
- `.claude/docs/HANDOFF.md` — prior session state (if exists)
- `.claude/docs/knowledge/planning-anti-patterns.md` — known pitfalls (if exists)

### 2. Discovery — Read Before You Write

This step is MANDATORY. Do not skip it for any reason.

- Use Glob to find all source files relevant to the requested feature
- **Open and read every file** the plan will modify or depend on
- For each file, record in the plan's System Context section:
  - Function signatures relevant to the change
  - Error handling patterns in use
  - Import dependencies and export surface
- Use Grep to find callers of functions you plan to modify
- Search for existing utilities, helpers, or patterns that could be reused
- Trace the data flow from entry point to output, including error paths
- If ARCHITECTURE.md is empty/placeholder, populate it from findings with [AUTO-DETECTED] tags

### 3. Verify External Dependencies (if external libraries/APIs are involved)

- Query Context7 for up-to-date API documentation
- If Context7 unavailable: WebSearch for "[library] docs [current year]"
- Verify version compatibility with the project's tech stack
- Check for breaking changes: "[library] migration guide [current year]"

### 4. Ask Clarifying Questions

Before writing the plan, surface ambiguities to the user:

- Requirements with multiple valid interpretations
- Performance constraints not specified
- Error handling behavior not defined
- Edge cases where desired behavior is unclear
  Wait for answers before proceeding.

### 5. Write the Plan

Write `.claude/docs/PLAN.md` with ALL mandatory sections filled:

**Top-level (required):**

- Goal (2-3 sentences)
- System Context: Files Read, Data Flow Diagram, Existing Patterns, Blast Radius Assessment

**Per phase (required):**

- Phase Type: one of `foundation`, `module`, `integration`, `e2e` — determines which QA steps are relevant when qa_runner.py runs with `--phase-type`
  - `foundation`: Core types, utilities, infrastructure (skips integration tests, coverage)
  - `module`: Self-contained module implementation (skips integration tests)
  - `integration`: Multi-module integration work (all QA steps run)
  - `e2e`: End-to-end feature validation (all QA steps run)
- Changes table with these 5 columns per row:

  | Action | File | Description | Test File | Test Type |
  | ------ | ---- | ----------- | --------- | --------- |
  - **Action**: ADD, MODIFY, or DELETE
  - **File**: Path to the file being changed
  - **Description**: What changes and why
  - **Test File**: Path to the test file that covers this change (or `N/A` with reason)
  - **Test Type**: `unit`, `integration`, `e2e`, or `manual`

- Untested Files table (required if any Changes table row has Test File = N/A):

  | File | Reason | Tested Via |
  | ---- | ------ | ---------- |
  - **File**: Path to the untested file
  - **Reason**: Why direct tests are not applicable (e.g., "markdown docs", "config only", "covered by integration test")
  - **Tested Via**: How the change is verified instead (e.g., "manual inspection", "integration test in test_foo.py", "linter")

- Interface Contracts (7-column table) — or "N/A — [reason]"
- Data Flow (source → transform → destination with error paths) — or "N/A — [reason]"
- Testing Strategy (what, type, real vs mock, justification, test file)
- Done When (requirement ID format: R-PN-NN, specific observable criteria)
- Verification Command (exact runnable bash command)

**Bottom-level (required):**

- Risks & Mitigations (with likelihood and impact)
- Dependencies (internal and external)
- Rollback Plan
- Open Questions (anything needing user input before building)

### 6a. Pre-Flight Validation (Manual)

Run through the Pre-Flight Checklist in `.claude/agents/architect.md`.
Every item must pass. Fix any failures before outputting the plan.

### 6b. Pre-Flight Validation (Automated)

After Step 6a passes, run these 7 automated checks against the plan. ANY failure requires fixing the plan before proceeding — no bypass.

**Check a — File existence**: For each file in Changes tables marked MODIFY, use Glob to verify the file exists. If not found: **FAIL** `"File not found: [path]"`.

**Check b — R-PN-NN format**: For each Done When item across all phases, verify it starts with the canonical pattern `R-P\d+-\d{2}` (see `.claude/docs/knowledge/conventions.md`). If any item lacks an R-PN-NN ID: **FAIL** `"Hollow criterion: [text]"`.

**Check c — Interface Contracts completeness**: For each phase where Changes table has Action = ADD or MODIFY on a function/component, verify an Interface Contracts row exists with matching Component name. If missing: **FAIL** `"Missing Interface Contract for [component] in Phase [N]"`.

**Check d — Testing Strategy completeness**: For each phase, verify the Testing Strategy section has at least one row. If empty: **FAIL** `"No Testing Strategy for Phase [N]"`.

**Check e — Verification Command validity**: For each phase, verify the Verification Command is not placeholder syntax. If it contains `[`, `]`, `your_command_here`, or `TBD`: **FAIL** `"Placeholder verification command in Phase [N]"`.

**Check f — Cross-phase consistency**: For each Interface Contract in Phase N that is consumed by Phase N+1 (identified by matching Component names in Called By/Calls columns), verify the signatures match. If mismatch: **FAIL** `"Signature mismatch: [component] between Phase [N] and Phase [M]"`.

**Check g — Plan validator**: Run `python .claude/hooks/plan_validator.py --plan .claude/docs/PLAN.md` on the generated plan. This validates measurable verbs in Done When criteria, R-PN-NN format IDs, non-empty Testing Strategy per phase, no placeholder verification commands, and Test File column presence in Changes tables. If the validator exits with code 1 (FAIL): **FAIL** with the validator's JSON output showing which checks failed. Fix the plan issues and re-run.

If ANY check fails: fix the plan, then re-run Step 6b.
If ALL checks pass: proceed to Step 7.

### 7. Auto-Generate prd.json from PLAN.md

After Step 6b passes, run the **deterministic prd generator** to produce `.claude/prd.json`. This step runs ONLY after Pre-Flight validation succeeds. Do NOT manually parse PLAN.md — the generator handles all extraction deterministically.

#### 7a. Run the Generator

```bash
python .claude/hooks/prd_generator.py --plan .claude/docs/PLAN.md --output .claude/prd.json
```

The generator will:

1. Parse each phase header → `STORY-NNN` with phase number, title, and phase type
2. Extract Done When bullets → `acceptanceCriteria[]` with R-PN-NN IDs (including AC-level like `R-P1-01-AC1`)
3. Infer `testType` from Testing Strategy "Type" column (unit/integration/e2e/manual)
4. Infer `testFile` from Testing Strategy and Changes table "Test File" columns
5. Classify Verification Command → `gateCmds{}` (lint/unit/integration by keyword)
6. Compute scope: extract directories from Changes table → `scope[]` per story; compute component from common path; estimate complexity score from file count, criteria count, and cross-package detection → `maxTurns`
7. Analyze file overlap between phases → `dependsOn` and `parallelGroup`
8. Compute `plan_hash` (SHA-256 of sorted R-marker lines only)

**Exit codes**: 0 = success, 1 = partial (some phases had parse errors), 2 = fatal error.

If exit code is 1, review the generated prd.json for `"parseError"` fields and fix the plan. If exit code is 0, proceed to Step 8.

Use `--dry-run` to preview without writing:

```bash
python .claude/hooks/prd_generator.py --plan .claude/docs/PLAN.md --dry-run
```

#### 7b. Verify sync (optional sanity check)

After generation, verify PLAN.md and prd.json are in sync:

```bash
python -c "import sys; sys.path.insert(0,'.claude/hooks'); from _qa_lib import check_plan_prd_sync; from pathlib import Path; r=check_plan_prd_sync(Path('.claude/docs/PLAN.md'), Path('.claude/prd.json')); print('in_sync:', r['in_sync']); [print(f'  {k}: {v}') for k,v in r.items() if k != 'in_sync']"
```

#### Reference: prd.json v2.2 Schema

Per-story fields produced by the generator:

```json
{
  "id": "STORY-001",
  "description": "Phase title",
  "phase": 1,
  "phase_type": "module",
  "component": ".claude/",
  "scope": [".claude/"],
  "complexity": "medium",
  "maxTurns": 150,
  "dependsOn": [],
  "parallelGroup": null,
  "acceptanceCriteria": [
    {
      "id": "R-P1-01",
      "criterion": "...",
      "testType": "unit",
      "testFile": "..."
    }
  ],
  "gateCmds": { "unit": "..." },
  "passed": false,
  "verificationRef": null
}
```

Valid `phase_type` values: `"foundation"`, `"module"`, `"integration"`, `"e2e"`, `null`.

**Error handling**: Phases that fail parsing get `"parseError": "..."` and `"passed": null`.

### 8. Review & Confirm (Human in the Loop)

After prd.json is generated, present the plan summary for user approval. **Do NOT proceed to implementation automatically.**

Display:

```
========================================
  PLAN COMPLETE
========================================
Phases: [count]
Stories: [count] (in prd.json)
Requirements: [count] R-PN-NN criteria

Files affected:
  [list key files from Changes tables]
========================================
```

Then ask the user:

```
What would you like to do?
1. Run /ralph (autonomous implementation in new context)
2. Run /ralph here (implement in current context)
3. Revise the plan (describe what to change)
4. Just save (review later, no implementation now)
```

- **Option 1**: Tell the user to start a new Claude session and run `/ralph`
- **Option 2**: Invoke `/ralph` in the current session
- **Option 3**: Wait for user feedback, then revise PLAN.md and re-run Steps 6b-7
- **Option 4**: Confirm files saved, display paths, stop

**NEVER skip this step. NEVER auto-start implementation.**

## What NOT To Do

- Write implementation code
- Assume file contents without reading them during Discovery
- Skip Discovery for "simple" changes (there is no Quick Plan mode)
- Leave Interface Contracts blank for phases that change function signatures
- Use generic Done When like "code works" or "tests pass" — be specific
- Specify mock-only tests for pure functions or internal module interactions
- Plan phases that depend on later phases (ordering must be correct)
- Skip automated Pre-Flight validation (Step 6b)
- Manually author prd.json when auto-generation is available (Step 7)
