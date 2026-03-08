# Requirements Traceability Matrix (RTM)
**Project:** WIT V2
**Phase:** 1 (Requirements)

| Req ID | Requirement Description | Design Component (TBD Ph3) | Test Case / Verification Suite | UAT Scenario |
|:---|:---|:---|:---|:---|
| **FR-1.1** | Guest session bootstrapping / binding | Auth Service | `auth_guest_flow`, `auth_bind_sso` | Scenario 1 |
| **FR-1.2** | Native SSO Registration (Apple/Google) | Auth Service | `auth_sso_verify` | Scenario 1 |
| **FR-1.3** | Private Room generation | Matchmaking API | `room_code_gen_test` | Phase 5 Suite |
| **FR-1.4** | Friends List | Social Graph API | `friend_graph_sync` | Phase 5 Suite |
| **FR-2.1** | Active players count (1v1, 2-4t) | Live WS Match Gateway | `player_capacity_limits` | Phase 5 Suite |
| **FR-2.2** | Live MMR Matchmaking | Matchmaking Queue Worker| `mmr_bucket_routing` | Scenario 6 |
| **FR-2.3** | Async Matchmaking | Matchmaking Queue Worker| `async_queue_routing` | Scenario 4 |
| **FR-2.4** | AI Practice Matches | Practice Bot Engine | `bot_instantiation_test` | Scenario 1 |
| **FR-3.1a**| Shuffled Deck generation (with wilds) | Core State Engine | `deck_seed_composition` | Phase 5 Suite |
| **FR-3.1b**| Deal 9 letters | Core State Engine | `initial_hand_alloc` | Phase 5 Suite |
| **FR-3.1c**| Reveal 1 discard | Core State Engine | `initial_discard_alloc` | Phase 5 Suite |
| **FR-3.2** | Validate against Dictionary Context | Lexicon Service | `lexicon_validation_layer` | Scenario 2 |
| **FR-3.3** | Strict Capture Validation | Core Rules Engine | `capture_morph_eval` | Scenario 2 |
| **FR-3.4** | Wildcard assignment and locking | Core Rules Engine | `wildcard_mutation_lock` | Scenario 2 |
| **FR-3.5** | Exact Turn sequencing | Core State Engine | `turn_sequence_sm` | Scenario 7 |
| **FR-4.1** | Length-based scoring calculation | Score Engine | `score_math_base` | Scenario 5 |
| **FR-4.2** | +2 point capture bonus | Score Engine | `score_math_capture` | Scenario 2 |
| **FR-4.3** | -1 point remaining letter penalty | Score Engine | `score_penalty_eval` | Scenario 7 |
| **FR-4.4** | Timer expiry behaviors | Match Timeout Worker | `timer_expiry_eval` | Scenario 6 |
| **FR-5.1** | Rule modifier payloads | Mod Payload Engine | `mod_application` | Scenario 5 |
| **FR-5.2** | Modifier precedence | Mod Payload Engine | `mod_stacking_logic` | Scenario 5 |
| **FR-6.1** | Lineage log history parsing | Match History DB | `lineage_playback` | Scenario 2 |
| **FR-6.2** | Capture ownership transfer | Match State Memory | `ownership_swap` | Scenario 2 |
| **FR-7.1** | Async push triggers | Notification Gateway | `push_dispatch` | Scenario 4 |
| **FR-7.2** | Match completion push | Notification Gateway | `push_dispatch` | Phase 5 Suite |
| **FR-8.1** | Admin lexicon versions | Admin CMS | `admin_lex_upload` | Phase 5 Suite |
| **FR-8.2** | Admin blocklist | Admin CMS | `admin_block_update` | Phase 5 Suite |
| **FR-9.1** | Ranked idempotent results | Result Ledger | `ledger_idempotency` | Scenario 6 |
| **FR-9.2** | Rematch distinct IDs | Matchmaking API | `rematch_generation` | Scenario 6 |
| **FR-9.3** | Bo3 aggregations | Result Ledger | `bo3_aggregate` | Phase 5 Suite |
| **NFR-1.1**| p95 live move ≤ 150ms | Live Gateway | `load_latency_test` | Phase 5 Suite |
| **NFR-1.2**| p95 client ack ≤ 400ms | Client Sync Layer | `client_ack_test` | Phase 5 Suite |
| **NFR-1.3**| Reconnect restore ≤ 3s | Sync Payload | `reconnect_time_test`| Scenario 3 |
| **NFR-1.4**| Push emission ≥ 98% | Notification Gateway | `push_delivery_rate` | Scenario 4 |
| **NFR-1.5**| Deep-link match open ≥ 98%| Client Routing Layer | `deep_link_eval` | Scenario 4 |
| **NFR-1.6**| State divergence rate = 0 | Client Sync Layer | `state_hash_eval` | Scenario 3 |
| **NFR-2.1**| Timer continues during disconnect| Server Timer Core| `timer_network_drop` | Scenario 3 |
| **NFR-2.2**| Deterministic background resume| Core State Engine | `resume_sync_playback` | Scenario 4 |
| **NFR-3.1**| Client blindness to deck | Schema Definition | `schema_blindness` | Phase 5 Suite |
| **NFR-3.2**| Double-submit idempotency keys| API Layer | `idempotency_eval` | Scenario 6 |
