# WIT V2 — System Architecture

> Auto-detected from project specs and PLAN.md. Updated 2026-03-08.

## System Overview

WIT V2 is a server-authoritative, deterministic, mobile-first word strategy card game with live 1v1, ranked 1v1, async 1v1, private rooms, tutorial, and bot practice modes.

## Service Topology

```
┌─────────────────────────────────────────────────────┐
│                    CLIENTS                           │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ Mobile (RN)  │  │ Admin Web    │                 │
│  │ (Expo)       │  │ (React)      │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
└─────────┼──────────────────┼────────────────────────┘
          │ REST + WS        │ REST
          ▼                  ▼
┌─────────────────────────────────────────────────────┐
│                   INGRESS LAYER                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │  ALB (REST)  │  │  NLB (WS)   │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
└─────────┼──────────────────┼────────────────────────┘
          ▼                  ▼
┌──────────────────┐ ┌──────────────────┐
│   meta-api       │ │  game-server     │
│   (Node.js/TS)   │ │  (Go)            │
│                  │ │                  │
│ - Auth           │ │ - WS sessions    │
│ - Profiles       │ │ - Match state    │
│ - Friend graph   │ │ - Turn validation│
│ - Room creation  │ │ - Timers         │
│ - Matchmaking    │ │ - Reconnect      │
│   tickets        │ │ - Score calc     │
│ - Async inbox    │ │ - Replay logging │
│ - Cosmetic inv   │ │ - State broadcast│
│ - Admin auth     │ │                  │
└────────┬─────────┘ └────────┬─────────┘
         │                    │
         ▼                    ▼
┌──────────────────────────────────────────────────────┐
│                    DATA LAYER                         │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │  PostgreSQL   │  │  Redis        │                 │
│  │  (RDS)        │  │  (ElastiCache)│                 │
│  │              │  │              │                  │
│  │ - Users      │  │ - Matchmaking│                  │
│  │ - Matches    │  │   queues     │                  │
│  │ - Actions    │  │ - Session    │                  │
│  │ - Rankings   │  │   cache      │                  │
│  │ - Inventory  │  │ - Rate limit │                  │
│  └──────────────┘  └──────────────┘                  │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│                    WORKERS                            │
│  ┌─────────────────┐ ┌─────────────────┐             │
│  │ notification    │ │ matchmaking     │             │
│  │ worker          │ │ worker          │             │
│  ├─────────────────┤ ├─────────────────┤             │
│  │ ranked-ledger   │ │ async-timeout   │             │
│  │ worker          │ │ worker          │             │
│  ├─────────────────┤ ├─────────────────┤             │
│  │ moderation      │ │                 │             │
│  │ audit worker    │ │                 │             │
│  └─────────────────┘ └─────────────────┘             │
└──────────────────────────────────────────────────────┘
```

## Match State Machine (10 States)

```
LOBBY → MATCH_FOUND → DEALING → ACTIVE_TURN → SUBMISSION_PENDING
  → TURN_COMMITTED → (next turn: ACTIVE_TURN | ROUND_COMPLETE)
  → ROUND_COMPLETE → (next round: DEALING | MATCH_COMPLETE)
  → MATCH_COMPLETE → RESULT_PERSISTED

  RECONNECT_GRACE can be entered from ACTIVE_TURN or SUBMISSION_PENDING
```

See `docs/state-machine/gameplay_state_machine_spec.md` for full specification.

## Data Model (Core Tables)

| Table | Owner | Purpose |
|-------|-------|---------|
| users | meta-api | Account identity |
| guest_accounts | meta-api | Anonymous guest sessions |
| auth_bindings | meta-api | OAuth/social login bindings |
| friendships | meta-api | Friend graph |
| matches | game-server | Match metadata |
| match_rounds | game-server | Round state per match |
| match_players | game-server | Player seats |
| match_actions | game-server | Deterministic action log |
| lineage_entries | game-server | Word transformation chains |
| ranked_results | ranked-ledger | Idempotent match results |
| mmr_ratings | ranked-ledger | Hidden MMR + visible rank |
| async_turn_deadlines | meta-api | Async turn timers |
| notifications | notification-worker | Push notification log |
| lexicon_versions | meta-api | Dictionary version registry |
| banned_word_overlays | meta-api | Per-version banned words |
| admin_audit_log | meta-api | Admin action audit trail |
| inventory_items | meta-api | Cosmetic inventory |
| profile_cosmetics | meta-api | Equipped cosmetics |
| tutorial_progress | meta-api | Tutorial step completion |
| quest_progress | meta-api | Daily/weekly quest state |
| abuse_reports | meta-api | Player reports |

## Contract Layer

- **Protobuf schemas** in `packages/contracts/` — single source of truth
- Generated types for Go (game-server), TypeScript (meta-api + mobile), via `buf generate`
- All WebSocket messages use Protobuf binary encoding
- All REST API responses use JSON (with Protobuf-defined schemas for validation)
- Event versioning: `v{major}` prefix on message types

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Game server language | Go | Low-latency WebSocket handling, goroutine concurrency |
| Meta API language | Node.js/TypeScript | Fast iteration for CRUD, rich ecosystem |
| Schema format | Protobuf | Cross-language type safety, prevents drift |
| State machine | Server-authoritative | Anti-cheat, deterministic replay |
| Match transport | WebSocket (binary) | Low-latency bidirectional for live play |
| Database | PostgreSQL | ACID for ranked results, rich querying |
| Cache | Redis | Ephemeral matchmaking queues, session cache |
| Mobile framework | React Native (Expo) | Cross-platform, OTA updates |
| Infrastructure | AWS ECS Fargate | Managed containers, autoscaling |

## File Organization

### Committed to Git
- Source code (apps/, services/, packages/)
- Documentation (docs/)
- Infrastructure as code (infra/)
- Test files and fixtures
- Configuration files (package.json, go.mod, etc.)
- .claude/ agents, skills, hooks, rules, templates

### NOT Committed
- .claude/.workflow-state.json
- .claude/runtime/
- .claude/errors/
- .env files
- node_modules/, vendor/
- Build artifacts (dist/, build/)
- .terraform/, *.tfstate

## Hooks

6 Python hooks enforce quality gates (defined in `.claude/settings.json`):

| Hook | Trigger | Purpose |
|------|---------|---------|
| post_compact_restore.py | SessionStart | Restore state after context compaction |
| pre_bash_guard.py | PreToolUse (Bash) | Block destructive commands |
| post_bash_capture.py | PostToolUse (Bash) | Capture command outputs |
| post_format.py | PostToolUse (Edit/Write) | Auto-format on save |
| post_write_prod_scan.py | PostToolUse (Edit/Write) | Production code scan |
| stop_verify_gate.py | Stop | Verify gate on session end |
