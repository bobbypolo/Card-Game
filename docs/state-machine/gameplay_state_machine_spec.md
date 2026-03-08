# Authoritative Gameplay State Machine Spec
**Project:** WIT V2

## Overview
Live match states reside on the authoritative server. Actions can only transition between explicitly defined states.

## State Transitions & Invariants

### 1. `STATE_LOBBY`
- **Incoming:** Initial queue entry.
- **Outgoing:** Wait -> `STATE_MATCH_FOUND` | Cancel -> Exit
- **Valid Actions:** Leave Queue.
- **Invariants:** User must have valid matchmaking ticket.

### 2. `STATE_MATCH_FOUND`
- **Incoming:** Queue Processor succeeds.
- **Outgoing:** `STATE_DEALING`
- **Valid Actions:** Client handshake ACK.
- **Invariants:** UUID match instantiated, both clients connected.

### 3. `STATE_DEALING`
- **Incoming:** from `STATE_MATCH_FOUND` or `STATE_ROUND_COMPLETE` (for next round).
- **Outgoing:** `STATE_ACTIVE_TURN`
- **Valid Actions:** None (Server internal execution).
- **Server Execution:** Shuffles configuration-specific deck, draws exactly 9 tiles for Active Players, sets exact 1 discard tile.

### 4. `STATE_ACTIVE_TURN`
- **Incoming:** from `STATE_DEALING` or `STATE_TURN_COMMITTED`
- **Outgoing:** `STATE_SUBMISSION_PENDING`, `STATE_RECONNECT_GRACE`, `STATE_MATCH_COMPLETE` (if timeout forfeit hits match limit).
- **Valid Actions:** `PLAY_WORD`, `CAPTURE_WORD`, `DISCARD` (only valid to end turn).
- **Invalid Actions:** Taking actions out of sequence (e.g. discarding before drawing).
- **Timeout Behavior:** Timer ticks on the server. If timer hits 0, Auto-Forfeit logic applied -> `STATE_TURN_COMMITTED`.
- **Invariants:** Only the active player may submit payloads.

### 5. `STATE_SUBMISSION_PENDING`
- **Incoming:** Upon client submission from `STATE_ACTIVE_TURN`.
- **Outgoing:** Success -> `STATE_TURN_COMMITTED` | Reject -> `STATE_ACTIVE_TURN`
- **Invariants:** 
  - ONLY ONE active submission processed at a time (locked by match ID).
  - No secondary submit accepted until promise resolution.
  - Requires strict UUID idempotency key.
- **Failure Rollback:** If Lexicon validation fails, transaction rolls back, error WS payload emitted, returns clock and state to `STATE_ACTIVE_TURN`.

### 6. `STATE_TURN_COMMITTED`
- **Incoming:** Validated success from `STATE_SUBMISSION_PENDING`.
- **Outgoing:** Board update -> `STATE_ROUND_COMPLETE` (if hand clear) OR -> `STATE_ACTIVE_TURN` (turn passes).
- **Server Execution:** Points tallied, lineage logged to Postgres, WS patch broadcasted, turn passed to opposing player ID.

### 7. `STATE_RECONNECT_GRACE` (Network Drop)
- **Incoming:** WebSocket disruption detected.
- **Outgoing:** `STATE_ACTIVE_TURN` (if reconnected) | `STATE_TURN_COMMITTED` (if timer expires -> auto-forfeit).
- **Timeout Behavior:** The active server turn timer DOES NOT FREEZE. It continues checking the expiration threshold representing the player's allotted time. 

### 8. `STATE_ROUND_COMPLETE`
- **Incoming:** `STATE_TURN_COMMITTED` invokes hand-clear or stock-exhaustion trigger.
- **Outgoing:** `STATE_DEALING` (if Bo3 next) OR `STATE_MATCH_COMPLETE`
- **Server Execution:** Process -1 hand penalties. 

### 9. `STATE_MATCH_COMPLETE`
- **Incoming:** Best-of-3 limit reached OR Match Forfeit applied.
- **Outgoing:** `STATE_RESULT_PERSISTED`
- **Server Execution:** Final tie-breakers (unused tiles -> capture count) processed.

### 10. `STATE_RESULT_PERSISTED`
- **Incoming:** `STATE_MATCH_COMPLETE`
- **Outgoing:** Terminated.
- **Invariants:** Win/Loss ELO updates written to Postgres idempotently. Match ID is sealed. Rematch requests queue entirely new `STATE_MATCH_FOUND` flows.
