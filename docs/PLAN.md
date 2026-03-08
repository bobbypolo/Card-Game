WIT V2 — End-to-End Greenfield Build Plan
0. North Star

The goal is not merely “a working prototype.”

The goal is:

a server-authoritative, deterministic, mobile-first, globally playable word strategy card game with:

live 1v1 casual

live 1v1 ranked

async 1v1

private rooms

tutorial

bot practice

capture visualization

lineage/replay

progression basics

moderation and lexicon governance

analytics and operational observability

enough hardening to survive real users

For honesty: “completely stable” in software means stable against defined SLOs and acceptance gates, not “nothing will ever break.”

1. Build Strategy
1.1 Delivery philosophy

WIT V2 should be built with four rules:

Rule 1 — 1v1 is the critical path

Do not build 2–4 player complexity first. The whole roadmap should optimize for:

live 1v1

ranked 1v1

async 1v1

Everything else expands from there.

Rule 2 — Server-authoritative gameplay from day one

Do not make a client-trusting prototype and “fix it later.”

Authoritative server logic must own:

deck generation

hand contents

turn legality

dictionary validation

score calculation

timers

result writes

ranking updates

Rule 3 — Determinism is a first-class requirement

Every committed match action must be replayable from logs. That is what enables:

reconnect recovery

anti-cheat review

lineage replay

debugging

UAT verification

production incident investigation

Rule 4 — Continuous vertical integration

Every week, there must be a build where:

client connects to real backend

backend talks to real DB/cache

game server validates real turns

analytics emit real events

No long-lived “UI only” or “backend only” branches without integration.

2. Recommended Team Structure

Assuming you want the fastest practical build with parallel work, this is the right structure.

2.1 Core pods
Pod A — Gameplay Core

Owns:

authoritative rules engine

state machine

scoring

capture logic

wildcard logic

lineage/replay

bot logic

Roles:

Gameplay Tech Lead

Go engineer

backend/gameplay engineer

QA automation partner

Pod B — Meta Backend / Platform

Owns:

auth

profiles

matchmaking

ranked ledger

async orchestration

notifications

admin tooling

moderation services

Roles:

Backend Lead

Node/TypeScript engineer

platform engineer

DB/data engineer

Pod C — Mobile Client

Owns:

React Native app

screen flows

match UI

tutorial UX

capture animations

push/deep-link handling

progression/shop/profile UI

Roles:

Mobile Lead

RN engineer

UI engineer

motion/interaction designer

Pod D — Quality / Release / Observability

Owns:

CI/CD

test harnesses

synthetic match runners

telemetry

load/soak

release pipelines

incident tooling

Roles:

QA automation engineer

DevOps/SRE engineer

analytics engineer

2.2 Product/Design layer

Owns:

GDD integrity

SRS/RTM governance

UAT governance

economy/cosmetics guardrails

moderation policy

balance tuning

Roles:

Product owner

game designer

UX designer

producer/project manager

3. Repo and System Structure
3.1 Start greenfield in a new repo

This should be built in a new greenfield codebase, not inside a messy or broken existing app folder.

3.2 Recommended repo layout

A single monorepo is the fastest choice here.

wit-v2/
  apps/
    mobile/
    admin-web/
  services/
    meta-api/
    game-server/
    notification-worker/
    matchmaking-worker/
    ranked-ledger-worker/
  packages/
    contracts/
    shared-types/
    telemetry-schema/
    ui-kit/
    game-fixtures/
  infra/
    terraform/
    ecs/
    rds/
    redis/
    datadog/
    sentry/
  docs/
    gdd/
    srs/
    rtm/
    state-machine/
    runbooks/
    adr/
  tools/
    load-test/
    replay-runner/
    simulation/
3.3 Canonical contract policy

Your earlier contract decision is correct: one authoritative schema layer.

Use:

Protobuf + Buf for network/event contracts

generated types for:

Go server

Node meta services

RN client

This prevents polyglot drift.

4. Macro Roadmap

This is the actual build roadmap.

Phase	Name	Goal
0	Program Setup & Freeze	Lock vision, legal, scope, environments, operating model
1	Requirements & Test Architecture	Freeze SRS/GDD/UAT/RTM and convert to engineering backlog
2	System Architecture & Low-Level Design	Finalize data models, services, contracts, client flows
3	Platform Foundations	Working infra, CI/CD, auth skeleton, observability, base app
4	Deterministic Gameplay Core	Build authoritative rules/state engine and replayability
5	Live Duel Vertical Slice	Internal playable live 1v1 E2E
6	Async, Notifications, Reconnect Hardening	Full async loop and resilience behavior
7	Ranked, Social, Private Rooms	Competitive and social product core
8	Tutorial, Bots, Onboarding	New-user entry and practice systems
9	Progression, Cosmetics, Admin, Live Ops	MVP meta layer and moderation operations
10	Full Verification & Hardening	Performance, soak, UAT, exploit, release gating
11	Soft Launch & Stabilization	Real-user validation and controlled rollout
12	Global Launch Readiness	Scale, content cadence, support, incident readiness
5. Phase-by-Phase Build Plan
Phase 0 — Program Setup & Freeze
Objective

Create a controlled production program before writing feature code.

Work items
Product / Legal

confirm IP/brand rights

decide whether this ships as WIT or spiritual successor

approve launch scope:

live casual 1v1

live ranked 1v1

async 1v1

private room

bot practice

tutorial

explicitly defer:

4-player ranked

guilds

spectator

multi-language

tournament systems

Delivery governance

create product roadmap

create milestone calendar

assign pod ownership

define change control policy

define release train cadence

define severity taxonomy: P0/P1/P2/P3 incidents

Environment strategy

Create:

local

dev

staging

preprod

production

Branching and CI policy

trunk-based or short-lived branches only

all merges gated by:

lint

unit tests

contract tests

build verification

Deliverables

Program Charter

Scope Freeze v1

Environment Matrix

Release Policy

Incident Severity Policy

Ownership Matrix

Exit gate

No feature coding begins until:

scope is approved

rights risk is acknowledged

environments and repo exist

team ownership is assigned

Phase 1 — Requirements & Test Architecture
Objective

Turn your existing docs into buildable engineering requirements with no ambiguity.

Work items
Normalize the documents

Your existing materials are strong, but now they need to become implementation-grade.

Finalize:

GDD

SRS

RTM

UAT scenarios

state machine

lexicon governance

API/event contract governance

SLO/SLI spec

Add the missing engineering artifacts

You still need these:

1. Authoritative score rules document

Must define exact math for:

base word score

capture bonus

modifier precedence

penalty order

tie-break order

rounding policy if ever needed

wild-card scoring behavior

2. Turn legality matrix

Every action combination must be enumerated:

draw stock + play + discard

draw discard + capture + discard

multi-word turn with capture + new word

zero-play turn with discard

illegal sequences

timer expiry auto-actions

3. Replay determinism spec

Must define exactly what gets logged:

match UUID

seed/deck composition version

sequence_id

action payload

resolved state hash

score delta

lineage delta

timer state

lexicon version

modifier version

4. Telemetry event taxonomy

Define every analytics event up front:

app_open

tutorial_started

tutorial_completed

live_queue_entered

live_match_found

turn_submitted

turn_rejected

capture_success

capture_rejected

async_turn_ready_push_sent

reconnect_success

ranked_result_written

match_abandon

purchase_started

purchase_completed

5. Abuse and moderation policy

Need explicit rules for:

usernames

emotes

room abuse

repeated stalling

suspicious solver behavior

collusion signals

alt-account escalation

6. Test architecture plan

Map each requirement to:

unit tests

property tests

contract tests

integration tests

system tests

UAT scenario

load/soak tests

Deliverables

Requirements Freeze Pack

Test Architecture Pack

Telemetry Schema v1

Abuse/Moderation Spec

Gameplay Legality Matrix

Replay Determinism Spec

Exit gate

Every FR/NFR must be test-mapped.
No “we’ll figure that out in implementation.”

Phase 2 — System Architecture & Low-Level Design
Objective

Convert frozen requirements into a detailed system blueprint.

Work items
Service architecture

Define exact service boundaries:

meta-api (Node/TS)

Owns:

auth

profile

friend graph

room creation

matchmaking tickets

async inbox

cosmetic inventory

admin authentication

game-server (Go)

Owns:

live match sessions

active match state

authoritative turn validation

timers

reconnect

state transitions

broadcast patches

deterministic action log generation

Workers

notification worker

matchmaking worker

ranked ledger worker

async timeout worker

moderation audit worker

Data model design

Model the DB now, not later.

Core tables:

users

guest_accounts

auth_bindings

friendships

matches

match_rounds

match_players

match_actions

lineage_entries

ranked_results

mmr_ratings

async_turn_deadlines

notifications

lexicon_versions

banned_word_overlays

admin_audit_log

inventory_items

profile_cosmetics

tutorial_progress

quest_progress

abuse_reports

Contract design

Define:

REST endpoints

WS message schemas

event versioning

error codes

idempotency semantics

reconnect handshake structure

Client architecture

Define:

navigation tree

offline/cache policy

match rendering layers

state synchronization strategy

notification routing

deep-link destinations

feature-flag behavior

analytics wrapper

Art and UX system

Need a design system now:

typography

board layout

letter tile system

word ownership colors

capture animation language

ranked badge system

profile theme system

Deliverables

System Architecture Doc

LLD package per service

DB schema spec

API/WS contract package

Mobile navigation and state map

design system starter spec

ADRs for major technical decisions

Exit gate

Architecture review signed off.
No unresolved “major later decisions.”

Phase 3 — Platform Foundations
Objective

Stand up the production skeleton and prove the stack works E2E.

Parallel workstreams
Pod B / Platform

initialize monorepo

set up CI/CD

set up Terraform/CDK

provision Postgres, Redis, ECS, Datadog, Sentry, Secrets Manager

configure staging environment

implement auth skeleton

implement user/profile CRUD skeleton

Pod A / Gameplay

create Go game server skeleton

implement match lifecycle shell

implement in-memory session management

implement WS connection/session model

integrate contracts package

Pod C / Mobile

initialize Expo app

auth shell

lobby shell

home navigation

feature flag bootstrapping

telemetry wrapper

push/deep link scaffolding

Pod D / QA/Release

add lint/test/build pipelines

add contract test pipeline

add snapshot test pipeline

add synthetic build smoke checks

add deployment verification scripts

First E2E milestone

By end of Phase 3, you must have:

mobile app launches

user can enter as guest

app can fetch profile from meta-api

app can connect to staging WS server

server can create a dummy match session

analytics event flows to telemetry backend

errors appear in Sentry

traces appear in Datadog

Deliverables

working staging stack

guest auth flow

mobile shell

backend shell

WS handshake shell

observability baseline

CI/CD baseline

Exit gate

The stack must already be integrated. No isolated code piles.

Phase 4 — Deterministic Gameplay Core
Objective

Build the heart of the game: the authoritative rules engine.

This is the most important technical phase in the whole project.

Core modules to implement
4.1 Match state model

Implement canonical state objects:

match metadata

round state

active player

hands

stock

discard

word zones

timer state

modifier context

lexicon context

action history

score ledger

4.2 Deck and dealing engine

Implement:

deck composition versioning

secure shuffle

2 wild cards

9-letter deal

initial discard

deterministic seed support for testing only

4.3 Turn state machine

Implement your defined states:

lobby

match found

dealing

active turn

submission pending

turn committed

reconnect grace

round complete

match complete

result persisted

4.4 Dictionary context engine

Implement:

lexicon version lock at match start

banned-word overlay

playlist filters

morphology/root policy hooks

strict/ranked vs relaxed/family mode policy support

4.5 Play legality engine

Implement checks for:

draw source legality

hand membership

discard access

word validity

capture legality

multi-word legality

wildcard assignment

wildcard mutation locking

illegal sequence rejection

duplicate submit protection

4.6 Scoring engine

Implement:

base score table

capture bonus

modifier overlays

penalty scoring

tie-break logic

round winner logic

match winner logic

4.7 Lineage/replay engine

Implement:

transformation chain tracking

score delta log

ownership transfer

sequence_id generation

state hash generation

replay reconstruction

Testing required here

This phase must have the deepest test coverage in the program.

Unit tests

deck composition

deal counts

scoring tables

wildcard locking

tie-breaks

round end logic

Property tests

no illegal hand mutation

no duplicate card creation

no hidden stock leak

deterministic replay rebuild

state machine invariant preservation

Scenario tests

TOP → STOP

wildcard transforms

invalid plural-only transforms

stock exhaustion cases

timeout auto-forfeit

multi-word mixed play

hand-empty end states

Deliverables

production-grade gameplay core library

replay runner

test fixture pack

golden match corpus

deterministic state hash harness

Exit gate

Before you move on:

all core UAT gameplay scenarios must pass in automation

replay must reconstruct committed games exactly

state divergence rate must be 0 in controlled test runs

Phase 5 — Live Duel Vertical Slice
Objective

Ship the first fully playable internal product: live 1v1 duel E2E.

Work items
Pod A / Game server

create live match session lifecycle

attach active timers

handle turn submission and rejection

broadcast authoritative board patch events

implement reconnect grace flow

Pod B / Matchmaking/meta

create casual live queue

queue ticket issuance

match found event

match instance creation

player seat assignment

match completion persistence

Pod C / Mobile

Implement real match screen:

hand tray

stock/discard display

own/opponent word zones

timer

score display

active modifier panel

preview panel

submit/undo

invalid play feedback

capture targeting

turn transition rendering

Required UX behaviors

The player must be able to:

join queue

get matched

enter match

draw

compose a word

capture an opponent word

preview score

commit move

watch score and lineage update

reconnect after drop

finish round

finish match

return to summary

Deliverables

internal playable live duel

live queue flow

live result persistence

match summary screen

reconnect support

Exit gate

Internal team can play full live matches without admin help.

Phase 6 — Async, Notifications, and Resilience
Objective

Complete the second core pillar: asynchronous 1v1.

Work items
Async engine

async match creation

turn deadline storage

turn-ready event scheduling

async inbox model

match resume at arbitrary time

immutable lexicon context lock for long-lived matches

Notification system

APNs/FCM integration

notification worker

delivery logging

deep-link payload construction

retry policies

notification preference controls

Mobile

async inbox screen

“your turn” entry

match restore

replay history loading

notification tap handling

background/foreground state sync

Reliability

deadline expiry job

async forfeit rules

missed-turn resolution

push fallback to polling

re-open consistency handling

Required tests

deep link opens correct match

push sent after opponent move

async match resumes under same lexicon version after days

timed-out async match forfeits correctly

duplicate push/re-open does not duplicate actions

Deliverables

full async loop

push notifications

async inbox

deadline enforcement

deep-link routing

Exit gate

Scenario 4 from your UAT must pass repeatedly under staging conditions.

Phase 7 — Ranked, Social, and Private Rooms
Objective

Finish the core competitive/social product.

Ranked system

Implement:

hidden MMR

visible rank tiers

result ledger

idempotent match-close writes

best-of-3 aggregation

season identity

rematch generates new match UUID

anti-dodge basic enforcement

Social systems

Implement:

friend handles

add friend

recent opponents

invite to private room

rematch flow

Private rooms

Implement:

room code generation

join by code

ready state

custom playlist selection

classic vs arena rules toggle

private duel start

Competitive integrity

Implement:

suspicious move-pattern logging

repeated-opponent detection

solver suspicion telemetry hooks

report button

abuse evidence storage

Deliverables

live ranked duel

MMR/rank update pipeline

private room duels

rematch support

basic friend graph

report system

Exit gate

Ranked result writes must be idempotent and auditable.

Phase 8 — Tutorial, Bots, and Onboarding
Objective

Make the game learnable and survivable for new players.

Tutorial implementation

Build the scripted lessons exactly:

make a word

draw/discard

capture

round end

modifier intro

Bot practice

Implement bot tiers:

Beginner

Standard

Advanced

Bot engine does not need to be “human genius.”
It needs to:

obey all rules

create realistic practice pressure

support onboarding and QA

generate automated match traffic for soak tests

New player protection

Implement:

first-match casual bucket

tutorial completion gate before ranked

optional hints in early casual

loss framing and rematch encouragement

Deliverables

guided tutorial flow

bot match mode

new player protection rules

tutorial telemetry and funnels

Exit gate

New users can install, finish tutorial, play bot, then enter casual without confusion.

Phase 9 — Progression, Cosmetics, Admin, and Live Ops
Objective

Complete MVP meta retention and operational control.

Progression

Implement:

account level

XP grants

quest system basics

profile frame/title unlocks

cosmetic inventory

Cosmetics/shop

Implement minimal MVP:

card backs

board themes

profile frames

basic store surfaces

entitlements

restore purchase logic

Admin tools

Implement internal admin web:

lexicon version publish

banned-word overlay edits

username moderation

report review

event modifier publishing

audit log view

Live ops controls

Implement:

feature flags

modifier rotation config

seasonal config

quest config

notification campaign config

Deliverables

XP/profile system

cosmetic inventory

admin CMS

lexicon governance tooling

live-ops config system

Exit gate

Ops can safely change lexicon blocklists and rule modifiers without code deploy.

Phase 10 — Full Verification & Hardening
Objective

Move from “works” to “production-stable.”

This is where many game teams fail by rushing.

10.1 Testing layers
Component verification

game engine unit and property tests

API tests

contract compatibility tests

mobile screen and state tests

Integration tests

app ↔ meta-api

app ↔ game-server

game-server ↔ Postgres

workers ↔ queues

notifications ↔ mobile deep links

System tests

full match playthroughs

reconnect during active turn

queue to match to result to rank write

async move to push to resume to finish

Load tests

match creation spikes

WS concurrent connections

timer storm scenarios

ranked result write spikes

push fanout bursts

Soak tests

Run long-lived sessions continuously:

thousands of bot matches

repeated reconnects

extended async matches

memory leak observation

CPU growth observation

Chaos tests

kill live game node mid-match

Redis restart

Postgres failover simulation

notification worker outage

packet delay/reorder in staging

10.2 Security and exploit testing

JWT misuse

match spoofing

payload tampering

duplicate submit flooding

hidden information leakage

ranked ledger double-write attempts

10.3 Store/release readiness

App Store/Play compliance

privacy policies

age rating

parental control behavior

data deletion/export requirements

crash-free session thresholds

Deliverables

hardening report

exploit report

load/soak benchmark pack

release candidate checklist

incident runbooks

support escalation runbooks

Exit gate

Must satisfy release SLOs, not just “feel okay.”

Phase 11 — Soft Launch & Stabilization
Objective

Release to a controlled region/user cohort and fix reality gaps.

Rollout plan

region-limited or invite-only launch

feature flags on all risky systems

low concurrency first

observe:

tutorial completion

live queue conversion

async retention

reconnect success

invalid play rate

crash rate

ranked completion

moderation incidents

Required response loop

Every week:

review telemetry

review gameplay exploits

review dictionary complaints

review balance pain points

patch bugs

update modifier pool cautiously

Deliverables

soft-launch telemetry dashboard

top-issues list

first balance patch

first onboarding patch

first ops patch

Exit gate

Soft-launch KPIs and operational stability must clear the bar before broader rollout.

Phase 12 — Global Launch Readiness
Objective

Prepare the game to operate as a real live product.

Final launch requirements

incident on-call rotation

rollback plan

hotfix process

customer support flows

moderation staffing plan

content calendar for first season

shop rotation calendar

event rotation calendar

post-launch backlog prioritized

Deliverables

launch command center plan

on-call and escalation runbook

season 1 content plan

day-1/day-7/day-30 KPI dashboard

post-launch roadmap

6. Exact Build Order Inside the Critical Path

If you want the strictest “what gets built first” order, this is it.

Step-by-step critical path
Step 1

Create repo, CI/CD, infra skeleton, staging environments.

Step 2

Create canonical contracts package and event/versioning policy.

Step 3

Implement guest auth, profile shell, app shell, WS handshake shell.

Step 4

Implement authoritative match state model and state machine.

Step 5

Implement deck generation, hand dealing, discard, timer core.

Step 6

Implement dictionary context engine.

Step 7

Implement play legality engine.

Step 8

Implement scoring engine.

Step 9

Implement replay/lineage/state-hash engine.

Step 10

Implement live matchmaking and match creation.

Step 11

Implement live duel mobile UI and turn submission flow.

Step 12

Implement reconnect, timeout, and result persistence.

Step 13

Get internal live 1v1 fully playable E2E.

Step 14

Implement async orchestration, inbox, and notifications.

Step 15

Implement ranked MMR and idempotent result ledger.

Step 16

Implement private rooms and rematch.

Step 17

Implement tutorial and bot practice.

Step 18

Implement progression basics and cosmetics.

Step 19

Implement admin tools, lexicon controls, moderation, and live-ops configs.

Step 20

Run hardening, load, soak, chaos, UAT, soft launch, stabilization.

That is the correct build sequence.

7. What Can Run in Parallel
Parallel lane A — Platform

Can begin immediately in Phase 3:

infra

auth

profile

telemetry

admin auth

CI/CD

Parallel lane B — Mobile shell

Can begin immediately in Phase 3:

navigation

home screens

auth shell

async inbox shell

match screen scaffold

animation prototypes

Parallel lane C — Gameplay core

Can begin immediately after contracts/state model freeze:

rules engine

scoring

wildcard logic

capture logic

replay engine

Parallel lane D — Design/content

Can run throughout:

UI kit

visual system

tutorial content

bot personality rules

modifier catalog

cosmetics

onboarding copy

Parallel lane E — QA automation

Must start early, not late:

golden fixture library

synthetic matches

replay verification harness

WS contract checks

notification E2E harness

8. V-Model Mapping

Since you asked for a full implementation plan, this should explicitly stay aligned to the V-model.

Left side — definition/design

business vision / GDD

SRS / NFRs

system architecture

low-level design

implementation

Right side — verification

unit/property tests verify LLD

integration tests verify subsystem interactions

system tests verify architecture and workflows

UAT verifies business/user scenarios

production telemetry verifies operational promises

WIT V2 exact mapping

gameplay core ↔ component/property/replay tests

API/contracts ↔ contract/integration tests

live duel ↔ system tests

async and push ↔ system/UAT tests

ranked ledger ↔ integrity and idempotency tests

onboarding/tutorial ↔ UAT and funnel telemetry

release ↔ SLO validation in production

9. Non-Negotiable Acceptance Gates

These should be treated as release blockers.

Gate A — Gameplay correctness

100% pass on authoritative rules regression suite

0 state divergence in deterministic replay corpus

invalid capture rejection accuracy at 100% on known-case suite

Gate B — Reconnect integrity

reconnect restore ≤ 3s in staging for tested scenarios

server timer never freezes incorrectly during disconnect

Gate C — Ranked integrity

0 duplicate result writes in repeated rematch/closeout testing

best-of-3 emits one authoritative match result only

Gate D — Async integrity

notification deep-link success ≥ defined threshold

lexicon version remains frozen across long-lived async matches

Gate E — Operational stability

crash-free sessions at or above target

move validation p95 at or below target

match completion rate at or above target

Gate F — New-user viability

tutorial completion and bot/practice progression are healthy enough that new users are not churning before first PvP exposure

10. Biggest Risks and How the Plan Neutralizes Them
Risk 1 — Rules ambiguity causes endless bugs

Neutralization:

legality matrix

deterministic replay

explicit capture/root policy

golden fixture suites

Risk 2 — Multiplayer is built before engine correctness

Neutralization:

gameplay core completed and test-hardened before broad mode expansion

Risk 3 — Live and async drift into two separate games

Neutralization:

same authoritative rules engine for both

only transport/orchestration differs

Risk 4 — Client and server contract drift

Neutralization:

one canonical contracts package

generated types

contract-gated CI

Risk 5 — Ranked fraud / double writes / disconnect abuse

Neutralization:

idempotency keys

result ledger uniqueness

reconnect/timer authoritative server behavior

abuse telemetry hooks

Risk 6 — Production instability late in the project

Neutralization:

observability from Phase 3

weekly integrated builds

synthetic bot traffic

hardening phase before soft launch

11. What Should Not Be in MVP

To keep this build sane and fast, do not allow these to pollute MVP critical path:

4-player ranked

spectator mode

guild/clubs

full replay sharing/social export

multi-language lexicons

advanced AI “smart hints”

complex battle pass economy

country/team events

high-volume emote/chat systems

Those are expansion layers, not launch-critical systems.

12. Final Recommended Milestone Sequence

If I were running this program, I would define milestones exactly like this:

Milestone 1 — Foundation Complete

infra, auth shell, contracts, observability, mobile shell

Milestone 2 — Engine Correctness Complete

deterministic rules engine, replay, scoring, legality suite

Milestone 3 — Live Duel Internal Alpha

internal playable 1v1 live duel end to end

Milestone 4 — Async and Ranked Alpha

async loop, push, ranked writes, private rooms

Milestone 5 — Content and Onboarding Beta

tutorial, bots, progression, cosmetics basics, admin tools

Milestone 6 — Release Candidate

hardening, UAT, performance, security, store readiness

Milestone 7 — Soft Launch

limited rollout, telemetry, stabilization

Milestone 8 — Launch

production-scale operations live

13. The Most Important Implementation Rule

If there is one rule to enforce across the entire program, it is this:

Every feature must land as part of a fully integrated vertical slice with automated evidence, not as isolated code that “will be wired later.”

For WIT V2, that means:

gameplay code is never accepted without replay/test evidence

client UI is never accepted without real server integration

backend flows are never accepted without telemetry

ranked/async systems are never accepted without idempotency and resilience evidence

That is how you get to “functional and stable,” not just “built.”