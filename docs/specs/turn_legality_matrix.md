# Turn Legality Matrix
**Project:** WIT V2
**Phase:** 1 (Requirements)
**Status:** Engineering Specification — Implementation Grade
**Linked Requirements:** FR-3.3, FR-3.4, FR-3.5, FR-4.4

---

## 1. Purpose

This document enumerates every legal and illegal action combination within a single turn. The server's play-legality engine must accept exactly the combinations marked Legal and reject all others. There are no implicit allowances — if a combination is not listed as Legal, it is Illegal.

---

## 2. Turn Phase Model

Every turn consists of three sequential phases. Actions may only occur within their designated phase:

```
Phase A: DRAW        (exactly 1 draw action — mandatory)
Phase B: PLAY        (0 or more play/capture actions — optional)
Phase C: END_TURN    (exactly 1 end action — mandatory)
```

### Phase A: Draw
The player must draw exactly one card from one of two sources.

### Phase B: Play
The player may play zero or more words and/or capture zero or more words, in any combination and any order, subject to hand-letter availability and dictionary validity.

### Phase C: End Turn
The player must end the turn by one of:
- Discarding exactly 1 letter from hand (if hand is non-empty after Phase B).
- Manual completion (if hand is empty after Phase B — no discard needed).
- Timer expiry auto-action (server forces the end).

---

## 3. Legal Action Combinations Matrix

### 3.1 Standard Turn Combinations

| # | Draw Source | Phase B Actions | End Action | Legal? | Notes |
|:-:|:-----------|:----------------|:-----------|:------:|:------|
| 1 | Stock | Play 1 word | Discard 1 | **Legal** | Standard play-and-discard turn. |
| 2 | Stock | Play 2+ words | Discard 1 | **Legal** | Multi-word turn. All words must use letters from hand. |
| 3 | Stock | Capture 1 word | Discard 1 | **Legal** | Standard capture turn. |
| 4 | Stock | Capture 2+ words | Discard 1 | **Legal** | Multi-capture in single turn. Each capture must independently satisfy capture rules. |
| 5 | Stock | Play 1+ words AND Capture 1+ words | Discard 1 | **Legal** | Mixed play+capture turn. Order within Phase B is unrestricted. |
| 6 | Stock | No plays, no captures | Discard 1 | **Legal** | Legal pass. Player draws 1, discards 1. Net hand change: swap 1 card. |
| 7 | Stock | Play all remaining letters (hand empty) | Manual complete | **Legal** | Player empties hand through plays. No discard needed. |
| 8 | Stock | Capture using all remaining hand letters (hand empty) | Manual complete | **Legal** | Player empties hand through capture(s). No discard needed. |
| 9 | Stock | Play + Capture using all remaining letters (hand empty) | Manual complete | **Legal** | Mixed actions empty the hand. No discard needed. |
| 10 | Discard pile (top card) | Play 1 word | Discard 1 | **Legal** | Draw from discard, play, discard different card. |
| 11 | Discard pile (top card) | Play 2+ words | Discard 1 | **Legal** | Multi-word after discard draw. |
| 12 | Discard pile (top card) | Capture 1 word | Discard 1 | **Legal** | Capture after discard draw. |
| 13 | Discard pile (top card) | Capture 2+ words | Discard 1 | **Legal** | Multi-capture after discard draw. |
| 14 | Discard pile (top card) | Play + Capture combined | Discard 1 | **Legal** | Mixed turn after discard draw. |
| 15 | Discard pile (top card) | No plays, no captures | Discard 1 | **Legal** | Legal pass from discard pile. Player swaps the picked-up card for a different one. |
| 16 | Discard pile (top card) | Play all remaining letters (hand empty) | Manual complete | **Legal** | Empty hand after discard draw. |
| 17 | Discard pile (top card) | Capture all remaining letters (hand empty) | Manual complete | **Legal** | Empty hand after discard draw. |
| 18 | Discard pile (top card) | Play + Capture all remaining letters (hand empty) | Manual complete | **Legal** | Mixed empty hand after discard draw. |

### 3.2 Timer Expiry Combinations

| # | Trigger | Server Auto-Action | Legal? | Notes |
|:-:|:--------|:-------------------|:------:|:------|
| 19 | Timer expires during Phase A (player has not drawn) | Server auto-draws 1 from stock, auto-discards 1 from hand (random selection), passes turn | **Legal (forced)** | Auto-forfeit turn. No plays. |
| 20 | Timer expires during Phase B (player drew but has not ended) | Server auto-discards 1 from hand (random selection), passes turn. Any uncommitted Phase B plays are discarded. | **Legal (forced)** | Partial turn forfeited. Only committed sub-actions (if atomic commit model allows partial) are retained — see Section 5. |
| 21 | Timer expires during Phase C (player has not discarded) | Server auto-discards 1 from hand (random selection), passes turn | **Legal (forced)** | Player delayed on discard selection. |
| 22 | 3 consecutive timer-expiry forfeits (Live Ranked/Casual) | Match Forfeit for the stalling player | **Legal (forced)** | FR-4.4: automatic match forfeit after 3 consecutive timeouts. |
| 23 | Timer expires in Async mode (e.g., 24h window) | Match Forfeit for expired player | **Legal (forced)** | FR-4.4: async timeout = immediate match forfeit. |

### 3.3 Stock Exhaustion Edge Cases

| # | Condition | Draw Source | Phase B | End Action | Legal? | Notes |
|:-:|:----------|:-----------|:--------|:-----------|:------:|:------|
| 24 | Stock is empty, discard pile has 1+ cards | Discard pile | Normal play rules | Discard 1 or complete | **Legal** | Player must draw from discard if stock is empty. |
| 25 | Stock is empty AND discard pile is empty | N/A | N/A | N/A | **N/A** | Round ends immediately. See Section 4.3. |

---

## 4. Illegal Action Sequences

### 4.1 Structural Illegalities

| # | Attempted Sequence | Violation | Server Response |
|:-:|:-------------------|:----------|:----------------|
| I1 | Play word before drawing | Phase B action before Phase A | REJECT: `ERR_DRAW_REQUIRED` |
| I2 | Capture before drawing | Phase B action before Phase A | REJECT: `ERR_DRAW_REQUIRED` |
| I3 | Discard before drawing | Phase C action before Phase A | REJECT: `ERR_DRAW_REQUIRED` |
| I4 | Draw twice in one turn (stock + stock) | Double draw | REJECT: `ERR_ALREADY_DRAWN` |
| I5 | Draw twice in one turn (stock + discard) | Double draw | REJECT: `ERR_ALREADY_DRAWN` |
| I6 | Draw twice in one turn (discard + stock) | Double draw | REJECT: `ERR_ALREADY_DRAWN` |
| I7 | Discard twice in one turn | Double end-turn | REJECT: `ERR_TURN_ALREADY_ENDED` |
| I8 | Play after discarding | Phase B action after Phase C | REJECT: `ERR_TURN_ALREADY_ENDED` |
| I9 | Capture after discarding | Phase B action after Phase C | REJECT: `ERR_TURN_ALREADY_ENDED` |
| I10 | Non-active player submits action | Wrong player | REJECT: `ERR_NOT_YOUR_TURN` |
| I11 | Submit action in non-ACTIVE_TURN state | Invalid state | REJECT: `ERR_INVALID_MATCH_STATE` |
| I12 | Manual complete with non-empty hand | Hand not empty | REJECT: `ERR_HAND_NOT_EMPTY` |
| I13 | Discard with empty hand | No card to discard | REJECT: `ERR_HAND_EMPTY` (turn ends via manual complete) |
| I14 | Draw from empty stock when discard available | Wrong draw source | REJECT: `ERR_STOCK_EMPTY_USE_DISCARD` |

### 4.2 Play/Capture Content Illegalities

| # | Attempted Action | Violation | Server Response |
|:-:|:-----------------|:----------|:----------------|
| I15 | Play a word not in the dictionary context | Invalid word | REJECT: `ERR_INVALID_WORD` |
| I16 | Play a word using letters not in hand | Letter not available | REJECT: `ERR_LETTER_NOT_IN_HAND` |
| I17 | Capture without using all original letters | Incomplete capture | REJECT: `ERR_CAPTURE_INCOMPLETE` |
| I18 | Capture without adding any new letter | No new letter | REJECT: `ERR_CAPTURE_NO_NEW_LETTER` |
| I19 | Capture forming invalid dictionary word | Invalid result | REJECT: `ERR_INVALID_WORD` |
| I20 | Play 1-letter word | Below minimum | REJECT: `ERR_WORD_TOO_SHORT` |
| I21 | Play a word on the banned-word overlay | Offensive content | REJECT: `ERR_WORD_BANNED` |
| I22 | Capture violating root/morphology policy (ranked) | Policy violation | REJECT: `ERR_CAPTURE_POLICY_VIOLATION` |
| I23 | Use same hand letter in two different words within one turn | Double-spend | REJECT: `ERR_LETTER_ALREADY_USED` |
| I24 | Assign wild card as non-letter character | Invalid assignment | REJECT: `ERR_INVALID_WILD_ASSIGNMENT` |

### 4.3 Edge Case: Stock and Discard Both Exhausted

When both stock and discard pile are empty at the start of a player's draw phase:
- The round ends immediately **before** the player's turn.
- No draw, no play, no discard occurs.
- End-of-round penalties are applied to all players.
- This is not an error — it is a terminal game condition.

---

## 5. Atomic Turn Submission Model

The server processes turns as **atomic transactions**. The client batches all Phase B actions into a single `ws_action_turn_submit` payload:

```json
{
    "idempotency_key": "uuid-v4",
    "draw_source": "STOCK" | "DISCARD",
    "plays": [
        { "type": "PLAY_WORD", "word": "STOP", "letters": [...], "wild_assignments": [...] },
        { "type": "CAPTURE_WORD", "target_word_id": "uuid", "new_word": "POSTER", "letters_from_hand": [...], "wild_assignments": [...] }
    ],
    "discard": { "letter_id": "uuid" } | null
}
```

### 5.1 Validation Order

The server validates the submitted turn in this exact order:

1. **Idempotency check:** If `idempotency_key` was already processed within the 60s window, return cached response.
2. **State check:** Match must be in `STATE_ACTIVE_TURN` and submitter must be the active player.
3. **Draw validation:** `draw_source` must be legal (stock non-empty, or discard non-empty).
4. **Hand computation:** After applying the draw, compute the available hand.
5. **Play validation (per action, in order):**
   a. Check letter availability in the remaining hand pool.
   b. Check dictionary context validity.
   c. Check capture prerequisites (all original letters, at least 1 new, valid result).
   d. Check wild-card assignment validity.
   e. Deduct used letters from the hand pool.
6. **End-turn validation:** If hand is empty, `discard` must be null. If hand is non-empty, `discard` must reference a valid letter remaining in hand.
7. **Score computation:** Apply scoring per `authoritative_score_rules.md`.
8. **State hash computation:** Compute resolved state hash per `replay_determinism_spec.md`.
9. **Commit:** Write action log, update match state, broadcast event.

If any step fails, the entire turn is rejected. No partial commits.

---

## 6. Capture-of-Own-Word Rules

| Scenario | Legal? | Notes |
|:---------|:------:|:------|
| Capture own word played in a previous turn | **Legal** | Player must still add at least 1 new letter and form a valid new word. |
| Capture own word played in the current turn (same Phase B batch) | **Legal** | The word becomes a board word after its play action resolves within the batch. A subsequent capture action in the same batch may target it. |
| Capture a word that was just captured in this same turn | **Illegal** | A word may only be captured once per turn. Prevents infinite chain exploits within a single submission. |

---

## 7. Multi-Capture Constraints

| Constraint | Rule |
|:-----------|:-----|
| Maximum captures per turn | No explicit limit. Bounded by available hand letters. |
| Same word captured twice in one turn | **Illegal.** Each board word may be targeted at most once per turn submission. |
| Different words captured in same turn | **Legal.** Each capture is independently validated. |
| Capture target must exist on board at time of action | **Required.** If a capture target was itself captured earlier in the same turn batch, the second capture targeting the original form is invalid. |

---

## 8. Discard Pile Interaction Rules

| Rule | Detail |
|:-----|:-------|
| Drawing from discard | Takes the **top card only**. The discard pile is not searchable. |
| Discard immediately after drawing from discard | **Legal** (pass turn), but the player must discard a **different** card, not the one just drawn. |
| Visibility | Only the top card of the discard pile is visible to all players. Cards below are hidden (face-down). |
| Empty discard pile | If the discard pile is empty, draw from discard is unavailable. Player must draw from stock. |

**Clarification on "must discard a different card":** If a player draws the top discard card and wants to pass, they must discard a card that was already in their hand before the draw. The drawn card must remain in hand for at least one turn. This prevents a no-op cycle of drawing and immediately returning the same card.

---

## 9. Timer Expiry Auto-Action Detail

### 9.1 Live Mode (Ranked and Casual)

When the turn timer reaches 0:

1. **If Phase A incomplete (no draw yet):**
   - Server draws 1 card from stock into player's hand.
   - Server selects 1 card at random from the player's hand and discards it.
   - Turn passes. No plays or captures.

2. **If Phase A complete but Phase C incomplete (drew, but hasn't ended turn):**
   - Any pending uncommitted Phase B actions are discarded (the turn submission was never atomically committed).
   - Server selects 1 card at random from the player's hand and discards it.
   - Turn passes.

3. **Random selection algorithm:** Uniform random using the match's CSPRNG instance. The selection is deterministic given the match seed for replay purposes.

### 9.2 Consecutive Forfeit Escalation

| Consecutive Timeouts | Action |
|:--------------------:|:-------|
| 1 | Auto-forfeit turn. Warning emitted to player. |
| 2 | Auto-forfeit turn. Final warning emitted. |
| 3 | **Match Forfeit.** Match transitions to `STATE_MATCH_COMPLETE`. The timing-out player loses. |

The consecutive counter resets to 0 when the player successfully commits a voluntary turn.

### 9.3 Async Mode

There is no per-turn timer in async. Instead, the entire turn has a deadline window (e.g., 24 hours). If the deadline passes without a committed turn:
- The match is forfeited by the expired player.
- Transition to `STATE_MATCH_COMPLETE`.

---

## 10. Summary Decision Table

For quick reference, the legality engine can be reduced to these rules:

```
RULE 1: Exactly 1 draw must occur before any play/capture/discard.
RULE 2: 0 or more plays/captures may occur after draw, before end-turn.
RULE 3: Each play/capture must independently pass dictionary + letter validation.
RULE 4: Each letter in hand may be used at most once across all Phase B actions.
RULE 5: Each board word may be captured at most once per turn.
RULE 6: If hand is non-empty after Phase B, exactly 1 discard is required.
RULE 7: If hand is empty after Phase B, no discard occurs (manual complete).
RULE 8: Timer expiry triggers forced auto-action per Section 9.
RULE 9: All actions must come from the active player in STATE_ACTIVE_TURN.
RULE 10: The entire turn is atomic — partial commits are not allowed.
```

---

## 11. Traceability

| Section | Requirement |
|:--------|:------------|
| 2-3     | FR-3.5      |
| 4 (I15-I22) | FR-3.2, FR-3.3, FR-3.4 |
| 5       | NFR-3.2     |
| 6       | FR-3.3      |
| 9       | FR-4.4      |
| All     | FR-3.5      |
