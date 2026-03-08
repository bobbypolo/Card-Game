# Telemetry Event Taxonomy
**Project:** WIT V2
**Phase:** 1 (Requirements)
**Status:** Engineering Specification — Implementation Grade
**Linked Requirements:** FR-6.1, FR-7.1, NFR-1.4, NFR-1.5

---

## 1. Purpose

This document defines every analytics event emitted by WIT V2 client and server components. Events follow a structured taxonomy to support product analytics, operational monitoring, funnel analysis, anti-cheat detection, and live-ops decision making. All events flow through the telemetry pipeline to the analytics backend (Datadog + data warehouse).

---

## 2. Event Structure

### 2.1 Common Envelope

Every event is wrapped in a common envelope:

```json
{
    "event_name": "string",
    "event_category": "string",
    "event_timestamp_ms": 1709901234567,
    "event_id": "uuid-v4",
    "session_id": "uuid-v4",
    "user_id": "uuid-v4 | null",
    "device_id": "string",
    "platform": "ios | android | web",
    "app_version": "1.2.3",
    "build_number": "456",
    "properties": { ... }
}
```

### 2.2 Property Conventions

- All timestamps are UNIX epoch milliseconds (int64).
- All IDs are UUID v4 strings.
- Boolean properties use `true`/`false`.
- Numeric properties use integers unless explicitly specified as float.
- String enums are UPPER_SNAKE_CASE.
- Null/missing optional properties are omitted from the payload (not sent as `null`).

---

## 3. Event Catalog

### 3.1 App Lifecycle

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `app_open` | lifecycle | App cold-starts or is launched from terminated state. | `launch_type`: "COLD" \| "WARM", `time_since_last_open_ms`: int64 | `deep_link_url`: string, `notification_id`: string |
| `app_background` | lifecycle | App moves to background (home button, task switch). | `active_screen`: string, `session_duration_ms`: int64 | `active_match_uuid`: string |
| `app_foreground` | lifecycle | App returns to foreground from background. | `background_duration_ms`: int64 | `active_match_uuid`: string |
| `session_start` | lifecycle | New analytics session begins. Triggered on cold start or after 30+ minutes of inactivity. | `is_first_session`: boolean, `days_since_install`: int32 | `referral_source`: string |
| `session_end` | lifecycle | Session ends (app terminated or 30-min inactivity timeout). | `session_duration_ms`: int64, `screens_visited`: int32, `matches_played`: int32 | `last_active_screen`: string |

### 3.2 Authentication

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `auth_guest_created` | auth | Device-based guest account is created on first launch. | `guest_id`: string | |
| `auth_login` | auth | User successfully authenticates via SSO or session restore. | `auth_method`: "APPLE" \| "GOOGLE" \| "SESSION_RESTORE", `is_new_account`: boolean | `account_age_days`: int32 |
| `auth_logout` | auth | User explicitly logs out. | `auth_method`: string | |
| `auth_bind_started` | auth | Guest begins SSO binding flow. | `bind_provider`: "APPLE" \| "GOOGLE" | |
| `auth_bind_completed` | auth | Guest successfully binds to SSO account. | `bind_provider`: string, `guest_id`: string | |
| `auth_bind_failed` | auth | SSO binding attempt fails. | `bind_provider`: string, `error_code`: string | `error_message`: string |

### 3.3 Tutorial

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `tutorial_started` | tutorial | Player begins the tutorial flow. | `entry_point`: "FIRST_LAUNCH" \| "MENU" | |
| `tutorial_step_completed` | tutorial | Player completes a tutorial lesson. | `step_index`: int32, `step_name`: "MAKE_WORD" \| "DRAW_DISCARD" \| "CAPTURE" \| "ROUND_END" \| "MODIFIER_INTRO", `duration_ms`: int64 | `attempts`: int32, `hints_used`: int32 |
| `tutorial_completed` | tutorial | Player finishes all tutorial steps. | `total_duration_ms`: int64, `steps_completed`: int32 | `skipped_steps`: int32 |
| `tutorial_skipped` | tutorial | Player exits tutorial before completion. | `last_completed_step`: int32, `skip_point`: string | |

### 3.4 Matchmaking

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `live_queue_entered` | matchmaking | Player enters a live matchmaking queue. | `queue_type`: "RANKED_1V1" \| "CASUAL_1V1" \| "CASUAL_TABLE", `playlist`: "CLASSIC" \| "ARENA" | `mmr_bucket`: int32 |
| `live_queue_cancelled` | matchmaking | Player cancels out of the queue before matching. | `queue_type`: string, `wait_duration_ms`: int64 | |
| `live_match_found` | matchmaking | Server pairs players and creates a match instance. | `match_uuid`: string, `queue_type`: string, `wait_duration_ms`: int64, `player_count`: int32 | `mmr_diff`: int32, `region`: string |
| `async_match_created` | matchmaking | An asynchronous match is created. | `match_uuid`: string, `initiator_player_id`: string, `opponent_type`: "FRIEND" \| "RANDOM" | `turn_deadline_hours`: int32 |
| `private_room_match_started` | matchmaking | A match begins in a private room. | `match_uuid`: string, `room_code`: string, `player_count`: int32 | `playlist`: string |
| `bot_match_started` | matchmaking | Player starts a practice match vs AI. | `match_uuid`: string, `bot_difficulty`: "BEGINNER" \| "STANDARD" \| "ADVANCED" | |

### 3.5 Gameplay

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `turn_submitted` | gameplay | Player commits a turn (server accepts the submission). | `match_uuid`: string, `round_number`: int32, `turn_number`: int32, `action_count`: int32, `words_played`: int32, `captures_made`: int32, `score_delta`: int32, `turn_duration_ms`: int64 | `draw_source`: "STOCK" \| "DISCARD", `letters_remaining`: int32, `wild_cards_used`: int32 |
| `turn_rejected` | gameplay | Server rejects a player's turn submission. | `match_uuid`: string, `error_code`: string, `action_type`: string | `error_detail`: string |
| `word_played` | gameplay | A new word is successfully placed on the board. | `match_uuid`: string, `word_text`: string, `word_length`: int32, `word_score`: int32 | `contains_wild`: boolean, `wild_bonus_applied`: boolean, `modifier_bonus`: int32 |
| `capture_success` | gameplay | A capture is successfully validated and committed. | `match_uuid`: string, `original_word`: string, `new_word`: string, `added_letter_count`: int32, `capture_score`: int32 | `self_capture`: boolean, `lineage_depth`: int32 |
| `capture_rejected` | gameplay | A capture attempt is rejected by the server. | `match_uuid`: string, `attempted_word`: string, `target_word`: string, `rejection_reason`: string | |
| `round_completed` | gameplay | A round ends (any trigger). | `match_uuid`: string, `round_number`: int32, `round_trigger`: "HAND_EMPTY" \| "STOCK_EXHAUSTED" \| "FORFEIT", `winner_player_id`: string \| null, `round_duration_ms`: int64, `turns_in_round`: int32 | `score_spread`: int32, `modifier_active`: string |
| `match_completed` | gameplay | A match concludes with a final result. | `match_uuid`: string, `winner_player_id`: string, `match_duration_ms`: int64, `rounds_played`: int32, `final_scores`: object, `match_type`: string | `tiebreaker_used`: string, `forfeit`: boolean |
| `score_preview_shown` | gameplay | Client displays score preview before submission. | `match_uuid`: string, `preview_total`: int32, `words_in_preview`: int32 | `captures_in_preview`: int32 |
| `timer_warning` | gameplay | Turn timer reaches warning threshold (e.g., 10s remaining). | `match_uuid`: string, `remaining_ms`: int64, `phase`: "DRAW" \| "PLAY" \| "END_TURN" | |

### 3.6 Async

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `async_turn_ready_push_sent` | async | Server dispatches a push notification that it is the player's turn. | `match_uuid`: string, `target_player_id`: string, `push_provider`: "APNS" \| "FCM" | `delivery_id`: string |
| `async_turn_submitted` | async | Player submits a turn in an async match. | `match_uuid`: string, `time_since_notification_ms`: int64 | `opened_via`: "PUSH" \| "INBOX" \| "DEEP_LINK" |
| `async_match_resumed` | async | Player opens an async match to view current state or take their turn. | `match_uuid`: string, `entry_point`: "PUSH_NOTIFICATION" \| "INBOX" \| "DEEP_LINK" \| "MATCH_LIST" | `time_since_last_visit_ms`: int64 |
| `async_deadline_warning` | async | System sends a deadline-approaching notification (e.g., 2h remaining). | `match_uuid`: string, `target_player_id`: string, `deadline_remaining_ms`: int64 | |
| `async_deadline_expired` | async | Turn deadline passes without player action, triggering forfeit. | `match_uuid`: string, `expired_player_id`: string, `deadline_hours`: int32 | |

### 3.7 Reconnect

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `reconnect_attempted` | reconnect | Client detects WebSocket drop and begins reconnection. | `match_uuid`: string, `disconnect_duration_ms`: int64 | `disconnect_reason`: string |
| `reconnect_success` | reconnect | Client successfully reconnects and receives state resync. | `match_uuid`: string, `reconnect_duration_ms`: int64, `state_hash_match`: boolean, `actions_replayed`: int32 | |
| `reconnect_failed` | reconnect | Client fails to reconnect within the grace window. | `match_uuid`: string, `total_attempt_duration_ms`: int64, `attempts`: int32, `final_error`: string | |

### 3.8 Ranked

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `ranked_result_written` | ranked | Server persists a ranked match result to the ledger. | `match_uuid`: string, `winner_player_id`: string, `loser_player_id`: string, `write_latency_ms`: int64 | `idempotent_retry`: boolean |
| `rank_changed` | ranked | Player's visible rank tier changes (promotion or demotion). | `player_id`: string, `old_rank`: string, `new_rank`: string, `direction`: "PROMOTION" \| "DEMOTION" | `mmr_delta`: int32, `season_id`: string |
| `season_reset` | ranked | Seasonal ranked ladder resets. | `season_id`: string, `season_end_timestamp_ms`: int64, `players_reset`: int32 | |
| `mmr_updated` | ranked | Hidden MMR is updated after a ranked match. | `player_id`: string, `old_mmr`: int32, `new_mmr`: int32, `match_uuid`: string | `confidence_factor`: float |

### 3.9 Social

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `friend_added` | social | Two players become friends. | `initiator_player_id`: string, `target_player_id`: string, `method`: "HANDLE" \| "CODE" \| "RECENT_OPPONENT" | |
| `friend_removed` | social | A player removes a friend. | `player_id`: string, `removed_friend_id`: string | |
| `private_room_created` | social | A private room is created. | `room_code`: string, `creator_player_id`: string, `playlist`: string | `max_players`: int32 |
| `private_room_joined` | social | A player joins a private room. | `room_code`: string, `player_id`: string | `join_method`: "CODE" \| "FRIEND_INVITE" |
| `rematch_requested` | social | A player requests a rematch after match completion. | `original_match_uuid`: string, `requesting_player_id`: string | |
| `rematch_accepted` | social | Opponent accepts a rematch request. | `original_match_uuid`: string, `new_match_uuid`: string | |
| `emote_sent` | social | Player sends an emote/reaction during a match. | `match_uuid`: string, `emote_id`: string, `sender_player_id`: string | |

### 3.10 Moderation

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `report_submitted` | moderation | A player submits a report against another player. | `reporter_player_id`: string, `reported_player_id`: string, `report_type`: "OFFENSIVE_USERNAME" \| "STALLING" \| "SUSPECTED_CHEATING" \| "COLLUSION" \| "HARASSMENT", `match_uuid`: string | `report_detail`: string |
| `match_abandon` | moderation | A player voluntarily abandons a match (surrender/quit). | `match_uuid`: string, `abandoning_player_id`: string, `reason`: "VOLUNTARY_SURRENDER" \| "APP_UNINSTALL" \| "EXTENDED_DISCONNECT" | `match_duration_at_abandon_ms`: int64 |
| `player_muted` | moderation | System mutes a player's emote/reaction capability. | `player_id`: string, `mute_duration_hours`: int32, `reason`: string | `triggered_by`: "AUTO" \| "ADMIN" |
| `player_banned` | moderation | System issues a temporary or permanent ban. | `player_id`: string, `ban_type`: "TEMP" \| "PERMANENT", `ban_duration_hours`: int32 \| null, `reason`: string | `triggered_by`: "AUTO" \| "ADMIN", `appeal_eligible`: boolean |
| `username_rejected` | moderation | A username change or creation is rejected by the filter. | `player_id`: string, `attempted_username`: string, `rejection_reason`: string | |

### 3.11 Commerce

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `purchase_started` | commerce | Player initiates an in-app purchase flow. | `product_id`: string, `product_type`: "COSMETIC" \| "BATTLE_PASS" \| "AD_REMOVAL" \| "BUNDLE", `price_cents`: int32, `currency`: string | `store`: "APP_STORE" \| "PLAY_STORE" |
| `purchase_completed` | commerce | Purchase transaction is confirmed and entitlement granted. | `product_id`: string, `transaction_id`: string, `price_cents`: int32, `currency`: string | `is_first_purchase`: boolean |
| `purchase_failed` | commerce | Purchase flow fails or is cancelled. | `product_id`: string, `failure_reason`: "USER_CANCELLED" \| "PAYMENT_DECLINED" \| "NETWORK_ERROR" \| "STORE_ERROR", `stage`: "INITIATION" \| "PAYMENT" \| "VERIFICATION" | `error_code`: string |
| `purchase_restored` | commerce | Previously purchased entitlements are restored (e.g., reinstall). | `product_ids`: array of string, `restore_count`: int32 | |

### 3.12 Admin / System (Server-Side Only)

| Event Name | Category | Trigger | Required Properties | Optional Properties |
|:-----------|:---------|:--------|:-------------------|:-------------------|
| `lexicon_version_published` | admin | Admin publishes a new lexicon version. | `admin_id`: string, `old_version`: string, `new_version`: string | `word_count_delta`: int32 |
| `banned_word_updated` | admin | Admin modifies the banned-word overlay. | `admin_id`: string, `action`: "ADD" \| "REMOVE", `word_count`: int32 | |
| `modifier_config_updated` | admin | Admin updates a Rule Modifier configuration. | `admin_id`: string, `modifier_id`: string, `change_type`: "CREATE" \| "UPDATE" \| "DISABLE" | |
| `feature_flag_changed` | admin | A feature flag value changes in LaunchDarkly. | `flag_key`: string, `old_value`: string, `new_value`: string | `changed_by`: string |
| `state_divergence_detected` | system | Client or server detects a state hash mismatch. | `match_uuid`: string, `sequence_id`: int32, `expected_hash`: string, `actual_hash`: string, `detection_source`: "CLIENT" \| "SERVER" \| "REPLAY_AUDIT" | |
| `dlq_message_enqueued` | system | A failed message is sent to the Dead Letter Queue. | `queue_name`: string, `message_type`: string, `failure_count`: int32 | `last_error`: string |

---

## 4. Event Volume Estimates

| Category | Estimated Events per Match | Estimated Daily Volume (10K DAU) |
|:---------|:--------------------------:|:--------------------------------:|
| lifecycle | 2-4 | 20K-40K |
| auth | 1-2 | 10K-20K |
| tutorial | 0-6 (first session only) | 1K-5K |
| matchmaking | 2-3 | 30K-50K |
| gameplay | 20-60 | 400K-1M |
| async | 2-10 per async match | 50K-200K |
| reconnect | 0-2 | 5K-20K |
| ranked | 1-3 per ranked match | 10K-30K |
| social | 0-2 | 5K-20K |
| moderation | 0-1 | 500-2K |
| commerce | 0-1 | 500-5K |
| admin/system | Rare | <100 |

---

## 5. Event Routing

| Category | Primary Destination | Secondary Destination |
|:---------|:-------------------|:---------------------|
| lifecycle, auth, tutorial, matchmaking, social, commerce | Data Warehouse (analytics) | Datadog (operational metrics) |
| gameplay, async, reconnect | Data Warehouse + Datadog | Match action log (Postgres) |
| ranked | Data Warehouse + Datadog | Ranked ledger audit |
| moderation | Data Warehouse | Admin CMS dashboard |
| admin/system | Datadog (alerts) | Data Warehouse |
| state_divergence_detected | PagerDuty (P1 alert) | Datadog + Data Warehouse |

---

## 6. Privacy and Data Classification

| Property Type | Classification | Handling |
|:-------------|:---------------|:---------|
| user_id, player_id | PII-adjacent (pseudonymous) | Stored with encryption at rest. Deletable under GDPR/CCPA. |
| device_id | Device identifier | Hashed before warehouse storage. Deletable on request. |
| IP address | PII | NOT included in analytics events. Captured only in server access logs with 30-day retention. |
| match_uuid, word_text | Gameplay data | Non-PII. Standard retention. |
| transaction_id, price | Financial | Encrypted at rest. Audit-retained per tax/legal requirements. |
| attempted_username | Moderation evidence | Retained for 90 days for appeal review, then deleted. |

---

## 7. Implementation Notes

### 7.1 Client SDK

The React Native client uses a thin telemetry wrapper that:
- Batches events (max 10 or 5-second window, whichever comes first).
- Persists unsent events to local storage for offline resilience.
- Retries failed sends with exponential backoff (1s, 2s, 4s, max 3 retries, then DLQ).
- Adds common envelope fields automatically.

### 7.2 Server SDK

Backend services emit events via a shared telemetry package:
- Events are published to an internal event bus (SQS/SNS).
- A telemetry worker consumes and forwards to Datadog and the data warehouse.
- Server events include `server_instance_id` and `service_name` for tracing.

### 7.3 Schema Versioning

The telemetry schema follows the same semantic versioning policy as the API contracts. Adding new optional properties is a minor version change. Removing or renaming required properties is a major version change. The `schema_version` field is included in the event envelope for consumer compatibility.

---

## 8. Traceability

| Section | Requirement |
|:--------|:------------|
| 3.3     | GDD 16.2    |
| 3.5     | FR-6.1      |
| 3.6     | FR-7.1, NFR-1.4 |
| 3.7     | NFR-1.3     |
| 3.8     | FR-9.1      |
| 3.10    | FR-8.2      |
| 3.12    | NFR-1.6     |
| 6       | GDPR/CCPA compliance |
