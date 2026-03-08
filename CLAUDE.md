<!-- BEGIN ADE MANAGED — do not edit this section -->

# Claude Workflow (ADE) — Machine Instructions

## Quick Start

- **Current Work**: Read `.claude/docs/PLAN.md`
- **Last Session**: Read `.claude/docs/HANDOFF.md`
- **Reference** (read on demand): `PROJECT_BRIEF.md`, `.claude/docs/ARCHITECTURE.md`, `WORKFLOW.md`

## Role Commands

| Command            | Agent        | Behavior                                                                                                                                       |
| ------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `Act as Architect` | architect.md | Planning mode. Reads codebase, produces PLAN.md with phased implementation. Never writes code.                                                 |
| `Act as Builder`   | builder.md   | Implementation mode. Follows PLAN.md exactly, one phase at a time. TDD mandatory. Escalates at thresholds (2 compile errors, 3 test failures). |
| `Act as QA`        | /verify      | Runs 12-step QA pipeline via verify/SKILL.md + qa_runner.py. Reports issues, does not fix them.                                                |
| `Act as Librarian` | librarian.md | Documentation mode. Updates knowledge base, decisions, handoffs.                                                                               |

## Hooks (Always Active)

6 Python hooks enforce quality gates automatically. See `.claude/docs/ARCHITECTURE.md` → Hooks section for full details.
Edit/write → auto-format + prod scan → run tests → verify gate on stop. Configuration in `.claude/workflow.json`.

See `.claude/rules/production-standards.md` for code standards, data classification, and precedence rules (auto-loaded when code files are touched).

## Non-Negotiables

1. **No secrets in code** — Use environment variables via `.env`
2. **No unverified changes** — Tests must pass before commit
3. **No scope creep** — If it's not in `.claude/docs/PLAN.md`, don't build it
4. **Conventional commits** — `feat:`, `fix:`, `docs:`, `chore:`
5. **Safety first** — Destructive commands require confirmation

## Git Workflow

- **Feature branches**: Ralph creates `ralph/[plan-name]` branch before any story work
- **All commits to feature branch**: Story commits NEVER go directly to main or master
- **Worktree isolation**: Each sub-agent works in its own git worktree — failed work never touches the feature branch. Successful work is merged via `git merge --no-ff`
- **Merge conflict recovery**: `git merge --abort` on conflict, treated as FAIL with auto-retry
- **Selective staging**: Sub-agents use explicit file paths in `git add` (NEVER `git add -A` or `git add .`). Only source code, test files, and documentation are staged. `.claude/` state files are never staged
- **PR creation**: At session end, Ralph offers `gh pr create` with auto-generated summary

See `.claude/docs/ARCHITECTURE.md` → File Organization for the commit/ignore table.

## When Stuck

If blocked for 3+ attempts on the same issue:

1. Run `/learn` to document what was tried
2. Ask for guidance with specific context
3. Do NOT compound errors with more attempts

## MCP Servers

**Global** (always on): `github`, `context7`. **Project** (disabled by default): `trello` — enable in `.claude/settings.local.json` by removing from `disabledMcpjsonServers`.

## Environment

Hooks are configured per-project in `.claude/settings.json`.
Required environment variables are documented in `PROJECT_BRIEF.md`.

<!-- END ADE MANAGED -->

<!-- Project-specific instructions below this line -->

## Project: WIT V2

Multiplayer word strategy card game — server-authoritative architecture with polyglot backend (Node.js + Go).

### Architecture Overview

- **Client**: React Native (Expo) + Zustand + Reanimated
- **Meta API**: Node.js/TypeScript — REST endpoints for auth, social, matchmaking, admin
- **Game Server**: Go — WebSocket connections for live match state, server-authoritative validation
- **Schema**: Single canonical Protobuf repo shared by Node.js and Go (prevents polyglot drift)
- **Database**: PostgreSQL (durable state) + Redis (ephemeral matchmaking queues only)
- **Infrastructure**: AWS ECS Fargate, NLB (WebSocket), ALB (REST), RDS, ElastiCache

### Critical Design Rules

1. **Server-authoritative**: The client NEVER has access to deck order or performs game validation. All word validation, scoring, and state transitions happen server-side.
2. **Protobuf-first**: All shared types must be defined in the canonical Protobuf repo. Do not duplicate type definitions across Node.js and Go.
3. **Dictionary context**: Word validation requires the full context: Lexicon Version + Banned-Word Overlay + Playlist Rule Filters + Root/Morphology Policies. Matches are locked to lexicon version at creation.
4. **Idempotency**: All mutative client actions (PLAY, CAPTURE, DISCARD) require a UUIDv4 idempotency key. Server deduplicates within 60s window per Match UUID.
5. **State machine**: Match lifecycle follows 10 explicit states (see `gameplay_state_machine_spec.md`). No implicit transitions.
6. **Turn sequencing**: Strict order — Draw -> Play/Capture -> End turn (discard or manual complete). Out-of-sequence actions are rejected.
7. **Monorepo structure**: All code lives in the monorepo structure: apps/, services/, packages/, infra/, docs/, tools/. No code outside these directories.
8. **Parallel lane awareness**: Work is organized into 5 parallel lanes (Platform, Mobile Shell, Gameplay Core, Design/Content, QA Automation). Stories in the same parallelGroup can be built simultaneously. Stories must declare dependsOn correctly.
9. **Phase gate enforcement**: No phase N+1 work begins until phase N exit gate is met. Exit gates are defined in docs/PLAN.md per phase.
10. **Contract-first development**: Any new service boundary requires Protobuf schema definition in packages/contracts/ BEFORE implementation. Generated types must be used — no hand-rolled duplicates.
11. **Deterministic replay**: Every gameplay state mutation must be logged with sequence_id and state_hash. If replay reconstruction diverges from live state, that is a P0 bug.
12. **Dictionary immutability per match**: Once a match starts, its lexicon_version is frozen. Mid-match dictionary updates are forbidden.

### Monorepo Structure

```
wit-v2/
  apps/
    mobile/          # React Native (Expo) client
    admin-web/       # Internal admin dashboard
  services/
    meta-api/        # Node.js/TS — auth, profiles, matchmaking, admin
    game-server/     # Go — WebSocket, authoritative game state
    notification-worker/  # Push notifications
    matchmaking-worker/   # Queue processing
    ranked-ledger-worker/ # Ranked result processing
  packages/
    contracts/       # Canonical Protobuf schemas (single source of truth)
    shared-types/    # Generated types from Protobuf
    telemetry-schema/ # Analytics event definitions
    ui-kit/          # Shared React Native components
    game-fixtures/   # Golden test fixtures for gameplay
  infra/             # Terraform/CDK, ECS, RDS, Redis configs
  docs/              # GDD, SRS, RTM, specs, ADRs, runbooks
  tools/             # Load test, replay runner, simulation
```

### Build Phase Rules

- **Phase 0-1**: Documentation and spec freeze only. No feature code.
- **Phase 2**: System architecture and LLD. DB schema design. No feature code.
- **Phase 3**: Platform foundations. Auth skeleton, CI/CD, observability. First E2E handshake.
- **Phase 4**: Deterministic gameplay core. DEEPEST test coverage. Property tests mandatory.
- **Phase 5**: Live duel vertical slice. First playable E2E.
- **Phase 6+**: Async, ranked, tutorial, progression, hardening, launch.

### Parallel Work Lanes

Stories are assigned to parallel lanes. Within a lane, stories execute sequentially. Across lanes, stories with no dependencies execute in parallel via Ralph's parallelGroup mechanism.

| Lane | Pod | Owns |
|------|-----|------|
| A — Platform | Pod B | infra, auth, profiles, CI/CD, telemetry, admin auth |
| B — Mobile Shell | Pod C | navigation, home screens, auth shell, match screen scaffold |
| C — Gameplay Core | Pod A | rules engine, scoring, capture, wildcard, replay |
| D — Design/Content | Pod D | UI kit, tutorial content, modifier catalog, cosmetics |
| E — QA Automation | Pod D | fixtures, synthetic matches, replay harness, contract checks |

### Non-Negotiable Acceptance Gates

These are release blockers. Reference them in every /plan:

- **Gate A — Gameplay correctness**: 100% pass on rules regression, 0 state divergence in replay corpus
- **Gate B — Reconnect integrity**: restore ≤ 3s, timer never freezes during disconnect
- **Gate C — Ranked integrity**: 0 duplicate result writes, best-of-3 emits one result only
- **Gate D — Async integrity**: deep-link success ≥ threshold, lexicon frozen across async matches
- **Gate E — Operational stability**: crash-free ≥ target, move validation p95 ≤ target
- **Gate F — New-user viability**: tutorial completion rate healthy

### Spec Documents (read on demand)

- `docs/gdd/game_design_document.md` — Full GDD
- `docs/srs/software_requirements_specification.md` — FR/NFR definitions
- `docs/tech_stack_proposal.md` — Technology choices
- `docs/state-machine/gameplay_state_machine_spec.md` — 10-state match lifecycle
- `docs/specs/api_event_contract_spec.md` — Protobuf governance, WebSocket contracts
- `docs/specs/dictionary_governance_spec.md` — Lexicon versioning, banned-word policy
- `docs/specs/operational_slo_sli_spec.md` — SLOs
- `docs/rtm/requirements_traceability_matrix.md` — FR/NFR -> test mapping
- `docs/user_acceptance_test_plan.md` — 7 UAT scenarios
- `docs/specs/authoritative_score_rules.md` — Exact scoring math
- `docs/specs/turn_legality_matrix.md` — Every legal/illegal action combo
- `docs/specs/replay_determinism_spec.md` — Replay logging and reconstruction
- `docs/specs/telemetry_event_taxonomy.md` — All analytics events
- `docs/specs/abuse_moderation_policy.md` — Moderation rules and penalties
- `docs/specs/test_architecture_plan.md` — Test strategy per requirement category
- `docs/PLAN.md` — Master build plan (12 phases + milestones)

### Current Phase

Phase 1 (Requirements Analysis) near completion. All spec documents created. Next: Phase 1 Freeze signoff, then Phase 2 System Design.

### workflow.json Language Configuration Note

The `.claude/workflow.json` file currently only contains Python language configuration. When Go and TypeScript code is introduced (Phase 3+), update workflow.json to add language configs for Go and TypeScript alongside the existing Python config. This ensures hooks (formatting, linting, test runners) apply correctly to polyglot code.
