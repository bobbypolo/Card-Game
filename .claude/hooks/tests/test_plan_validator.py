"""Tests for plan_validator.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plan_validator import _check_vague_criteria, validate_plan


def _good_plan_md() -> str:
    """Return a minimal but valid PLAN.md that passes all checks."""
    return """\
# PLAN: Test Feature

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

| Action | File           | Description       | Test File            | Test Type |
| ------ | -------------- | ----------------- | -------------------- | --------- |
| CREATE | `src/widget.py` | Widget module     | `tests/test_widget.py` | unit      |
| CREATE | `tests/test_widget.py` | Widget tests | N/A (self)           | unit      |

### Testing Strategy

| What          | Type | Real / Mock | Justification | Test File          |
| ------------- | ---- | ----------- | ------------- | ------------------ |
| Widget create | unit | Real        | Core logic    | `test_widget.py`   |

### Done When

- R-P1-01: `widget.py` returns a dict containing keys `name` and `value` when `create_widget()` is called
- R-P1-02: `widget.py` rejects empty name input by raising `ValueError` with message containing "name required"

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


def _plan_md_vague_criteria() -> str:
    """Plan where Done When criteria contain only vague verbs."""
    return """\
# PLAN: Vague Feature

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Testing Strategy

| What     | Type | Real / Mock | Justification | Test File      |
| -------- | ---- | ----------- | ------------- | -------------- |
| App test | unit | Real        | Core logic    | `test_app.py`  |

### Done When

- R-P1-01: App works correctly and handles all cases properly
- R-P1-02: System supports all input formats and manages state correctly

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


def _plan_md_missing_testing_strategy() -> str:
    """Plan where a phase has no Testing Strategy section."""
    return """\
# PLAN: No Testing

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Done When

- R-P1-01: `app.py` returns correct output when called

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


def _plan_md_placeholder_command() -> str:
    """Plan with placeholder syntax in the verification command."""
    return """\
# PLAN: Placeholder

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Testing Strategy

| What     | Type | Real / Mock | Justification | Test File      |
| -------- | ---- | ----------- | ------------- | -------------- |
| App test | unit | Real        | Core logic    | `test_app.py`  |

### Done When

- R-P1-01: `app.py` returns correct output when called

### Verification Command

```bash
[your_command_here]
```
"""


def _plan_md_missing_test_file_column() -> str:
    """Plan where Changes table production files lack Test File entries."""
    return """\
# PLAN: No Test File

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File           | Description       |
| ------ | -------------- | ----------------- |
| CREATE | `src/widget.py` | Widget module     |
| CREATE | `src/utils.py`  | Utility functions |

### Testing Strategy

| What          | Type | Real / Mock | Justification | Test File          |
| ------------- | ---- | ----------- | ------------- | ------------------ |
| Widget create | unit | Real        | Core logic    | `test_widget.py`   |

### Done When

- R-P1-01: `widget.py` returns correct output when called

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


def _plan_md_missing_r_id() -> str:
    """Plan where Done When items lack R-PN-NN format IDs."""
    return """\
# PLAN: No R-IDs

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Testing Strategy

| What     | Type | Real / Mock | Justification | Test File      |
| -------- | ---- | ----------- | ------------- | -------------- |
| App test | unit | Real        | Core logic    | `test_app.py`  |

### Done When

- Widget returns a list of items when queried
- App raises ValueError on invalid input

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


def _plan_md_tbd_command() -> str:
    """Plan with TBD in verification command."""
    return """\
# PLAN: TBD Command

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Testing Strategy

| What     | Type | Real / Mock | Justification | Test File      |
| -------- | ---- | ----------- | ------------- | -------------- |
| App test | unit | Real        | Core logic    | `test_app.py`  |

### Done When

- R-P1-01: `app.py` returns correct output when called

### Verification Command

```bash
TBD
```
"""


def _plan_md_with_untested_justification() -> str:
    """Plan where production files have no Test File but an Untested Files table exists."""
    return """\
# PLAN: Justified Untested

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File           | Description       | Test File | Test Type |
| ------ | -------------- | ----------------- | --------- | --------- |
| CREATE | `src/widget.py` | Widget module     |           | unit      |
| CREATE | `src/config.py` | Config loader     |           | unit      |

### Untested Files

| File             | Reason               | Tested Via           |
| ---------------- | -------------------- | -------------------- |
| `src/widget.py`  | Pure data class       | Integration tests    |
| `src/config.py`  | Config-only module    | Manual verification  |

### Testing Strategy

| What          | Type | Real / Mock | Justification | Test File          |
| ------------- | ---- | ----------- | ------------- | ------------------ |
| Widget create | unit | Real        | Core logic    | `test_widget.py`   |

### Done When

- R-P1-01: `widget.py` returns correct output when called

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


def _plan_md_mixed_vague_and_measurable() -> str:
    """Plan where some criteria are vague but at least one is measurable."""
    return """\
# PLAN: Mixed Criteria

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File         | Description | Test File          | Test Type |
| ------ | ------------ | ----------- | ------------------ | --------- |
| CREATE | `src/app.py` | App module  | `tests/test_app.py` | unit      |

### Testing Strategy

| What     | Type | Real / Mock | Justification | Test File      |
| -------- | ---- | ----------- | ------------- | -------------- |
| App test | unit | Real        | Core logic    | `test_app.py`  |

### Done When

- R-P1-01: `app.py` returns a list of exactly 3 items when `get_items()` is called
- R-P1-02: System ensures proper handling works correctly

### Verification Command

```bash
python -m pytest tests/ -v
```
"""


# ── Tests ────────────────────────────────────────────────────────────────
class TestGoodPlanPasses:
    """Tests that a well-formed plan passes all validation checks."""

    def test_good_plan_passes_all_checks(self, tmp_path: Path) -> None:
        """A well-formed plan passes all validation checks."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_good_plan_md(), encoding="utf-8")

        result = validate_plan(plan_file)

        outcome = result["result"]
        assert outcome == "PASS"
        checks = result["checks"]
        checks_len = len(checks)
        assert checks_len >= 1
        # Every individual check should pass
        for check in checks:
            check_result = check["result"]
            assert check_result == "PASS", (
                f"Check '{check['name']}' failed: {check.get('evidence', '')}"
            )


class TestVagueCriteriaRejected:
    """# Tests R-P4-01"""

    def test_rejects_only_vague_verbs(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- criteria with only vague verbs and no measurable verb are rejected."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_vague_criteria(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        # Find the vague criteria check
        vague_checks = [c for c in result["checks"] if "vague" in c["name"].lower()]
        assert len(vague_checks) >= 1
        vague_check = vague_checks[0]
        assert vague_check["result"] == "FAIL"
        # Evidence should contain the failing criterion text
        assert (
            "works" in vague_check["evidence"].lower()
            or "handles" in vague_check["evidence"].lower()
        )

    def test_mixed_criteria_detects_vague(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- criteria mixing vague and measurable are detected per-criterion."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_mixed_vague_and_measurable(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        vague_checks = [c for c in result["checks"] if "vague" in c["name"].lower()]
        assert len(vague_checks) >= 1
        vague_check = vague_checks[0]
        assert vague_check["result"] == "FAIL"
        # Should flag the vague criterion but not the measurable one
        assert "R-P1-02" in vague_check["evidence"]


class TestMissingTestFileColumn:
    """# Tests R-P4-02"""

    def test_rejects_missing_test_file_column(self, tmp_path: Path) -> None:
        """# Tests R-P4-02 -- phases with CREATE/MODIFY production files but no Test File column are rejected."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_missing_test_file_column(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        test_file_checks = [
            c
            for c in result["checks"]
            if "test" in c["name"].lower() and "file" in c["name"].lower()
        ]
        assert len(test_file_checks) >= 1
        assert test_file_checks[0]["result"] == "FAIL"

    def test_accepts_untested_files_justification(self, tmp_path: Path) -> None:
        """# Tests R-P4-02 -- phases with Untested Files justification table pass the test file check."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_with_untested_justification(), encoding="utf-8")

        result = validate_plan(plan_file)

        # The test file check specifically should pass because untested files are justified
        test_file_checks = [
            c
            for c in result["checks"]
            if "test" in c["name"].lower() and "file" in c["name"].lower()
        ]
        if test_file_checks:
            assert test_file_checks[0]["result"] == "PASS"


class TestPlaceholderCommandRejected:
    """# Tests R-P4-03"""

    def test_rejects_bracket_placeholder(self, tmp_path: Path) -> None:
        """# Tests R-P4-03 -- verification commands with bracket placeholders are rejected."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_placeholder_command(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        placeholder_checks = [
            c for c in result["checks"] if "placeholder" in c["name"].lower()
        ]
        assert len(placeholder_checks) >= 1
        assert placeholder_checks[0]["result"] == "FAIL"

    def test_rejects_tbd_placeholder(self, tmp_path: Path) -> None:
        """# Tests R-P4-03 -- verification commands containing TBD are rejected."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_tbd_command(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        placeholder_checks = [
            c for c in result["checks"] if "placeholder" in c["name"].lower()
        ]
        assert len(placeholder_checks) >= 1
        assert placeholder_checks[0]["result"] == "FAIL"


class TestRIdAndTestingStrategy:
    """# Tests R-P4-04"""

    def test_rejects_missing_r_ids(self, tmp_path: Path) -> None:
        """# Tests R-P4-04 -- Done When items without R-PN-NN format IDs are rejected."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_missing_r_id(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        r_id_checks = [
            c
            for c in result["checks"]
            if "r-p" in c["name"].lower()
            or "marker" in c["name"].lower()
            or "id" in c["name"].lower()
        ]
        assert len(r_id_checks) >= 1
        assert r_id_checks[0]["result"] == "FAIL"

    def test_rejects_missing_testing_strategy(self, tmp_path: Path) -> None:
        """# Tests R-P4-04 -- phases without a Testing Strategy section are rejected."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_plan_md_missing_testing_strategy(), encoding="utf-8")

        result = validate_plan(plan_file)

        assert result["result"] == "FAIL"
        strategy_checks = [
            c
            for c in result["checks"]
            if "testing" in c["name"].lower() and "strategy" in c["name"].lower()
        ]
        assert len(strategy_checks) >= 1
        assert strategy_checks[0]["result"] == "FAIL"


class TestACLevelRIds:
    """Tests that AC-level IDs (R-P0-01-AC1) are accepted in Done When items."""

    def test_ac_level_ids_accepted(self, tmp_path: Path) -> None:
        plan_content = """\
# PLAN: AC-Level IDs

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File           | Description       | Test File            | Test Type |
| ------ | -------------- | ----------------- | -------------------- | --------- |
| CREATE | `src/widget.py` | Widget module     | `tests/test_widget.py` | unit      |

### Testing Strategy

| What          | Type | Real / Mock | Justification | Test File          |
| ------------- | ---- | ----------- | ------------- | ------------------ |
| Widget create | unit | Real        | Core logic    | `test_widget.py`   |

### Done When

- R-P1-01-AC1: returns a dict containing key `name`
- R-P1-01-AC2: rejects empty name input by raising `ValueError`

### Verification Command

```bash
python -m pytest tests/ -v
```
"""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(plan_content, encoding="utf-8")

        result = validate_plan(plan_file)

        r_id_check = [c for c in result["checks"] if "r_id" in c["name"]]
        assert len(r_id_check) == 1
        assert r_id_check[0]["result"] == "PASS"

    def test_mixed_story_and_ac_level_ids(self, tmp_path: Path) -> None:
        plan_content = """\
# PLAN: Mixed IDs

## Phase 1: Build

**Phase Type**: `module`

### Changes Table

| Action | File           | Description       | Test File            | Test Type |
| ------ | -------------- | ----------------- | -------------------- | --------- |
| CREATE | `src/widget.py` | Widget module     | `tests/test_widget.py` | unit      |

### Testing Strategy

| What          | Type | Real / Mock | Justification | Test File          |
| ------------- | ---- | ----------- | ------------- | ------------------ |
| Widget create | unit | Real        | Core logic    | `test_widget.py`   |

### Done When

- R-P1-01: returns a dict containing key `name`
- R-P1-02-AC1: rejects empty name by raising `ValueError`
- R-P1-02-AC2: logs validation error on empty name

### Verification Command

```bash
python -m pytest tests/ -v
```
"""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(plan_content, encoding="utf-8")

        result = validate_plan(plan_file)

        r_id_check = [c for c in result["checks"] if "r_id" in c["name"]]
        assert len(r_id_check) == 1
        assert r_id_check[0]["result"] == "PASS"


class TestMissingFileReturnsSkip:
    """Tests that validate_plan on a non-existent file returns SKIP."""

    def test_missing_plan_file_returns_skip(self, tmp_path: Path) -> None:
        """Validate_plan on a non-existent file returns SKIP."""
        missing_path = tmp_path / "nonexistent" / "PLAN.md"

        result = validate_plan(missing_path)

        assert result["result"] == "SKIP"
        assert "reason" in result


class TestRealMockColumn:
    """Tests that the Real/Mock column in Testing Strategy is validated."""

    def test_good_plan_has_real_mock_column(self, tmp_path: Path) -> None:
        """Good plan with Real/Mock column passes validation."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_good_plan_md(), encoding="utf-8")
        result = validate_plan(plan_file)
        rm_checks = [c for c in result["checks"] if "real_mock" in c["name"]]
        assert len(rm_checks) == 1
        assert rm_checks[0]["result"] == "PASS"

    def test_missing_real_mock_column_fails(self, tmp_path: Path) -> None:
        """Plan without Real/Mock column in Testing Strategy fails."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(
            "# PLAN: No Mock Column\n\n"
            "## Phase 1: Build\n\n"
            "**Phase Type**: `module`\n\n"
            "### Changes Table\n\n"
            "| Action | File | Description | Test File | Test Type |\n"
            "| ------ | ---- | ----------- | --------- | --------- |\n"
            "| CREATE | `src/app.py` | App | `tests/test_app.py` | unit |\n\n"
            "### Testing Strategy\n\n"
            "| What | Type | Test File |\n"
            "| ---- | ---- | --------- |\n"
            "| App  | unit | test.py   |\n\n"
            "### Done When\n\n"
            "- R-P1-01: `app.py` returns correct output\n\n"
            "### Verification Command\n\n"
            "```bash\npython -m pytest tests/ -v\n```\n",
            encoding="utf-8",
        )
        result = validate_plan(plan_file)
        rm_checks = [c for c in result["checks"] if "real_mock" in c["name"]]
        assert len(rm_checks) == 1
        assert rm_checks[0]["result"] == "FAIL"
        assert "no Real/Mock column" in rm_checks[0]["evidence"]


class TestStructuredOutput:
    """# Tests R-P4-05"""

    def test_result_has_per_check_structure(self, tmp_path: Path) -> None:
        """# Tests R-P4-05 -- result dict has checks list with name, result, evidence per check."""
        plan_file = tmp_path / "PLAN.md"
        plan_file.write_text(_good_plan_md(), encoding="utf-8")

        result = validate_plan(plan_file)

        checks = result["checks"]
        checks_type = type(checks).__name__
        assert checks_type == "list"
        for check in checks:
            check_keys = set(check.keys())
            assert check_keys >= {"name", "result", "evidence"}
            check_result = check["result"]
            assert check_result in ("PASS", "FAIL", "SKIP")


class TestCheckVagueCriteria:
    """# Tests R-P6-01, R-P6-02"""

    def test_vague_first_verb_returns_fail(self) -> None:
        """# Tests R-P6-01 -- first verb 'handles' is vague → FAIL."""
        result = _check_vague_criteria(
            "R-P1-01: handles errors by returning error code"
        )
        assert result == "FAIL"

    def test_measurable_first_verb_returns_pass(self) -> None:
        """# Tests R-P6-02 -- first verb 'returns' is measurable → PASS."""
        result = _check_vague_criteria(
            "R-P1-01: returns error code when handling fails"
        )
        assert result == "PASS"

    def test_vague_verb_manages_returns_fail(self) -> None:
        """Extra coverage: 'manages' as first verb → FAIL."""
        result = _check_vague_criteria("R-P2-01: manages state transitions")
        assert result == "FAIL"

    def test_measurable_verb_raises_returns_pass(self) -> None:
        """Extra coverage: 'raises' as first verb → PASS."""
        result = _check_vague_criteria("R-P3-01: raises ValueError on empty input")
        assert result == "PASS"

    def test_criterion_without_r_prefix_is_evaluated(self) -> None:
        """Criterion text without R-marker prefix is evaluated on first word."""
        result = _check_vague_criteria("supports multiple connection types")
        assert result == "FAIL"

    def test_empty_criterion_returns_pass(self) -> None:
        """Empty criterion text returns PASS (no vague verb found)."""
        result = _check_vague_criteria("")
        assert result == "PASS"
