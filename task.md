# WIT V2 SDLC Tasks

## Phase Governance Rules
All phases require formal Entry and Exit conditions.
- **Entry Gate:** All prerequisite documents approved.
- **Exit Gate:** 100% traceability coverage, 0 blocking unresolved spec ambiguities.
- **Approval Authority:** Executive Sponsor / Lead Architect.
- **Master Build Plan:** See `docs/PLAN.md` for the full 12-phase roadmap.

---

## Phase 0: Program Setup & Freeze
**Inputs:** Game Design Document (Final Draft V2)
**Outputs:** Repo, monorepo structure, environment matrix, scope freeze
**Exit Criteria:** Scope approved, repo exists, team ownership assigned.

- [x] Create GitHub repo (bobbypolo/Card-Game)
- [x] Initialize monorepo directory structure (apps/, services/, packages/, infra/, docs/, tools/)
- [x] Set up ADE workflow framework (.claude/ agents, hooks, skills, rules)
- [x] Configure polyglot workflow.json (Python, Go, TypeScript, Protobuf)
- [x] Create .claude/docs/ARCHITECTURE.md
- [ ] User Approval of Phase 0 Freeze

---

## Phase 1: Requirements Analysis (Current)
**Inputs:** Final Draft V2 GDD
**Outputs:** Approved SRS, UAT Plan, Tech Stack, RTM, Core Specs, Engineering Specs
**Exit Criteria:** All FR/NFRs uniquely identified, 100% RTM coverage, Canonical Schema & State Machine drafted, No P1/P2 spec ambiguities, all 6 engineering specs complete.

- [x] Initial Requirements Drafts (SRS, UAT, Tech Stack)
- [x] Refined Traceability and Specs (RTM, State Machine, API Contracts, Dictionary Governance, SLOs)
- [x] Final Tightening (State Machine Invariants, Full RTM, SLO Windows, Lexicon Governance)
- [x] Authoritative Score Rules Document
- [x] Turn Legality Matrix
- [x] Replay Determinism Spec
- [x] Telemetry Event Taxonomy
- [x] Abuse & Moderation Policy
- [x] Test Architecture Plan
- [ ] User Approval of Phase 1 Freeze (Formal Signoff)

---

## Phase 2: System Architecture & Low-Level Design
**Inputs:** Phase 1 Approved Package
**Outputs:** System Architecture Document, DB Schema, API/WS Contracts, Mobile Nav Map, Design System, ADRs
**Exit Criteria:** Architecture review signed off, no unresolved "major later decisions."

- [ ] Define exact service boundaries (meta-api, game-server, workers)
- [ ] Database schema design (20+ core tables)
- [ ] REST endpoint contract package
- [ ] WebSocket message schema package
- [ ] Define error codes and idempotency semantics
- [ ] Reconnect handshake structure
- [ ] Mobile navigation tree and state sync strategy
- [ ] Design system starter spec (typography, tiles, colors, animations)
- [ ] ADRs for major technical decisions
- [ ] User Approval of Phase 2

---

## Phase 3: Platform Foundations
**Inputs:** Phase 2 Approved Package
**Outputs:** Working staging stack, guest auth, mobile shell, backend shell, WS handshake, observability, CI/CD
**Exit Criteria:** Stack integrated end-to-end. Mobile launches, guest auth works, WS connects, telemetry flows.

**Parallel Lanes:**
- [ ] **Lane A (Platform):** CI/CD, Terraform/CDK, Postgres/Redis/ECS provisioning, auth skeleton, profile CRUD
- [ ] **Lane B (Mobile):** Expo app init, auth shell, lobby shell, nav, feature flags, telemetry, push scaffold
- [ ] **Lane C (Game Server):** Go server skeleton, match lifecycle shell, in-memory sessions, WS model, contracts
- [ ] **Lane E (QA):** Lint/test/build pipelines, contract test pipeline, deployment verification
- [ ] First E2E milestone: guest enters, fetches profile, connects WS, creates dummy match, events flow
- [ ] User Approval of Phase 3

---

## Phase 4: Deterministic Gameplay Core
**Inputs:** Phase 3 approved stack
**Outputs:** Production-grade gameplay library, replay runner, test fixtures, golden match corpus
**Exit Criteria:** All core UAT gameplay scenarios pass, replay reconstructs exactly, 0 state divergence.

- [ ] Match state model (metadata, round, hands, stock, discard, word zones, timers, modifiers)
- [ ] Deck and dealing engine (composition versioning, shuffle, wild cards, 9-letter deal)
- [ ] Turn state machine (10 states with transitions)
- [ ] Dictionary context engine (lexicon lock, banned-word overlay, playlist filters)
- [ ] Play legality engine (draw, hand, discard, word validity, capture, wildcard, multi-word)
- [ ] Scoring engine (base table, capture bonus, modifiers, penalties, tiebreaks)
- [ ] Lineage/replay engine (chains, deltas, ownership, sequence_id, state hash, reconstruction)
- [ ] Property tests (no illegal mutation, no duplicate cards, no stock leak, deterministic rebuild)
- [ ] Scenario tests (TOP→STOP, wildcards, invalid plurals, stock exhaustion, timeout, multi-word)
- [ ] User Approval of Phase 4

---

## Phase 5: Live Duel Vertical Slice
**Inputs:** Phase 4 gameplay core
**Outputs:** Internal playable live 1v1 E2E
**Exit Criteria:** Internal team plays full matches without admin help.

- [ ] Live match session lifecycle + timers
- [ ] Turn submission, rejection, broadcast
- [ ] Reconnect grace flow
- [ ] Casual live queue + matchmaking
- [ ] Match found → seat assignment → result persistence
- [ ] Mobile match screen (hand, stock/discard, word zones, timer, score, preview, submit/undo)
- [ ] Capture targeting and turn transition rendering
- [ ] User Approval of Phase 5

---

## Phase 6: Async, Notifications, Resilience
**Inputs:** Phase 5 live duel
**Outputs:** Full async loop, push notifications, async inbox, deadline enforcement, deep-link routing
**Exit Criteria:** UAT Scenario 4 passes repeatedly under staging.

- [ ] Async engine (creation, deadlines, inbox, resume, lexicon lock)
- [ ] Notification system (APNs/FCM, worker, delivery logging, deep-links, retries)
- [ ] Mobile async inbox + match restore + notification tap handling
- [ ] Reliability (deadline expiry, forfeit rules, push fallback, re-open consistency)
- [ ] User Approval of Phase 6

---

## Phase 7: Ranked, Social, Private Rooms
**Inputs:** Phase 6 async complete
**Outputs:** Ranked duel, MMR pipeline, private rooms, friend graph, report system
**Exit Criteria:** Ranked writes are idempotent and auditable.

- [ ] Ranked system (MMR, tiers, ledger, best-of-3, season, anti-dodge)
- [ ] Social (friends, recent opponents, invite, rematch)
- [ ] Private rooms (code gen, join, ready, playlist, rules toggle)
- [ ] Competitive integrity (pattern logging, detection, report, evidence storage)
- [ ] User Approval of Phase 7

---

## Phase 8: Tutorial, Bots, Onboarding
**Inputs:** Phase 7 ranked/social
**Outputs:** Tutorial flow, bot match mode, new player protection
**Exit Criteria:** New users complete tutorial → play bot → enter casual without confusion.

- [ ] Tutorial (5 scripted lessons: word, draw/discard, capture, round end, modifier)
- [ ] Bot practice (beginner, standard, advanced tiers)
- [ ] New player protection (matchmaking bucket, tutorial gate, hints, loss framing)
- [ ] User Approval of Phase 8

---

## Phase 9: Progression, Cosmetics, Admin, Live Ops
**Inputs:** Phase 8 onboarding
**Outputs:** XP/profile, cosmetics, admin CMS, live-ops config
**Exit Criteria:** Ops can change lexicon blocklists and modifiers without code deploy.

- [ ] Progression (account level, XP, quests, unlocks)
- [ ] Cosmetics/shop (card backs, themes, frames, store, entitlements)
- [ ] Admin tools (lexicon publish, banned words, username mod, reports, audit log)
- [ ] Live ops (feature flags, modifier rotation, season config, quest config)
- [ ] User Approval of Phase 9

---

## Phase 10: Full Verification & Hardening
**Inputs:** Phase 9 feature complete
**Outputs:** Hardening report, exploit report, load/soak benchmarks, release candidate
**Exit Criteria:** Release SLOs satisfied.

- [ ] Component verification (unit, property, API, contract, screen tests)
- [ ] Integration tests (app↔meta, app↔game, game↔PG, workers↔queues)
- [ ] System tests (full match, reconnect, queue→rank write, async→push→resume)
- [ ] Load tests (match spikes, WS concurrency, timer storms, write spikes, push fanout)
- [ ] Soak tests (bot matches, reconnects, extended async, memory/CPU observation)
- [ ] Chaos tests (kill node, Redis restart, PG failover, worker outage, packet delay)
- [ ] Security/exploit tests (JWT, spoofing, tampering, flooding, info leak, double-write)
- [ ] Store/release readiness (App Store/Play compliance, privacy, age rating)

---

## Phase 11: Soft Launch & Stabilization
**Inputs:** Phase 10 release candidate
**Outputs:** Telemetry dashboard, balance patch, onboarding patch

- [ ] Region-limited or invite-only launch
- [ ] Weekly review loop (telemetry, exploits, dictionary, balance)
- [ ] Bug patches and stabilization

---

## Phase 12: Global Launch
**Inputs:** Phase 11 stabilized
**Outputs:** Production-scale operations

- [ ] Incident on-call rotation
- [ ] Rollback plan and hotfix process
- [ ] Season 1 content plan
- [ ] KPI dashboards (D1/D7/D30)
- [ ] Post-launch roadmap
