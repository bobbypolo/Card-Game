#!/usr/bin/env python3
"""Pre-Bash Guard - Block dangerous commands before execution.

Exit codes:
  0 = Allow command
  2 = Block command (shows message to user)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import audit_log, parse_hook_stdin

# Patterns that should be blocked with explanations.
# Each pattern optionally allows a leading 'sudo ' prefix.
DENY_PATTERNS = [
    # Destructive file operations
    (r"rm\s+(-rf?|--recursive).*[/~*]", "Recursive delete of root/home/glob"),
    (r"rm\s+-rf?\s+\.\s*$", "Delete current directory"),
    (r"rm\s+-rf?\s+\*", "Delete all files with glob"),
    (r"\brd\s+/s\s+/q\b", "Windows recursive delete"),
    (r"\brmdir\s+/s\s+/q\b", "Windows rmdir recursive delete"),
    (r"\bdel\s+/f\b", "Windows force delete"),
    # Destructive find / xargs
    (r"find\b.*-delete\b", "Destructive find -delete"),
    (r"xargs\b.*\brm\b", "Piped rm via xargs"),
    # Disk/filesystem operations
    (r">\s*/dev/sd[a-z]", "Write to raw disk device"),
    (r"\bmkfs\.", "Format filesystem"),
    (r"dd\s+.*of=/dev/", "Raw disk write with dd"),
    (r"\bformat\s+[A-Z]:", "Format disk drive"),
    # Permission disasters
    (r"chmod\s+(-R\s+)?777\s+/", "Chmod 777 on root paths"),
    # Git destructive operations
    (r"git\s+push.*--force.*main", "Force push to main branch"),
    (r"git\s+push.*--force.*master", "Force push to master branch"),
    (r"git\s+reset\s+--hard\s+origin", "Hard reset to origin"),
    (r"git\s+reset\s+--hard\s*$", "Bare hard reset (no target)"),
    (
        r"git\s+reset\s+--hard\s+(?![0-9a-fA-F]{7,}\s*$)(?!(?:HEAD|ORIG_HEAD|MERGE_HEAD|FETCH_HEAD)(?:[~^]\d*)?\s*$)",
        "Hard reset to non-hash target",
    ),
    (r"git\s+clean\s+-fd", "Git clean (removes untracked)"),
    (r"git\s+branch\s+-D\b", "Force delete git branch", 0),
    # Git mass discard
    (r"git\s+checkout\s+--\s+\.", "Mass discard all changes"),
    (r"git\s+restore\s+\.", "Mass discard all changes"),
    # Database destructive
    (r"\bdrop\s+database\b", "Drop database"),
    (r"\btruncate\b", "Truncate table"),
    # Remote code execution risks
    (r"curl.*\|\s*sh", "Piping curl to shell"),
    (r"wget.*\|\s*sh", "Piping wget to shell"),
    (r"eval\s*\$\(curl", "Eval with curl"),
    # Profile injection
    (r"echo.*>>\s*~/\.bashrc", "Profile injection via .bashrc"),
    # Fork bomb
    (r":\s*\(\s*\)\s*\{.*\}", "Fork bomb pattern"),
]


# Interpreter/wrapper patterns whose inline argument should be recursively unwrapped.
# Each entry is (wrapper_regex, arg_group_index) where the regex captures the
# inline script in group 1.
_EXEC_WRAPPER_PATTERNS = [
    # python -c "..." or python3 -c "..."
    re.compile(r"^\s*python3?\s+-c\s+(?:\"(.*)\"|'(.*)')\s*$", re.DOTALL),
    # bash -c "..." or sh -c "..."
    re.compile(r"^\s*(?:bash|sh)\s+-c\s+(?:\"(.*)\"|'(.*)')\s*$", re.DOTALL),
    # pwsh -Command "..." or powershell -Command "..."
    re.compile(
        r"^\s*(?:pwsh|powershell)\s+-(?:Command|c)\s+(?:\"(.*)\"|'(.*)')\s*$",
        re.DOTALL | re.IGNORECASE,
    ),
    # node -e "..."
    re.compile(r"^\s*node\s+-e\s+(?:\"(.*)\"|'(.*)')\s*$", re.DOTALL),
    # perl -e "..."
    re.compile(r"^\s*perl\s+-e\s+(?:\"(.*)\"|'(.*)')\s*$", re.DOTALL),
    # ruby -e "..."
    re.compile(r"^\s*ruby\s+-e\s+(?:\"(.*)\"|'(.*)')\s*$", re.DOTALL),
]

_MAX_UNWRAP_DEPTH = 4


def _unwrap_exec_chain(cmd: str, depth: int = 0) -> list[str]:
    """Recursively unwrap interpreter/wrapper invocations.

    Returns a list of command strings in the execution chain.
    Recursion is capped at _MAX_UNWRAP_DEPTH to prevent infinite recursion.

    Examples:
        "bash -c 'echo hi'" -> ["bash -c 'echo hi'", "echo hi"]
        "python -c \"os.system('rm')\"" -> ["python -c ...", "os.system('rm')"]
    """
    if depth >= _MAX_UNWRAP_DEPTH:
        return [cmd]

    for wrapper_re in _EXEC_WRAPPER_PATTERNS:
        m = wrapper_re.match(cmd)
        if m:
            # Find the first non-None group (double-quoted vs single-quoted)
            inner = next((g for g in m.groups() if g is not None), None)
            if inner is not None:
                # Recursively unwrap the inner script
                inner_chain = _unwrap_exec_chain(inner, depth + 1)
                return [cmd] + inner_chain

    return [cmd]


def _check_single(normalized: str) -> tuple[bool, str]:
    """Check one normalized command string against DENY_PATTERNS."""
    for entry in DENY_PATTERNS:
        if len(entry) == 3:
            pattern, reason, flags = entry
        else:
            pattern, reason = entry
            flags = re.IGNORECASE
        full_pattern = r"(?:sudo\s+)?" + pattern
        if re.search(full_pattern, normalized, flags):
            return False, reason
    return True, ""


def check_command(cmd: str) -> tuple[bool, str]:
    """Check if command is safe. Returns (allowed, reason).

    DENY_PATTERNS entries may be 2-tuples ``(pattern, reason)`` which default
    to ``re.IGNORECASE``, or 3-tuples ``(pattern, reason, flags)`` for
    per-pattern flag control (e.g. ``0`` for case-sensitive matching).

    The command is unwrapped through any interpreter/wrapper chain (e.g.
    ``bash -c``, ``python -c``, ``pwsh -Command``) before checking, so that
    dangerous payloads embedded in wrapper invocations are caught.
    """
    # Build the chain of commands to check (outer wrapper + all inner scripts)
    chain = _unwrap_exec_chain(cmd)

    for raw in chain:
        # Normalize whitespace: collapse multiple spaces/tabs/newlines to single space
        normalized = re.sub(r"\s+", " ", raw)
        allowed, reason = _check_single(normalized)
        if not allowed:
            return False, reason

    return True, ""


def main():
    data = parse_hook_stdin()
    tool_input = data.get("tool_input", {})
    cmd = tool_input.get("command", "")

    if not cmd:
        sys.exit(0)

    allowed, reason = check_command(cmd)

    if not allowed:
        audit_log("pre_bash_guard", "block", f"{reason}: {cmd[:200]}")
        print(f"[BLOCKED] {reason}")
        print(f"  Command: {cmd[:200]}{'...' if len(cmd) > 200 else ''}")
        print("  To proceed, ask user for explicit confirmation.")
        sys.exit(2)

    audit_log("pre_bash_guard", "allow", cmd[:200])
    sys.exit(0)


if __name__ == "__main__":
    main()
