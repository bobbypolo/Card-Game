# Replay Determinism Specification
**Project:** WIT V2
**Phase:** 1 (Requirements)
**Status:** Engineering Specification — Implementation Grade
**Linked Requirements:** FR-6.1, FR-6.2, NFR-1.6, NFR-2.2

---

## 1. Purpose

This document defines the exact data logged per match action, the state hash algorithm, and the replay reconstruction algorithm. These together guarantee that any committed match can be deterministically replayed from its action log, producing identical state at every step. This is the foundation for reconnect recovery, anti-cheat review, lineage replay, debugging, and UAT verification.

---

## 2. Determinism Invariants

### 2.1 Core Guarantee

Given the same initial conditions and the same ordered sequence of actions, the match engine MUST produce byte-identical state at every step. Formally:

```
For any match M with initial seed S and action sequence [A1, A2, ..., An]:
  Replay(S, [A1..An]) == Original(S, [A1..An])

  where equality is defined as:
    state_hash(Replay, step_i) == state_hash(Original, step_i)
    for all i in [0, n]
```

### 2.2 Sources of Non-Determinism (Banned)

The following are prohibited in the match engine:
- System clock reads for game logic (timestamps are metadata only, not inputs to game state).
- Unseeded random number generation.
- Hash-map iteration order dependency (Go maps are intentionally randomized).
- Floating-point arithmetic in scoring (all integer math).
- Concurrent state mutation without deterministic ordering.
- External service calls during state computation (dictionary lookups must be pre-resolved before state transition).

### 2.3 Permitted Sources of Controlled Randomness

The following use a seeded CSPRNG (Cryptographically Secure Pseudo-Random Number Generator) initialized from the match seed:

- Deck shuffle at round start.
- Timer-expiry random discard selection.
- Starting player selection (first round only; subsequent rounds alternate).

The CSPRNG implementation must be identical across all server instances. The Go standard library `crypto/rand` is used for seed generation only. Game-state randomness uses a deterministic PRNG (e.g., `math/rand` seeded from the match seed) for replayability.

---

## 3. Action Log Schema

Every committed action in a match is persisted as a row in the `match_actions` table.

### 3.1 Action Record Fields

| Field | Type | Description |
|:------|:-----|:------------|
| `action_id` | UUID v4 | Unique identifier for this action record. |
| `match_uuid` | UUID v4 | The match this action belongs to. |
| `round_number` | uint8 | 1-indexed round within the match (1, 2, or 3 for Bo3). |
| `sequence_id` | uint32 | Strictly monotonically increasing integer, scoped per `match_uuid`. Starts at 1. No gaps. |
| `action_type` | enum | One of the defined action types (Section 3.2). |
| `action_payload` | JSONB | Type-specific payload (Section 3.3). |
| `actor_player_id` | UUID v4 | The player who performed the action, or `SYSTEM` for server-initiated actions. |
| `resolved_state_hash` | bytes(32) | SHA-256 hash of the canonical state after this action is applied (Section 4). |
| `score_delta` | JSONB | Per-player score changes caused by this action. `{"player_a_uuid": +9, "player_b_uuid": 0}` |
| `cumulative_scores` | JSONB | Per-player cumulative scores after this action. |
| `lineage_delta` | JSONB | Word ownership changes caused by this action (Section 3.4). |
| `timer_state_snapshot` | JSONB | Timer state after this action (Section 3.5). |
| `lexicon_version` | string | Lexicon version locked to this match (e.g., `lexicon_v_1.0.4`). Constant across all actions in a match. |
| `modifier_version` | string | Active Rule Modifier config ID for the current round, or `null` if none. |
| `deck_composition_version` | string | Deck composition config ID locked at match creation (e.g., `deck_v_1.0.0`). |
| `match_seed` | bytes(32) | PRNG seed for the match. Constant across all actions. Stored on the first action only; subsequent actions reference the match record. |
| `server_timestamp_ms` | int64 | Server UTC timestamp in milliseconds when this action was committed. Metadata only — not used in state computation. |
| `idempotency_key` | UUID v4 | The client-provided idempotency key for player-initiated actions. `null` for system actions. |

### 3.2 Action Type Enum

```protobuf
enum ActionType {
    MATCH_CREATED        = 0;   // Match instantiated, seed generated
    ROUND_STARTED        = 1;   // Deck shuffled, hands dealt, initial discard placed
    TURN_STARTED         = 2;   // Active player designated, timer started
    DRAW_STOCK           = 3;   // Player drew from stock
    DRAW_DISCARD         = 4;   // Player drew top of discard pile
    PLAY_WORD            = 5;   // Player played a new word from hand
    CAPTURE_WORD         = 6;   // Player captured and transformed an existing word
    DISCARD              = 7;   // Player discarded a letter to end turn
    MANUAL_COMPLETE      = 8;   // Player ended turn with empty hand (no discard)
    TIMER_EXPIRY_FORFEIT = 9;   // Server auto-forfeited a turn due to timer
    ROUND_ENDED          = 10;  // Round complete, penalties applied
    MATCH_FORFEIT        = 11;  // Player forfeited (disconnect/timeout escalation)
    MATCH_COMPLETED      = 12;  // Final result, tiebreakers resolved
    RECONNECT_RESTORE    = 13;  // Player reconnected, state snapshot sent
    MODIFIER_APPLIED     = 14;  // Round modifier activated (informational)
}
```

### 3.3 Action Payloads (Per Type)

#### MATCH_CREATED
```json
{
    "match_seed": "base64-encoded-32-bytes",
    "deck_composition_version": "deck_v_1.0.0",
    "lexicon_version": "lexicon_v_1.0.4",
    "player_ids": ["uuid-a", "uuid-b"],
    "match_format": "BEST_OF_3",
    "playlist": "ARENA",
    "initial_timer_seconds": 45
}
```

#### ROUND_STARTED
```json
{
    "round_number": 1,
    "deck_order": ["letter_id_1", "letter_id_2", "..."],
    "hands": {
        "uuid-a": ["letter_id_10", "letter_id_22", "..."],
        "uuid-b": ["letter_id_5", "letter_id_33", "..."]
    },
    "initial_discard": "letter_id_99",
    "starting_player_id": "uuid-a",
    "modifier_id": "long_form_v1" | null
}
```

**Note:** `deck_order` is the full shuffled deck. This is logged for replay reconstruction but is **never** sent to clients.

#### TURN_STARTED
```json
{
    "active_player_id": "uuid-a",
    "turn_number": 3,
    "timer_deadline_ms": 1709901234567
}
```

#### DRAW_STOCK
```json
{
    "drawn_letter_id": "letter_id_42",
    "drawn_letter_value": "T",
    "stock_remaining_count": 28
}
```

#### DRAW_DISCARD
```json
{
    "drawn_letter_id": "letter_id_99",
    "drawn_letter_value": "E",
    "new_discard_top": "letter_id_88" | null
}
```

#### PLAY_WORD
```json
{
    "word_id": "uuid-new-word",
    "word_text": "STOP",
    "letter_ids": ["letter_id_10", "letter_id_22", "letter_id_42", "letter_id_7"],
    "wild_assignments": [
        { "letter_id": "letter_id_7", "assigned_as": "P", "is_wild": true }
    ],
    "word_score": 7,
    "wild_card_bonus": 0,
    "modifier_bonus": 0,
    "total_score": 7
}
```

#### CAPTURE_WORD
```json
{
    "captured_word_id": "uuid-original-word",
    "captured_word_text": "TOP",
    "new_word_id": "uuid-new-word",
    "new_word_text": "STOP",
    "letters_from_hand": ["letter_id_10"],
    "all_letter_ids": ["letter_id_22", "letter_id_42", "letter_id_7", "letter_id_10"],
    "wild_assignments": [],
    "original_owner_id": "uuid-b",
    "new_owner_id": "uuid-a",
    "base_score": 7,
    "wild_card_bonus": 0,
    "capture_bonus": 2,
    "modifier_bonus": 0,
    "total_score": 9
}
```

#### DISCARD
```json
{
    "discarded_letter_id": "letter_id_55",
    "discarded_letter_value": "Q",
    "hand_remaining_count": 6
}
```

#### MANUAL_COMPLETE
```json
{
    "hand_remaining_count": 0
}
```

#### TIMER_EXPIRY_FORFEIT
```json
{
    "forfeited_player_id": "uuid-a",
    "auto_drawn_letter_id": "letter_id_60" | null,
    "auto_discarded_letter_id": "letter_id_33",
    "consecutive_forfeit_count": 2,
    "phase_at_expiry": "DRAW" | "PLAY" | "END_TURN"
}
```

#### ROUND_ENDED
```json
{
    "round_number": 1,
    "trigger": "HAND_EMPTY" | "STOCK_EXHAUSTED" | "FORFEIT",
    "penalties": {
        "uuid-a": { "remaining_letters": 0, "penalty": 0 },
        "uuid-b": { "remaining_letters": 3, "penalty": -3 }
    },
    "round_scores": {
        "uuid-a": 22,
        "uuid-b": 14
    },
    "round_winner": "uuid-a" | null
}
```

#### MATCH_FORFEIT
```json
{
    "forfeited_player_id": "uuid-a",
    "reason": "CONSECUTIVE_TIMEOUT" | "ASYNC_DEADLINE" | "VOLUNTARY_SURRENDER",
    "winning_player_id": "uuid-b"
}
```

#### MATCH_COMPLETED
```json
{
    "round_results": [
        { "round": 1, "winner": "uuid-a", "scores": { "uuid-a": 22, "uuid-b": 14 } },
        { "round": 2, "winner": "uuid-b", "scores": { "uuid-a": 10, "uuid-b": 18 } },
        { "round": 3, "winner": "uuid-a", "scores": { "uuid-a": 15, "uuid-b": 12 } }
    ],
    "match_winner": "uuid-a",
    "tiebreaker_used": null | "UNPLAYED_LETTERS" | "CAPTURE_COUNT" | "SUDDEN_DEATH",
    "final_match_scores": { "uuid-a": 47, "uuid-b": 44 }
}
```

#### RECONNECT_RESTORE
```json
{
    "reconnected_player_id": "uuid-a",
    "state_snapshot_hash": "sha256-hex",
    "actions_since_disconnect": [3, 4, 5]
}
```

#### MODIFIER_APPLIED
```json
{
    "round_number": 2,
    "modifier_id": "sharp_steal_v1",
    "modifier_name": "Sharp Steal",
    "modifier_config": { "capture_per_letter_bonus": 3 }
}
```

### 3.4 Lineage Delta Format

The `lineage_delta` field tracks word ownership changes:

```json
{
    "created": [
        { "word_id": "uuid-new", "text": "STOP", "owner": "uuid-a" }
    ],
    "destroyed": [
        { "word_id": "uuid-old", "text": "TOP", "previous_owner": "uuid-b" }
    ],
    "transferred": [
        {
            "from_word_id": "uuid-old",
            "to_word_id": "uuid-new",
            "from_owner": "uuid-b",
            "to_owner": "uuid-a",
            "transformation": "TOP -> STOP"
        }
    ]
}
```

For `PLAY_WORD`, only `created` is populated. For `CAPTURE_WORD`, `destroyed` and `created` are both populated, plus a `transferred` entry recording the lineage chain.

### 3.5 Timer State Snapshot Format

```json
{
    "active_player_id": "uuid-a",
    "turn_timer_remaining_ms": 32500,
    "turn_timer_deadline_ms": 1709901267000,
    "consecutive_forfeit_count": { "uuid-a": 0, "uuid-b": 1 }
}
```

---

## 4. State Hash Algorithm

### 4.1 Purpose

After every committed action, the server computes a SHA-256 hash of the canonical game state. This hash is:
- Stored in the action log (`resolved_state_hash`).
- Sent to clients in the `ws_event_turn_committed` payload for divergence detection.
- Used during replay verification to confirm determinism.

### 4.2 Canonical State Object

The state hash is computed over a deterministically serialized canonical state object containing exactly these fields in this exact order:

```
CanonicalState {
    match_uuid:             UUID (16 bytes, big-endian)
    round_number:           uint8
    sequence_id:            uint32 (big-endian)
    active_player_index:    uint8 (0 or 1, by sorted player UUID)

    // Player states (ordered by lexicographic sort of player UUID strings)
    player_states: [
        {
            player_uuid:    UUID (16 bytes, big-endian)
            hand:           sorted array of LetterEntry
            word_zone:      sorted array of WordEntry
            round_score:    int32 (big-endian)
            match_score:    int32 (big-endian)
        }
    ]

    // Shared state
    stock_remaining:        sorted array of LetterEntry
    discard_pile:           ordered array of LetterEntry (top-first)
    turn_number:            uint16 (big-endian)
    round_phase:            uint8 (enum: DEALING=0, ACTIVE_TURN=1, ROUND_COMPLETE=2)
    match_phase:            uint8 (enum: IN_PROGRESS=0, COMPLETE=1)
    modifier_id_hash:       SHA-256 of modifier config JSON string, or 32 zero bytes if null
}
```

### 4.3 Serialization Rules

1. **UUIDs:** Serialized as 16 raw bytes in big-endian (network byte order), without dashes or formatting.
2. **Integers:** Big-endian byte encoding. int32 = 4 bytes, uint32 = 4 bytes, uint16 = 2 bytes, uint8 = 1 byte.
3. **Strings:** UTF-8 encoded, prefixed with uint16 length.
4. **Arrays:** Prefixed with uint16 element count, then each element serialized in sequence.
5. **LetterEntry:** `{ letter_id: UUID, letter_value: uint8 (ASCII code), is_wild: uint8 (0 or 1), wild_assigned_as: uint8 (ASCII code, or 0 if not assigned) }` = 19 bytes.
6. **WordEntry:** `{ word_id: UUID, word_text: length-prefixed string, letter_ids: sorted array of UUID, owner_player_uuid: UUID }`.
7. **Sorting:** All arrays of LetterEntry are sorted by `letter_id` (UUID lexicographic). All arrays of WordEntry are sorted by `word_id` (UUID lexicographic). Player states are sorted by `player_uuid` lexicographic.

### 4.4 Hash Computation

```
serialized_bytes = serialize(CanonicalState)  // per rules in 4.3
state_hash = SHA-256(serialized_bytes)         // 32 bytes
```

The hash is stored as 32 raw bytes in the database and transmitted as a 64-character lowercase hex string in JSON/WebSocket payloads.

### 4.5 Hash Verification Points

| Event | Hash Computed? | Hash Stored? | Hash Sent to Client? |
|:------|:--------------:|:------------:|:--------------------:|
| MATCH_CREATED | Yes (initial state) | Yes | No (match hasn't started for clients) |
| ROUND_STARTED | Yes | Yes | Yes (in dealing payload) |
| TURN_STARTED | No (state unchanged) | No | No |
| DRAW_STOCK | Yes | Yes | No (private to active player) |
| DRAW_DISCARD | Yes | Yes | No (private to active player) |
| PLAY_WORD | Yes | Yes | Yes (in turn committed broadcast) |
| CAPTURE_WORD | Yes | Yes | Yes (in turn committed broadcast) |
| DISCARD | Yes | Yes | Yes (in turn committed broadcast) |
| MANUAL_COMPLETE | Yes | Yes | Yes |
| TIMER_EXPIRY_FORFEIT | Yes | Yes | Yes |
| ROUND_ENDED | Yes | Yes | Yes |
| MATCH_COMPLETED | Yes (final) | Yes | Yes |

---

## 5. Replay Reconstruction Algorithm

### 5.1 Inputs

```
Input:
    match_uuid: UUID
    match_seed: bytes(32)
    deck_composition_version: string
    lexicon_version: string
    action_log: ordered list of ActionRecord (sorted by sequence_id ASC)
```

### 5.2 Algorithm (Step-by-Step)

```
1. INITIALIZE
   a. Load deck composition config for deck_composition_version.
   b. Load lexicon data for lexicon_version.
   c. Initialize PRNG with match_seed.
   d. Create empty CanonicalState with match_uuid and player_ids from
      the MATCH_CREATED action (sequence_id = 1).
   e. Compute initial state_hash. Assert it matches action_log[0].resolved_state_hash.

2. FOR EACH action in action_log (ordered by sequence_id):
   a. VALIDATE that action.sequence_id == expected_next_sequence_id.
      (expected starts at 1, increments by 1).

   b. APPLY action to state:
      - MATCH_CREATED: Set match metadata. No state change beyond initialization.
      - ROUND_STARTED:
          i.   Consume PRNG outputs to shuffle the deck.
          ii.  Deal 9 cards to each player from the shuffled deck.
          iii. Place 1 card as initial discard.
          iv.  Set starting player.
          v.   Load modifier config if specified.
      - DRAW_STOCK:
          i.   Remove top card from stock.
          ii.  Add to active player's hand.
      - DRAW_DISCARD:
          i.   Remove top card from discard pile.
          ii.  Add to active player's hand.
      - PLAY_WORD:
          i.   Remove letter_ids from active player's hand.
          ii.  Create word entry in active player's word zone.
          iii. Apply wild card assignments.
          iv.  Add score delta to player's round score.
      - CAPTURE_WORD:
          i.   Remove original word from original owner's word zone.
          ii.  Remove letters_from_hand from active player's hand.
          iii. Create new word entry in active player's word zone.
          iv.  Apply wild card assignments.
          v.   Add score delta to active player's round score.
          vi.  Update lineage chain.
      - DISCARD:
          i.   Remove letter from active player's hand.
          ii.  Push letter onto discard pile (becomes new top).
      - MANUAL_COMPLETE:
          i.   Assert active player's hand is empty.
      - TIMER_EXPIRY_FORFEIT:
          i.   Apply auto-draw if specified.
          ii.  Apply auto-discard.
          iii. Increment consecutive forfeit counter.
      - ROUND_ENDED:
          i.   Apply hand penalties per player.
          ii.  Finalize round scores.
          iii. Determine round winner.
      - MATCH_FORFEIT:
          i.   Set match winner.
          ii.  Transition to MATCH_COMPLETE.
      - MATCH_COMPLETED:
          i.   Apply tiebreakers if needed.
          ii.  Finalize match result.
      - RECONNECT_RESTORE:
          i.   No state change. Informational only.
      - MODIFIER_APPLIED:
          i.   No state change. Informational only.

   c. COMPUTE state_hash of current CanonicalState.

   d. ASSERT state_hash == action.resolved_state_hash.
      If mismatch: REPLAY DIVERGENCE DETECTED — log P1 alert with:
        - match_uuid
        - sequence_id where divergence occurred
        - expected hash (from log)
        - computed hash (from replay)
        - full state dump

3. RETURN final CanonicalState and verification result.
```

### 5.3 Replay Verification Modes

| Mode | Purpose | When Used |
|:-----|:--------|:----------|
| Full Replay | Reconstruct entire match from seed + actions. Verify every hash. | Anti-cheat review, incident investigation, UAT. |
| Partial Replay | Replay from a specific sequence_id checkpoint to the end. | Reconnect recovery (server loads last known state + replays missed actions). |
| Hash-Only Verification | Walk actions and compare hashes without full state reconstruction. | Periodic integrity audit jobs. |
| Client Replay | Walk committed actions to render the match visually. Client does not have stock/opponent-hand data — only public state transitions. | Post-match replay viewer, lineage review. |

---

## 6. PRNG Specification

### 6.1 Seed Generation

At match creation, the server generates a 32-byte seed using `crypto/rand`. This seed is stored in the `matches` table and in the first action log entry.

### 6.2 Deterministic PRNG

All game-state randomness uses a deterministic PRNG seeded from the match seed:

- **Algorithm:** ChaCha20-based stream (Go: use `golang.org/x/exp/rand` with ChaCha8 source, or a custom ChaCha20 implementation).
- **Seed derivation per round:** `round_seed = HMAC-SHA256(match_seed, "round:" || round_number_as_uint8)`.
- **Deck shuffle:** Fisher-Yates shuffle using the round PRNG.
- **Timer expiry random discard:** Uses the same PRNG stream at the current consumption point.

### 6.3 PRNG Consumption Order

The PRNG must be consumed in a deterministic order. Per round:

1. Shuffle: `len(deck) - 1` random values consumed for Fisher-Yates.
2. Starting player (round 1 only): 1 random value consumed.
3. Timer expiry discards: 1 random value per occurrence, consumed in sequence_id order.

No other game logic may consume PRNG values. If future features require randomness, they must be appended to this consumption order with a version bump to `deck_composition_version`.

---

## 7. Data Retention and Integrity

### 7.1 Retention Policy

| Data | Retention |
|:-----|:----------|
| `match_actions` table | Indefinite for ranked matches. 90 days for casual/practice. |
| Match seed | Retained as long as actions are retained. |
| State hashes | Retained as long as actions are retained. |
| Full deck order (in ROUND_STARTED payload) | Retained but access-restricted (admin/anti-cheat only). |

### 7.2 Integrity Constraints

- `sequence_id` has a UNIQUE constraint scoped to `match_uuid`.
- `idempotency_key` has a UNIQUE constraint scoped to `match_uuid` within a 60-second TTL window.
- `resolved_state_hash` is indexed for integrity audit queries.
- Action records are append-only. No updates or deletes are permitted on the `match_actions` table outside of retention-policy cleanup jobs.

### 7.3 Backup and Recovery

The `match_actions` table is included in point-in-time RDS backups. In a disaster recovery scenario, replaying the action log from backup must produce valid state hashes, confirming data integrity.

---

## 8. Client-Side Divergence Detection

### 8.1 Client Hash Computation

The client maintains a local state model updated from server broadcasts. After each `ws_event_turn_committed`, the client:

1. Applies the board patch to its local state.
2. Computes a state hash using the same algorithm (Section 4) but over the **client-visible subset** of state (excludes stock order and opponent hand contents).
3. Compares with the `client_visible_state_hash` field in the server broadcast.

### 8.2 Divergence Handling

If the client detects a hash mismatch:

1. Client emits a `state_divergence_detected` telemetry event.
2. Client requests a full state resync from the server.
3. Server sends a `RECONNECT_RESTORE` payload with the authoritative state.
4. Client replaces its local state entirely.

Under NFR-1.6, the divergence rate must be 0% for committed moves. Any divergence triggers a P1 investigation.

---

## 9. Traceability

| Section | Requirement |
|:--------|:------------|
| 2       | NFR-1.6     |
| 3       | FR-6.1      |
| 3.4     | FR-6.2      |
| 4       | NFR-1.6, NFR-2.2 |
| 5       | FR-6.1      |
| 6       | FR-3.1a     |
| 8       | NFR-1.6     |
