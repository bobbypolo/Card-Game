# Software Requirements Specification (SRS)
**Project:** WIT V2
**Phase:** 1 (Requirements)

## 1. Introduction
This SRS dictates the functional and non-functional requirements for WIT V2, a server-authoritative global multiplayer word strategy card game. The verbs "shall" and "must" denote strict system requirements.

## 2. Functional Requirements (FR)

### FR-1: Account & Social Systems
- **FR-1.1:** The system shall support guest session bootstrapping leveraging device IDs to allow immediate gameplay, with the ability to bind the session later via SSO.
- **FR-1.2:** The system shall allow users to register and log in natively via Apple and Google SSO.
- **FR-1.3:** The system shall support generating and joining 'Private Rooms' via alphanumeric invite codes.
- **FR-1.4:** The system shall support a 'Friends List' maintaining relationships via unique user handles.

### FR-2: Matchmaking & Game Modes
- **FR-2.1:** The system shall support active player counts of precisely 2 players (1v1) for Ranked priorities, and scalable 2-4 players for Casual tables.
- **FR-2.2:** The system shall provide Live Matchmaking using MMR / ELO variants for 1v1 casual and ranked games.
- **FR-2.3:** The system shall provide Asynchronous Matchmaking with strict, configuration-driven turn timers.
- **FR-2.4:** The system shall support Practice Matches against AI Bots of configuration-driven difficulty profiles.

### FR-3: Game Engine & Validation (Server Authoritative)
- **FR-3.1a:** The server shall generate a shuffled deck from the active deck composition configuration, including precisely 2 Wild Cards by default.
- **FR-3.1b:** At round start, the server shall deal exactly 9 letters to each active player by default.
- **FR-3.1c:** The server shall reveal exactly 1 initial discard after hands are dealt.
- **FR-3.2:** The server shall validate any submitted word against the absolute "dictionary context" which explicitly bundles: Lexicon Version, Banned-Word Overlay, Playlist Rule Filters, and Root/Morphology Policies.
- **FR-3.3 (Capture Logic):** A valid capture must consume 100% of the letters of the original target word, contain at least one new letter from the active player's hand at the time of submission, and form a valid new dictionary entry under the current context.
- **FR-3.4 (Wildcards):** The system shall allow users to assign a letter to a wild card dynamically upon play submission, locking its representation visually and logically thereafter until transformed by a subsequent capture.
- **FR-3.5 (Turn Execution):** The system shall strictly sequence a given turn order as: (A) Draw from Stock OR Pickup top of Discard, (B) Play word(s) and/or Capture word(s) in any legal combination utilizing the drawn/held letters, (C) End turn by manual completion or discarding 1 letter.

### FR-4: Scoring & Timers
- **FR-4.1:** word scores shall be calculated based on explicitly mapped hardcoded length thresholds (2 to 10+ letters).
- **FR-4.2:** Captures shall natively award an additional +2 points per added letter. When captured, the original word's prior point value is retained permanently by the original owner.
- **FR-4.3:** The system shall deduct 1 point per remaining letter in hand at the end of a round.
- **FR-4.4:** Turn expiry behavior defaults:
  - **Live Ranked:** Timer expiry results in an immediate automatic turn forfeit (draw 1, pass turn). 3 consecutive forfeits results in Match Forfeit.
  - **Live Casual:** Timer expiry identical to ranked; AI bot takeover is disabled by default.
  - **Async:** Timer expiry (e.g., 24h) results in an immediate Match Forfeit loss for the expired player.

### FR-5: Rule Modifiers
- **FR-5.1:** The system shall support loading a "Rule Modifier" configuration per match or round which overrides base scoring or rules.
- **FR-5.2:** Modifier definitions shall explicitly state their precedence, whether they stack, and if they alter validation rules or exclusively scoring bonuses.

### FR-6: Replay & Lineage Logic
- **FR-6.1:** The system shall persist and emit match action history sufficient to replay turn-level word transformations (lineage logs) and incremental score changes deterministically.
- **FR-6.2:** The system shall track and visually indicate newly acquired word ownership after a successful capture.

### FR-7: Notification Systems
- **FR-7.1:** The system shall deliver turn-ready push notifications for async matches.
- **FR-7.2:** The system shall deliver notifications for friend invites and asynchronous match completions.

### FR-8: Admin & Moderation Configurations
- **FR-8.1:** The system shall provide administrative tooling to manage dictionary lexicons and versioning.
- **FR-8.2:** The system shall provide administrative tooling to manage dynamic blocklists for username and content moderation.

### FR-9: Ranking & Data Integrity
- **FR-9.1:** The system shall ensure ranked match results persist securely with idempotent win/loss writes enforcing uniqueness per match UUID.
- **FR-9.2:** Rematches shall instigate distinct new match instance IDs and shall not override prior match records.
- **FR-9.3:** Best-of-3 formats shall aggregate round wins internally and emit only a single Match Result upon termination.

## 3. Non-Functional Requirements (NFR)

### NFR-1: Performance & Latency
- **NFR-1.1:** The p95 server action processing time for a live move validation shall be ≤ 150ms measured at the server ingress.
- **NFR-1.2:** The p95 client-visible action acknowledgment within matched regions shall be ≤ 400ms.
- **NFR-1.3:** The client session reconnect restore time shall be ≤ 3 seconds after a successful network rejoin.
- **NFR-1.4:** Push emission success rate to APNs/FCM shall be ≥ 98%.
- **NFR-1.5:** Deep-link open-to-correct-match success rate for delivered notifications shall be ≥ 98%.
- **NFR-1.6:** The state divergence rate shall be 0 for authoritative committed moves.

### NFR-2: Reliability & State Preservation
- **NFR-2.1:** If a player disconnects during a live match, the turn timer CONTINUES server-side. The disconnected player has the duration of the remaining clock to reconnect and submit, otherwise FR-4.4 is invoked.
- **NFR-2.2:** Multi-word turns and background/foreground resumes shall resolve deterministically via the state machine sync payload.

### NFR-3: Security & Competitive Integrity
- **NFR-3.1:** The client application shall never have access to the randomized deck stock order in memory.
- **NFR-3.2:** Double-submit protection must be strictly enforced via idempotency keys on actions.
