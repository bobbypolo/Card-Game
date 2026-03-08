# WIT V2 — Global Multiplayer Game Design Document

**Document Type:** Final Draft V2 Game Design Document
**Product Type:** Digital word strategy card game
**Platform Priority:** Mobile first (iOS / Android), tablet supported, web companion later
**Primary Focus:** Live and asynchronous multiplayer between players around the world
**Design Status:** Final Draft V2
**Working Title:** WIT V2
**Important Note:** If rights to the original WIT brand and original packaged rules are not controlled by the project owner, this document should be treated as a **spiritual-successor design framework** and the final shipped name, copy, visuals, and exact rules wording must be original.

---

# 1. Executive Summary

WIT V2 is a competitive digital word card game built around four core fantasies:

1. **Create** a clever word from a private hand of letters.
2. **Steal** an opponent’s word by extending and rearranging it into something new.
3. **Manage risk** through hand control, discard timing, and turn order.
4. **Outplay real people globally** in a clean, fair, highly social multiplayer environment.

The heart of the product remains the elegant word-dueling identity of the original concept: players form words from letters, lay them down for points, and opportunistically capture previously played words by adding letters and changing meaning. The digital version modernizes that core with server-authoritative rules enforcement, automated scoring, guided onboarding, robust live and asynchronous online multiplayer, fair matchmaking, seasonal content, and a signature rule-modifier system that makes the game feel contemporary and distinct.

WIT V2 is not positioned as “just another spelling app.” It is positioned as a **multiplayer tactical word duel** with strong social tension, high replayability, and a clear identity: **build, bait, steal, transform**.

The flagship product experience is global multiplayer. Players can queue for live matches, start asynchronous games with friends or strangers, join private rooms, climb ranked ladders, and participate in rotating global events. The game is turn-based rather than twitch-based, making it naturally compatible with cross-region play, variable latency, and players across time zones.

---

# 2. Product Vision

## 2.1 Vision Statement

Create the most satisfying multiplayer word battle game on mobile: one that combines the accessibility of a family word game, the tension of a card duel, and the retention power of a modern live-service multiplayer product.

## 2.2 Product Promise

Every match should make the player feel one or more of the following:

* “I made a smart word.”
* “I stole that perfectly.”
* “I saw the board state better than my opponent.”
* “I want one more round.”
* “I want to rematch or share that play.”

## 2.3 High-Level Positioning

WIT V2 sits at the intersection of:

* word games
* tactical card games
* turn-based multiplayer
* asynchronous social competition

It should feel more competitive and interactive than passive word builders, but less intimidating and less cognitively punishing than elite tournament word games.

---

# 3. Design Goals

## 3.1 Primary Goals

### Goal A — Preserve the core identity

The game must preserve the essential fantasy of forming words and capturing opponents’ words by adding letters and rearranging them into a new valid word.

### Goal B — Make multiplayer the star

The most engaging mode must be human-vs-human. Solo features should support retention and onboarding, but the product identity should be strongest in live and async multiplayer.

### Goal C — Reduce friction and disputes

All scoring, validation, legality checks, timers, and capture logic must be clear, automated, and visually explained.

### Goal D — Increase originality without losing elegance

The product should not feel like a bare digital port. It needs digital-native systems that create differentiation while respecting the original core.

### Goal E — Support strong long-term retention

The product must have enough progression, variation, social energy, and event cadence to keep players coming back daily and weekly.

## 3.2 Secondary Goals

* Family-friendly by default, competitive in advanced modes
* Easy to learn, hard to master
* Strong spectator and streaming moments
* Fair across global latency conditions
* Monetizable without pay-to-win

## 3.3 Non-Goals

* Not a real-time reflex word race
* Not a Scrabble clone
* Not a pure solitaire puzzle app
* Not a heavily power-crept collectible card game
* Not a monetization-first casino wrapper around letters

---

# 4. Core Design Pillars

## 4.1 Pillar 1 — Tactical Word Combat

Words are not merely submitted for points. They are weapons, bait, liabilities, opportunities, and targets.

## 4.2 Pillar 2 — Visible Cleverness

When a player makes a brilliant capture, everyone should instantly understand what changed and why it mattered.

## 4.3 Pillar 3 — Turn-Based Global Play

The game should feel excellent with opponents in any region because the design is turn-based, timing-tolerant, and server authoritative.

## 4.4 Pillar 4 — Fairness Over Chaos

Luck from letter draws creates texture, but the product must reward strategic play, planning, and vocabulary skill rather than pure variance.

## 4.5 Pillar 5 — Clean Social Tension

The game should create emotional heat through steals, close scores, and word denial, but never through confusing rules or opaque systems.

---

# 5. Audience Definition

## 5.1 Primary Audience

### Audience A — Social Word Players

People who enjoy mobile word games, casual strategy, and asynchronous play with friends.

Traits:

* likes words and light competition
* values convenience and polish
* prefers short-to-medium session lengths
* often plays daily habit games

### Audience B — Competitive Thinkers

Players who enjoy tactical PvP, ranking, and feeling smarter than opponents.

Traits:

* enjoys mastery loops
* likes analysis and optimization
* is motivated by rating, leaderboards, and visible skill

## 5.2 Secondary Audience

### Audience C — Families / Couples / Pass-and-Play Users

Players looking for a smart, nonviolent game to play together.

### Audience D — Solo Puzzle Users

Players who may enter through daily challenge content and later convert into PvP users.

## 5.3 Audience Risks

* vocabulary gaps can create intimidation
* strong steal mechanics can feel mean if not presented well
* younger players may need simpler validation rules and lighter competition

---

# 6. Product Identity and Differentiation

## 6.1 What Makes WIT V2 Different

The differentiating identity of WIT V2 is not just “make words.” It is:

* **private hand management** rather than pure shared-pool reaction play
* **discard-pile strategy** that adds prediction and denial
* **capture and transformation** of existing words
* **global turn-based multiplayer** designed for both live and async
* **Rule Modifiers** that change strategic incentives each round
* strong digital explanation of steals and word lineage

## 6.2 Signature System — Rule Modifiers

To make the product more distinctive in the digital market, WIT V2 introduces a rotating round-based system called **Rule Modifiers**.

A Rule Modifier is a light, easily understood condition or scoring incentive applied to a round or playlist. Rule Modifiers create freshness, reduce solved-play patterns, and give the game a recognizable modern identity.

### Examples of Rule Modifiers

* **Long Form:** 6+ letter words gain bonus points.
* **Sharp Steal:** successful captures award +1 additional point per letter added.
* **Vowel Pressure:** vowels in hand at round end count as +2 penalty each instead of +1.
* **No Safety:** discard pile remains visible and stealable for one full turn cycle.
* **Double Edge:** wild cards no longer double long-word points this round.
* **Chain Link:** first capture after an opponent capture gains a response bonus.
* **Theme Round:** only words matching a chosen category gain bonus points.

Rule Modifiers are used carefully. They must enrich strategy without bloating the rules or making the game unreadable.

## 6.3 Playlists

To serve different audiences without fragmenting the game beyond recovery, WIT V2 launches with two major rule families:

### Classic Playlist

Closest to traditional WIT-style play. Good for purists, onboarding, and private friend tables.

### Arena Playlist

The flagship digital mode. Uses curated Rule Modifiers, ranked support, seasonal ladders, and stronger progression hooks.

---

# 7. Game Structure Overview

## 7.1 Match Layering

A full player experience is structured as:

* **Account / profile progression**
* **Playlist selection**
* **Matchmaking or room join**
* **Match**
* **Rounds within match**
* **Turns within round**
* **Words and captures within turn**

## 7.2 Default Match Formats

### Live Duel

* 1v1
* fastest competitive format
* intended for ranked ladder MVP

### Live Table

* 2 to 4 players
* more social, more chaotic, more table-game energy

### Async Duel

* 1v1
* long-timer format
* ideal for cross-time-zone play

### Private Table

* invite code / friends only
* supports 2 to 4 players
* classic social mode

### Daily Challenge (solo)

* fixed scenario
* supports retention and skill building

---

# 8. Core Ruleset — Digital V2

This section defines the main V2 gameplay rules.

## 8.1 Components (Digital Equivalent)

### Letter Deck

Base digital deck derived from the traditional letter-card concept. Final letter distribution must be balance-tested extensively before ship. The digital implementation allows iteration, but the live-service team should still treat deck tuning as a high-impact change requiring careful telemetry review.

### Wild Cards

Two wild cards in the base rule set.

### Stock

Face-down draw source.

### Discard Pile

Public face-up pile showing the most recent discarded letter.

### Word Zone

Each player has a visible played-word area.

### Hand

Private letters visible only to the player.

### Score Track

Auto-managed by the system.

## 8.2 Recommended Launch Rule Set

### Players

* Supported: 2 to 4
* Ranked launch priority: 1v1
* Casual launch support: 2 to 4

### Age Positioning

* Marketed broadly as family-friendly
* Real competitive skill band likely older than the youngest family segment
* In-game onboarding must support beginners aggressively

### Language at Launch

* English only at launch
* Dictionary and UI are controlled centrally
* International players are welcome, but the competitive language pool is unified

## 8.3 Objective

Win rounds by emptying your hand through valid word plays and/or a final discard, while scoring enough points to win the match.

## 8.4 Default Match Win Condition

For digital play, the recommended default is:

* **Best of 3 rounds** in live modes
* or **first to 2 round wins**

Reason: This is cleaner, more emotionally readable, and more session-stable than a simple race to 25 points in all contexts.

### Alternative Classic Win Condition

Classic custom rooms may use the original-style **first to 25 total points** format.

## 8.5 Deal / Start of Round

At round start:

1. Deck is shuffled server-side.
2. Each player receives **9 letters**.
3. Remaining letters form the stock.
4. One card is placed face up as the initial discard.
5. Starting player is selected by digital turn-order logic.

## 8.6 Turn Structure

On a normal turn, the active player completes the following sequence:

1. **Draw Phase**

   * draw top card from stock, or
   * take the top face-up discard

2. **Play Phase**

   * create one or more valid words from letters in hand, or
   * capture and transform existing words if legal, or
   * perform a combination of fresh play and capture if legal under ruleset

3. **End Phase**

   * if the player has not emptied hand completely through legal play, they discard one card to the discard pile
   * turn passes clockwise or to the next player in digital order

## 8.7 Word Play Rules

A valid word must satisfy the currently active dictionary and mode rules.

### Standard Rule Set

At launch, the recommended default is:

* minimum 2 letters
* no proper nouns
* no banned slurs or offensive terms
* dictionary controlled by the server
* variant handling standardized by the dictionary backend

### Relaxed / Family Rule Set

* broader allowable word list
* easier onboarding
* fewer frustrating rejections

### Competitive Rule Set

* stricter dictionary
* fixed official lexicon
* no ambiguity in ranked play

## 8.8 Capture Rules

Capturing is the signature mechanic.

A player may capture an existing word in the word zone if all of the following are true:

1. the new word uses **all letters from the original word**
2. the player adds **at least one additional letter**
3. the final result is a valid word
4. the final result is not forbidden by the root/identity rules for the current mode

### Digital Clarification Rule

The app must visibly demonstrate the capture transformation:

* original word highlighted
* letters retained highlighted in one color
* added letters highlighted in another color
* final new word animated into place

### Root / Meaning Rule Handling

Because “change the meaning” is ambiguous in tabletop play, digital modes need explicit policy.

#### Recommended Launch Policy

For ranked play, replace the vague “change the meaning” rule with a **server-checkable transformation policy** such as:

* must produce a distinct valid dictionary entry
* cannot be merely the same word plus pluralization in strict modes if that pattern is disallowed
* optional morphology filters can be added later after telemetry review

This gives clean enforcement and reduces disputes.

## 8.9 Word Ownership

When a word is captured:

* the capturing player becomes the new owner of the transformed word
* the previously played owner retains any points already earned unless the playlist explicitly says otherwise
* the transformed word now occupies the capturing player’s word zone

## 8.10 Multi-Word Turns

Players may play multiple words in a turn if all created words are valid and all letters used are legally sourced from their hand and/or a legal capture.

The UI must show a preview of:

* total points gained
* number of words formed
* letters remaining
* whether the play empties the hand

## 8.11 Wild Cards

Wild cards may stand in for any letter.

### Wild Card Rules

* assignment is locked when the word is submitted
* the UI must show what letter the wild card represents
* once committed inside a played word, the represented value remains tied to that word until the word is captured and transformed, at which point the new play defines the new state

### Recommended V2 Wild Card Bonus Adjustment

The original long-word wild-card doubling rule is exciting but can be swingy. For V2, use one of the following:

**Recommended default:**

* if a word containing at least one wild card has 7+ letters, award **+2 bonus points** rather than doubling the entire word score

Reason:

* easier to explain
* less explosive variance
* still feels special

Classic custom rooms may enable original-style doubling.

## 8.12 Scoring Model

### Base Word Score Table (Recommended Launch Baseline)

* 2-letter word = 2 points
* 3-letter word = 5 points
* 4-letter word = 7 points
* 5-letter word = 9 points
* 6-letter word = 12 points
* 7-letter word = 14 points
* 8-letter word = 16 points
* 9-letter word = 20 points
* 10+ letter word = 25 points cap unless special mode overrides

### Capture Bonus

When capturing and transforming an existing word, award:

* **2 points per added letter** by default

This preserves the original spirit.

### Modifier Bonus

If a Rule Modifier is active, any additional scoring is shown as a separate line item.

## 8.13 End of Round Conditions

A round ends when one of the following occurs:

### Standard End

A player legally empties hand by playing all remaining letters, or by playing all but one and discarding the last card.

### Stock Exhaustion End

If stock is exhausted and no player has ended the round, the round ends after a final full turn cycle or according to playlist rules.

### Timeout End

If a player’s turn timer expires, timeout handling applies.

## 8.14 End of Round Penalties

If the round ends before a player empties hand:

* each remaining letter in hand is worth **-1 point** by default
* optional future balance tuning may weight wild cards differently

## 8.15 Match Tiebreakers

If the final match score is tied:

1. player with fewer unplayed letters across the match wins
2. if still tied, player with more successful captures wins
3. if still tied, sudden-death round or shared draw depending on playlist

---

# 9. Digital-First Improvements Over Original Rules

## 9.1 Automated Validation

Players never manually debate basic legality during the flow of play.

## 9.2 Clear Capture Visualization

Every capture is visually explained to all players.

## 9.3 Predictive Scoring Preview

Before confirming a play, the system shows the score breakdown.

## 9.4 Word History / Replay Log

Each match stores:

* words played
* words captured
* who captured them
* score changes
* turn timeline

## 9.5 Reduced Rule Ambiguity

Ambiguous tabletop phrases are replaced with explicit server-enforced logic.

## 9.6 Guided Learning Tools

The app can optionally show:

* playable words from tutorial rack samples
* why a capture is valid or invalid
* what letters were left unused

---

# 10. Multiplayer Design

This is the central product section.

## 10.1 Multiplayer Principles

* must be fair across regions
* must allow meaningful competition without twitch dependence
* must support both short live sessions and long async sessions
* must make social play easy to start
* must protect the integrity of ranked play

## 10.2 Live Multiplayer

### Core Live Modes

* 1v1 ranked duel
* 1v1 unranked duel
* 2 to 4 player casual table
* 2 to 4 player private room

### Turn Timers

Recommended launch settings:

* Live duel: 30 to 45 seconds per turn
* Live table: 45 to 60 seconds per turn
* Blitz playlist later: 20 to 25 seconds per turn

### Timer Aids

To reduce frustration:

* one short grace extension per round
* reconnect buffer
* visible countdown

## 10.3 Asynchronous Multiplayer

Async is a major global-engagement system, not a side mode.

### Async Core Rules

* players take turns at their convenience
* each turn has a longer window, such as 12 hours or 24 hours
* notifications remind players when it is their move
* multiple async games can run concurrently

### Why Async Matters

* supports cross-time-zone play
* supports adult schedules
* increases retention and habit play
* creates “check-in” behavior throughout the day

## 10.4 Matchmaking

### Ranked Matchmaking Inputs

* visible rank tier
* hidden MMR
* recent performance confidence window
* latency / region preference where applicable
* queue time guardrails

### Casual Matchmaking Inputs

* speed preference
* table size preference
* beginner-protection buckets

## 10.5 Social Systems

### Friends

* add by code / handle
* recent opponents list
* invite to rematch

### Private Rooms

* share room code
* set rules and round format
* observer slots later

### Rematch

* instant rematch after live match
* best-of series support later

### Reactions / Emotes

* lightweight and non-toxic by default
* muted by parental or privacy settings

## 10.6 Anti-Cheat and Competitive Integrity

Because this is a word game, cheating risks include dictionary scraping, solver assistance, collusion, alt accounts, and timeout abuse.

### Required Integrity Systems

* server-authoritative word validation
* suspicious move-pattern detection for ranked review
* anti-collusion monitoring in repeated matchups
* report system
* ladder integrity enforcement
* rate limiting and bot detection

### Philosophy

Do not promise impossible cheat elimination. Instead, build ranked around deterrence, detection, and consequence.

## 10.7 Reconnect and Disconnect Handling

### Live Match Rules

* short reconnect window after disconnect
* if player fails to return, AI does not take over in ranked by default
* repeated disconnects count as losses or penalties after policy threshold

### Async Match Rules

* missed timer results in automatic forfeit or soft timeout behavior depending on playlist

---

# 11. Originality Strategy for V2

## 11.1 Preserve Core, Add Identity

The product becomes more original by combining the old core with three modern systems:

1. **Rule Modifiers**
2. **Global async + live multiplayer structure**
3. **Word lineage and steal spectacle presentation**

## 11.2 Word Lineage System

Every important word in a match has a history.

Example:

* TOP → STOP → POSTER → PRESTO

The game visually records the chain. At end of round, the player can see which words evolved, who captured them, and which transformation had the highest swing.

This turns the abstract language battle into a memorable story.

## 11.3 Featured Event Formats

Examples:

* World Ladder Week
* No Wild Weekend
* Long Word Cup
* Global Capture Rush
* Team Country Event later if moderation and geo systems justify it

---

# 12. Modes and Playlists

## 12.1 Launch Modes

### Mode A — Tutorial

Highly guided. Teaches draw, play, discard, steal, score, and round end.

### Mode B — Practice vs Bot

Safe environment for first-time players.

### Mode C — Live Casual Duel

Unranked 1v1.

### Mode D — Live Ranked Duel

Primary competitive mode.

### Mode E — Async Duel

Major retention mode.

### Mode F — Private Table

Invite-based friend play.

### Mode G — Daily Challenge

Solo scenario.

## 12.2 Post-Launch Modes

* 4-player ranked tables if balance and social performance justify it
* tournaments / bracket weekends
* guild or club competition
* cooperative event challenges
* spectator mode

---

# 13. Progression and Meta Systems

## 13.1 Core Progression Philosophy

Monetization and progression must not alter letter odds, scoring power, or word legality in ranked play.

### Allowed Progression Rewards

* cosmetics
* titles
* profile frames
* card backs
* board themes
* emotes
* win effects
* seasonal badges

### Forbidden Progression Rewards

* stronger wild cards
* extra draws
* custom weighted letter distributions in ranked
* hidden paid advantages

## 13.2 Account Level

Players gain XP from:

* completing matches
* finishing tutorial steps
* daily quests
* event participation
* sportsmanlike play bonuses if implemented

## 13.3 Ranked Ladder

### Recommended Structure

* Bronze
* Silver
* Gold
* Platinum
* Diamond
* Master
* Grandmaster / Champion

Seasons reset softly with rewards.

## 13.4 Quests and Missions

Examples:

* win one live duel
* complete three async turns
* make two captures in one day
* form one 7+ letter word
* play with a friend

## 13.5 Collections

Players can collect purely cosmetic unlockables tied to seasons, events, and achievements.

---

# 14. Monetization Strategy

## 14.1 Monetization Principles

* no pay-to-win
* low friction for casual players
* cosmetic-first
* optional convenience only where fair
* ads must not destroy the premium-feeling competitive loop

## 14.2 Recommended Monetization Model

### Free-to-Play Core

Players can access the main game free.

### Monetized Layers

* cosmetic shop
* premium seasonal pass
* optional ad-removal purchase
* premium board/card packs
* event bundles with cosmetics only

### Optional Ads

Use carefully in casual / solo layers only.
Avoid intrusive ads in ranked or friend play.

## 14.3 Premium Alternative

If the project is positioned as a more premium word game, one-time purchase plus cosmetic DLC is viable, but F2P is generally better for global multiplayer liquidity.

---

# 15. User Experience and Interface Design

## 15.1 UX Goals

* every move should feel legible
* every rule should feel enforced, not argued
* every steal should feel dramatic
* every match should be easy to enter and hard to abandon

## 15.2 Core Screens

* splash / login
* tutorial onboarding
* home lobby
* live play queue screen
* async inbox
* private room lobby
* match screen
* round-end summary
* match-end summary
* profile / rank / season page
* shop / cosmetics
* settings / notifications / parental controls

## 15.3 In-Match Layout

### Must Display Clearly

* hand letters
* stock and discard
* own played words
* opponent played words
* current score
* current turn
* timer
* active Rule Modifier
* play preview panel

## 15.4 Critical Interaction Patterns

* tap letters to compose word
* drag to reorder easily
* one-tap select opponent word for capture attempt
* preview before commit
* undo during composition before final submission

## 15.5 Capture Animation Requirements

When a capture occurs, the UI should:

1. spotlight the old word
2. show retained letters
3. show added letters entering
4. morph into the new word
5. show score swing
6. update ownership clearly

This is one of the most important delight moments in the entire product.

---

# 16. Onboarding and Teaching Strategy

## 16.1 Teaching Goals

Teach the player in layers:

* letters and hand
* make a word
* draw and discard
* capture and transform
* scoring and round end
* advanced tactics

## 16.2 Tutorial Sequence

### Lesson 1 — Make a Word

Player forms a simple word from a starter hand.

### Lesson 2 — Draw or Discard

Player sees why discard choice matters.

### Lesson 3 — Capture

Player transforms an opponent word with an added letter.

### Lesson 4 — End the Round

Player empties the hand and sees penalties.

### Lesson 5 — Arena Modifier

Player experiences one rule modifier.

## 16.3 New Player Protection

For first several matches:

* softer matchmaking
* optional hints in casual modes
* simplified rule set if needed
* loss-framing that emphasizes learning, not failure

---

# 17. Bot Design

## 17.1 Why Bots Matter

Bots support:

* onboarding
* practice
* queue-fill backup for low concurrency regions if necessary
* testing and QA

## 17.2 Bot Skill Tiers

* Beginner Bot
* Standard Bot
* Advanced Bot
* Event Bot variants later

## 17.3 Bot Behavior Goals

Bots should feel human enough for learning but not deceptive in ranked contexts. If bots are ever used to fill casual queues, disclosure policy must be explicit.

---

# 18. Balance and Tuning Framework

## 18.1 Balance Targets

The game should reward skill without allowing dominant runaway patterns.

## 18.2 Key Variables to Tune

* letter distribution
* wild card power
* hand size
* timer lengths
* capture bonus values
* remaining-letter penalties
* round length pacing
* Rule Modifier pool frequency

## 18.3 Balance Risks

* long-word snowballing
* vowel starvation
* overly oppressive stealing
* excessive luck in opening hands
* weak comeback potential

## 18.4 Safety Valve System — Word Shield

Recommended optional V2 mechanic for selected playlists, not necessarily MVP default:

* each player receives **1 Shield** per match
* Shield protects one owned word from capture until that player’s next turn

Purpose:

* reduce feel-bad chain steals
* create tactical timing decisions
* provide comeback tools

This should be tested carefully before default inclusion.

---

# 19. Content Policy and Dictionary Governance

## 19.1 Dictionary Must Be Centralized

All legal-word decisions come from the server’s approved lexicon.

## 19.2 Offensive Content Handling

Because dictionary products can contain problematic terms, the game must maintain a filtered policy layer for:

* slurs
* hateful terms
* disallowed abuse words
* names / identifiers if not allowed in ranked

## 19.3 Naming and Social Safety

* username filters
* reporting tools
* mute/block tools
* private-room privacy controls

---

# 20. Live Operations Strategy

## 20.1 Seasonal Cadence

A season should introduce some combination of:

* new cosmetic rewards
* curated Rule Modifiers
* new board theme
* ladder reset
* limited-time event goals

## 20.2 Weekly Cadence

Examples:

* weekend capture bonus event
* async marathon quest
* featured modifier rotation
* friend challenge objective

## 20.3 Daily Cadence

* daily challenge
* daily quests
* shop refresh
* async notifications

---

# 21. Analytics and Success Metrics

## 21.1 Product-Level Metrics

* D1 retention
* D7 retention
* D30 retention
* daily active users
* monthly active users
* session frequency
* average session length
* async games per active user
* live match completion rate

## 21.2 Match-Level Metrics

* turns per round
* rounds per match
* match duration
* timeout rate
* disconnect rate
* valid play rate
* average score spread
* capture frequency
* long-word frequency
* usage rate of discard pickup vs stock draw

## 21.3 Onboarding Metrics

* tutorial completion rate
* first-match completion rate
* first-win conversion
* first-capture conversion
* day-1 PvP entry rate

## 21.4 Fairness Metrics

* comeback frequency
* snowball rate after first capture
* opener advantage rate
* wild-card win-rate impact
* surrender rate after opponent capture

## 21.5 Monetization Metrics

* conversion rate
* average revenue per daily active user
* battle pass attach rate
* cosmetic purchase frequency
* ad opt-in / watch-through in solo modes

---

# 22. MVP Scope Recommendation

## 22.1 MVP Must Include

* polished core ruleset
* live 1v1 casual
* live 1v1 ranked
* async 1v1
* private room friend matches
* tutorial
* bot practice
* one official dictionary mode
* score preview and capture visualization
* profile and progression basics
* limited cosmetics
* analytics foundation
* notifications for async turns

## 22.2 MVP Nice-to-Have

* 2 to 4 player private tables
* Daily Challenge
* first event modifier playlist
* basic seasonal track

## 22.3 Post-MVP

* expanded async social tools
* tournaments
* guilds/clubs
* spectator mode
* replay sharing
* advanced rule sets and event playlists
* multiple languages if feasible

---

# 23. Technical Design Constraints for Game Design

This is not a full engineering spec, but the game design must acknowledge implementation realities.

## 23.1 Server Authority

Critical gameplay state must be server authoritative for:

* deck state
* hand legality
* word validation
* score changes
* timers
* rank results

## 23.2 Determinism

All core match actions should be deterministic and replayable.

## 23.3 Latency Tolerance

The game must feel good across regions because it is turn-based and does not depend on reaction windows.

## 23.4 Notification Dependence

Async mode requires reliable push notification design and clear in-app inbox behavior.

---

# 24. Production and Content Risks

## 24.1 Major Design Risks

### Risk A — Too derivative

Mitigation:

* emphasize Rule Modifiers, async/live structure, and word lineage identity
* strong presentation and UX

### Risk B — Skill gap drives churn

Mitigation:

* beginner onboarding
* softer casual matchmaking
* practice bots
* family mode
* optional shield / comeback tuning

### Risk C — Rules feel too complicated

Mitigation:

* guided tutorial
* clean previews
* simplified default modes
* hide advanced options until later

### Risk D — Global multiplayer liquidity

Mitigation:

* async 1v1 at launch
* cross-region friendly design
* prioritize 1v1 ranked first
* use private invite rooms to leverage social graphs

### Risk E — Dictionary disputes / offensive words

Mitigation:

* centralized dictionary
* policy filter layer
* transparent help text

### Risk F — IP ambiguity

Mitigation:

* confirm rights before branding or direct rules-port claims
* if rights unclear, ship as spiritual successor with original title and fully original presentation

---

# 25. Final Product Recommendation

## 25.1 Recommended Launch Identity

WIT V2 should launch as a **global multiplayer word strategy card game** with two clear promises:

1. **Classic tactical word play**
2. **Modern online rivalry and replayability**

## 25.2 Recommended Launch Priorities

Priority order:

1. core rules feel excellent
2. live 1v1 and async 1v1 feel excellent
3. captures are thrilling and readable
4. onboarding is smooth
5. progression and cosmetics support retention
6. larger tables and broader event systems expand after proof of retention

## 25.3 Final Design Thesis

Do not attempt to win by claiming absolute originality of the word-steal concept. Win by executing the **best version of this fantasy**: a polished, highly social, strategically rich, globally playable word duel where players feel clever every few seconds.

That is the correct product path.

---

# 26. Final V2 Rule Summary (Player-Facing Condensed Form)

This condensed form is useful for future adaptation into a public rules screen.

## Objective

Empty your hand and outscore your opponents by building words, stealing words, and transforming them into better ones.

## Setup

Each player starts with 9 letters. One discard is revealed. The rest form the stock.

## On Your Turn

1. Draw from the stock or take the top discard.
2. Play new words from your hand and/or capture an existing word by adding letters and transforming it into a new valid word.
3. If you still have letters left, discard one.

## Capturing

To capture, you must use every letter in the original word, add at least one new letter, and form a new legal word.

## Round End

The round ends when a player empties their hand through plays and/or a final discard, or when the stock runs out under the playlist rules.

## Scoring

Longer words score more. Captures earn bonus points for the letters you add. Unused letters remaining in hand at round end reduce your score.

## Win

In most digital modes, win 2 rounds to win the match. In Classic custom rooms, optional score-race rules may be enabled.

---

# 27. Closing Statement

WIT V2 should be built as a polished multiplayer-first product, not merely a digital transcription of a paper rules sheet. The correct strategy is to preserve the elegance of word formation and capture while upgrading everything around it: rules clarity, online fairness, social frictionlessness, global accessibility, event structure, progression, and visual delight.

The game is strongest when two players around the world feel like they are in a tense little battle of wit, timing, and language — and when every brilliant steal becomes a story worth replaying.
