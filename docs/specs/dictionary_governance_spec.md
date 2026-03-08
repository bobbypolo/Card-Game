# Dictionary and Lexicon Governance Spec
**Project:** WIT V2

## Overview
Because dictionary management is a profound risk source for word games, WIT V2 operates under an explicitly tracked Lexicon context engine.

## Policies

**1. Source Lexicon & Licensing**
- The application shall fork a baseline open-source valid dictionary (e.g., specific CSW/NWL/Collins variations), stripped of proper nouns safely.
- **Executive Approval:** Any ingestion of a new root lexicon MUST pass legal/licensing approval via written sign-off from the executive team before PR merge.

**2. Banned-Word Policy Layer**
- An administrative blocklist layer must prevent slur generation and offensive combinations. This blocklist sits ATOP the valid dictionary.

**3. Versioning Context & Immutability**
- Matches are irrevocably locked to the string version of the Lexicon active precisely at the Match generation (e.g., `lexicon_v_1.0.4`).
- Mid-match updates are completely disallowed. 
- An asynchronous match running for 14 days will respectfully finish executing under the lexicon version it began with, even if the primary server lexicon evaluates to `lexicon_v_1.0.5`.

**4. Admin Audit Trail**
- Modifying the Lexicon Blocklist or publishing a new Lexicon Context requires passing through an Admin CMS Tool.
- Every commit or update via the CMS is indelibly logged to an `admin_audit_log` Postgres table, tracking the `Admin_ID`, `Timestamp`, `Action_Type`, and `Diff`.

**5. Rollback Policy**
- A previous Lexicon Version can be instantly restored via the Admin CMS "Revert" function, propagating to the active Game Server instances caching layer within 60 seconds.

**6. Capture "Root" Policy Enforcement**
- If Ranked standard specifies strict prefix/plural rules, the Server Dictionary Engine must compute lexical stems/roots for validation.
