"""Tests for prd_generator.py — deterministic prd.json generation from PLAN.md."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prd_generator import (
    _classify_gate_cmd,
    _compute_complexity,
    _compute_component,
    _compute_scope,
    _extract_changes_table,
    _extract_phase_type,
    _extract_testing_strategy,
    _infer_test_file,
    _infer_test_type,
    _parse_phase_header,
    generate_prd,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_GOOD_PLAN = """\
# Plan: Test Feature

## Goal

Build a test feature.

## System Context

### Files Read

| File | Key Observations |
| ---- | ---------------- |
| foo  | bar              |

---

## Phase 1: Build the Widget

**Phase Type**: `module`

### Changes Table

| Action | File               | Description     | Test File                | Test Type |
| ------ | ------------------ | --------------- | ------------------------ | --------- |
| CREATE | `.claude/hooks/widget.py` | Widget module   | `.claude/hooks/tests/test_widget.py` | unit      |
| CREATE | `.claude/hooks/tests/test_widget.py` | Widget tests | N/A (self)               | unit      |

### Testing Strategy

| What          | Type | Real / Mock | Justification | Test File                           |
| ------------- | ---- | ----------- | ------------- | ----------------------------------- |
| Widget create | unit | Real        | Core logic    | `.claude/hooks/tests/test_widget.py` |

### Done When

- R-P1-01: `widget.py` returns a dict containing keys `name` and `value`
- R-P1-02: `widget.py` rejects empty name input by raising `ValueError`

### Verification Command

```bash
python -m pytest .claude/hooks/tests/test_widget.py -v --tb=short
```

## Phase 2: Integrate the Widget

**Phase Type**: `integration`

### Changes Table

| Action | File               | Description        | Test File                | Test Type   |
| ------ | ------------------ | ------------------ | ------------------------ | ----------- |
| MODIFY | `.claude/hooks/widget.py` | Add integration hooks | `.claude/hooks/tests/test_integration.py` | integration |
| CREATE | `.claude/hooks/tests/test_integration.py` | Integration tests | N/A (self) | integration |

### Testing Strategy

| What               | Type        | Real / Mock | Justification | Test File                               |
| ------------------ | ----------- | ----------- | ------------- | --------------------------------------- |
| Widget integration | integration | Real        | Full stack    | `.claude/hooks/tests/test_integration.py` |

### Done When

- R-P2-01: Widget integrates with the main pipeline
- R-P2-02: Integration tests pass end-to-end

### Verification Command

```bash
ruff check .claude/hooks/widget.py
python -m pytest .claude/hooks/tests/test_integration.py -v --tb=short
```
"""

_AC_LEVEL_PLAN = """\
# Plan: AC-Level IDs

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Testing Strategy

| What | Type | Real / Mock | Justification | Test File      |
| ---- | ---- | ----------- | ------------- | -------------- |
| App  | unit | Real        | Core          | `tests/test_app.py` |

### Done When

- R-P1-01-AC1: returns a dict containing key `name`
- R-P1-01-AC2: rejects empty name by raising `ValueError`
- R-P1-02: logs validation error on empty name

### Verification Command

```bash
python -m pytest tests/ -v
```
"""

_NO_R_ID_PLAN = """\
# Plan: Missing R-IDs

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File | Description | Test File | Test Type |
| ------ | ---- | ----------- | --------- | --------- |
| CREATE | `src/app.py` | App | `tests/test.py` | unit |

### Testing Strategy

| What | Type | Real / Mock | Justification | Test File |
| ---- | ---- | ----------- | ------------- | --------- |
| App  | unit | Real        | Core          | `tests/test.py` |

### Done When

- Widget returns items
- R-P1-01: returns correct output

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


# ---------------------------------------------------------------------------
# Phase header parsing
# ---------------------------------------------------------------------------


class TestParsePhaseHeader:
    def test_colon_separator(self) -> None:
        num, title = _parse_phase_header("## Phase 1: Build the Widget")
        assert num == 1
        assert title == "Build the Widget"

    def test_dash_separator(self) -> None:
        num, title = _parse_phase_header("## Phase 2 - Integration")
        assert num == 2
        assert title == "Integration"

    def test_em_dash_separator(self) -> None:
        num, title = _parse_phase_header("## Phase 3 — E2E Tests")
        assert num == 3
        assert title == "E2E Tests"

    def test_invalid_header_raises(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse"):
            _parse_phase_header("## Not a Phase")


# ---------------------------------------------------------------------------
# Phase type extraction
# ---------------------------------------------------------------------------


class TestExtractPhaseType:
    def test_module_type(self) -> None:
        assert _extract_phase_type("**Phase Type**: `module`") == "module"

    def test_foundation_type(self) -> None:
        assert _extract_phase_type("**Phase Type**: `foundation`") == "foundation"

    def test_integration_type(self) -> None:
        assert _extract_phase_type("**Phase Type**: `integration`") == "integration"

    def test_e2e_type(self) -> None:
        assert _extract_phase_type("**Phase Type**: `e2e`") == "e2e"

    def test_invalid_type_returns_none(self) -> None:
        assert _extract_phase_type("**Phase Type**: `unknown`") is None

    def test_missing_type_returns_none(self) -> None:
        assert _extract_phase_type("No phase type here") is None


# ---------------------------------------------------------------------------
# Changes table extraction
# ---------------------------------------------------------------------------


class TestExtractChangesTable:
    def test_extracts_rows(self) -> None:
        body = (
            "### Changes Table\n\n"
            "| Action | File | Description | Test File | Test Type |\n"
            "| ------ | ---- | ----------- | --------- | --------- |\n"
            "| CREATE | `src/app.py` | App | `tests/test.py` | unit |\n"
            "| MODIFY | `src/lib.py` | Lib | N/A | manual |\n"
        )
        rows = _extract_changes_table(body)
        assert len(rows) == 2
        assert rows[0]["file"] == "src/app.py"
        assert rows[0]["test_file"] == "tests/test.py"
        assert rows[1]["test_file"] == ""  # N/A cleaned up

    def test_empty_body(self) -> None:
        assert _extract_changes_table("No table here") == []


# ---------------------------------------------------------------------------
# Testing Strategy extraction
# ---------------------------------------------------------------------------


class TestExtractTestingStrategy:
    def test_extracts_rows(self) -> None:
        body = (
            "### Testing Strategy\n\n"
            "| What | Type | Real / Mock | Justification | Test File |\n"
            "| ---- | ---- | ----------- | ------------- | --------- |\n"
            "| App  | unit | Real        | Core          | `test.py` |\n"
        )
        rows = _extract_testing_strategy(body)
        assert len(rows) == 1
        assert rows[0]["type"] == "unit"
        assert rows[0]["test_file"] == "test.py"

    def test_empty_body(self) -> None:
        assert _extract_testing_strategy("No strategy here") == []


# ---------------------------------------------------------------------------
# Test type inference
# ---------------------------------------------------------------------------


class TestInferTestType:
    def test_unit_type(self) -> None:
        assert _infer_test_type([{"type": "unit"}]) == "unit"

    def test_integration_type(self) -> None:
        assert _infer_test_type([{"type": "integration"}]) == "integration"

    def test_e2e_normalized(self) -> None:
        assert _infer_test_type([{"type": "e2e"}]) == "e2e"
        assert _infer_test_type([{"type": "end-to-end"}]) == "e2e"
        assert _infer_test_type([{"type": "system"}]) == "e2e"

    def test_manual_fallback(self) -> None:
        assert _infer_test_type([]) == "manual"
        assert _infer_test_type([{"type": "manual"}]) == "manual"


# ---------------------------------------------------------------------------
# Test file inference
# ---------------------------------------------------------------------------


class TestInferTestFile:
    def test_from_changes_table(self) -> None:
        changes = [{"test_file": "tests/test_app.py"}]
        assert _infer_test_file(changes, []) == "tests/test_app.py"

    def test_from_strategy(self) -> None:
        strategy = [{"test_file": "tests/test_app.py"}]
        assert _infer_test_file([], strategy) == "tests/test_app.py"

    def test_none_when_no_files(self) -> None:
        assert _infer_test_file([], []) is None

    def test_non_py_files_ignored(self) -> None:
        changes = [{"test_file": "README.md"}]
        assert _infer_test_file(changes, []) is None


# ---------------------------------------------------------------------------
# Gate command classification
# ---------------------------------------------------------------------------


class TestClassifyGateCmd:
    def test_single_pytest(self) -> None:
        gates = _classify_gate_cmd("python -m pytest tests/ -v")
        assert "unit" in gates

    def test_single_lint(self) -> None:
        gates = _classify_gate_cmd("ruff check src/")
        assert "lint" in gates

    def test_compound_lint_and_pytest(self) -> None:
        gates = _classify_gate_cmd("ruff check src/ && python -m pytest tests/")
        assert "unit" in gates

    def test_multiline(self) -> None:
        gates = _classify_gate_cmd("ruff check src/\npython -m pytest tests/ -v")
        assert "lint" in gates
        assert "unit" in gates

    def test_integration_pytest(self) -> None:
        gates = _classify_gate_cmd("python -m pytest tests/ -v -k integration")
        assert "integration" in gates

    def test_empty_command(self) -> None:
        assert _classify_gate_cmd("") == {}


# ---------------------------------------------------------------------------
# Scope / component / complexity
# ---------------------------------------------------------------------------


class TestScopeAndComplexity:
    def test_compute_scope(self) -> None:
        rows = [
            {"file": ".claude/hooks/app.py"},
            {"file": ".claude/hooks/tests/test.py"},
            {"file": "src/main.py"},
        ]
        scope = _compute_scope(rows)
        assert ".claude/" in scope
        assert "src/" in scope

    def test_compute_component(self) -> None:
        rows = [
            {"file": ".claude/hooks/a.py"},
            {"file": ".claude/hooks/b.py"},
            {"file": "src/c.py"},
        ]
        assert _compute_component(rows) == ".claude/"

    def test_compute_complexity_simple(self) -> None:
        label, turns = _compute_complexity(["src/"], 3)
        assert label == "simple"
        assert turns == 100

    def test_compute_complexity_medium(self) -> None:
        label, turns = _compute_complexity(["src/", "lib/"], 8)
        assert label == "medium"
        assert turns == 150

    def test_compute_complexity_complex(self) -> None:
        label, turns = _compute_complexity(["a/", "b/", "c/", "d/"], 10)
        assert label == "complex"
        assert turns == 200


# ---------------------------------------------------------------------------
# Full generator: generate_prd()
# ---------------------------------------------------------------------------


class TestGeneratePrd:
    def test_generates_valid_prd_from_good_plan(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_GOOD_PLAN, encoding="utf-8")

        prd = generate_prd(plan)

        assert prd["version"] == "2.0"
        assert prd["plan_hash"] != ""
        assert len(prd["stories"]) == 2

        # Story 1
        s1 = prd["stories"][0]
        assert s1["id"] == "STORY-001"
        assert s1["description"] == "Build the Widget"
        assert s1["phase"] == 1
        assert s1["phase_type"] == "module"
        assert len(s1["acceptanceCriteria"]) == 2
        assert s1["acceptanceCriteria"][0]["id"] == "R-P1-01"
        assert s1["acceptanceCriteria"][0]["testType"] == "unit"
        assert s1["passed"] is False

        # Story 2
        s2 = prd["stories"][1]
        assert s2["id"] == "STORY-002"
        assert s2["phase_type"] == "integration"
        assert len(s2["acceptanceCriteria"]) == 2

    def test_ac_level_ids_extracted(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_AC_LEVEL_PLAN, encoding="utf-8")

        prd = generate_prd(plan)

        criteria_ids = [c["id"] for c in prd["stories"][0]["acceptanceCriteria"]]
        assert "R-P1-01-AC1" in criteria_ids
        assert "R-P1-01-AC2" in criteria_ids
        assert "R-P1-02" in criteria_ids

    def test_missing_r_id_creates_parse_error(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_NO_R_ID_PLAN, encoding="utf-8")

        prd = generate_prd(plan)

        criteria = prd["stories"][0]["acceptanceCriteria"]
        # First item has no R-ID
        assert criteria[0]["id"] == ""
        assert "parseError" in criteria[0]
        # Second item has valid R-ID
        assert criteria[1]["id"] == "R-P1-01"

    def test_dependency_detection(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_GOOD_PLAN, encoding="utf-8")

        prd = generate_prd(plan)

        # Phase 2 modifies widget.py which Phase 1 creates → dependency
        s2 = prd["stories"][1]
        assert "STORY-001" in s2["dependsOn"]

    def test_gate_cmds_classification(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_GOOD_PLAN, encoding="utf-8")

        prd = generate_prd(plan)

        # Phase 1: single pytest → unit
        assert "unit" in prd["stories"][0]["gateCmds"]

        # Phase 2: ruff + pytest → lint and unit
        s2_gates = prd["stories"][1]["gateCmds"]
        assert "lint" in s2_gates or "unit" in s2_gates

    def test_plan_hash_is_deterministic(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_GOOD_PLAN, encoding="utf-8")

        prd1 = generate_prd(plan)
        prd2 = generate_prd(plan)
        assert prd1["plan_hash"] == prd2["plan_hash"]

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        plan = tmp_path / "PLAN.md"
        plan.write_text(_GOOD_PLAN, encoding="utf-8")

        prd = generate_prd(plan)
        # Round-trip through JSON
        serialized = json.dumps(prd)
        deserialized = json.loads(serialized)
        assert deserialized == prd


# ---------------------------------------------------------------------------
# AC-level ID regression: extract_plan_r_markers
# ---------------------------------------------------------------------------


class TestACLevelRegexFix:
    """Verify the regex fix for AC-level IDs in _qa_lib.py functions."""

    def test_extract_plan_r_markers_finds_ac_level(self, tmp_path: Path) -> None:
        from _qa_lib import extract_plan_r_markers

        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "- R-P1-01-AC1: first criterion\n"
            "- R-P1-01-AC2: second criterion\n"
            "- R-P1-02: base level criterion\n",
            encoding="utf-8",
        )
        result = extract_plan_r_markers(plan)
        assert "R-P1-01-AC1" in result
        assert "R-P1-01-AC2" in result
        assert "R-P1-02" in result

    def test_compute_plan_hash_includes_ac_level(self, tmp_path: Path) -> None:
        from _qa_lib import compute_plan_hash

        plan_with_ac = tmp_path / "with_ac.md"
        plan_with_ac.write_text(
            "- R-P1-01-AC1: first\n- R-P1-01-AC2: second\n",
            encoding="utf-8",
        )
        plan_without_ac = tmp_path / "without_ac.md"
        plan_without_ac.write_text(
            "- R-P1-01: first\n- R-P1-02: second\n",
            encoding="utf-8",
        )
        # Different content → different hashes
        assert compute_plan_hash(plan_with_ac) != compute_plan_hash(plan_without_ac)
        # Hash should not be empty
        assert compute_plan_hash(plan_with_ac) != ""

    def test_check_plan_prd_sync_with_ac_level(self, tmp_path: Path) -> None:
        from _qa_lib import check_plan_prd_sync

        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "- R-P1-01-AC1: first\n- R-P1-01-AC2: second\n",
            encoding="utf-8",
        )
        prd = tmp_path / "prd.json"
        prd.write_text(
            json.dumps(
                {
                    "stories": [
                        {
                            "id": "S1",
                            "acceptanceCriteria": [
                                {"id": "R-P1-01-AC1"},
                                {"id": "R-P1-01-AC2"},
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        result = check_plan_prd_sync(plan, prd)
        assert result["in_sync"] is True
        assert result["added"] == []
        assert result["removed"] == []
