# Abuse and Moderation Policy
**Project:** WIT V2
**Phase:** 1 (Requirements)
**Status:** Engineering Specification — Implementation Grade
**Linked Requirements:** FR-8.2, NFR-3.1, NFR-3.2, GDD 10.6, GDD 19

---

## 1. Purpose

This document defines the explicit rules, detection signals, penalty tiers, and operational procedures for abuse prevention and content moderation in WIT V2. All automated enforcement is server-side. Human review is required for escalations beyond temporary mutes. The goal is deterrence, detection, and proportional consequence — not a promise of zero abuse.

---

## 2. Username Policy

### 2.1 Username Format Rules

| Rule | Constraint |
|:-----|:----------|
| Minimum length | 3 characters |
| Maximum length | 20 characters |
| Allowed characters | a-z, A-Z, 0-9, underscore (_), hyphen (-) |
| Case sensitivity | Usernames are case-insensitive for uniqueness (stored in original case, compared lowercase) |
| Leading/trailing whitespace | Stripped automatically |
| Leading/trailing special characters | Allowed (e.g., `_player1`, `test-user`) |
| Consecutive special characters | Maximum 2 consecutive (reject `a___b` or `a---b`) |
| Unicode / emoji | Not allowed. ASCII Latin only at launch. |
| Reserved prefixes | `admin`, `mod`, `system`, `wit_`, `bot_` are reserved (case-insensitive) |

### 2.2 Banned Username Patterns

The username filter operates in two layers:

**Layer 1: Exact Match Blocklist**
A curated list of prohibited exact usernames (case-insensitive). Maintained in the Admin CMS. Examples: slurs, hate group names, impersonation targets.

**Layer 2: Substring / Pattern Match**
A regex-based pattern list that catches common evasion techniques:
- Leet-speak substitutions (e.g., `a55hole`, `sh1t`).
- Character insertion (e.g., `f.u.c.k`).
- Known offensive substring patterns.
- Patterns matching real-name formats that could enable impersonation (e.g., `officialdeveloper`).

Both layers are evaluated at username creation and username change. Rejection returns `ERR_USERNAME_REJECTED` with a generic message ("Username not available") — the system does not reveal which filter triggered.

### 2.3 Username Change Policy

| Policy | Value |
|:-------|:------|
| Change cooldown | 30 days between successful changes |
| Changes per account lifetime | Unlimited (subject to cooldown) |
| Admin-forced rename | Immediate, bypasses cooldown, triggers notification to player |
| Rename after ban | Required before account reinstatement if username was the violation |
| Display during cooldown | Current username displayed; "Change available in X days" shown in settings |

### 2.4 Display Name vs Handle

- **Handle:** Unique identifier used for friend-add and match history. Subject to all username rules above.
- **Display Name:** Optional cosmetic name shown in-match. Subject to the same filtering rules. If not set, handle is displayed.

---

## 3. Emote and Reaction Policy

### 3.1 Curated Emote Set

All in-match emotes come from a curated, pre-approved set. Players cannot create custom emotes or send free-text chat. The launch emote set:

| Emote ID | Visual | Intent | Risk Level |
|:---------|:-------|:-------|:-----------|
| `emote_gg` | "GG" text | Good game / sportsmanship | None |
| `emote_nice` | Thumbs up | Compliment a play | None |
| `emote_wow` | Surprised face | React to unexpected play | Low (can be passive-aggressive) |
| `emote_thinking` | Thinking face | Deliberation | Low |
| `emote_oops` | Sheepish face | Self-deprecation | None |
| `emote_wave` | Waving hand | Greeting / farewell | None |

### 3.2 Emote Spam Prevention

| Limit | Value |
|:------|:------|
| Max emotes per turn | 3 |
| Min interval between emotes | 2 seconds |
| Burst detection | 5+ emotes in 15 seconds triggers a 60-second emote cooldown for that player |
| Per-match cap | 20 emotes per player per match |

### 3.3 Mute Capability

- **Player-initiated mute:** Any player can mute their opponent's emotes via a single tap. Persists for the duration of the match. Not reported to the muted player.
- **Global emote disable:** Player can disable all emotes in Settings. This suppresses both incoming and outgoing emotes.
- **Parental control mute:** If parental controls are active, emotes are disabled by default.

---

## 4. Room Abuse Policy

### 4.1 Private Room Moderation

| Action | Rule |
|:-------|:-----|
| Room creator kick | Room creator can remove any player before match starts. |
| Mid-match kick | Not allowed. Once a match starts, it must complete or forfeit. |
| Report from room | Any player can report the room creator or other players. |
| Auto-dissolve: inactivity | Room with no match start for 15 minutes auto-dissolves. |
| Auto-dissolve: repeated reports | If 2+ unique players report the same room creator within 24 hours, room is dissolved and creator receives a warning. |
| Room code reuse | Codes are single-use. Dissolved rooms cannot be re-joined. |

### 4.2 Public Queue Abuse

| Signal | Detection | Action |
|:-------|:----------|:-------|
| Queue sniping (coordinated queue entries) | Repeated matchups between same player pair within short window | Flag for review after 3 occurrences in 1 hour |
| Queue dodging | Player cancels queue after match-found but before handshake | After 3 dodges in 1 hour: 5-minute queue cooldown. Escalates with repeat offenses. |
| Intentional deranking | Player with established MMR suddenly losing many games in a pattern inconsistent with normal play | Flag for review. No auto-action. |

---

## 5. Stalling Detection

### 5.1 Definition

Stalling is deliberately running the turn timer to the maximum on every turn without meaningful play intent, with the goal of annoying the opponent into abandoning the match.

### 5.2 Detection Signals

| Signal | Threshold | Weight |
|:-------|:----------|:-------|
| Consecutive timer-expiry forfeits | 3 in a match | High (auto-forfeit already triggers per FR-4.4) |
| Average turn time > 90% of timer | Across 5+ consecutive turns | Medium |
| Turn time > 95% of timer AND zero plays submitted | 3+ times in a match | Medium |
| Pattern: consistent last-second submissions with minimal actions | 5+ turns | Low (legitimate slow players may trigger this) |

### 5.3 Stalling Enforcement

| Occurrence | Action |
|:-----------|:-------|
| First match flagged | No player-visible action. Internal flag recorded. |
| Second match flagged within 7 days | Warning notification sent to player: "We noticed extended timer usage. Repeated stalling may result in penalties." |
| Third match flagged within 7 days | Temporary queue restriction: player must wait 60 seconds before re-queuing for 24 hours. |
| Fourth occurrence within 30 days | 24-hour ranked queue suspension. |
| Fifth+ occurrences | Escalate to manual review for potential temporary ban. |

### 5.4 False Positive Mitigation

- Players with high valid-play rates (many words played per match) are exempted from stalling flags even if they play slowly.
- Async matches are exempt from stalling detection (long timers are intentional).
- Only live ranked and live casual modes are subject to stalling detection.

---

## 6. Solver Suspicion Signals

### 6.1 Purpose

Because WIT V2 is a word game, external solver/anagram tools pose a significant competitive integrity risk in ranked play. The system does not attempt to prevent solver use outright (impossible) but builds a statistical detection model for flagging suspicious accounts for human review.

### 6.2 Detection Signals

| Signal | Description | Threshold / Anomaly |
|:-------|:------------|:--------------------|
| **Move timing patterns** | Consistent sub-5-second submissions for complex 7+ letter words. | Z-score > 2.5 relative to the player's own historical mean AND global mean for that word length. |
| **Vocabulary anomaly** | Playing extremely rare dictionary words (frequency rank > 99th percentile) at a rate far exceeding the player's skill tier. | Rare word rate > 3x the 95th percentile for the player's rank bracket, sustained over 10+ matches. |
| **Win rate outlier** | Win rate significantly above expected for the player's MMR bracket over a sustained period. | Win rate > 80% over 30+ ranked matches with MMR not converging upward at the expected rate. |
| **Play optimality** | Consistently playing the highest-scoring legal move available, computed post-hoc. | Optimality rate > 85% over 20+ matches (requires server-side post-match analysis). |
| **Multi-word turn complexity** | Unusually frequent complex multi-word turns with optimal letter utilization. | Flag if 3+ multi-word turns per match over 10+ matches, combined with high optimality. |
| **Session pattern** | Player performance dramatically differs between sessions (e.g., brilliant at some times, poor at others — potential account sharing or intermittent solver use). | Performance variance > 3 standard deviations across session clusters. |

### 6.3 Solver Enforcement

Solver detection is **never auto-enforced**. All signals produce flags for human review only.

| Review Outcome | Action |
|:---------------|:-------|
| Insufficient evidence | Clear flag. No action. |
| Probable solver use | Account flagged. Shadow monitoring for 30 days. No immediate penalty. |
| Confirmed solver use (high confidence) | First offense: 7-day ranked ban + rank reset. Second offense: permanent ranked ban. |
| Confirmed account sharing | Treated as solver use. Same penalty ladder. |

---

## 7. Collusion Signals

### 7.1 Definition

Collusion occurs when two or more players coordinate across separate matches or accounts to manipulate ranked results (e.g., one player intentionally loses to boost the other's MMR).

### 7.2 Detection Signals

| Signal | Description | Threshold |
|:-------|:------------|:----------|
| **Repeated matchups** | Same player pair matched in ranked queue an abnormally high number of times. | 5+ ranked matches between the same pair within 7 days. |
| **Lopsided results** | One player consistently wins against the same opponent with the loser making minimal plays. | Loser averages < 2 words played per round over 3+ matches against the same opponent. |
| **Coordinated queue timing** | Both players enter ranked queue within seconds of each other repeatedly. | 3+ instances of queue entry within 5-second windows, matching each time. |
| **Device fingerprint correlation** | Two accounts originating from the same device or IP with ranked interactions. | Any ranked match between accounts sharing a device fingerprint within 90 days. |
| **Score gifting pattern** | One player plays high-value words and then intentionally loses by timeout while opponent captures them. | Statistical analysis of capture-to-timeout ratio in repeated matchups. |

### 7.3 Collusion Enforcement

| Review Outcome | Action |
|:---------------|:-------|
| Suspected collusion | Both accounts flagged. 30-day shadow monitoring. Matches between the pair excluded from ranked during investigation. |
| Confirmed collusion | Both accounts: ranked results voided for the flagged period. 30-day ranked ban. MMR reset. |
| Repeated confirmed collusion | Permanent ranked ban for both accounts. |

---

## 8. Alt-Account Escalation

### 8.1 Detection Methods

| Method | Implementation |
|:-------|:---------------|
| **Device fingerprint** | Client collects a device fingerprint hash (combination of device model, OS version, screen dimensions, timezone, installed fonts subset). Stored server-side. |
| **IP correlation** | Server logs login IPs. Shared IPs between accounts are noted but not conclusive (shared WiFi is common). |
| **Behavioral correlation** | Accounts with similar play patterns (vocabulary, timing, preferred words) flagged by ML model (post-launch). |
| **Linked auth providers** | If two accounts attempt to bind to the same Apple/Google identity, the second bind is rejected and flagged. |

### 8.2 Alt-Account Policy

| Scenario | Action |
|:---------|:-------|
| Multiple accounts, no ranked abuse | Permitted. No penalty. Many legitimate reasons (family device, reinstall). |
| Alt account used to smurf ranked | If detected: warning on first offense. Alt account ranked ban on second offense. |
| Alt account used to evade ban | Immediate ban of alt account. Original ban extended by 30 days. |
| Alt account used for collusion | See Section 7 collusion enforcement. |

### 8.3 Privacy Considerations

Device fingerprinting data is:
- Hashed before storage (one-way).
- Not shared with third parties.
- Disclosed in the privacy policy.
- Deletable upon account deletion request (GDPR/CCPA).

---

## 9. Penalty Tiers

### 9.1 Penalty Ladder

| Tier | Name | Duration | Scope | Trigger Examples |
|:----:|:-----|:---------|:------|:-----------------|
| 0 | **Warning** | Instant notification | Informational only | First stalling flag, first emote spam, first username rejection |
| 1 | **Temporary Mute** | 24 hours | Emotes disabled | Emote spam after warning, reported for emote abuse by 2+ players |
| 2 | **Queue Cooldown** | 1-24 hours | Delayed re-queue | Repeated queue dodging, stalling pattern |
| 3 | **Temporary Ranked Ban** | 7-30 days | Cannot enter ranked queue | Confirmed solver use (first), confirmed collusion (first), severe stalling escalation |
| 4 | **Temporary Account Ban** | 7-30 days | Cannot log in | Severe or repeated username violations, ban evasion, multiple confirmed offenses |
| 5 | **Permanent Ban** | Indefinite | Account terminated | Repeated confirmed cheating after prior bans, extreme harassment/hate, ban evasion after permanent ban |

### 9.2 Penalty Stacking

- Multiple concurrent penalties from different categories stack (e.g., a player can be both muted and on ranked ban simultaneously).
- Penalties within the same category escalate to the next tier on repeat offense.
- Penalty history has a decay window: offenses older than 6 months reduce in weight for tier escalation (but are never deleted from the audit log).

### 9.3 Automatic vs Manual Penalties

| Penalty | Can Be Auto-Applied? | Requires Human Review? |
|:--------|:--------------------:|:----------------------:|
| Warning (Tier 0) | Yes | No |
| Temporary Mute (Tier 1) | Yes | No |
| Queue Cooldown (Tier 2) | Yes | No |
| Temporary Ranked Ban (Tier 3) | No | Yes |
| Temporary Account Ban (Tier 4) | No | Yes |
| Permanent Ban (Tier 5) | No | Yes (requires 2 admin approvals) |

---

## 10. Appeal Process

### 10.1 Appeal Eligibility

| Penalty Tier | Appealable? | Method |
|:-------------|:------------|:-------|
| 0-2 (Warning, Mute, Cooldown) | No | Too minor for appeal. Automatically expires. |
| 3 (Temporary Ranked Ban) | Yes | In-app appeal form |
| 4 (Temporary Account Ban) | Yes | Email appeal |
| 5 (Permanent Ban) | Yes, once | Email appeal within 30 days of ban |

### 10.2 Appeal Workflow

1. **Submission:** Player submits appeal via in-app form or email with:
   - Account ID
   - Description of circumstances
   - Any supporting context

2. **Acknowledgment:** Automated response within 1 hour confirming receipt.

3. **Review:** A moderation team member reviews:
   - Original evidence (match logs, telemetry, reports)
   - Player's account history (prior offenses, tenure, spending)
   - Appeal text

4. **Decision:** Within 72 hours of submission:
   - **Upheld:** Ban remains. Player notified with explanation.
   - **Reduced:** Ban tier reduced (e.g., permanent to 30-day). Player notified.
   - **Overturned:** Ban removed. Player notified. Apology token granted (cosmetic).

5. **Finality:** Each penalty may be appealed once. The appeal decision is final.

### 10.3 Appeal Volume Management

If appeal volume exceeds capacity:
- Priority is given to Tier 5 (permanent) appeals.
- Tier 3-4 appeals are processed FIFO.
- SLA: 72 hours for Tier 5, 7 days for Tier 3-4.

---

## 11. Admin Audit Trail

### 11.1 Logged Actions

Every moderation action is logged to the `admin_audit_log` table:

| Field | Type | Description |
|:------|:-----|:------------|
| `audit_id` | UUID v4 | Unique log entry ID |
| `admin_id` | UUID v4 | The admin who performed the action |
| `action_timestamp_ms` | int64 | When the action was performed |
| `action_type` | enum | `USERNAME_FORCE_RENAME`, `MUTE_PLAYER`, `BAN_PLAYER`, `UNBAN_PLAYER`, `RANKED_BAN`, `RANKED_UNBAN`, `APPEAL_REVIEWED`, `FLAG_CLEARED`, `MATCH_REVIEWED`, `LEXICON_UPDATED`, `BLOCKLIST_UPDATED` |
| `target_player_id` | UUID v4 | The affected player (if applicable) |
| `target_match_uuid` | UUID v4 | The affected match (if applicable) |
| `penalty_tier` | int8 | The penalty tier applied (0-5) |
| `reason` | text | Free-text justification from the admin |
| `evidence_refs` | JSONB | Array of match UUIDs, report IDs, and telemetry event IDs used as evidence |
| `previous_state` | JSONB | Player's moderation state before the action |
| `new_state` | JSONB | Player's moderation state after the action |

### 11.2 Audit Retention

- Audit logs are retained **indefinitely** and are append-only.
- No admin may delete or modify audit log entries.
- Audit logs are included in quarterly compliance reviews.

### 11.3 Admin Access Controls

| Role | Permissions |
|:-----|:------------|
| Moderation Reviewer | View reports, view match logs, view player history, clear flags |
| Moderation Admin | All Reviewer permissions + apply Tier 0-2 penalties, review appeals |
| Senior Moderation Admin | All Admin permissions + apply Tier 3-4 penalties |
| Moderation Lead | All Senior Admin permissions + apply Tier 5 penalties (requires 2 approvals from Lead-level) |
| System Admin | All permissions + audit log export + role management |

---

## 12. Reporting System

### 12.1 In-Game Report Flow

1. Player taps "Report" on opponent's profile (accessible during or after match).
2. Player selects report category:
   - Offensive Username
   - Stalling / Time Wasting
   - Suspected Cheating
   - Suspected Collusion
   - Other
3. Player optionally adds free-text detail (max 500 characters).
4. Report is submitted with the current `match_uuid` automatically attached.
5. Player receives confirmation: "Report submitted. We'll review this."

### 12.2 Report Rate Limiting

| Limit | Value |
|:------|:------|
| Reports per player per day | 5 |
| Reports against same player per 7 days | 2 |
| Duplicate report (same reporter + same target + same match) | Rejected |

### 12.3 Report Processing

- Reports are queued in the moderation dashboard.
- Reports with 3+ unique reporters against the same player within 7 days are auto-escalated to priority review.
- Reports are enriched with automated analysis: match replay summary, player stats, prior report history.

---

## 13. Traceability

| Section | Requirement |
|:--------|:------------|
| 2       | FR-8.2, GDD 19.3 |
| 3       | GDD 10.5 |
| 4       | FR-1.3 |
| 5       | FR-4.4, GDD 10.6 |
| 6       | NFR-3.1, GDD 10.6 |
| 7       | GDD 10.6 |
| 8       | GDD 10.6 |
| 9-10    | FR-8.2 |
| 11      | FR-8.1, FR-8.2 |
