# API / Event Contract Spec
**Project:** WIT V2

## Canonical Schema Strategy
A single GitHub repository will host our strict JSON Schema / Protobuf definitions. Both Node.js and Golang environments will generate their types from this repository to preclude polyglot drift.

## Contract Governance Rules
**1. Schema Versioning Policy**
- Schemas strictly employ semantic versioning (Major.Minor.Patch).
- No fields may be removed or renamed without a Major version bump.
- The Git repository enforces required review from a Lead Backend Architect on all PRs.

**2. Backward Compatibility**
- Minor/Patch updates MUST be strictly additive. Clients parsing an older schema must not crash when encountering unknown additive fields. 

**3. Event Ordering Guarantees**
- All WebSocket events broadcasted by the server include a strictly monotonically increasing `sequence_id` scoped to the Match UUID.
- Clients MUST buffer and reorder packets arriving out of sequence.

**4. Timestamp Standards**
- All protocol timestamps MUST be emitted as integer UNIX Epoch values in milliseconds natively. 

**5. Idempotency Semantics & Deduplication**
- Mutative Client payload submissions (`PLAY`, `CAPTURE`, `DISCARD`) MUST include a client-generated UUIDv4 `idempotency_key`.
- The Server caches the key for 60 seconds against the specific Match UUID. If a duplicate key arrives, the Server returns the exact previous synthetic response without mutating state.

**6. Auth & Signature Requirements**
- WebSocket handshakes MUST include a short-lived bearer JWT acquired via the Meta REST API. 
- Reconnect handshakes MUST pass the match-specific session token to resume cleanly.

**7. Retry Semantics**
- Meta-events (e.g., Match Completion emitting to the ranking ledger) MUST utilize exponential backoff (e.g., 500ms, 1s, 2s, 4s, 8s) if the database is unreachable, leveraging a durable Dead Letter Queue (DLQ) after 5 fails.

## Primary Contract Payloads

### 1. `ws_action_turn_submit` (Client -> Server)
- **IDEMPOTENCY_KEY:** uuid
- **MOVES:** Array of operations: `PLAY`, `CAPTURE`, `DISCARD`.

### 2. `ws_event_turn_committed` (Server -> Client)
- **SEQUENCE_ID:** integer
- **SCORE_DELTAS:** Array of point allocations.
- **BOARD_PATCH:** Operations mutating UI.
- **LINEAGE_LOG:** Audit trace of word transformations.
