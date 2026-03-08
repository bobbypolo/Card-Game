"""Deterministic prd.json generator from PLAN.md.

Replaces LLM-based prd.json generation (plan/SKILL.md Step 7) with a
deterministic parser.  Reads PLAN.md, extracts phases, criteria, testing
strategy, verification commands, and computes scope/complexity/dependencies.

Usage:
    python prd_generator.py --plan PATH [--output PATH] [--dry-run]

Exit codes:
    0 = Success (prd.json written or printed)
    1 = Parse errors (partial prd.json written with parseError fields)
    2 = Bad arguments or file not found
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Imports from sibling modules
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _qa_lib import _DEFAULT_COMPLEXITY_THRESHOLDS, compute_plan_hash
from plan_validator import (
    _extract_done_when_items,
    _extract_verification_command,
    _split_plan_into_phases,
)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Phase header: "## Phase N: Title" or "## Phase N — Title"
_PHASE_NUM_RE = re.compile(r"##\s+Phase\s+(\d+)\s*[:—–-]\s*(.*)", re.IGNORECASE)

# R-marker ID from a Done When bullet (supports AC-level IDs)
_R_ID_RE = re.compile(r"^(R-P\d+-\d{2}(?:-AC\d+)?):\s*(.*)")

# Phase Type field: **Phase Type**: `module`
_PHASE_TYPE_RE = re.compile(r"\*\*Phase\s+Type\*\*\s*:\s*`?(\w+)`?", re.IGNORECASE)

# Changes table row: | Action | File | Description | Test File | Test Type |
_CHANGES_ROW_RE = re.compile(
    r"^\|\s*(ADD|MODIFY|CREATE|DELETE)\s*\|"
    r"\s*`?([^`|\n]+?)`?\s*\|"  # File
    r"\s*([^|\n]*?)\s*\|"  # Description
    r"(?:\s*`?([^`|\n]*?)`?\s*\|)?"  # Test File (optional 4th column)
    r"(?:\s*([^|\n]*?)\s*\|)?",  # Test Type (optional 5th column)
    re.MULTILINE,
)

# Testing Strategy row: | What | Type | Real/Mock | Justification | Test File |
_STRATEGY_ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|"  # What
    r"\s*([^|]+?)\s*\|"  # Type
    r"\s*([^|]*?)\s*\|"  # Real / Mock
    r"\s*([^|]*?)\s*\|"  # Justification
    r"\s*`?([^`|]*?)`?\s*\|",  # Test File
    re.MULTILINE,
)

_VALID_PHASE_TYPES = frozenset({"foundation", "module", "integration", "e2e"})


# ---------------------------------------------------------------------------
# Phase parsing helpers
# ---------------------------------------------------------------------------


def _parse_phase_header(header: str) -> tuple[int, str]:
    """Extract phase number and title from a phase header line.

    Returns (phase_number, title). Raises ValueError if unparseable.
    """
    m = _PHASE_NUM_RE.search(header)
    if m:
        return int(m.group(1)), m.group(2).strip()
    # Fallback: try just extracting the number
    num_match = re.search(r"Phase\s+(\d+)", header, re.IGNORECASE)
    if num_match:
        title = header.split(":", 1)[1].strip() if ":" in header else ""
        return int(num_match.group(1)), title
    raise ValueError(f"Cannot parse phase header: {header}")


def _extract_phase_type(body: str) -> str | None:
    """Extract the Phase Type field from a phase body."""
    m = _PHASE_TYPE_RE.search(body)
    if m:
        val = m.group(1).lower().strip()
        return val if val in _VALID_PHASE_TYPES else None
    return None


def _extract_changes_table(body: str) -> list[dict]:
    """Extract rows from the Changes table in a phase body.

    Returns list of dicts with keys: action, file, description, test_file, test_type.
    """
    rows = []
    for m in _CHANGES_ROW_RE.finditer(body):
        action = m.group(1).strip().upper()
        filepath = m.group(2).strip()
        description = m.group(3).strip() if m.group(3) else ""
        test_file = m.group(4).strip() if m.group(4) else ""
        test_type = m.group(5).strip().lower() if m.group(5) else ""

        # Clean up test_file: remove N/A variants
        if test_file.lower() in ("n/a", "n/a (self)", "(self)", "—", "-", ""):
            test_file = ""

        rows.append(
            {
                "action": action,
                "file": filepath,
                "description": description,
                "test_file": test_file,
                "test_type": test_type,
            }
        )
    return rows


def _extract_testing_strategy(body: str) -> list[dict]:
    """Extract rows from the Testing Strategy table.

    Returns list of dicts with keys: what, type, test_file.
    """
    # Find the Testing Strategy section
    in_strategy = False
    strategy_lines: list[str] = []
    for line in body.splitlines():
        if "testing strategy" in line.lower() and line.strip().startswith("#"):
            in_strategy = True
            continue
        if in_strategy:
            stripped = line.strip()
            if stripped.startswith("###") or stripped.startswith("## "):
                break
            strategy_lines.append(line)

    if not strategy_lines:
        return []

    rows = []
    strategy_text = "\n".join(strategy_lines)
    for m in _STRATEGY_ROW_RE.finditer(strategy_text):
        what = m.group(1).strip()
        type_val = m.group(2).strip().lower()
        test_file = m.group(5).strip()

        # Skip header/separator rows
        if "what" in what.lower() or "---" in what:
            continue

        rows.append(
            {
                "what": what,
                "type": type_val,
                "test_file": test_file,
            }
        )
    return rows


def _infer_test_type(strategy_rows: list[dict]) -> str:
    """Infer testType for a criterion from the Testing Strategy table.

    Falls back to "manual" if no match found.
    """
    for row in strategy_rows:
        test_type = row["type"]
        if test_type in ("unit", "integration", "e2e", "end-to-end", "system"):
            # Normalize type
            if test_type in ("e2e", "end-to-end", "system"):
                return "e2e"
            return test_type
    return "manual"


def _infer_test_file(changes_rows: list[dict], strategy_rows: list[dict]) -> str | None:
    """Infer testFile for a criterion from Changes and Testing Strategy tables.

    Returns None if no test file can be inferred.
    """
    # First: check Changes table for test files
    test_files_from_changes = set()
    for row in changes_rows:
        if row["test_file"] and row["test_file"].endswith(".py"):
            test_files_from_changes.add(row["test_file"])

    # Check Testing Strategy for test files
    test_files_from_strategy = set()
    for row in strategy_rows:
        tf = row.get("test_file", "")
        if tf and tf.endswith(".py"):
            test_files_from_strategy.add(tf)

    # Combine all test files found
    all_test_files = test_files_from_changes | test_files_from_strategy

    # If exactly one test file, use it
    if len(all_test_files) == 1:
        return all_test_files.pop()

    # If multiple, return the first from strategy (more specific)
    if test_files_from_strategy:
        return sorted(test_files_from_strategy)[0]
    if test_files_from_changes:
        return sorted(test_files_from_changes)[0]

    return None


def _classify_gate_cmd(cmd: str) -> dict[str, str]:
    """Classify a verification command into gateCmds buckets.

    Returns dict mapping gate type to command string.
    """
    gates: dict[str, str] = {}
    if not cmd:
        return gates

    # Multi-line: split and classify each
    lines = [line.strip() for line in cmd.splitlines() if line.strip()]

    if len(lines) == 1:
        line = lines[0]
        if re.search(r"ruff|eslint|lint", line, re.IGNORECASE):
            # If also has pytest, it's a compound command
            if re.search(r"pytest", line, re.IGNORECASE):
                gates["unit"] = line
            else:
                gates["lint"] = line
        elif re.search(r"pytest.*integration", line, re.IGNORECASE):
            gates["integration"] = line
        else:
            gates["unit"] = line
    else:
        for line in lines:
            if re.search(r"ruff|eslint|lint", line, re.IGNORECASE):
                gates["lint"] = line
            elif re.search(r"pytest.*integration", line, re.IGNORECASE):
                gates["integration"] = line
            elif re.search(r"pytest", line, re.IGNORECASE):
                gates["unit"] = line
            else:
                # Default: unit
                gates.setdefault("unit", line)

    return gates


def _compute_scope(changes_rows: list[dict]) -> list[str]:
    """Compute scope (unique top-level directories) from Changes table files."""
    dirs = set()
    for row in changes_rows:
        filepath = row["file"]
        # Extract first path component
        parts = filepath.replace("\\", "/").split("/")
        if len(parts) > 1:
            dirs.add(parts[0] + "/")
        elif filepath:
            dirs.add(filepath)
    return sorted(dirs)


def _compute_component(changes_rows: list[dict]) -> str:
    """Compute component (most common top-level directory) from Changes table."""
    dirs: list[str] = []
    for row in changes_rows:
        filepath = row["file"]
        parts = filepath.replace("\\", "/").split("/")
        if len(parts) > 1:
            dirs.append(parts[0] + "/")
    if dirs:
        counter = Counter(dirs)
        return counter.most_common(1)[0][0]
    return ""


def _compute_complexity(scope: list[str], criteria_count: int) -> tuple[str, int]:
    """Compute complexity and maxTurns from scope and criteria count.

    Returns (complexity_label, maxTurns).
    """
    score = len(scope) + criteria_count
    # Cross-package detection
    unique_dirs = set(scope)
    if len(unique_dirs) > 2:
        score += 3

    thresholds = _DEFAULT_COMPLEXITY_THRESHOLDS
    if score <= thresholds["simple"]["max_score"]:
        return "simple", thresholds["simple"]["maxTurns"]
    elif score <= thresholds["medium"]["max_score"]:
        return "medium", thresholds["medium"]["maxTurns"]
    else:
        return "complex", thresholds["complex"]["maxTurns"]


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_prd(plan_path: Path) -> dict:
    """Generate prd.json dict from a PLAN.md file.

    Returns dict with keys: version, planRef, conventionsRef, plan_hash, stories.
    Each story may have a 'parseError' key if extraction failed for that phase.
    """
    content = plan_path.read_text(encoding="utf-8")
    phases = _split_plan_into_phases(content)

    stories: list[dict] = []
    all_story_files: dict[str, set[str]] = {}  # story_id -> set of files

    for header, body in phases:
        try:
            phase_num, title = _parse_phase_header(header)
        except ValueError as exc:
            stories.append(
                {
                    "parseError": str(exc),
                    "passed": None,
                }
            )
            continue

        story_id = f"STORY-{phase_num:03d}"

        # Extract phase type
        phase_type = _extract_phase_type(body)

        # Extract Changes table
        changes_rows = _extract_changes_table(body)

        # Extract Testing Strategy
        strategy_rows = _extract_testing_strategy(body)

        # Extract Done When items
        done_when_items = _extract_done_when_items(body)

        # Parse acceptance criteria
        acceptance_criteria = []
        for item in done_when_items:
            m = _R_ID_RE.match(item)
            if m:
                cid = m.group(1)
                criterion_text = m.group(2).strip()

                # Infer testType from strategy
                test_type = _infer_test_type(strategy_rows)

                # Infer testFile
                test_file = _infer_test_file(changes_rows, strategy_rows)

                acceptance_criteria.append(
                    {
                        "id": cid,
                        "criterion": criterion_text,
                        "testType": test_type,
                        "testFile": test_file,
                    }
                )
            else:
                # Criterion without R-ID — include with parseError
                acceptance_criteria.append(
                    {
                        "id": "",
                        "criterion": item,
                        "testType": "manual",
                        "testFile": None,
                        "parseError": f"Missing R-PN-NN ID in Phase {phase_num}",
                    }
                )

        # Extract verification command
        verification_cmd = _extract_verification_command(body)
        gate_cmds = _classify_gate_cmd(verification_cmd)

        # Compute scope, component, complexity
        scope = _compute_scope(changes_rows)
        component = _compute_component(changes_rows)
        complexity, max_turns = _compute_complexity(scope, len(acceptance_criteria))

        # Track files for dependency analysis
        story_files = {row["file"] for row in changes_rows}
        all_story_files[story_id] = story_files

        story = {
            "id": story_id,
            "description": title,
            "phase": phase_num,
            "phase_type": phase_type,
            "component": component,
            "scope": scope,
            "complexity": complexity,
            "maxTurns": max_turns,
            "dependsOn": [],
            "parallelGroup": None,
            "acceptanceCriteria": acceptance_criteria,
            "gateCmds": gate_cmds,
            "passed": False,
            "verificationRef": None,
        }
        stories.append(story)

    # -- Dependency analysis --
    _assign_dependencies(stories, all_story_files)

    # Compute plan hash
    plan_hash = compute_plan_hash(plan_path)

    return {
        "version": "2.0",
        "planRef": ".claude/docs/PLAN.md",
        "conventionsRef": ".claude/docs/knowledge/conventions.md",
        "plan_hash": plan_hash,
        "stories": stories,
    }


def _assign_dependencies(
    stories: list[dict], all_story_files: dict[str, set[str]]
) -> None:
    """Assign dependsOn and parallelGroup fields based on file overlap."""
    valid_stories = [s for s in stories if "parseError" not in s]

    parallel_group = 1
    for j, story_j in enumerate(valid_stories):
        sid_j = story_j["id"]
        files_j = all_story_files.get(sid_j, set())

        for i in range(j):
            story_i = valid_stories[i]
            sid_i = story_i["id"]
            files_i = all_story_files.get(sid_i, set())

            if files_i & files_j:
                # Overlapping files — sequential dependency
                if sid_i not in story_j["dependsOn"]:
                    story_j["dependsOn"].append(sid_i)

    # Assign parallel groups for stories with no dependencies
    independent_stories = [s for s in valid_stories if not s["dependsOn"]]
    if len(independent_stories) > 1:
        # Group non-overlapping independent stories
        groups: list[list[dict]] = []
        for story in independent_stories:
            sid = story["id"]
            files = all_story_files.get(sid, set())
            placed = False
            for group in groups:
                # Check if this story's files overlap with any in the group
                group_files = set()
                for gs in group:
                    group_files |= all_story_files.get(gs["id"], set())
                if not (files & group_files):
                    group.append(story)
                    placed = True
                    break
            if not placed:
                groups.append([story])

        for group in groups:
            if len(group) > 1:
                for story in group:
                    story["parallelGroup"] = parallel_group
                parallel_group += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for prd.json generation."""
    parser = argparse.ArgumentParser(
        description="Generate prd.json deterministically from PLAN.md"
    )
    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="Path to PLAN.md",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for prd.json (default: .claude/prd.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prd.json to stdout without writing",
    )
    args = parser.parse_args()

    if not args.plan.is_file():
        sys.stderr.write(f"Error: Plan file not found: {args.plan}\n")
        sys.exit(2)

    try:
        prd = generate_prd(args.plan)
    except Exception as exc:
        sys.stderr.write(f"Error generating prd.json: {exc}\n")
        sys.exit(2)

    output_json = json.dumps(prd, indent=2, ensure_ascii=False)

    if args.dry_run:
        sys.stdout.buffer.write((output_json + "\n").encode("utf-8"))
    else:
        output_path = args.output or Path(".claude/prd.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json + "\n", encoding="utf-8")
        sys.stdout.write(f"Written: {output_path}\n")

    # Check for parse errors
    has_errors = any("parseError" in s for s in prd.get("stories", []))
    if has_errors:
        sys.stderr.write("Warning: Some phases had parse errors\n")
        sys.exit(1)

    # Summary
    story_count = len(prd.get("stories", []))
    criteria_count = sum(
        len(s.get("acceptanceCriteria", [])) for s in prd.get("stories", [])
    )
    sys.stderr.write(
        f"Generated: {story_count} stories, {criteria_count} criteria, "
        f"hash={prd['plan_hash'][:12]}...\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
