# Test Architecture Plan
**Project:** WIT V2
**Phase:** 1 (Requirements)
**Status:** Engineering Specification — Implementation Grade
**Linked Requirements:** All FR/NFR via RTM, UAT Scenarios 1-7

---

## 1. Purpose

This document maps every requirement category to its test types, defines the test pyramid targets, specifies framework choices per technology layer, and details the CI pipeline stages. It serves as the blueprint for Pod D (Quality / Release / Observability) and establishes quality gates that all other pods must satisfy.

---

## 2. Test Pyramid Targets

### 2.1 Distribution Goals

| Test Level | Target Ratio | Execution Speed | Feedback Loop |
|:-----------|:------------:|:---------------:|:-------------:|
| Unit tests | 70% | < 50ms each | Pre-commit, CI |
| Integration tests | 20% | < 5s each | CI per-PR |
| System / E2E tests | 10% | < 60s each | CI nightly + pre-release |

### 2.2 Definitions

- **Unit tests:** Test a single function, module, or struct in isolation. External dependencies are mocked or stubbed. No network, no database, no file I/O.
- **Integration tests:** Test interactions between 2+ components (e.g., game engine + database, API + matchmaking worker). Real dependencies may be used via containers (testcontainers).
- **System tests (E2E):** Test full user workflows through the real system stack (client -> API -> game server -> DB). Run against a dedicated staging environment or local Docker Compose stack.

---

## 3. Test Framework Choices

### 3.1 Go (Game Server, Workers)

| Purpose | Framework / Tool | Notes |
|:--------|:----------------|:------|
| Unit tests | `testing` (stdlib) + `testify/assert` + `testify/require` | Standard Go test runner. `testify` for assertions and readable failures. |
| Table-driven tests | `testing` sub-tests | Go convention: `t.Run("case_name", ...)` |
| Property tests | `rapid` (pgregory.net/rapid) | QuickCheck-style property testing for Go. Generates random inputs, shrinks failures. |
| Mocking | `testify/mock` or `gomock` | Interface-based mocking for dependencies (DB, lexicon service, PRNG). |
| Benchmarks | `testing.B` | For latency-sensitive paths (scoring, dictionary lookup, state hash). |
| Integration tests | `testcontainers-go` | Spin up Postgres/Redis containers for integration testing. |
| Golden fixtures | Custom fixture loader | JSON/YAML fixture files loaded by test helpers. |
| Coverage | `go test -cover` + `go tool cover` | Minimum 80% line coverage on gameplay core packages. |

### 3.2 Node.js / TypeScript (Meta API, Workers)

| Purpose | Framework / Tool | Notes |
|:--------|:----------------|:------|
| Unit tests | Vitest | Fast, ESM-native, TypeScript-first. Drop-in replacement for Jest in most cases. |
| Integration tests | Vitest + `testcontainers-node` | Real Postgres/Redis for API integration tests. |
| Contract tests | Vitest + `@bufbuild/protobuf` | Validate that Protobuf-generated types match expected schemas. |
| API tests | Vitest + `supertest` | HTTP-level testing of REST endpoints. |
| Mocking | Vitest built-in mocks (`vi.mock`, `vi.fn`) | |
| Coverage | `vitest --coverage` (v8 provider) | Minimum 80% line coverage on business logic. |

### 3.3 React Native (Mobile Client)

| Purpose | Framework / Tool | Notes |
|:--------|:----------------|:------|
| Unit tests (logic) | Jest | Test Zustand stores, utility functions, scoring preview logic. |
| Component tests | Jest + React Native Testing Library | Render components, simulate interactions, assert output. |
| Snapshot tests | Jest snapshots | Detect unintended UI changes. Update snapshots intentionally. |
| E2E tests (device) | Detox | Full app testing on iOS Simulator / Android Emulator. |
| Coverage | Jest `--coverage` | Minimum 70% on business logic modules, 50% on UI components. |

### 3.4 Cross-Cutting

| Purpose | Framework / Tool | Notes |
|:--------|:----------------|:------|
| Contract compatibility | Buf breaking-change detection | CI gate: `buf breaking --against origin/main`. Prevents schema drift. |
| Load testing | k6 (Grafana) | JavaScript-based load scripts. WebSocket support. |
| Soak testing | k6 + custom bot runner | Long-duration runs with synthetic match traffic. |
| Chaos testing | AWS Fault Injection Simulator + custom scripts | Kill containers, inject latency, simulate failovers. |
| Replay verification | Custom `replay-runner` tool (Go) | Replays match action logs and verifies state hashes. |

---

## 4. Requirement Category to Test Type Mapping

### 4.1 Gameplay Core (FR-3.x, FR-4.x, FR-5.x)

| Requirement | Test Types | Test Location | Key Test Cases |
|:------------|:-----------|:-------------|:---------------|
| FR-3.1a Deck generation | Unit + Property | `game-server/engine/deck_test.go` | Correct card count, exactly 2 wilds, deterministic shuffle from seed |
| FR-3.1b Deal 9 letters | Unit | `game-server/engine/deal_test.go` | Each player gets exactly 9, cards removed from stock |
| FR-3.1c Initial discard | Unit | `game-server/engine/deal_test.go` | Exactly 1 discard revealed, not in any hand |
| FR-3.2 Dictionary validation | Unit + Integration | `game-server/lexicon/validate_test.go` | Valid words accepted, invalid rejected, banned words rejected, lexicon version lock |
| FR-3.3 Capture logic | Unit + Property + Scenario | `game-server/engine/capture_test.go` | All-letters-used check, new-letter check, valid-word check, self-capture, multi-capture |
| FR-3.4 Wildcard logic | Unit + Scenario | `game-server/engine/wildcard_test.go` | Assignment locking, mutation on capture, scoring bonus at 7+ letters |
| FR-3.5 Turn sequencing | Unit + Scenario | `game-server/engine/turn_test.go` | Legal sequences accepted, illegal sequences rejected per turn_legality_matrix.md |
| FR-4.1 Base scoring | Unit | `game-server/engine/score_test.go` | Every length 2-10+ produces correct score |
| FR-4.2 Capture bonus | Unit | `game-server/engine/score_test.go` | +2 per added letter, interaction with wild bonus |
| FR-4.3 Penalty scoring | Unit | `game-server/engine/score_test.go` | -1 per remaining letter, negative scores allowed |
| FR-4.4 Timer behavior | Unit + Integration | `game-server/engine/timer_test.go` | Expiry auto-forfeit, consecutive forfeit escalation, async deadline |
| FR-5.1 Modifier loading | Unit | `game-server/engine/modifier_test.go` | Modifier config parsed, applied to scoring |
| FR-5.2 Modifier precedence | Unit + Scenario | `game-server/engine/modifier_test.go` | Additive before multiplicative, stacking rules, penalty overrides |

**Property test invariants for gameplay core:**

| Invariant | Generator | Property |
|:----------|:----------|:---------|
| No card duplication | Random valid match sequences | Total cards in play (all hands + stock + discard + word zones) == initial deck size at all times |
| No hidden stock leak | Random turns with draws | Client-visible state never reveals stock order |
| Hand mutation legality | Random play/capture submissions | Hand after action == hand before action minus used letters plus drawn letter |
| Score determinism | Same seed + same actions | Replay produces identical scores at every step |
| State machine invariant | Random action sequences | State only transitions via defined edges in state machine spec |
| Capture completeness | Random capture attempts | Captured word always contains 100% of original letters |

### 4.2 API / Contracts (FR-1.x, FR-2.x, FR-7.x)

| Requirement | Test Types | Test Location | Key Test Cases |
|:------------|:-----------|:-------------|:---------------|
| FR-1.1 Guest auth | Contract + Integration | `meta-api/auth/guest_test.ts` | Device ID creates session, session persists, bind to SSO |
| FR-1.2 SSO auth | Integration | `meta-api/auth/sso_test.ts` | Apple/Google token exchange, account creation, duplicate handling |
| FR-1.3 Private rooms | Contract + Integration | `meta-api/rooms/room_test.ts` | Code generation, join by code, room lifecycle |
| FR-1.4 Friends list | Contract + Integration | `meta-api/social/friend_test.ts` | Add by handle, remove, recent opponents |
| FR-2.1 Player counts | Contract | `meta-api/matchmaking/capacity_test.ts` | 1v1 enforced, 2-4 casual enforced |
| FR-2.2 Live matchmaking | Integration + System | `meta-api/matchmaking/live_test.ts` | Queue entry, matching, MMR bucketing |
| FR-2.3 Async matchmaking | Integration + System | `meta-api/matchmaking/async_test.ts` | Async match creation, turn deadline |
| FR-7.1 Push notifications | Integration | `notification-worker/push_test.ts` | Turn-ready push dispatched, APNs/FCM payload format |
| FR-7.2 Match completion push | Integration | `notification-worker/completion_test.ts` | Notification sent on match end |
| Schema compatibility | Contract | `contracts/buf_test.yaml` | No breaking changes, additive-only for minor versions |
| Idempotency | Integration | `game-server/api/idempotency_test.go` | Duplicate keys return cached response, no double mutation |

### 4.3 Live Duel (System Tests)

| Scenario | Test Type | Test Location | Description |
|:---------|:----------|:-------------|:------------|
| Full match E2E | System | `tests/system/live_duel_test.go` | Two simulated clients play a complete Bo3 match through real WebSocket connections |
| Reconnect during turn | System | `tests/system/reconnect_test.go` | Client disconnects mid-turn, reconnects, state restored, timer correct |
| Timer expiry cascade | System | `tests/system/timer_test.go` | Player times out 3 times, match forfeited |
| Multi-word turn | System | `tests/system/multiword_test.go` | Player plays 2 words + 1 capture in single turn, scores correct |
| Queue to result | System | `tests/system/queue_to_result_test.go` | Enter queue -> match found -> play match -> result persisted -> MMR updated |
| Concurrent matches | System | `tests/system/concurrent_test.go` | Multiple matches running simultaneously on same server instance |

### 4.4 Async + Push (System + UAT)

| Scenario | Test Type | Test Location | Description |
|:---------|:----------|:-------------|:------------|
| Async full loop | System | `tests/system/async_loop_test.go` | Create async match -> submit turns with delays -> push sent -> deep link opens correct match |
| Async deadline expiry | System | `tests/system/async_deadline_test.go` | Turn deadline passes -> forfeit applied -> match concluded |
| Lexicon lock across days | Integration | `tests/integration/lexicon_lock_test.go` | Async match uses original lexicon version even after server lexicon update |
| Push delivery verification | Integration | `tests/integration/push_delivery_test.ts` | Verify push payload format, delivery receipt |
| UAT Scenario 4 | UAT (manual + automated) | `tests/uat/scenario_4_async.md` | Per UAT plan: async turn notification deep-link flow |

### 4.5 Ranked Ledger (Integrity + Idempotency)

| Test Case | Test Type | Test Location | Description |
|:----------|:----------|:-------------|:------------|
| Idempotent result write | Unit + Integration | `ranked-ledger-worker/write_test.ts` | Same match UUID written twice produces no duplicate |
| Concurrent result writes | Integration | `ranked-ledger-worker/concurrent_test.ts` | Two workers processing same result simultaneously — exactly one succeeds |
| Bo3 aggregation | Unit | `ranked-ledger-worker/bo3_test.ts` | Bo3 match emits exactly 1 result (not per-round) |
| MMR calculation | Unit + Property | `ranked-ledger-worker/mmr_test.ts` | MMR converges, no negative MMR, symmetric updates |
| Rematch distinct IDs | Integration | `meta-api/matchmaking/rematch_test.ts` | Rematch creates new match UUID, old match immutable |
| Season reset | Integration | `ranked-ledger-worker/season_test.ts` | Reset preserves history, adjusts visible rank |

### 4.6 Onboarding / Tutorial (UAT + Funnel Telemetry)

| Test Case | Test Type | Test Location | Description |
|:----------|:----------|:-------------|:------------|
| Tutorial step progression | E2E (Detox) | `apps/mobile/e2e/tutorial_test.ts` | Fresh install -> complete all 5 tutorial steps -> reach lobby |
| Tutorial skip | E2E (Detox) | `apps/mobile/e2e/tutorial_skip_test.ts` | Skip tutorial -> still reach lobby -> tutorial accessible from menu |
| Tutorial telemetry | Integration | `tests/integration/tutorial_telemetry_test.ts` | All tutorial events emitted with correct properties |
| Funnel analysis | Analytics validation | Dashboard + automated query | `tutorial_started` -> `tutorial_step_completed` x5 -> `tutorial_completed` conversion rate |
| UAT Scenario 1 | UAT (manual + automated) | `tests/uat/scenario_1_onboarding.md` | Per UAT plan: guest -> tutorial -> bind SSO |
| First match flow | E2E (Detox) | `apps/mobile/e2e/first_match_test.ts` | Post-tutorial -> enter casual queue -> play first match |

---

## 5. CI Pipeline Test Stages

### 5.1 Pipeline Architecture

```
PR Opened / Push to Feature Branch
    |
    v
[Stage 1: Lint + Format]  -----> FAIL: Block merge
    |
    v
[Stage 2: Unit Tests]     -----> FAIL: Block merge
    |
    v
[Stage 3: Contract Tests] -----> FAIL: Block merge
    |
    v
[Stage 4: Integration Tests] --> FAIL: Block merge (can be parallelized with Stage 2-3)
    |
    v
[Stage 5: Build Verification] -> FAIL: Block merge
    |
    v
PR Approved + Merged to main
    |
    v
[Stage 6: System Tests (nightly)] -> FAIL: P1 alert, block release
    |
    v
[Stage 7: Load/Soak (weekly)]  --> FAIL: P1 alert, block release
    |
    v
Release Candidate
    |
    v
[Stage 8: UAT (manual)]   -----> FAIL: Block release
    |
    v
[Stage 9: Release Smoke]  -----> FAIL: Rollback
```

### 5.2 Stage Details

| Stage | Trigger | Timeout | Parallelism | Tools |
|:------|:--------|:--------|:------------|:------|
| 1. Lint + Format | Every push | 3 min | Per-language parallel | `golangci-lint`, `eslint`, `prettier`, `buf lint` |
| 2. Unit Tests | Every push | 5 min | Per-package parallel | `go test ./...`, `vitest run`, `jest --ci` |
| 3. Contract Tests | Every push | 2 min | Sequential | `buf breaking`, contract snapshot tests |
| 4. Integration Tests | Every push | 10 min | Per-service parallel | `testcontainers`, real DB |
| 5. Build Verification | Every push | 5 min | Per-target parallel | Docker build (Go, Node), EAS build check (RN) |
| 6. System Tests | Nightly + pre-release | 30 min | Sequential | Docker Compose stack, Detox |
| 7. Load/Soak | Weekly + pre-release | 2 hours | Dedicated env | k6, bot runner |
| 8. UAT | Pre-release | Manual | Manual | Per UAT plan |
| 9. Release Smoke | Post-deploy | 5 min | Sequential | Health checks, synthetic match |

### 5.3 Coverage Gates

| Service | Minimum Line Coverage | Gate Stage |
|:--------|:---------------------:|:----------:|
| `game-server` (gameplay core packages) | 85% | Stage 2 |
| `game-server` (other packages) | 70% | Stage 2 |
| `meta-api` (business logic) | 80% | Stage 2 |
| `meta-api` (route handlers) | 60% | Stage 2 |
| `mobile` (Zustand stores, utils) | 70% | Stage 2 |
| `mobile` (UI components) | 50% | Advisory (not blocking) |
| `workers` | 75% | Stage 2 |

---

## 6. Property Test Strategy

### 6.1 What Invariants to Test

| Domain | Invariant | Formulation |
|:-------|:----------|:------------|
| Deck | Conservation of cards | `forall actions: sum(all_cards_in_play) == DECK_SIZE` |
| Hand | No phantom letters | `forall plays: letters_used ⊆ hand_before_play` |
| Score | Determinism | `forall (seed, actions): replay(seed, actions).scores == original(seed, actions).scores` |
| Score | Non-negative base | `forall words: base_score(word) >= 2` |
| State hash | Collision resistance | `forall (state_a, state_b): state_a != state_b => hash(state_a) != hash(state_b)` (probabilistic) |
| Turn | Phase ordering | `forall turns: draw_index < play_indices < end_index` |
| Capture | Letter superset | `forall captures: original_letters ⊂ new_word_letters` |
| Capture | New letter requirement | `forall captures: len(new_word) > len(original_word)` |
| Modifier | No base table mutation | `forall modifiers: base_score_table == CANONICAL_TABLE` |
| Timer | Monotonic decrease | `forall timer_updates: remaining[t+1] <= remaining[t]` |
| Ranked | Idempotency | `forall results: write(result); write(result) => exactly_one_row_in_ledger` |

### 6.2 What Generators to Build

| Generator | Produces | Used By |
|:----------|:---------|:--------|
| `GenDeck` | Valid shuffled deck with correct composition | Deck tests, match simulation |
| `GenHand` | Valid 9-letter hand drawn from a deck | Play tests, scoring tests |
| `GenWord` | Valid dictionary word from available letters | Play legality tests |
| `GenCapture` | Valid capture (original word + new letters + valid result) | Capture tests |
| `GenTurn` | Complete valid turn (draw + 0..N plays/captures + end) | Turn sequence tests, state machine tests |
| `GenMatchSequence` | Complete sequence of valid turns forming a partial or full match | Replay tests, state hash tests, scoring tests |
| `GenModifier` | Valid modifier configuration | Modifier precedence tests |
| `GenIllegalAction` | Intentionally invalid action (wrong phase, bad letters, invalid word) | Rejection tests |

### 6.3 Shrinking Strategy

All property test generators must support shrinking. When a failing case is found:
- Shrink toward the minimal reproduction: fewest turns, shortest words, simplest state.
- Log the shrunk case as a regression fixture (automatically added to golden fixtures if confirmed bug).

---

## 7. Golden Fixture Format and Management

### 7.1 Purpose

Golden fixtures are pre-computed, version-controlled test cases that represent known-correct match states. They serve as regression anchors — if the engine produces different results for a golden fixture, something has changed (intentionally or not).

### 7.2 Fixture File Format

Each fixture is a JSON file:

```json
{
    "fixture_id": "golden_001_basic_play",
    "fixture_version": "1.0.0",
    "description": "Basic 3-turn match: play, capture, round end",
    "match_seed": "base64-encoded-32-bytes",
    "deck_composition_version": "deck_v_1.0.0",
    "lexicon_version": "lexicon_v_1.0.4",
    "modifier_config": null,
    "players": ["player-a-uuid", "player-b-uuid"],
    "actions": [
        {
            "sequence_id": 1,
            "action_type": "MATCH_CREATED",
            "payload": { ... },
            "expected_state_hash": "sha256-hex"
        },
        {
            "sequence_id": 2,
            "action_type": "ROUND_STARTED",
            "payload": { ... },
            "expected_state_hash": "sha256-hex"
        },
        ...
    ],
    "expected_final_scores": { "player-a-uuid": 22, "player-b-uuid": 14 },
    "expected_winner": "player-a-uuid"
}
```

### 7.3 Fixture Categories

| Category | Count (Target) | Purpose |
|:---------|:--------------:|:--------|
| Basic plays | 10+ | Simple word plays, single-word turns |
| Captures | 10+ | TOP->STOP, wildcard captures, self-captures |
| Multi-word turns | 5+ | Multiple plays and captures in one turn |
| Timer expiry | 5+ | Auto-forfeit, consecutive forfeit, async deadline |
| Modifier scenarios | 5+ per modifier | Long Form, Sharp Steal, Vowel Pressure, etc. |
| Edge cases | 10+ | Stock exhaustion, hand-empty completion, negative scores, tiebreakers |
| Full Bo3 matches | 5+ | Complete match lifecycle including round transitions |
| Wildcard scenarios | 5+ | Wild assignment, 7+ bonus, capture with wild |
| Replay verification | 5+ | Fixtures specifically designed for replay determinism testing |

### 7.4 Fixture Management

- Fixtures live in `packages/game-fixtures/golden/`.
- Each fixture file is version-controlled in Git.
- A fixture update requires review from a Gameplay Tech Lead.
- When the scoring algorithm or state hash algorithm changes, affected fixtures must be regenerated and reviewed.
- A CI job validates all golden fixtures on every push (Stage 2).

### 7.5 Fixture Generation Tool

A CLI tool `fixture-gen` produces golden fixtures:

```bash
# Generate a fixture from a scripted match
fixture-gen --script scripts/basic_play.yaml --output golden/golden_001_basic_play.json

# Generate a fixture from a production match replay
fixture-gen --replay-match-uuid abc123 --output golden/production_replay_001.json

# Verify all golden fixtures against current engine
fixture-gen --verify-all golden/
```

---

## 8. Synthetic Match Runner Design

### 8.1 Purpose

The synthetic match runner is an automated tool that generates and plays thousands of matches against the real game server. It serves as:
- A soak test harness (long-duration stability).
- A load test traffic generator.
- A state-divergence detector (compare runner-computed hashes vs server hashes).
- A balance telemetry source (generate data for game designer analysis).

### 8.2 Architecture

```
┌──────────────────┐     WebSocket      ┌──────────────┐
│  Synthetic Bot    │ ◄──────────────► │  Game Server  │
│  (Go process)     │                    │  (staging)    │
│                   │                    │               │
│  - Play strategy  │     REST           │               │
│  - State tracking │ ◄──────────────► │  Meta API     │
│  - Hash verify    │                    │  (staging)    │
│  - Telemetry emit │                    │               │
└──────────────────┘                    └──────────────┘
         │
         ▼
┌──────────────────┐
│  Results DB       │
│  (metrics, hashes,│
│   anomalies)      │
└──────────────────┘
```

### 8.3 Bot Play Strategies

| Strategy | Description | Purpose |
|:---------|:------------|:--------|
| `random_legal` | Plays a random legal move each turn. Captures randomly. | Baseline stress testing, state machine coverage. |
| `greedy_score` | Plays the highest-scoring legal move available. | Score engine stress testing, balance analysis. |
| `capture_heavy` | Prioritizes captures over new plays. | Capture logic stress testing, lineage chain testing. |
| `pass_heavy` | Frequently passes (draw + discard only). | Timer and pass-turn logic, stalling detection testing. |
| `multi_word` | Attempts to play multiple words per turn when possible. | Multi-word turn validation, complex scoring. |
| `timeout_mix` | Intentionally times out some percentage of turns. | Timer expiry logic, forfeit escalation, reconnect. |

### 8.4 Runner Configuration

```yaml
synthetic_runner:
  target_environment: "staging"
  concurrent_matches: 50
  match_duration_target: "normal"  # or "fast" (low timers) or "slow" (high timers)
  bot_strategy_distribution:
    random_legal: 30%
    greedy_score: 30%
    capture_heavy: 20%
    multi_word: 10%
    pass_heavy: 5%
    timeout_mix: 5%
  hash_verification: true
  telemetry_emission: true
  anomaly_threshold:
    state_hash_mismatch: 0     # zero tolerance
    server_5xx_rate: 0.1%
    turn_rejection_rate: 5%    # expected for random_legal strategy
  duration: "4h"
  report_output: "results/soak_$(date).json"
```

### 8.5 Runner Output

After each run, the runner produces:
- **Summary report:** Total matches, win/loss distribution, average duration, error rates.
- **Anomaly report:** Any state hash mismatches, unexpected rejections, server errors.
- **Performance report:** Turn latency percentiles (p50, p95, p99), WebSocket reconnect count.
- **Balance report:** Score distributions, capture rates, modifier impact, word length distributions.

### 8.6 Runner Integration

| Integration Point | Trigger | Action on Failure |
|:-------------------|:--------|:------------------|
| CI nightly (Stage 6) | Automated | 20-match smoke run. Any hash mismatch = P1. |
| Weekly soak (Stage 7) | Automated | 4-hour run, 50 concurrent. Anomaly report reviewed by QA. |
| Pre-release gate | Manual trigger | Full soak run. Must pass zero-anomaly before release. |
| Post-deploy verification | Automated | 5-match smoke run against production. |

---

## 9. V-Model Test Alignment

| V-Model Left Side | V-Model Right Side | Test Type | WIT V2 Coverage |
|:-------------------|:-------------------|:----------|:----------------|
| Business Vision / GDD | Production Telemetry | Analytics validation | Funnel dashboards, KPI monitoring |
| SRS / NFRs | UAT | Acceptance tests | 7 UAT scenarios (Phase 5 execution) |
| System Architecture | System Tests | E2E tests | Live duel, async loop, reconnect, ranked pipeline |
| Low-Level Design | Integration Tests | Component interaction | API ↔ DB, game-server ↔ Postgres, workers ↔ queues |
| Implementation | Unit + Property Tests | Function-level verification | Scoring, capture, deck, timer, state machine |

---

## 10. Test Data Management

### 10.1 Test Database Strategy

| Environment | Database | Reset Policy |
|:------------|:---------|:-------------|
| Unit tests | In-memory mocks or SQLite | Per-test |
| Integration tests | Testcontainers Postgres | Per-test-suite (truncate between tests) |
| System tests | Staging Postgres | Reset before each test run (schema migrations applied fresh) |
| Load/soak tests | Staging Postgres | Cleaned after run. Metrics retained. |

### 10.2 Test User Accounts

| Account Type | Purpose | Creation |
|:-------------|:--------|:---------|
| `test-player-a` through `test-player-z` | Deterministic test accounts for system tests | Seeded by test setup script |
| `bot-soak-N` (N=1..100) | Synthetic runner accounts | Created by runner on first use |
| `admin-test` | Admin CMS testing | Seeded with elevated permissions |

### 10.3 Lexicon Test Data

| Dataset | Purpose | Management |
|:--------|:--------|:-----------|
| `lexicon_test_v1` | Minimal dictionary (1000 words) for fast unit tests | Version-controlled in `packages/game-fixtures/lexicons/` |
| `lexicon_full_v1` | Full production dictionary for integration/system tests | Stored in artifact registry, version-tagged |
| `lexicon_banned_test` | Test banned-word overlay (50 entries) | Version-controlled |

---

## 11. Traceability to RTM

Every test case ID referenced in the RTM (`requirements_traceability_matrix.md`) maps to a concrete test implementation:

| RTM Test Case | Test Level | Implementation Path |
|:-------------|:-----------|:-------------------|
| `auth_guest_flow` | Integration | `meta-api/auth/guest_test.ts` |
| `auth_bind_sso` | Integration | `meta-api/auth/sso_test.ts` |
| `auth_sso_verify` | Integration | `meta-api/auth/sso_test.ts` |
| `room_code_gen_test` | Unit + Integration | `meta-api/rooms/room_test.ts` |
| `friend_graph_sync` | Integration | `meta-api/social/friend_test.ts` |
| `player_capacity_limits` | Contract | `meta-api/matchmaking/capacity_test.ts` |
| `mmr_bucket_routing` | Integration | `meta-api/matchmaking/live_test.ts` |
| `async_queue_routing` | Integration | `meta-api/matchmaking/async_test.ts` |
| `bot_instantiation_test` | Unit | `game-server/bot/bot_test.go` |
| `deck_seed_composition` | Unit + Property | `game-server/engine/deck_test.go` |
| `initial_hand_alloc` | Unit | `game-server/engine/deal_test.go` |
| `initial_discard_alloc` | Unit | `game-server/engine/deal_test.go` |
| `lexicon_validation_layer` | Unit + Integration | `game-server/lexicon/validate_test.go` |
| `capture_morph_eval` | Unit + Property + Scenario | `game-server/engine/capture_test.go` |
| `wildcard_mutation_lock` | Unit + Scenario | `game-server/engine/wildcard_test.go` |
| `turn_sequence_sm` | Unit + Scenario | `game-server/engine/turn_test.go` |
| `score_math_base` | Unit | `game-server/engine/score_test.go` |
| `score_math_capture` | Unit | `game-server/engine/score_test.go` |
| `score_penalty_eval` | Unit | `game-server/engine/score_test.go` |
| `timer_expiry_eval` | Unit + Integration | `game-server/engine/timer_test.go` |
| `mod_application` | Unit | `game-server/engine/modifier_test.go` |
| `mod_stacking_logic` | Unit + Scenario | `game-server/engine/modifier_test.go` |
| `lineage_playback` | Unit + Integration | `game-server/engine/lineage_test.go` |
| `ownership_swap` | Unit | `game-server/engine/capture_test.go` |
| `push_dispatch` | Integration | `notification-worker/push_test.ts` |
| `admin_lex_upload` | Integration | `admin-web/lexicon_test.ts` |
| `admin_block_update` | Integration | `admin-web/blocklist_test.ts` |
| `ledger_idempotency` | Unit + Integration | `ranked-ledger-worker/write_test.ts` |
| `rematch_generation` | Integration | `meta-api/matchmaking/rematch_test.ts` |
| `bo3_aggregate` | Unit | `ranked-ledger-worker/bo3_test.ts` |
| `load_latency_test` | Load | `tools/load-test/latency.k6.js` |
| `client_ack_test` | System | `tests/system/client_ack_test.go` |
| `reconnect_time_test` | System | `tests/system/reconnect_test.go` |
| `push_delivery_rate` | Integration + Load | `tests/integration/push_rate_test.ts` |
| `deep_link_eval` | E2E (Detox) | `apps/mobile/e2e/deep_link_test.ts` |
| `state_hash_eval` | Unit + System | `game-server/engine/hash_test.go` + `tests/system/hash_verify_test.go` |
| `timer_network_drop` | System | `tests/system/reconnect_test.go` |
| `resume_sync_playback` | System | `tests/system/resume_test.go` |
| `schema_blindness` | Unit + Contract | `contracts/blindness_test.ts` |
| `idempotency_eval` | Integration | `game-server/api/idempotency_test.go` |

---

## 12. Traceability

| Section | Requirement |
|:--------|:------------|
| 4.1     | FR-3.x, FR-4.x, FR-5.x |
| 4.2     | FR-1.x, FR-2.x, FR-7.x |
| 4.3     | NFR-1.x, NFR-2.x |
| 4.4     | FR-7.1, NFR-1.4 |
| 4.5     | FR-9.x |
| 4.6     | GDD 16, FR-1.1 |
| 5       | All (CI quality gate) |
| 7       | FR-6.1, NFR-1.6 |
| 8       | NFR-1.6, NFR-2.2 |
