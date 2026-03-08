# Project Brief — WIT V2

## What This Is

Server-authoritative global multiplayer word strategy card game. Players draw letter tiles, form words, and capture opponents' words to score points. Supports live 1v1 ranked, casual 2-4 player, and asynchronous game modes with Best-of-3 formats.

## Tech Stack

| Layer            | Technology                | Version |
| ---------------- | ------------------------- | ------- |
| Client           | React Native (Expo)       | TBD     |
| Client State     | Zustand                   | TBD     |
| Client Animation | React Native Reanimated   | TBD     |
| Meta API         | Node.js (TypeScript)      | TBD     |
| Game Server      | Go (Golang)               | TBD     |
| Database         | PostgreSQL (RDS)          | TBD     |
| Cache            | Redis (ElastiCache)       | TBD     |
| Schema           | Protobuf (canonical repo) | TBD     |
| Infrastructure   | AWS ECS Fargate           | —       |
| IaC              | Terraform or AWS CDK      | TBD     |

## External Dependencies

| Service             | Purpose                                | Documentation |
| ------------------- | -------------------------------------- | ------------- |
| AWS ECS             | Container orchestration                |               |
| AWS NLB             | WebSocket ingress (Go servers)         |               |
| AWS ALB             | REST API ingress (Node.js)             |               |
| AWS RDS             | PostgreSQL managed hosting             |               |
| ElastiCache         | Redis managed hosting                  |               |
| Sentry              | Crash/error reporting (mobile+backend) |               |
| Datadog             | Observability / OpenTelemetry          |               |
| LaunchDarkly        | Feature flags                          |               |
| APNs / FCM          | Push notifications                     |               |
| EAS Build           | React Native CI/CD pipeline            |               |
| AWS Secrets Manager | Secrets management                     |               |

## Key Constraints

- **Server-authoritative**: Client never sees deck order; all validation server-side
- **Polyglot boundary**: Node.js (meta/REST) + Go (game/WebSocket) — single canonical Protobuf repo prevents schema drift
- **Dictionary immutability**: Matches lock to lexicon version at creation; mid-match updates forbidden
- **Zero state divergence**: NFR-1.6 mandates 0% desync rate for committed moves
- **p95 latency**: Live move validation <= 150ms at server ingress, client ack <= 400ms
- **Idempotency**: All mutative client actions require UUIDv4 idempotency keys with 60s dedup window

## Current Focus

> **Active Work**: Phase 1 Complete — all spec documents created and reviewed
> **Target Milestone**: Phase 2 System Design (architecture document, database schema, ingress/WebSocket routing)
> **Last Updated**: 2026-03-08

## Spec Documents

| Document                                 | Purpose                                                     |
| ---------------------------------------- | ----------------------------------------------------------- |
| `software_requirements_specification.md` | FR/NFR definitions (FR-1 through FR-9, NFR-1 through NFR-3) |
| `tech_stack_proposal.md`                 | Technology choices and rationale                            |
| `gameplay_state_machine_spec.md`         | 10-state authoritative match lifecycle                      |
| `api_event_contract_spec.md`             | Protobuf governance, WebSocket payloads, idempotency        |
| `dictionary_governance_spec.md`          | Lexicon versioning, banned-word policy, admin audit         |
| `operational_slo_sli_spec.md`            | SLOs: match integrity, latency, reliability targets         |
| `requirements_traceability_matrix.md`    | FR/NFR -> design component -> test case -> UAT mapping      |
| `user_acceptance_test_plan.md`           | 7 UAT scenarios for Phase 5 execution                       |
| `task.md`                                | SDLC phase tracker (Phases 1-6)                             |

## Quick Commands

```bash
# Start a session
claude
/health

# Plan a feature
/plan

# Run Ralph orchestrator
/ralph

# Run audit
/audit

# Full pipeline (plan -> build -> audit -> handoff)
/build-system {slug}
```

## Monorepo Structure

```
Card-Game/
├── apps/
│   ├── mobile/          # React Native (Expo) client
│   ├── meta-api/        # Node.js/TypeScript REST API
│   └── game-server/     # Go WebSocket game server
├── packages/
│   └── proto/           # Canonical Protobuf definitions
├── infra/               # Terraform / AWS CDK
├── docs/                # Spec documents
├── PROJECT_BRIEF.md
├── task.md
└── .gitignore
```

## Environment Setup

```bash
# Phase 1-2: No runtime dependencies required (spec & design only)
# Starting Phase 3 (Implementation), the following will be needed:
#   - Node.js (LTS)       — Meta API + client tooling
#   - Go (latest stable)  — Game server
#   - Expo CLI             — React Native builds
#   - PostgreSQL           — Primary database
#   - Redis                — Matchmaking queues / ephemeral cache
#   - Protobuf / Buf CLI   — Schema compilation & linting
# Environment variables will be documented once Phase 2 infrastructure design is complete.
```

## Team Contacts

- **Owner**:
- **Repository**: github.com/bobbypolo/Card-Game
