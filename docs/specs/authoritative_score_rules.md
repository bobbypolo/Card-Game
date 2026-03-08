# Authoritative Score Rules
**Project:** WIT V2
**Phase:** 1 (Requirements)
**Status:** Engineering Specification — Implementation Grade
**Linked Requirements:** FR-4.1, FR-4.2, FR-4.3, FR-5.1, FR-5.2

---

## 1. Purpose

This document defines the exact scoring mathematics for WIT V2. All score calculations are server-authoritative. The client displays previews computed from the same formulas but the server is the sole source of truth for committed scores. No rounding, no floating-point arithmetic — all scoring uses signed 32-bit integers.

---

## 2. Base Word Score Table

Word length is defined as the count of letters in the submitted word, including any letters represented by wild cards.

| Word Length | Base Score (points) |
|:-----------:|:-------------------:|
| 2           | 2                   |
| 3           | 5                   |
| 4           | 7                   |
| 5           | 9                   |
| 6           | 12                  |
| 7           | 14                  |
| 8           | 16                  |
| 9           | 20                  |
| 10+         | 25                  |

**Rules:**
- The table is a lookup, not a formula. Words of 10, 11, 12, ... letters all score 25.
- The minimum playable word length is 2 letters.
- A 1-letter "word" is never legal and shall be rejected at the play-legality layer before scoring is invoked.
- The base score table is stored as a server-side configuration keyed by `deck_composition_version`. Changes require a new version and cannot be applied mid-match.

---

## 3. Wild Card Scoring Behavior

Wild cards count as full letters for all scoring purposes:

1. **Length contribution:** A wild card in a word adds 1 to the word's letter count for base-score lookup.
2. **7+ letter bonus:** If a submitted word contains **at least one wild card** AND the word has **7 or more letters**, an additive bonus of **+2 points** is applied. This bonus is flat — it does not scale with word length or wild-card count.
3. **No doubling:** The original tabletop doubling rule is replaced by the flat +2 bonus in all standard and ranked playlists. Classic custom rooms may enable original doubling via a Rule Modifier override (see Section 7).
4. **Multiple wild cards:** A word containing 2 wild cards still receives only a single +2 bonus (not +4). The bonus is per-word, not per-wild-card.

### Wild Card Score Formula (per word)

```
wild_card_bonus = 0
if word.contains_wild_card AND word.letter_count >= 7:
    wild_card_bonus = 2

word_score = base_score_table[word.letter_count] + wild_card_bonus
```

---

## 4. Capture Bonus Calculation

When a player captures an opponent's (or their own) word, the capture bonus is computed as follows:

### 4.1 Definitions

- `original_word`: the word being captured (already on the board).
- `new_word`: the valid word formed by using all of `original_word`'s letters plus at least 1 new letter from the capturing player's hand.
- `added_letter_count`: the number of new letters contributed from the capturing player's hand to form `new_word`. Formally: `added_letter_count = new_word.letter_count - original_word.letter_count`.

### 4.2 Capture Score Formula

```
capture_base_score     = base_score_table[new_word.letter_count]
capture_wild_bonus     = 2 if (new_word.contains_wild_card AND new_word.letter_count >= 7) else 0
capture_added_bonus    = added_letter_count * 2

capture_total_score    = capture_base_score + capture_wild_bonus + capture_added_bonus
```

### 4.3 Original Owner Score Retention

The original owner of the captured word **retains** the points they previously earned for that word. The capture does not retroactively reduce or remove the original owner's score. Points already committed are immutable.

### 4.4 Capture Scoring Example

Player A plays "TOP" (3 letters, base = 5 pts). Player A is credited +5.
Player B captures "TOP" into "STOP" (4 letters, 1 added letter):
- `capture_base_score = 7` (4-letter word)
- `capture_wild_bonus = 0` (no wild card or fewer than 7 letters)
- `capture_added_bonus = 1 * 2 = 2`
- `capture_total_score = 7 + 0 + 2 = 9`
- Player B is credited +9. Player A still retains their original +5.

### 4.5 Self-Capture

A player may capture their own word under the same rules (all original letters + at least 1 new letter + valid new word). Scoring is identical. The player receives the new word's score as a fresh credit. Their original score for the earlier word is retained.

---

## 5. Multi-Word Turn Scoring

A player may play multiple words and/or captures in a single turn. Scores are **additive**.

```
turn_score_delta = SUM(word_score for each new word played)
                 + SUM(capture_total_score for each capture performed)
```

There is no cap on the number of words or captures per turn, provided each individual action passes the play-legality engine. Each word/capture is scored independently — there is no interaction or combo multiplier between words in the same turn.

---

## 6. End-of-Round Penalty

### 6.1 Penalty Calculation

When a round ends, every player with remaining letters in hand receives a penalty:

```
hand_penalty = remaining_letter_count * (-1)
```

- Each remaining letter (including wild cards) costs -1 point.
- Wild cards in hand are penalized identically to regular letters (-1 each).
- The penalty is applied as a single negative score delta in the `STATE_ROUND_COMPLETE` phase.

### 6.2 Penalty Application Timing

Penalties are applied **after** all turn scores for the final turn are committed and **before** round-winner determination. The exact sequence within `STATE_ROUND_COMPLETE`:

1. Final turn score deltas are committed.
2. Hand penalty deltas are computed and committed for all players.
3. Round totals are finalized.
4. Round winner is determined.

### 6.3 Negative Round Scores

A player's round score **may go negative**. There is no floor clamp. If a player scores 3 points from words but has 5 remaining letters, their round score is `3 - 5 = -2`.

---

## 7. Rule Modifier Scoring Overlays

### 7.1 Modifier Application Precedence

When a Rule Modifier is active for a round, scoring modifications follow this strict order of operations:

```
Step 1: Compute base_score from the word-length table.
Step 2: Compute wild_card_bonus (if applicable).
Step 3: Compute capture_added_bonus (if applicable).
Step 4: Sum Steps 1-3 into raw_word_score.
Step 5: Apply additive modifier bonuses to raw_word_score.
Step 6: Apply multiplicative modifier bonuses to (raw_word_score + additive bonuses).
Step 7: Truncate to integer (floor toward zero) if any multiplication produced a non-integer.
Step 8: Result is final_word_score.
```

### 7.2 Modifier Stacking Policy

- **At most one** scoring modifier may be active per round in standard playlists.
- Custom/event playlists may stack up to 2 modifiers. When stacked, additive bonuses from all modifiers are summed in Step 5, and multiplicative bonuses are applied sequentially left-to-right in modifier declaration order in Step 6.
- Modifiers **never** alter the base score table itself. They overlay on top of it.

### 7.3 Known Modifier Scoring Effects

| Modifier        | Type           | Effect                                                                    |
|:----------------|:---------------|:--------------------------------------------------------------------------|
| Long Form       | Additive       | Words with 6+ letters receive +3 bonus points.                           |
| Sharp Steal     | Additive       | Capture `added_letter_count` bonus increases from +2 to +3 per letter.   |
| Vowel Pressure  | Penalty Override| Vowels (A, E, I, O, U) remaining in hand at round end cost -2 each instead of -1. Consonants and wild cards remain -1. |
| Double Edge     | Override        | Wild card 7+ letter bonus is disabled (set to 0) for this round.         |
| Chain Link      | Conditional     | If a player's capture immediately follows an opponent's capture (consecutive turns), +3 response bonus. |
| Theme Round     | Conditional     | Words matching the declared category receive +4 bonus. Non-matching words score normally. Theme matching is server-evaluated against a curated tag set. |

New modifiers may be added via the Admin CMS. Each modifier definition must declare its type (additive/multiplicative/override/conditional/penalty-override), its numeric value, and its applicability conditions.

### 7.4 Modifier and Penalty Interaction

- Vowel Pressure overrides the default penalty rate for vowels only. It does **not** interact with word-scoring modifiers.
- Penalty modifiers are evaluated in Step 2 of the end-of-round penalty phase (Section 6.2), using the modifier's override values instead of the default -1.

---

## 8. Rounding Policy

- **All intermediate and final scores are integers.** The base score table produces integers. Capture bonuses produce integers. Additive modifiers produce integers.
- **Multiplicative modifiers** are the only source of potential non-integer results. When a multiplicative modifier is applied: `floor(value)` is used (truncation toward zero). Example: if a multiplicative modifier yields 13.5, the result is 13.
- **No banker's rounding, no ceiling, no rounding-to-nearest.** Always floor toward zero.
- There are no fractional points at any layer. Client score previews must use the same floor policy.

---

## 9. Score Preview Calculation

The client displays a score preview before the player commits their turn. The preview follows the identical formula pipeline (Sections 2-7) using the proposed action set. The preview is advisory — the server recomputes independently upon submission.

### 9.1 Preview Input

The client sends the proposed moves to a local scoring function that mirrors the server logic:

```
preview_input = {
    proposed_plays: [
        { word: "STOP", letters_from_hand: ["S"], capture_target: "TOP" },
        { word: "HE", letters_from_hand: ["H", "E"], capture_target: null }
    ],
    active_modifier: modifier_config | null,
    hand_before: [...],
    hand_after: [...]   // remaining after proposed plays
}
```

### 9.2 Preview Output

```
preview_output = {
    play_scores: [
        { word: "STOP", base: 7, wild_bonus: 0, capture_bonus: 2, modifier_bonus: 0, total: 9 },
        { word: "HE", base: 2, wild_bonus: 0, capture_bonus: 0, modifier_bonus: 0, total: 2 }
    ],
    turn_total: 11,
    remaining_hand_count: N,
    potential_penalty_if_round_ends: -N
}
```

### 9.3 Preview Accuracy Contract

The preview must produce the same `turn_total` as the server for identical inputs. Any divergence is classified as a P1 bug under the state-divergence SLO (NFR-1.6).

---

## 10. Tiebreaker Rules

Tiebreakers apply at the **match level** when the best-of-3 round-win count is tied (which can only happen if both players have won 1 round and the 3rd round is a draw, or under alternative scoring formats).

### 10.1 Round-Level Tie

If two players have the same round score after penalties:

1. **Fewer unplayed letters** across the round wins. Count all remaining letters in hand at round end.
2. **If still tied:** Player with more successful captures during the round wins.
3. **If still tied:** The round is declared a draw. Neither player earns a round win.

### 10.2 Match-Level Tie

If the best-of-3 format ends without a player reaching 2 round wins (e.g., 1-1-draw):

1. **Fewer total unplayed letters** across all rounds of the match wins.
2. **If still tied:** Player with more total successful captures across the match wins.
3. **If still tied:** A sudden-death round is played. First player to win the sudden-death round wins the match. Sudden-death uses the same rules, modifiers, and lexicon version as the match.

### 10.3 Tiebreaker Evaluation Order (Summary)

```
Level 1: Round wins (best-of-3)
Level 2: Fewer unplayed letters (match aggregate)
Level 3: More captures (match aggregate)
Level 4: Sudden death round
```

No match may end in a draw. The tiebreaker chain guarantees a winner (sudden death is unbounded until one player wins a round).

---

## 11. Score Data Types and Overflow Policy

| Field                | Type   | Range                          |
|:---------------------|:-------|:-------------------------------|
| `base_score`         | int32  | 2 to 25                       |
| `wild_card_bonus`    | int32  | 0 or 2                        |
| `capture_added_bonus`| int32  | 2+ (minimum 1 added letter)   |
| `modifier_bonus`     | int32  | Defined per modifier config    |
| `hand_penalty`       | int32  | 0 to -9 (standard) or deeper  |
| `round_score`        | int32  | May be negative                |
| `match_score`        | int32  | Sum of round scores            |
| `turn_delta`         | int32  | Additive per turn              |

Overflow is not a practical concern given the score magnitudes (max theoretical single-turn score is bounded by hand size and available captures). The server shall log a warning if any single turn delta exceeds 200 points (anomaly detection).

---

## 12. Canonical Scoring Algorithm (Pseudocode)

```python
def score_turn(actions, active_modifier, match_state):
    turn_delta = 0

    for action in actions:
        if action.type == PLAY_WORD:
            word_len = len(action.word)
            base = BASE_SCORE_TABLE[min(word_len, 10)]
            wild_bonus = 2 if (action.has_wild and word_len >= 7) else 0
            raw = base + wild_bonus
            modifier_bonus = compute_modifier_bonus(raw, action, active_modifier)
            turn_delta += raw + modifier_bonus

        elif action.type == CAPTURE_WORD:
            word_len = len(action.new_word)
            added_count = word_len - len(action.original_word)
            base = BASE_SCORE_TABLE[min(word_len, 10)]
            wild_bonus = 2 if (action.new_word_has_wild and word_len >= 7) else 0
            capture_bonus = compute_capture_bonus(added_count, active_modifier)
            raw = base + wild_bonus + capture_bonus
            modifier_bonus = compute_modifier_bonus(raw, action, active_modifier)
            turn_delta += raw + modifier_bonus

    return turn_delta

def compute_capture_bonus(added_count, modifier):
    per_letter_rate = 2  # default
    if modifier and modifier.name == "Sharp Steal":
        per_letter_rate = 3
    return added_count * per_letter_rate

def compute_modifier_bonus(raw_score, action, modifier):
    if modifier is None:
        return 0
    bonus = 0
    if modifier.type == ADDITIVE:
        if modifier.condition_met(action):
            bonus = modifier.additive_value
    elif modifier.type == MULTIPLICATIVE:
        if modifier.condition_met(action):
            bonus = floor(raw_score * modifier.multiplier) - raw_score
    return bonus

def compute_round_penalties(players, active_modifier):
    for player in players:
        penalty = 0
        for letter in player.hand:
            if active_modifier and active_modifier.name == "Vowel Pressure" and letter.is_vowel():
                penalty -= 2
            else:
                penalty -= 1
        player.round_score += penalty

BASE_SCORE_TABLE = {2:2, 3:5, 4:7, 5:9, 6:12, 7:14, 8:16, 9:20, 10:25}
```

---

## 13. Traceability

| Section | Requirement |
|:--------|:------------|
| 2       | FR-4.1      |
| 3       | FR-3.4      |
| 4       | FR-4.2      |
| 5       | FR-3.5      |
| 6       | FR-4.3      |
| 7       | FR-5.1, FR-5.2 |
| 9       | FR-6.1      |
| 10      | GDD 8.15    |
