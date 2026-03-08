# UAT Strategy / Acceptance Plan
**Project:** WIT V2
**Phase:** Authored in Phase 1, Executed in Phase 5

## 1. Overview
This UAT plan validates that the delivered product meets the business logic and user fantasies per the SRS and GDD. It acts as the final gate check in Phase 5 before Deployment (Phase 6).

## 2. Acceptance Scenarios

### Scenario 1: Onboarding Basics & Account Migration
- **Objective:** Verify guest entry, tutorial flow, and account binding.
- **Preconditions:** Fresh install, no cached auth.
- **Execution Steps:** 
  1. Boot app and enter Guest flow. 
  2. Execute tutorial's basic word formation, draw/discard, and guided capture.
  3. Enter settings and bind account via Apple/Google SSO.
- **Expected Results:** User advances to lobby with persistent guest identifier; Binding process succeeds and merges Guest ID to Auth ID without data loss.
- **Pass/Fail Evidence:** Event analytics emissions (install, tutorial_complete, account_bound).
- **Linked Requirement IDs:** FR-1.1, FR-1.2, FR-3.5
- **Target Pass Criteria:** Tutorial completion rate ≥ 90%; Account bind success rate 100%.

### Scenario 2: The Capture Engine & Wildcard Locks
- **Objective:** Verify valid captures, wildcard mutations, invalid rejections, and state visualizations.
- **Preconditions:** Active match; Player A played word "TOP" (where 'O' is a wildcard).
- **Execution Steps:** Player B submits capture "STOP", keeping wildcard as 'O'. Next turn: attempt invalid capture "POPS".
- **Expected Results:** Server accepts "STOP", awards B +2 bonus points. Player A retains previously earned points for "TOP". Ownership transfers to B. Lineage log strictly records TOP -> STOP. "POPS" is rejected.
- **Pass/Fail Evidence:** Server validation trace; Screen recording of UI animation highlight.
- **Linked Requirement IDs:** FR-3.2, FR-3.3, FR-3.4, FR-4.2, FR-6.1
- **Target Pass Criteria:** 100% rejection accuracy for invalid combinations; 100% persistent lock of assigned wildcards.

### Scenario 3: Live Match State Integrity & Reconnect
- **Objective:** Verify network instability recovery and timer handling.
- **Preconditions:** Active live 1v1 match. Timer set to 60s per turn.
- **Execution Steps:** Player A forces app close (network drop). Wait 15 seconds, open app.
- **Expected Results:** App reconnects. Turn timer resumes from server state (-15s).
- **Pass/Fail Evidence:** State snapshot hashes before drop and after reconnect must match perfectly.
- **Linked Requirement IDs:** FR-4.4, NFR-1.3, NFR-2.1
- **Target Pass Criteria:** Reconnect logic resolves gameboard visually to parity in ≤ 3s with 0 state divergence.

### Scenario 4: Asynchronous Turn Notifications
- **Objective:** Verify async retention loop and fallback resilience.
- **Preconditions:** Async match initialized. Player B's app backgrounded. 
- **Execution Steps:** Player A commits turn. Player B taps push notification.
- **Expected Results:** App deep-links to specific match ID, loading replay history immediately.
- **Pass/Fail Evidence:** Push event payload IDs vs polling fetch events in analytics.
- **Linked Requirement IDs:** FR-7.1, NFR-1.4, NFR-1.5
- **Target Pass Criteria:** Async deep-link success rate is ≥ 98%.

### Scenario 5: Edge Rules & Modifiers Accuracy
- **Objective:** Verify rule modifier configurations execute accurately.
- **Preconditions:** Match running with Modifier "Long Form". Match 2 running vanilla.
- **Execution Steps:** Play a valid 6-letter word in both matches.
- **Expected Results:** Modifier bonus (+X points) exclusively applied on Match 1.
- **Pass/Fail Evidence:** JSON response payloads.
- **Linked Requirement IDs:** FR-5.1, FR-5.2
- **Target Pass Criteria:** Exact scalar alignment across 100% of permutations.

### Scenario 6: Disconnect Forfeits and Ranked Writes
- **Objective:** Verify idempotent ranked writes and dodge prevention.
- **Preconditions:** Active ranked match.
- **Execution Steps:** Player disconnects, out-waits clock. Player A and B both hit "Rematch" after conclusion.
- **Expected Results:** Server auto-commits forfeit. End round logic fires. MMR written idempotently. Rematch instantiates distinct new Match ID.
- **Pass/Fail Evidence:** DB Row updates.
- **Linked Requirement IDs:** FR-9.1, FR-9.2
- **Target Pass Criteria:** 0 duplicate writes globally observed.

### Scenario 7: End of Round Triggers and Penalties
- **Objective:** Validate game conclusion triggers and scoring.
- **Preconditions:** Player has 1 letter in hand (no plays possible) or 0 letters left. Stock is exhausted.
- **Execution Steps:** Player discards final letter OR plays final letter.
- **Expected Results:** Round End trigger fires immediately. Opponent receives -1 penalty per remaining letter in hand.
- **Pass/Fail Evidence:** Scoreboard logs showing negative penalty derivations.
- **Linked Requirement IDs:** FR-4.3
- **Target Pass Criteria:** Point deduplication aligns perfectly across 100 simulated test clients.
