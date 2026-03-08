#!/usr/bin/env python3
"""Stop hook: blocks completion if code changes are unverified.

Escape hatch: set ADE_ALLOW_UNVERIFIED_STOP=1 environment variable to bypass.
No hidden counter-based escape hatch — the env var is the only override.

Stdin parsing always fails open — NEVER locks user in on parse errors.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import (
    audit_log,
    increment_stop_block_count,
    is_subagent,
    is_worktree_path,
    parse_hook_stdin,
    read_workflow_state,
    update_workflow_state,
)


def main():
    state = read_workflow_state()
    marker_content = state.get("needs_verify")

    # Defense-in-depth: if hook fires in subagent context, allow stop without blocking.
    # Stop is a main-agent event; SubagentStop is a separate event handled elsewhere.
    data = parse_hook_stdin()
    if is_subagent(data):
        audit_log(
            "stop_verify_gate", "subagent_allow", "Subagent context — allowing stop"
        )
        sys.exit(0)

    # Sanitize stale worktree markers -- auto-clear if marker references a worktree path
    if marker_content and is_worktree_path(marker_content):
        update_workflow_state(needs_verify=None)
        audit_log(
            "stop_verify_gate",
            "sanitize",
            f"Cleared worktree marker: {marker_content[:200]}",
        )
        marker_content = None

    if not marker_content:
        # No unverified changes — allow stop
        sys.exit(0)

    # Env var override: ADE_ALLOW_UNVERIFIED_STOP=1 bypasses the block
    if os.environ.get("ADE_ALLOW_UNVERIFIED_STOP") == "1":
        audit_log(
            "stop_verify_gate",
            "env_override_allow",
            f"ADE_ALLOW_UNVERIFIED_STOP=1 — bypassing block for: {marker_content[:200]}",
        )
        print(
            json.dumps(
                {
                    "decision": "warn",
                    "reason": "ADE_ALLOW_UNVERIFIED_STOP=1: stopping with unverified code.",
                }
            )
        )
        sys.exit(0)

    # Block and increment counter
    new_count = increment_stop_block_count()

    reason_detail = f"unverified code: {marker_content}"

    audit_log(
        "stop_verify_gate",
        "block",
        f"Attempt {new_count}, {reason_detail[:200]}",
    )

    if new_count == 1:
        msg = f"Blocked: {reason_detail}. Run tests or /verify before finishing."
    else:
        msg = (
            f"Still blocked: {reason_detail}. Run tests, /verify, "
            f"or set ADE_ALLOW_UNVERIFIED_STOP=1 to bypass."
        )

    print(json.dumps({"decision": "block", "reason": msg}))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # NEVER lock user in — allow stop on any unhandled crash
        print(
            json.dumps(
                {
                    "decision": "warn",
                    "reason": "Stop hook crashed — allowing stop. Check .claude/errors/.",
                }
            )
        )
        sys.exit(0)
