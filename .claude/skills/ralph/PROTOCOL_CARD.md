# Ralph Protocol Card (condensed state machine)

## Loop: STEP 2->3->4->5->loop | all passed->STEP 6

| Step     | current_step         | Action                         | Key Decision                           |
| -------- | -------------------- | ------------------------------ | -------------------------------------- |
| STEP 1   | (init)               | Validate prd.json, init state  | Schema error? -> STOP                  |
| STEP 1.5 | (branch)             | Create/resume feature branch   | --                                     |
| STEP 2   | STEP_2_FIND_NEXT     | Find first unpassed story      | All passed? -> STEP 6                  |
| STEP 3   | (checkpoint+plan)    | Clean-tree check, plan check   | Dirty/gap? -> STOP                     |
| STEP 4   | STEP_4_DISPATCH      | Launch ralph-story via Agent   | ralph-story returns RALPH_STORY_RESULT |
| STEP 5   | STEP_5_HANDLE_RESULT | Parse RALPH_STORY_RESULT, gate | PASS -> merge; FAIL -> retry/skip      |
| STEP 6   | (end)                | Sprint summary + PR prompt     | --                                     |

## PASS Path (STEP 5)

1. ralph-story internally validates qa_receipt: exists, 12 steps, overall=PASS, criteria match
2. ralph-story runs diff review: 5 questions (Q1-Q5) all YES required
3. ralph-story merges worktree branch: `git merge --no-ff [worktree_branch]`
4. ralph-story runs regression gate
5. Ralph outer loop: update prd.json passed=true, log to verification-log.jsonl
6. Reset consecutive_skips=0, increment stories_passed -> STEP 2

## FAIL Path (STEP 5)

- attempt < max_attempts(4): increment attempt, store failure summary -> STEP 4 (retry)
- attempt >= max_attempts: skip story, increment consecutive_skips -> STEP 2

## Circuit Breaker

consecutive_skips >= 3 -> STOP sprint -> STEP 6

## Parallel Dispatch (parallelGroup)

Stories with same `parallelGroup` and all `dependsOn` satisfied dispatch simultaneously via multiple Agent calls in a single message.

## State Files

- **Read/Write**: `.claude/.workflow-state.json` (ralph section: consecutive_skips, stories_passed, stories_skipped, current_story_id, current_attempt, current_step, prior_failure_summary, checkpoint_hash)
- **Read + update passed**: `.claude/prd.json`
- **Append**: `.claude/docs/progress.md`, `verification-log.jsonl`
