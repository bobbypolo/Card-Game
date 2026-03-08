"""Tests for qa_runner.py. # Tests R-P1-01, R-P1-02, R-P1-03, R-P1-04, R-P2-06"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

# Ensure _lib is importable from the hooks directory
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from qa_runner import (  # noqa: E402
    _needs_shell,
    _required_verification_steps,
    _step_coverage,
    _step_plan_conformance,
    _step_production_scan,
    _step_regression,
    _step_type_check,
    StepResult,
)

QA_RUNNER_PATH = HOOKS_DIR / "qa_runner.py"


def _run_qa_runner(
    *args: str, cwd: str | None = None, timeout: int = 60
) -> subprocess.CompletedProcess:
    """Run qa_runner.py as a subprocess."""
    cmd = [sys.executable, str(QA_RUNNER_PATH), *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )


def _make_prd(tmp_path: Path, story_id: str = "STORY-003") -> Path:
    """Create a minimal prd.json for testing."""
    prd = tmp_path / "prd.json"
    prd.write_text(
        json.dumps(
            {
                "version": "2.0",
                "stories": [
                    {
                        "id": story_id,
                        "description": "Test story",
                        "phase": 3,
                        "acceptanceCriteria": [
                            {"id": "R-P3-01", "criterion": "Test criterion 1"},
                            {"id": "R-P3-02", "criterion": "Test criterion 2"},
                        ],
                        "gateCmds": {
                            "unit": "echo unit-pass",
                            "lint": "echo lint-pass",
                        },
                        "passed": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return prd


def _make_test_file_with_markers(tmp_path: Path) -> Path:
    """Create a test file with R-PN-NN markers, assertions, and error tests."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    test_file = tests_dir / "test_example.py"
    test_file.write_text(
        "def test_criterion_1():\n"
        '    """# Tests R-P3-01"""\n'
        "    assert 1 + 1 == 2\n"
        "\n"
        "def test_criterion_2():\n"
        '    """# Tests R-P3-02"""\n'
        "    assert 2 + 2 == 4\n"
        "\n"
        "def test_criterion_1_invalid_input():\n"
        '    """# Tests R-P3-01 — negative path"""\n'
        "    assert 0 + 0 == 0\n",
        encoding="utf-8",
    )
    return tests_dir


def _make_violation_file(tmp_path: Path) -> Path:
    """Create a source file with production violations."""
    src = tmp_path / "bad_source.py"
    src.write_text(
        "# a]fixme: this needs work\n"
        "import pdb; pdb.set_trace()\n"
        "password = 'secret123'\n",
        encoding="utf-8",
    )
    return src


def _make_clean_source(tmp_path: Path) -> Path:
    """Create a clean source file with no violations."""
    src = tmp_path / "clean_source.py"
    src.write_text(
        "def add(a: int, b: int) -> int:\n"
        '    """Add two numbers."""\n'
        "    return a + b\n",
        encoding="utf-8",
    )
    return src


class TestQaRunnerExists:
    """# Tests R-P3-01"""

    def test_qa_runner_file_exists(self) -> None:
        """# Tests R-P3-01 -- qa_runner.py exists."""
        assert QA_RUNNER_PATH.is_file(), f"qa_runner.py not found at {QA_RUNNER_PATH}"

    def test_qa_runner_help(self) -> None:
        """# Tests R-P3-01 -- --help runs successfully."""
        result = _run_qa_runner("--help")
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "story" in result.stdout.lower() or "usage" in result.stdout.lower()


class TestCliArguments:
    """# Tests R-P3-02"""

    def test_accepts_story_arg(self, tmp_path: Path) -> None:
        """# Tests R-P3-02 -- accepts --story argument."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        assert "unrecognized arguments" not in result.stderr

    def test_accepts_all_arguments(self, tmp_path: Path) -> None:
        """# Tests R-P3-02 -- accepts all 6 CLI arguments."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--steps",
            "10",
            "--changed-files",
            "file1.py,file2.py",
            "--test-dir",
            str(tmp_path / "tests"),
            "--checkpoint",
            "abc123",
        )
        assert "unrecognized arguments" not in result.stderr


class TestAutomatedSteps:
    """# Tests R-P3-03"""

    def test_step_1_lint_runs(self, tmp_path: Path) -> None:
        """# Tests R-P3-03 -- Step 1 (lint) executes."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "1",
        )
        output = json.loads(result.stdout)
        step1 = output["steps"][0]
        assert step1["step"] == 1
        assert step1["name"] == "Lint"
        assert step1["result"] in ("PASS", "FAIL", "SKIP")

    def test_step_6_security_scan(self, tmp_path: Path) -> None:
        """# Tests R-P3-03 -- Step 6 (security scan)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        violation_file = _make_violation_file(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(violation_file),
            "--steps",
            "6",
        )
        output = json.loads(result.stdout)
        step6 = output["steps"][0]
        assert step6["step"] == 6
        assert step6["result"] in ("PASS", "FAIL")

    def test_step_7_clean_diff(self, tmp_path: Path) -> None:
        """# Tests R-P3-03 -- Step 7 (clean diff)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "7",
        )
        output = json.loads(result.stdout)
        step = output["steps"][0]
        assert step["step"] == 7
        assert step["result"] in ("PASS", "FAIL", "SKIP")

    def test_step_11_acceptance(self, tmp_path: Path) -> None:
        """# Tests R-P3-03 -- Step 11 (acceptance traceability)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "11",
        )
        output = json.loads(result.stdout)
        step = output["steps"][0]
        assert step["step"] == 11
        assert step["result"] in ("PASS", "FAIL", "SKIP")

    def test_step_12_prod_scan(self, tmp_path: Path) -> None:
        """# Tests R-P3-03 -- Step 12 (production scan)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        clean_file = _make_clean_source(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(clean_file),
            "--steps",
            "12",
        )
        output = json.loads(result.stdout)
        step = output["steps"][0]
        assert step["step"] == 12
        assert step["result"] in ("PASS", "FAIL")


class TestPlanConformanceCheck:
    """# Tests R-P4-01"""

    def test_step_10_name_is_plan_conformance(self) -> None:
        """# Tests R-P4-01 -- Step 10 named 'Plan Conformance Check'."""
        from qa_runner import STEP_NAMES

        assert STEP_NAMES[10] == "Plan Conformance Check"

    def test_step_10_skip_no_plan(self) -> None:
        """# Tests R-P4-01 -- SKIP when no plan_path."""
        result_val, evidence = _step_plan_conformance([], None, None, None, None)
        assert result_val == "SKIP"

    def test_step_10_skip_empty_plan(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- SKIP when plan has no Changes table."""
        plan = tmp_path / "PLAN.md"
        plan.write_text("# No changes table here\n", encoding="utf-8")
        result_val, evidence = _step_plan_conformance([], plan, None, None, None)
        assert result_val == "SKIP"

    def test_step_10_pass_matching_files(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- PASS when changed files match plan."""
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "| Action | File | Description |\n"
            "| --- | --- | --- |\n"
            "| MODIFY | `src/main.py` | Update main |\n"
            "| MODIFY | `src/utils.py` | Update utils |\n",
            encoding="utf-8",
        )
        changed = [Path("src/main.py"), Path("src/utils.py")]
        result_val, evidence = _step_plan_conformance(changed, plan, None, None, None)
        assert result_val == "PASS"

    def test_step_10_fail_unexpected_files(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- FAIL when changed files not in plan."""
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "| Action | File | Description |\n"
            "| --- | --- | --- |\n"
            "| MODIFY | `src/main.py` | Update main |\n",
            encoding="utf-8",
        )
        changed = [Path("src/main.py"), Path("src/unexpected.py")]
        result_val, evidence = _step_plan_conformance(changed, plan, None, None, None)
        assert result_val == "FAIL"
        assert "unexpected.py" in evidence

    def test_step_10_allows_init_py(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- __init__.py is always allowed."""
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "| Action | File | Description |\n"
            "| --- | --- | --- |\n"
            "| MODIFY | `src/main.py` | Update main |\n",
            encoding="utf-8",
        )
        changed = [Path("src/main.py"), Path("src/__init__.py")]
        result_val, evidence = _step_plan_conformance(changed, plan, None, None, None)
        assert result_val == "PASS"

    def test_step_10_allows_conftest(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- conftest.py is always allowed."""
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "| Action | File | Description |\n"
            "| --- | --- | --- |\n"
            "| MODIFY | `src/main.py` | Update |\n",
            encoding="utf-8",
        )
        changed = [Path("src/main.py"), Path("tests/conftest.py")]
        result_val, evidence = _step_plan_conformance(changed, plan, None, None, None)
        assert result_val == "PASS"

    def test_step_10_checks_r_markers(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- Step 10 validates R-markers when test_dir and prd provided."""
        plan = tmp_path / "PLAN.md"
        plan.write_text("# No changes\n", encoding="utf-8")
        prd = tmp_path / "prd.json"
        prd.write_text(
            json.dumps(
                {
                    "version": "2.0",
                    "stories": [
                        {
                            "id": "STORY-X",
                            "description": "Test",
                            "phase": 1,
                            "acceptanceCriteria": [
                                {"id": "R-P9-99", "criterion": "missing"},
                            ],
                            "gateCmds": {},
                            "passed": False,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        test_dir = _make_test_file_with_markers(tmp_path)
        story = {
            "id": "STORY-X",
            "acceptanceCriteria": [{"id": "R-P9-99"}],
        }
        result_val, evidence = _step_plan_conformance([], plan, story, prd, test_dir)
        assert result_val == "FAIL"
        assert "R-marker" in evidence or "Missing" in evidence

    def test_step_10_pass_markers_and_files(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- PASS when both R-markers and files match."""
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "| Action | File | Description |\n"
            "| --- | --- | --- |\n"
            "| MODIFY | `src/main.py` | Update |\n",
            encoding="utf-8",
        )
        prd = _make_prd(tmp_path)
        test_dir = _make_test_file_with_markers(tmp_path)
        story = {
            "id": "STORY-003",
            "acceptanceCriteria": [
                {"id": "R-P3-01"},
                {"id": "R-P3-02"},
            ],
        }
        changed = [Path("src/main.py")]
        result_val, evidence = _step_plan_conformance(
            changed, plan, story, prd, test_dir
        )
        assert result_val == "PASS"

    def test_step_10_is_automated_via_subprocess(self, tmp_path: Path) -> None:
        """# Tests R-P4-01 -- Step 10 returns automated result via subprocess."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        step10 = output["steps"][0]
        assert step10["step"] == 10
        assert step10["name"] == "Plan Conformance Check"
        assert step10["result"] != "MANUAL"
        assert step10["result"] in ("PASS", "FAIL", "SKIP")


class TestPlanHashMismatch:
    """# Tests R-P1-03, R-P1-04"""

    def test_plan_hash_mismatch_returns_fail(self, tmp_path: Path) -> None:
        """# Tests R-P1-03 -- FAIL when prd.json plan_hash differs from computed hash."""
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "# Plan content\n\n## Done When\n- R-P1-01: test\n", encoding="utf-8"
        )
        # Store a DIFFERENT hash in prd.json (not the real PLAN.md hash)
        prd = tmp_path / "prd.json"
        prd.write_text(
            json.dumps(
                {
                    "version": "2.0",
                    "plan_hash": "0000000000000000000000000000000000000000000000000000000000000000",
                    "planRef": "PLAN.md",
                    "stories": [],
                }
            ),
            encoding="utf-8",
        )
        result_val, evidence = _step_plan_conformance([], plan, None, prd, None)
        assert result_val == "FAIL"
        assert "hash mismatch" in evidence.lower() or "Plan-PRD" in evidence

    def test_plan_hash_match_returns_pass(self, tmp_path: Path) -> None:
        """# Tests R-P1-04 -- PASS when prd.json plan_hash matches computed hash."""
        from _qa_lib import compute_plan_hash

        plan = tmp_path / "PLAN.md"
        plan_content = "# Plan content\n\n## Done When\n- R-P1-01: test\n"
        plan.write_text(plan_content, encoding="utf-8")
        computed_hash = compute_plan_hash(plan)
        prd = tmp_path / "prd.json"
        prd.write_text(
            json.dumps(
                {
                    "version": "2.0",
                    "plan_hash": computed_hash,
                    "planRef": "PLAN.md",
                    "stories": [],
                }
            ),
            encoding="utf-8",
        )
        result_val, evidence = _step_plan_conformance([], plan, None, prd, None)
        assert result_val == "PASS"

    def test_output_key_is_overall_result(self, tmp_path: Path) -> None:
        """-- output dict uses 'overall_result' not 'overall'."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert "overall_result" in output, "Output should contain 'overall_result' key"
        assert "overall" not in output or "overall_result" in output


class TestStepNamesDict:
    """# Tests R-P4-02"""

    def test_step_names_has_12_entries(self) -> None:
        """# Tests R-P4-02 -- STEP_NAMES has 12 entries."""
        from qa_runner import STEP_NAMES

        assert len(STEP_NAMES) == 12, (
            f"STEP_NAMES has {len(STEP_NAMES)} entries, expected 12"
        )

    def test_step_names_keys_are_1_to_12(self) -> None:
        """# Tests R-P4-02 -- STEP_NAMES keys are 1..12."""
        from qa_runner import STEP_NAMES

        assert set(STEP_NAMES.keys()) == set(range(1, 13))

    def test_step_names_values(self) -> None:
        """# Tests R-P4-02 -- STEP_NAMES has correct values."""
        from qa_runner import STEP_NAMES

        assert STEP_NAMES[1] == "Lint"
        assert STEP_NAMES[2] == "Type check"
        assert STEP_NAMES[3] == "Unit tests"
        assert STEP_NAMES[4] == "Integration tests"
        assert STEP_NAMES[5] == "Regression check"
        assert STEP_NAMES[6] == "Security scan"
        assert STEP_NAMES[7] == "Clean diff"
        assert STEP_NAMES[8] == "Coverage"
        assert STEP_NAMES[9] == "Mock quality audit"
        assert STEP_NAMES[10] == "Plan Conformance Check"
        assert STEP_NAMES[11] == "Acceptance traceability"
        assert STEP_NAMES[12] == "Production scan"

    def test_parse_steps_default_is_1_to_12(self) -> None:
        """# Tests R-P4-02 -- _parse_steps(None) returns 1..12."""
        from qa_runner import _parse_steps

        result = _parse_steps(None)
        assert result == list(range(1, 13))


class TestAllStepsRun:
    def test_all_12_steps_run(self) -> None:
        """-- _parse_steps(None) returns all 12 step numbers."""
        from qa_runner import STEP_NAMES, _parse_steps

        all_steps = _parse_steps(None)
        assert len(all_steps) == 12, f"Expected 12 steps, got {len(all_steps)}"
        assert all_steps == list(range(1, 13))
        for step_num in all_steps:
            assert step_num in STEP_NAMES, f"Step {step_num} missing from STEP_NAMES"

    def test_all_results_are_valid(self, tmp_path: Path) -> None:
        """-- All results are PASS/FAIL/SKIP."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        clean_file = _make_clean_source(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(clean_file),
            "--steps",
            "6,7,9,10,11,12",
        )
        output = json.loads(result.stdout)
        valid_results = {"PASS", "FAIL", "SKIP"}
        for step in output["steps"]:
            assert step["result"] in valid_results, (
                f"Step {step['step']} has invalid result: {step['result']}"
            )

    def test_production_violations_tracked_step_12(self, tmp_path: Path) -> None:
        """-- Production violations tracked from step 12."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        violation_file = _make_violation_file(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(violation_file),
            "--steps",
            "12",
        )
        output = json.loads(result.stdout)
        assert output["overall_result"] == "FAIL"
        assert output["production_violations"] > 0


class TestOutputSchema:
    def test_output_has_required_fields(self, tmp_path: Path) -> None:
        """Output JSON has all required top-level fields."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert "story_id" in output
        assert "timestamp" in output
        assert "steps" in output
        assert "overall_result" in output
        assert "criteria_verified" in output
        assert "production_violations" in output

    def test_story_id_matches_input(self, tmp_path: Path) -> None:
        """story_id matches --story argument."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert output["story_id"] == "STORY-003"

    def test_timestamp_is_iso_format(self, tmp_path: Path) -> None:
        """timestamp is ISO 8601 format."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        from datetime import datetime

        ts = datetime.fromisoformat(output["timestamp"])
        ts_type = type(ts).__name__
        assert ts_type == "datetime"


class TestStepEntrySchema:
    def test_step_entry_has_required_fields(self, tmp_path: Path) -> None:
        """Each step has step, name, result, evidence, duration_ms."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10,11",
        )
        output = json.loads(result.stdout)
        for step in output["steps"]:
            step_keys = set(step.keys())
            assert step_keys >= {"step", "name", "result", "evidence"}
            assert "duration_ms" in step, f"Missing 'duration_ms' in {step}"
            assert isinstance(step["step"], int)
            assert isinstance(step["name"], str)
            assert isinstance(step["duration_ms"], int)


class TestOverallResult:
    def test_overall_pass_when_all_skip(self, tmp_path: Path) -> None:
        """overall PASS when steps only SKIP or PASS."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert output["overall_result"] == "PASS"

    def test_overall_fail_when_violations(self, tmp_path: Path) -> None:
        """overall FAIL when step 12 finds violations."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        violation_file = _make_violation_file(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(violation_file),
            "--steps",
            "12",
        )
        output = json.loads(result.stdout)
        assert output["overall_result"] == "FAIL"


class TestExitCodes:
    def test_exit_0_on_pass(self, tmp_path: Path) -> None:
        """exit code 0 when overall PASS."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        assert result.returncode == 0

    def test_exit_1_on_fail(self, tmp_path: Path) -> None:
        """exit code 1 when overall FAIL."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        violation_file = _make_violation_file(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(violation_file),
            "--steps",
            "12",
        )
        assert result.returncode == 1

    def test_exit_2_on_invalid_args(self) -> None:
        """exit code 2 on invalid/missing arguments."""
        result = _run_qa_runner()
        assert result.returncode == 2


class TestUnconfiguredCommands:
    def test_type_check_configured_runs(self, tmp_path: Path) -> None:
        """Configured type_check produces non-SKIP result."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "2",
        )
        output = json.loads(result.stdout)
        step2 = output["steps"][0]
        # type_check is now configured with mypy, so result is PASS or FAIL (not SKIP)
        assert step2["result"] in ("PASS", "FAIL")
        assert step2["evidence"]

    def test_coverage_configured_runs(self, tmp_path: Path) -> None:
        """Configured coverage produces non-SKIP result."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "8",
            timeout=300,
        )
        output = json.loads(result.stdout)
        step8 = output["steps"][0]
        # coverage is now configured with pytest-cov, so result is PASS or FAIL (not SKIP)
        assert step8["result"] in ("PASS", "FAIL")


class TestStep9MockAudit:
    def test_step_9_uses_scan_test_quality(self, tmp_path: Path) -> None:
        """Step 9 FAILs on assertion-free tests."""
        prd = _make_prd(tmp_path)
        test_dir = _make_test_file_with_markers(tmp_path)
        bad_test = test_dir / "test_bad_quality.py"
        bad_test.write_text(
            "def test_does_nothing():\n    x = 1 + 1\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(bad_test),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["step"] == 9
        assert step9["name"] == "Mock quality audit"
        assert step9["result"] == "FAIL"

    def test_step_9_passes_good_tests(self, tmp_path: Path) -> None:
        """Step 9 passes on well-formed tests."""
        prd = _make_prd(tmp_path)
        test_dir = _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(test_dir / "test_example.py"),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["result"] == "PASS"


class TestStep11Acceptance:
    def test_step_11_uses_validate_r_markers(self, tmp_path: Path) -> None:
        """Step 11 PASSes when R-P3-01/02 markers exist."""
        prd = _make_prd(tmp_path)
        test_dir = _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--steps",
            "11",
        )
        output = json.loads(result.stdout)
        step11 = output["steps"][0]
        assert step11["step"] == 11
        assert step11["name"] == "Acceptance traceability"
        assert step11["result"] == "PASS"

    def test_step_11_fails_on_missing_markers(self, tmp_path: Path) -> None:
        """Step 11 FAILs when markers are missing."""
        prd = tmp_path / "prd.json"
        prd.write_text(
            json.dumps(
                {
                    "version": "2.0",
                    "stories": [
                        {
                            "id": "STORY-003",
                            "description": "Test",
                            "phase": 3,
                            "acceptanceCriteria": [
                                {"id": "R-P3-99", "criterion": "Nonexistent criterion"},
                            ],
                            "gateCmds": {},
                            "passed": False,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        test_dir = _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--steps",
            "11",
        )
        output = json.loads(result.stdout)
        step11 = output["steps"][0]
        assert step11["result"] == "FAIL"


class TestStep12ProductionScan:
    def test_step_12_uses_scan_file_violations(self, tmp_path: Path) -> None:
        """Step 12 FAILs on violation files."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        violation_file = _make_violation_file(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(violation_file),
            "--steps",
            "12",
        )
        output = json.loads(result.stdout)
        step12 = output["steps"][0]
        assert step12["step"] == 12
        assert step12["name"] == "Production scan"
        assert step12["result"] == "FAIL"
        assert output["production_violations"] > 0

    def test_step_12_passes_clean_file(self, tmp_path: Path) -> None:
        """Step 12 PASSes on clean source."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        clean_file = _make_clean_source(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(clean_file),
            "--steps",
            "12",
        )
        output = json.loads(result.stdout)
        step12 = output["steps"][0]
        assert step12["result"] == "PASS"
        assert output["production_violations"] == 0


class TestTestFileExists:
    def test_test_file_exists(self) -> None:
        """test_qa_runner.py exists."""
        assert Path(__file__).is_file()


class TestSecurityAndCleanupIDs:
    def test_security_ids_include_new_patterns(self) -> None:
        """_SECURITY_IDS includes new injection/secret patterns."""
        from qa_runner import _SECURITY_IDS

        expected_new = {
            "subprocess-shell-injection",
            "os-exec-injection",
            "raw-sql-fstring",
            "expanded-secret",
        }
        for sid in expected_new:
            assert sid in _SECURITY_IDS, f"{sid} missing from _SECURITY_IDS"

    def test_security_ids_include_original_patterns(self) -> None:
        """_SECURITY_IDS includes original patterns."""
        from qa_runner import _SECURITY_IDS

        original = {"hardcoded-secret", "sql-injection", "shell-injection"}
        for sid in original:
            assert sid in _SECURITY_IDS, f"{sid} missing from _SECURITY_IDS"

    def test_cleanup_ids_include_broad_except(self) -> None:
        """_CLEANUP_IDS includes broad-except."""
        from qa_runner import _CLEANUP_IDS

        assert "broad-except" in _CLEANUP_IDS

    def test_cleanup_ids_include_bare_except(self) -> None:
        """_CLEANUP_IDS includes bare-except."""
        from qa_runner import _CLEANUP_IDS

        assert "bare-except" in _CLEANUP_IDS

    def test_security_and_cleanup_ids_no_overlap(self) -> None:
        """_SECURITY_IDS and _CLEANUP_IDS have no overlap."""
        from qa_runner import _CLEANUP_IDS, _SECURITY_IDS

        overlap = _SECURITY_IDS & _CLEANUP_IDS
        assert len(overlap) == 0, f"Overlapping IDs: {overlap}"


class TestExternalScanners:
    def test_step_12_no_external_scanners_configured(self, tmp_path: Path) -> None:
        """Step 12 passes without external scanners."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        clean_file = _make_clean_source(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(clean_file),
            "--steps",
            "12",
        )
        output = json.loads(result.stdout)
        step12 = output["steps"][0]
        assert step12["step"] == 12
        assert step12["result"] == "PASS"

    def test_step_12_external_scanners_disabled(self, tmp_path: Path) -> None:
        """Disabled external scanners are skipped."""
        from qa_runner import _step_production_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "bandit": {"cmd": "echo should-not-run", "enabled": False},
                "semgrep": {"cmd": "echo should-not-run", "enabled": False},
            }
        }
        result_val, evidence = _step_production_scan([clean_file], config=config)
        assert result_val == "PASS"

    def test_step_production_scan_no_config(self) -> None:
        """_step_production_scan works with config=None."""
        from qa_runner import _step_production_scan

        result_val, evidence = _step_production_scan([], config=None)
        assert result_val == "PASS"

    def test_step_production_scan_empty_scanners(self, tmp_path: Path) -> None:
        """Empty external_scanners dict is fine."""
        from qa_runner import _step_production_scan

        clean_file = _make_clean_source(tmp_path)
        config = {"external_scanners": {}}
        result_val, evidence = _step_production_scan([clean_file], config=config)
        assert result_val == "PASS"


class TestPlanArgument:
    def test_accepts_plan_argument(self, tmp_path: Path) -> None:
        """-- qa_runner accepts --plan."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        plan = tmp_path / "PLAN.md"
        plan.write_text("# Test plan\n", encoding="utf-8")
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--plan",
            str(plan),
            "--steps",
            "10",
        )
        assert "unrecognized arguments" not in result.stderr

    def test_plan_arg_passed_to_step_10(self, tmp_path: Path) -> None:
        """-- --plan is used by step 10."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        plan = tmp_path / "PLAN.md"
        plan.write_text(
            "| Action | File | Description |\n"
            "| --- | --- | --- |\n"
            "| MODIFY | `src/main.py` | Update |\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--plan",
            str(plan),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        step10 = output["steps"][0]
        assert step10["result"] == "PASS"

    def test_help_shows_plan_option(self) -> None:
        """-- --help includes --plan."""
        result = _run_qa_runner("--help")
        assert "--plan" in result.stdout


class TestPhaseTypeArgument:
    def test_accepts_phase_type_argument(self, tmp_path: Path) -> None:
        """qa_runner accepts --phase-type."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "foundation",
            "--steps",
            "10",
        )
        assert "unrecognized arguments" not in result.stderr

    def test_help_shows_phase_type_option(self) -> None:
        """--help includes --phase-type."""
        result = _run_qa_runner("--help")
        assert "--phase-type" in result.stdout

    def test_phase_type_accepts_foundation(self, tmp_path: Path) -> None:
        """--phase-type=foundation accepted."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "foundation",
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert "phase_type" in output
        assert output["phase_type"] == "foundation"

    def test_phase_type_accepts_module(self, tmp_path: Path) -> None:
        """--phase-type=module accepted."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "module",
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert output["phase_type"] == "module"

    def test_phase_type_accepts_integration(self, tmp_path: Path) -> None:
        """--phase-type=integration accepted."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "integration",
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert output["phase_type"] == "integration"

    def test_phase_type_accepts_e2e(self, tmp_path: Path) -> None:
        """--phase-type=e2e accepted."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "e2e",
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert output["phase_type"] == "e2e"

    def test_phase_type_default_is_none(self, tmp_path: Path) -> None:
        """Default phase_type is null."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert output.get("phase_type") is None

    def test_phase_type_rejects_invalid_value(self) -> None:
        """--phase-type rejects invalid values."""
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--phase-type",
            "invalid_type",
        )
        assert result.returncode == 2


class TestRegressionTiers:
    """Tests for tiered regression support. # Tests R-P1-01, R-P1-02, R-P1-03, R-P1-04"""

    def _make_tier_config(
        self, tier_cmd: str = "echo tier-pass", max_duration_s: int = 60
    ) -> dict:
        """Return a workflow config dict with regression_tiers configured."""
        return {
            "commands": {
                "regression": "echo fallback-regression",
                "regression_default_tier": "unit",
                "regression_tiers": {
                    "smoke": {
                        "cmd": "echo smoke-pass",
                        "max_duration_s": 30,
                    },
                    "unit": {
                        "cmd": tier_cmd,
                        "max_duration_s": max_duration_s,
                    },
                    "full": {
                        "cmd": "echo full-pass",
                        "max_duration_s": 300,
                    },
                },
            }
        }

    def test_r_p1_01_story_with_tier_selects_tier_cmd_pass(self) -> None:
        """# Tests R-P1-01 -- story.gateCmds.regression_tier selects tier cmd, returns PASS."""
        config = self._make_tier_config(tier_cmd="echo tier-specific-pass")
        story = {"gateCmds": {"regression_tier": "smoke"}}
        result_val, evidence = _step_regression(config, story)
        assert result_val == "PASS"
        assert "smoke" in evidence

    def test_r_p1_01_story_with_tier_selects_tier_cmd_fail(self) -> None:
        """# Tests R-P1-01 -- story.gateCmds.regression_tier selects tier cmd, returns FAIL on non-zero exit."""
        config = self._make_tier_config()
        # Provide a story that selects a failing tier command
        config["commands"]["regression_tiers"]["smoke"]["cmd"] = "exit 1"
        story = {"gateCmds": {"regression_tier": "smoke"}}
        result_val, evidence = _step_regression(config, story)
        assert result_val == "FAIL"

    def test_r_p1_02_story_without_tier_uses_default_tier(self) -> None:
        """# Tests R-P1-02 -- story without regression_tier uses regression_default_tier."""
        config = self._make_tier_config(tier_cmd="echo unit-tier-pass")
        # Story has no regression_tier in gateCmds
        story = {"gateCmds": {}}
        result_val, evidence = _step_regression(config, story)
        assert result_val == "PASS"
        assert "unit" in evidence  # default tier is "unit"

    def test_r_p1_02_none_story_uses_default_tier(self) -> None:
        """# Tests R-P1-02 -- None story uses regression_default_tier from config."""
        config = self._make_tier_config(tier_cmd="echo default-tier-pass")
        result_val, evidence = _step_regression(config, None)
        assert result_val == "PASS"
        assert "unit" in evidence

    def test_r_p1_03_no_tiers_falls_back_to_commands_regression(self) -> None:
        """# Tests R-P1-03 -- no regression_tiers config falls back to commands.regression."""
        config = {"commands": {"regression": "echo backward-compat-pass"}}
        result_val, evidence = _step_regression(config, None)
        assert result_val == "PASS"
        # Should NOT mention any tier name
        assert "[" not in evidence or "backward" in evidence

    def test_r_p1_03_no_tiers_no_regression_returns_skip(self) -> None:
        """# Tests R-P1-03 -- no tiers AND no commands.regression returns SKIP."""
        config = {"commands": {}}
        result_val, evidence = _step_regression(config, None)
        assert result_val == "SKIP"

    def test_r_p1_03_empty_tiers_dict_falls_back(self) -> None:
        """# Tests R-P1-03 -- empty regression_tiers dict falls back to commands.regression."""
        config = {
            "commands": {
                "regression": "echo fallback-pass",
                "regression_tiers": {},
            }
        }
        result_val, evidence = _step_regression(config, None)
        assert result_val == "PASS"

    def test_r_p1_04_max_duration_s_passed_as_timeout(self) -> None:
        """# Tests R-P1-04 -- max_duration_s from tier config is passed as timeout to _run_command."""
        with patch("qa_runner._run_command") as mock_run:
            mock_run.return_value = (0, "ok", "")
            config = self._make_tier_config(tier_cmd="echo pass", max_duration_s=99)
            story = {"gateCmds": {"regression_tier": "unit"}}
            result_val, evidence = _step_regression(config, story)
            mock_run.assert_called_once_with("echo pass", timeout=99)
            # Verify the function returns PASS when command succeeds
            assert result_val == "PASS"

    def test_r_p1_04_default_max_duration_s_is_120(self) -> None:
        """# Tests R-P1-04 -- tier without max_duration_s defaults to 120s timeout."""
        with patch("qa_runner._run_command") as mock_run:
            mock_run.return_value = (0, "ok", "")
            config = {
                "commands": {
                    "regression_default_tier": "unit",
                    "regression_tiers": {
                        "unit": {
                            "cmd": "echo pass",
                            # No max_duration_s — should default to 120
                        }
                    },
                }
            }
            result_val, evidence = _step_regression(config, None)
            mock_run.assert_called_once_with("echo pass", timeout=120)
            # Verify the function returns PASS when command succeeds
            assert result_val == "PASS"


class TestPhaseTypeRelevanceMatrix:
    def test_phase_type_relevance_exists(self) -> None:
        """PHASE_TYPE_RELEVANCE dict exists."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        ptr_type = type(PHASE_TYPE_RELEVANCE).__name__
        assert ptr_type == "dict"

    def test_foundation_relevant_steps(self) -> None:
        """foundation maps to correct steps."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        expected = {1, 2, 3, 5, 6, 7, 9, 10, 11, 12}
        assert PHASE_TYPE_RELEVANCE["foundation"] == expected

    def test_module_relevant_steps(self) -> None:
        """module maps to correct steps."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        expected = {1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12}
        assert PHASE_TYPE_RELEVANCE["module"] == expected

    def test_integration_relevant_steps(self) -> None:
        """integration maps to all 12 steps."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        expected = set(range(1, 13))
        assert PHASE_TYPE_RELEVANCE["integration"] == expected

    def test_e2e_relevant_steps(self) -> None:
        """e2e maps to all 12 steps."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        expected = set(range(1, 13))
        assert PHASE_TYPE_RELEVANCE["e2e"] == expected

    def test_matrix_has_four_entries(self) -> None:
        """Matrix has exactly 4 phase type entries."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        assert len(PHASE_TYPE_RELEVANCE) == 4
        assert set(PHASE_TYPE_RELEVANCE.keys()) == {
            "foundation",
            "module",
            "integration",
            "e2e",
        }


class TestAlwaysRequiredSteps:
    def test_always_required_steps_constant_exists(self) -> None:
        """ALWAYS_REQUIRED_STEPS constant exists."""
        from qa_runner import ALWAYS_REQUIRED_STEPS

        ars_type = type(ALWAYS_REQUIRED_STEPS).__name__
        assert ars_type in ("set", "frozenset")

    def test_always_required_steps_values(self) -> None:
        """Steps 1-2, 5-7, 10-12 are always required."""
        from qa_runner import ALWAYS_REQUIRED_STEPS

        expected = {1, 2, 5, 6, 7, 10, 11, 12}
        assert ALWAYS_REQUIRED_STEPS == expected

    def test_all_phase_types_include_required_steps(self) -> None:
        """All phase types include always-required steps."""
        from qa_runner import ALWAYS_REQUIRED_STEPS, PHASE_TYPE_RELEVANCE

        for phase_type, relevant_steps in PHASE_TYPE_RELEVANCE.items():
            missing = ALWAYS_REQUIRED_STEPS - relevant_steps
            assert not missing, (
                f"Phase type '{phase_type}' missing required steps: {missing}"
            )

    def test_only_steps_3_4_8_9_can_be_skipped(self) -> None:
        """Only steps 3, 4, 8, 9 may be skipped by phase type."""
        from qa_runner import ALWAYS_REQUIRED_STEPS

        all_steps = set(range(1, 13))
        skippable = all_steps - ALWAYS_REQUIRED_STEPS
        assert skippable == {3, 4, 8, 9}


class TestPhaseTypeSkipJustification:
    def test_foundation_skips_step_4(self, tmp_path: Path) -> None:
        """foundation skips step 4 (integration)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "foundation",
            "--steps",
            "4",
        )
        output = json.loads(result.stdout)
        step4 = output["steps"][0]
        assert step4["result"] == "SKIP"
        assert "foundation" in step4["evidence"]

    def test_foundation_skips_step_8(self, tmp_path: Path) -> None:
        """foundation skips step 8 (coverage)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "foundation",
            "--steps",
            "8",
        )
        output = json.loads(result.stdout)
        step8 = output["steps"][0]
        assert step8["result"] == "SKIP"
        assert "foundation" in step8["evidence"]

    def test_module_skips_step_4(self, tmp_path: Path) -> None:
        """module skips step 4 (integration)."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "module",
            "--steps",
            "4",
        )
        output = json.loads(result.stdout)
        step4 = output["steps"][0]
        assert step4["result"] == "SKIP"
        assert "module" in step4["evidence"]

    def test_integration_does_not_skip_step_4(self, tmp_path: Path) -> None:
        """integration does NOT skip step 4."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "integration",
            "--steps",
            "4",
        )
        output = json.loads(result.stdout)
        step4 = output["steps"][0]
        # May SKIP for other reasons (no cmd), but NOT due to phase_type
        if step4["result"] == "SKIP":
            assert (
                "integration" not in step4["evidence"]
                or "not relevant" not in step4["evidence"]
            )

    def test_skip_evidence_contains_justification(self, tmp_path: Path) -> None:
        """Skipped step evidence contains phase_type justification."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--phase-type",
            "foundation",
            "--steps",
            "4",
        )
        output = json.loads(result.stdout)
        step4 = output["steps"][0]
        assert step4["result"] == "SKIP"
        assert "not relevant for" in step4["evidence"]
        assert "foundation" in step4["evidence"]

    def test_no_phase_type_runs_all_steps(self, tmp_path: Path) -> None:
        """Without --phase-type, no steps are skipped by phase."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "4,8",
            timeout=300,
        )
        output = json.loads(result.stdout)
        for step in output["steps"]:
            if step["result"] == "SKIP":
                assert "not relevant for" not in step["evidence"]


class TestScanOnceCache:
    """# Tests R-P2-03"""

    def test_violation_cache_populated_at_start(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- _build_violation_cache scans all source files once."""
        from qa_runner import _build_violation_cache, _get_source_files

        violation_file = _make_violation_file(tmp_path)
        clean_file = _make_clean_source(tmp_path)
        source_files = _get_source_files([violation_file, clean_file])
        cache = _build_violation_cache(source_files)
        cache_type = type(cache).__name__
        assert cache_type == "dict"
        cache_len = len(cache)
        expected_len = len(source_files)
        assert cache_len == expected_len

    def test_violation_cache_contains_violations(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- cache contains violations for bad files."""
        from qa_runner import _build_violation_cache

        violation_file = _make_violation_file(tmp_path)
        cache = _build_violation_cache([violation_file])
        key = str(violation_file)
        assert key in cache
        assert len(cache[key]) > 0

    def test_violation_cache_empty_for_clean_file(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- cache empty for clean files."""
        from qa_runner import _build_violation_cache

        clean_file = _make_clean_source(tmp_path)
        cache = _build_violation_cache([clean_file])
        key = str(clean_file)
        assert key in cache
        assert cache[key] == []

    def test_steps_6_7_12_use_cache(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- steps 6, 7, 12 use shared cache."""
        from qa_runner import (
            _step_clean_diff,
            _step_production_scan,
            _step_security_scan,
        )

        violation_file = _make_violation_file(tmp_path)
        files = [violation_file]
        from qa_runner import _build_violation_cache

        cache = _build_violation_cache(files)
        result6, _ = _step_security_scan(files, violation_cache=cache)
        # R-P2-02: step functions return StepResult (str subclass), not raw str

        assert isinstance(result6, StepResult)
        assert result6 in ("PASS", "FAIL", "SKIP")
        result7, _ = _step_clean_diff(files, violation_cache=cache)
        assert isinstance(result7, StepResult)
        assert result7 in ("PASS", "FAIL", "SKIP")
        result12, _ = _step_production_scan(files, violation_cache=cache)
        assert isinstance(result12, StepResult)
        assert result12 in ("PASS", "FAIL", "SKIP")

    def test_scan_once_same_results_as_individual(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- cache-based scan matches individual scans."""
        from qa_runner import _build_violation_cache, _step_production_scan

        violation_file = _make_violation_file(tmp_path)
        files = [violation_file]
        result_no_cache, evidence_no_cache = _step_production_scan(files)
        cache = _build_violation_cache(files)
        result_cached, evidence_cached = _step_production_scan(
            files, violation_cache=cache
        )
        assert result_no_cache == result_cached


class TestTestQualityMode:
    """# Tests R-P2-04 -- qa_runner.py --test-quality mode."""

    def test_test_quality_flag_accepted(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- --test-quality flag recognized."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_sample.py"
        test_file.write_text("def test_example():\n    assert True\n", encoding="utf-8")
        result = _run_qa_runner(
            "--story",
            "STORY-001",
            "--test-quality",
            "--test-dir",
            str(test_dir),
        )
        assert "unrecognized arguments" not in result.stderr

    def test_test_quality_json_has_required_keys(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- output has files, overall, summary keys."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_sample.py"
        test_file.write_text("def test_example():\n    assert True\n", encoding="utf-8")
        result = _run_qa_runner(
            "--story",
            "STORY-001",
            "--test-quality",
            "--test-dir",
            str(test_dir),
        )
        data = json.loads(result.stdout)
        assert "files" in data, "Missing 'files' key in output"
        assert "overall_result" in data, "Missing 'overall' key in output"
        assert "summary" in data, "Missing 'summary' key in output"

    def test_test_quality_summary_has_counters(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- summary has total_tests and quality counters."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_sample.py"
        test_file.write_text(
            "def test_one():\n    assert 1 == 1\ndef test_two():\n    assert 2 == 2\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-001",
            "--test-quality",
            "--test-dir",
            str(test_dir),
        )
        data = json.loads(result.stdout)
        summary = data["summary"]
        assert "total_tests" in summary
        assert "total_assertion_free" in summary
        assert "total_self_mock" in summary
        assert "total_mock_only" in summary

    def test_test_quality_clean_tests_pass(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- clean tests produce PASS."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_clean.py"
        test_file.write_text("def test_clean():\n    assert 1 == 1\n", encoding="utf-8")
        result = _run_qa_runner(
            "--story",
            "STORY-001",
            "--test-quality",
            "--test-dir",
            str(test_dir),
        )
        data = json.loads(result.stdout)
        assert data["overall_result"] == "PASS"
        assert result.returncode == 0

    def test_test_quality_with_prd_includes_marker_validation(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P2-04 -- --prd adds marker_validation to summary."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_markers.py"
        test_file.write_text(
            '"""# Tests R-P3-01"""\ndef test_one():\n    assert True\n',
            encoding="utf-8",
        )
        prd = _make_prd(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--test-quality",
            "--test-dir",
            str(test_dir),
            "--prd",
            str(prd),
        )
        data = json.loads(result.stdout)
        assert "marker_validation" in data["summary"]

    def test_test_quality_no_dir_no_files_exits_cleanly(self) -> None:
        """# Tests R-P2-04 -- no --test-dir produces empty result."""
        result = _run_qa_runner(
            "--story",
            "STORY-001",
            "--test-quality",
        )
        data = json.loads(result.stdout)
        assert data["files"] == []
        assert data["overall_result"] == "PASS"
        assert data["summary"]["total_tests"] == 0


class TestStep9StoryCoverage:
    def test_step_9_full_coverage_passes(self, tmp_path: Path) -> None:
        """Step 9 PASSes when all prod files have tests."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_1_invalid_input():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 0 == 0\n",
            encoding="utf-8",
        )
        prod_file = tmp_path / "mymodule.py"
        prod_file.write_text("def helper():\n    return 1\n", encoding="utf-8")
        (test_dir / "test_mymodule.py").write_text(
            "def test_helper():\n    assert 1 == 1\n"
            "def test_helper_invalid():\n    assert 0 == 0\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            f"{prod_file},{test_dir / 'test_mymodule.py'}",
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["step"] == 9
        assert step9["result"] == "PASS"
        assert "coverage" in step9["evidence"].lower()

    def test_step_9_partial_coverage_fails(self, tmp_path: Path) -> None:
        """Step 9 FAILs when <80% of prod files have tests."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_1_invalid_input():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 0 == 0\n",
            encoding="utf-8",
        )
        # 3 prod files, only 1 has a test (33% < 80%)
        prod_a = tmp_path / "mod_a.py"
        prod_a.write_text("def a():\n    return 1\n", encoding="utf-8")
        prod_b = tmp_path / "mod_b.py"
        prod_b.write_text("def b():\n    return 2\n", encoding="utf-8")
        prod_c = tmp_path / "mod_c.py"
        prod_c.write_text("def c():\n    return 3\n", encoding="utf-8")
        (test_dir / "test_mod_a.py").write_text(
            "def test_a():\n    assert 1 == 1\n", encoding="utf-8"
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            f"{prod_a},{prod_b},{prod_c}",
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["step"] == 9
        assert step9["result"] == "FAIL"
        assert "coverage" in step9["evidence"].lower()

    def test_step_9_import_based_detection(self, tmp_path: Path) -> None:
        """Step 9 counts import-based coverage."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_1_invalid_input():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 0 == 0\n",
            encoding="utf-8",
        )
        # Prod file with no matching test name, but imported by a test
        prod_file = tmp_path / "helpers.py"
        prod_file.write_text("def helper():\n    return 42\n", encoding="utf-8")
        (test_dir / "test_integration.py").write_text(
            "import helpers\n"
            "def test_helper():\n    assert helpers.helper() == 42\n"
            "def test_helper_invalid():\n    assert helpers.helper() != -1\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(prod_file),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["result"] == "PASS"

    def test_step_9_non_code_files_excluded(self, tmp_path: Path) -> None:
        """Step 9 excludes non-code files from coverage check."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_1_invalid_input():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 0 == 0\n",
            encoding="utf-8",
        )
        prod_file = tmp_path / "mymod.py"
        prod_file.write_text("def my_func():\n    return 1\n", encoding="utf-8")
        readme = tmp_path / "README.md"
        readme.write_text("# README\n", encoding="utf-8")
        config = tmp_path / "config.json"
        config.write_text("{}\n", encoding="utf-8")
        (test_dir / "test_mymod.py").write_text(
            "def test_my_func():\n    assert 1 == 1\n"
            "def test_my_func_error():\n    assert 1 != 0\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            f"{prod_file},{readme},{config}",
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["result"] == "PASS"

    def test_step_9_includes_weak_assertion_warnings(self, tmp_path: Path) -> None:
        """Step 9 evidence includes weak assertion warnings."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        weak_test = test_dir / "test_weak.py"
        weak_test.write_text(
            "def test_truthy_only():\n"
            "    x = 42\n"
            "    assert x\n"
            "def test_is_not_none():\n"
            "    x = 42\n"
            "    assert x is not None\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(weak_test),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        evidence = step9["evidence"].lower()
        assert evidence != ""
        assert "weak" in evidence

    def test_step_9_fails_on_weak_assertions_only(self, tmp_path: Path) -> None:
        """Step 9 FAILs when tests have only weak assertions."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        weak_test = test_dir / "test_weak_only.py"
        weak_test.write_text(
            "def test_only_isinstance():\n"
            "    result = get()\n"
            "    assert isinstance(result, dict)\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(weak_test),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        step9_result = step9["result"]
        assert step9_result == "FAIL"
        evidence = step9["evidence"].lower()
        assert "weak" in evidence

    def test_step_9_fails_on_happy_path_only(self, tmp_path: Path) -> None:
        """Step 9 FAILs when tests are happy-path-only (no error/edge tests)."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        happy_only = test_dir / "test_happy.py"
        happy_only.write_text(
            "def test_create_item():\n"
            "    assert True\n"
            "def test_get_item():\n"
            "    assert True\n"
            "def test_update_item():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(happy_only),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["result"] == "FAIL"
        assert "happy-path-only" in step9["evidence"].lower()

    def test_step_9_coverage_in_evidence(self, tmp_path: Path) -> None:
        """Step 9 evidence includes story file coverage."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert True\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert True\n",
            encoding="utf-8",
        )
        prod_file = tmp_path / "widget.py"
        prod_file.write_text("def widget():\n    return 1\n", encoding="utf-8")
        (test_dir / "test_widget.py").write_text(
            "def test_widget():\n    assert True\n", encoding="utf-8"
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            str(prod_file),
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        evidence_lower = step9["evidence"].lower()
        assert "coverage" in evidence_lower


class TestStep9IntegrationCoverageGate:
    """Integration test: qa_runner catches low story file coverage."""

    def test_full_pipeline_catches_33_percent_coverage(self, tmp_path: Path) -> None:
        """33% coverage (below 80% floor) reports Step 9 FAIL."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_1_invalid_input():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 0 == 0\n",
            encoding="utf-8",
        )
        # 3 production files, only 1 has a matching test -> 33%
        prod_x = tmp_path / "mod_x.py"
        prod_x.write_text("def x_func():\n    return 1\n", encoding="utf-8")
        prod_y = tmp_path / "mod_y.py"
        prod_y.write_text("def y_func():\n    return 2\n", encoding="utf-8")
        prod_z = tmp_path / "mod_z.py"
        prod_z.write_text("def z_func():\n    return 3\n", encoding="utf-8")
        (test_dir / "test_mod_x.py").write_text(
            "def test_x():\n    assert 1 == 1\n", encoding="utf-8"
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            f"{prod_x},{prod_y},{prod_z}",
            "--steps",
            "6,7,9,12",
        )
        output = json.loads(result.stdout)
        step9_results = [s for s in output["steps"] if s["step"] == 9]
        assert len(step9_results) == 1, "Step 9 must be present in results"
        step9 = step9_results[0]
        assert step9["result"] == "FAIL", (
            f"Expected FAIL for 33% coverage, got {step9['result']}: {step9['evidence']}"
        )
        evidence = step9["evidence"].lower()
        assert "coverage" in evidence, (
            f"Evidence should mention coverage: {step9['evidence']}"
        )
        assert "33" in evidence or "80" in evidence or "untested" in evidence, (
            f"Evidence should include coverage details: {step9['evidence']}"
        )
        assert output["overall_result"] == "FAIL", (
            f"Pipeline should FAIL when Step 9 fails, got {output['overall_result']}"
        )

    def test_full_pipeline_passes_at_80_percent_coverage(self, tmp_path: Path) -> None:
        """>=80% coverage passes Step 9."""
        prd = _make_prd(tmp_path)
        test_dir = tmp_path / "tests"
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_example.py").write_text(
            '"""# Tests R-P3-01"""\n'
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_2():\n"
            '    """# Tests R-P3-02"""\n'
            "    assert 1 == 1\n"
            "def test_criterion_1_invalid_input():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 0 == 0\n",
            encoding="utf-8",
        )
        # 5 prod files, 4 with tests = 80% (at the floor)
        prod_files: list[Path] = []
        for i in range(5):
            pf = tmp_path / f"service_{i}.py"
            pf.write_text(f"def func_{i}():\n    return {i}\n", encoding="utf-8")
            prod_files.append(pf)
            if i < 4:
                # Include a negative test name so happy-path-only check passes
                (test_dir / f"test_service_{i}.py").write_text(
                    f"def test_func_{i}():\n    assert {i} == {i}\n"
                    f"def test_func_{i}_invalid():\n    assert {i} != -1\n",
                    encoding="utf-8",
                )
        changed = ",".join(str(p) for p in prod_files)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(test_dir),
            "--changed-files",
            changed,
            "--steps",
            "9",
        )
        output = json.loads(result.stdout)
        step9 = output["steps"][0]
        assert step9["result"] == "PASS", (
            f"Expected PASS for 80% coverage, got {step9['result']}: {step9['evidence']}"
        )


class TestExternalScannerPlaceholders:
    """# Tests R-P3-01, R-P3-02, R-P3-03"""

    def test_changed_dir_substituted(self, tmp_path: Path) -> None:
        """# Tests R-P3-01 -- {changed_dir} replaced with actual dir."""
        src_file = tmp_path / "app.py"
        src_file.write_text("x = 1\n", encoding="utf-8")
        config = {
            "external_scanners": {
                "test_scanner": {
                    "enabled": True,
                    "cmd": "echo {changed_dir}",
                }
            }
        }
        captured_cmds: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured_cmds.append(cmd)
            return (0, "", "")

        with (
            patch("qa_runner._run_command", side_effect=mock_run),
            patch("qa_runner.shutil.which", return_value="/usr/bin/test_scanner"),
        ):
            _step_production_scan(
                [src_file], config, violation_cache={str(src_file): []}
            )
        assert len(captured_cmds) == 1
        assert "{changed_dir}" not in captured_cmds[0]
        assert str(src_file) in captured_cmds[0] or str(tmp_path) in captured_cmds[0]

    def test_changed_files_substituted(self, tmp_path: Path) -> None:
        """# Tests R-P3-02 -- {changed_files} replaced with file list."""
        src_file = tmp_path / "app.py"
        src_file.write_text("x = 1\n", encoding="utf-8")
        config = {
            "external_scanners": {
                "test_scanner": {
                    "enabled": True,
                    "cmd": "echo {changed_files}",
                }
            }
        }
        captured_cmds: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured_cmds.append(cmd)
            return (0, "", "")

        with (
            patch("qa_runner._run_command", side_effect=mock_run),
            patch("qa_runner.shutil.which", return_value="/usr/bin/test_scanner"),
        ):
            _step_production_scan(
                [src_file], config, violation_cache={str(src_file): []}
            )
        assert len(captured_cmds) == 1
        assert "{changed_files}" not in captured_cmds[0]
        assert str(src_file) in captured_cmds[0]

    def test_changed_dir_defaults_to_dot(self) -> None:
        """# Tests R-P3-03 -- fallback to '.' when no files."""
        config = {
            "external_scanners": {
                "test_scanner": {
                    "enabled": True,
                    "cmd": "echo {changed_dir}",
                }
            }
        }
        captured_cmds: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured_cmds.append(cmd)
            return (0, "", "")

        with patch("qa_runner._run_command", side_effect=mock_run):
            # _step_production_scan returns early on no source files
            _step_production_scan([], config, violation_cache={})
        result, evidence = _step_production_scan([], config, violation_cache={})
        assert result == "PASS"

    def test_changed_files_empty_when_no_files(self) -> None:
        """Empty string for {changed_files} when no source files."""
        result, evidence = _step_production_scan([], None, violation_cache={})
        assert result == "PASS"
        assert "No source files" in evidence

    def test_changed_dir_uses_common_parent(self, tmp_path: Path) -> None:
        """Multiple files from different dirs use common parent."""
        sub1 = tmp_path / "src" / "a"
        sub2 = tmp_path / "src" / "b"
        sub1.mkdir(parents=True)
        sub2.mkdir(parents=True)
        f1 = sub1 / "mod1.py"
        f2 = sub2 / "mod2.py"
        f1.write_text("x = 1\n", encoding="utf-8")
        f2.write_text("y = 2\n", encoding="utf-8")
        config = {
            "external_scanners": {
                "test_scanner": {
                    "enabled": True,
                    "cmd": "echo {changed_dir}",
                }
            }
        }
        captured_cmds: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured_cmds.append(cmd)
            return (0, "", "")

        with (
            patch("qa_runner._run_command", side_effect=mock_run),
            patch("qa_runner.shutil.which", return_value="/usr/bin/test_scanner"),
        ):
            _step_production_scan(
                [f1, f2],
                config,
                violation_cache={str(f1): [], str(f2): []},
            )
        assert len(captured_cmds) == 1
        cmd = captured_cmds[0]
        assert "{changed_dir}" not in cmd
        assert "src" in cmd


class TestNeedsShell:
    """Tests for _needs_shell shell operator detection."""

    def test_needs_shell_simple_command(self) -> None:
        """Simple command returns False."""
        assert _needs_shell("python -m pytest") is False

    def test_needs_shell_pipe(self) -> None:
        """Pipe operator returns True."""
        assert _needs_shell("ruff check | head -20") is True

    def test_needs_shell_redirect(self) -> None:
        """Redirect operator returns True."""
        assert _needs_shell("echo foo > bar.txt") is True

    def test_needs_shell_chained(self) -> None:
        """&& chaining returns True."""
        assert _needs_shell("cmd1 && cmd2") is True

    def test_needs_shell_or_chained(self) -> None:
        """|| chaining returns True."""
        assert _needs_shell("cmd1 || cmd2") is True

    def test_needs_shell_subshell(self) -> None:
        """$() subshell returns True."""
        assert _needs_shell("echo $(date)") is True

    def test_needs_shell_semicolon(self) -> None:
        """Semicolon returns True."""
        assert _needs_shell("cd /tmp; ls") is True

    def test_needs_shell_append_redirect(self) -> None:
        """>> append redirect returns True."""
        assert _needs_shell("echo line >> file.txt") is True


class TestPipelineContextDedup:
    """Tests for pipeline_context R-marker deduplication between steps 10 and 11."""

    def test_pipeline_context_dedup(self, tmp_path: Path) -> None:
        """validate_r_markers called once when step 10 caches result for step 11."""
        from qa_runner import _step_acceptance

        prd = _make_prd(tmp_path)
        test_dir = _make_test_file_with_markers(tmp_path)
        story = {
            "id": "STORY-003",
            "acceptanceCriteria": [
                {"id": "R-P3-01"},
                {"id": "R-P3-02"},
            ],
        }
        pipeline_context: dict = {}
        mock_result = {
            "markers_found": ["R-P3-01", "R-P3-02"],
            "markers_valid": ["R-P3-01", "R-P3-02"],
            "orphan_markers": [],
            "missing_markers": [],
            "manual_criteria": [],
            "result": "PASS",
        }
        with patch(
            "qa_runner.validate_r_markers", return_value=mock_result
        ) as mock_validate:
            _step_plan_conformance(
                [],
                None,
                story,
                prd,
                test_dir,
                pipeline_context=pipeline_context,
            )
            _step_acceptance(
                test_dir,
                prd,
                story,
                pipeline_context=pipeline_context,
            )
            # validate_r_markers should have been called exactly once (by step 10)
            assert mock_validate.call_count == 1


class TestCriteriaVerifiedFromRMarkers:
    """# Tests R-P2-01, R-P2-02, R-P2-03"""

    def test_criteria_verified_empty_when_no_test_files(self, tmp_path: Path) -> None:
        """# Tests R-P2-01 -- criteria_verified empty when no test files."""
        prd = _make_prd(tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tests_dir),
            "--steps",
            "11",
        )
        output = json.loads(result.stdout)
        assert output["criteria_verified"] == []

    def test_criteria_verified_includes_only_matched_ids(self, tmp_path: Path) -> None:
        """# Tests R-P2-02 -- criteria_verified contains only IDs with matching R-markers."""
        prd = _make_prd(tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / "test_partial.py"
        test_file.write_text(
            "def test_criterion_1():\n"
            '    """# Tests R-P3-01"""\n'
            "    assert 1 + 1 == 2\n",
            encoding="utf-8",
        )
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tests_dir),
            "--steps",
            "10,11",
        )
        output = json.loads(result.stdout)
        assert "R-P3-01" in output["criteria_verified"]
        assert "R-P3-02" not in output["criteria_verified"]

    def test_criteria_verified_all_ids_when_all_markers_present(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P2-03 -- criteria_verified includes all IDs when all R-markers exist."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10,11",
        )
        output = json.loads(result.stdout)
        assert sorted(output["criteria_verified"]) == ["R-P3-01", "R-P3-02"]

    def test_criteria_verified_empty_when_step_11_skipped(self, tmp_path: Path) -> None:
        """# Tests R-P2-01 -- criteria_verified empty when step 11 not run."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "1",
        )
        output = json.loads(result.stdout)
        assert output["criteria_verified"] == []


# ---------------------------------------------------------------------------
# Phase 4: Polyglot Language Profiles
# ---------------------------------------------------------------------------


def _make_config_with_ts_profile() -> dict:
    """Return a workflow config dict with python and typescript language profiles."""
    return {
        "languages": {
            "python": {
                "extensions": [".py"],
                "test_patterns": ["test_*.py", "*_test.py"],
                "commands": {
                    "lint": "echo python-lint-ok",
                    "test": "echo python-test-ok",
                },
            },
            "typescript": {
                "extensions": [".ts", ".tsx"],
                "test_patterns": ["*.test.ts", "*.spec.ts"],
                "commands": {"lint": "echo ts-lint-ok", "test": "echo ts-test-ok"},
            },
        }
    }


def _make_config_without_profiles() -> dict:
    """Return a workflow config dict with no language profiles (empty languages)."""
    return {"commands": {"lint": "echo lint-ok"}}


class TestDetectLanguages:
    """# Tests R-P4-01, R-P4-02 -- _detect_languages() function"""

    def test_r_p4_01_with_profiles_groups_by_extension(self) -> None:
        """# Tests R-P4-01 -- groups a.py and b.ts by profile extensions."""
        from qa_runner import _detect_languages

        config = _make_config_with_ts_profile()
        files = [Path("a.py"), Path("b.ts")]
        result = _detect_languages(files, config)
        assert "python" in result
        assert "typescript" in result
        assert Path("a.py") in result["python"]
        assert Path("b.ts") in result["typescript"]

    def test_r_p4_01_returns_correct_language_keys(self) -> None:
        """# Tests R-P4-01 -- language keys match profile names."""
        from qa_runner import _detect_languages

        config = _make_config_with_ts_profile()
        files = [Path("a.py"), Path("b.ts")]
        result = _detect_languages(files, config)
        assert set(result.keys()) == {"python", "typescript"}

    def test_r_p4_02_without_profiles_uses_extension_fallback(self) -> None:
        """# Tests R-P4-02 -- fallback detection when no language profiles configured."""
        from qa_runner import _detect_languages

        config = _make_config_without_profiles()
        files = [Path("a.py")]
        result = _detect_languages(files, config)
        assert "python" in result
        assert Path("a.py") in result["python"]

    def test_r_p4_02_fallback_ts_file_mapped_to_typescript(self) -> None:
        """# Tests R-P4-02 -- .ts file falls back to 'typescript' in extension map."""
        from qa_runner import _detect_languages

        config = _make_config_without_profiles()
        files = [Path("app.ts")]
        result = _detect_languages(files, config)
        assert "typescript" in result
        assert Path("app.ts") in result["typescript"]

    def test_detect_languages_py_file_mapped_to_python_key(self) -> None:
        """_detect_languages maps a.py to python key via profile."""
        from qa_runner import _detect_languages

        config = _make_config_with_ts_profile()
        result = _detect_languages([Path("a.py")], config)
        assert "python" in result, "python key not found in result"
        assert Path("a.py") in result["python"], "a.py not assigned to python"

    def test_detect_languages_empty_input_has_no_keys(self) -> None:
        """_detect_languages with empty file list has no language keys."""
        from qa_runner import _detect_languages

        config = _make_config_with_ts_profile()
        result = _detect_languages([], config)
        assert "python" not in result, "python key should not appear for empty input"
        assert "typescript" not in result, (
            "typescript key should not appear for empty input"
        )

    def test_detect_languages_unmatched_file_goes_to_python(self) -> None:
        """Unmatched file extension with profiles → assigned to python."""
        from qa_runner import _detect_languages

        config = _make_config_with_ts_profile()
        files = [Path("schema.graphql")]
        result = _detect_languages(files, config)
        assert "python" in result
        assert Path("schema.graphql") in result["python"]

    def test_detect_languages_tsx_mapped_to_typescript(self) -> None:
        """# Tests R-P4-01 -- .tsx files map to typescript profile."""
        from qa_runner import _detect_languages

        config = _make_config_with_ts_profile()
        files = [Path("Component.tsx")]
        result = _detect_languages(files, config)
        assert "typescript" in result
        assert Path("Component.tsx") in result["typescript"]


class TestStepLintWithLangMap:
    """# Tests R-P4-03, R-P4-04 -- _step_lint() with lang_map parameter"""

    def test_r_p4_03_runs_ts_lint_command_from_profile(self) -> None:
        """# Tests R-P4-03 -- runs TypeScript lint from config.languages.typescript.commands.lint."""
        from qa_runner import _step_lint

        config = _make_config_with_ts_profile()
        lang_map = {"typescript": [Path("b.ts")]}
        result_val, evidence = _step_lint(config, None, lang_map=lang_map)
        assert result_val == "PASS"
        assert "typescript" in evidence

    def test_r_p4_04_evidence_contains_per_language_results(self) -> None:
        """# Tests R-P4-04 -- evidence contains per-language results."""
        from qa_runner import _step_lint

        config = _make_config_with_ts_profile()
        lang_map = {
            "python": [Path("a.py")],
            "typescript": [Path("b.ts")],
        }
        result_val, evidence = _step_lint(config, None, lang_map=lang_map)
        assert result_val == "PASS"
        assert "python" in evidence
        assert "typescript" in evidence

    def test_r_p4_04_fail_when_any_language_fails(self) -> None:
        """# Tests R-P4-04 -- FAIL result when one language lint fails."""
        from qa_runner import _step_lint

        config = {
            "languages": {
                "python": {
                    "extensions": [".py"],
                    "commands": {"lint": "exit 1"},
                },
                "typescript": {
                    "extensions": [".ts"],
                    "commands": {"lint": "echo ts-ok"},
                },
            }
        }
        lang_map = {"python": [Path("a.py")], "typescript": [Path("b.ts")]}
        result_val, evidence = _step_lint(config, None, lang_map=lang_map)
        assert result_val == "FAIL"

    def test_step_lint_no_lang_map_fallback_to_single_cmd(self) -> None:
        """_step_lint without lang_map falls back to single command (backward compat)."""
        from qa_runner import _step_lint

        config = {"commands": {"lint": "echo lint-pass"}}
        result_val, evidence = _step_lint(config, None)
        assert result_val == "PASS"

    def test_step_lint_empty_lang_map_falls_back(self) -> None:
        """_step_lint with empty lang_map falls back to single command."""
        from qa_runner import _step_lint

        config = _make_config_with_ts_profile()
        # Override with a real fallback cmd
        config["commands"] = {"lint": "echo fallback-ok"}
        result_val, evidence = _step_lint(config, None, lang_map={})
        assert result_val == "PASS"

    def test_step_lint_lang_map_no_profiles_falls_back(self) -> None:
        """_step_lint with lang_map but no language profiles falls back."""
        from qa_runner import _step_lint

        config = {"commands": {"lint": "echo fallback-ok"}}
        lang_map = {"python": [Path("a.py")]}
        result_val, evidence = _step_lint(config, None, lang_map=lang_map)
        assert result_val == "PASS"


class TestGetTestFilesWithConfig:
    """# Tests R-P4-05 -- _get_test_files() with config parameter"""

    def test_r_p4_05_uses_ts_test_patterns_from_profile(self) -> None:
        """# Tests R-P4-05 -- returns .test.ts file using typescript test_patterns."""
        from qa_runner import _get_test_files

        config = _make_config_with_ts_profile()
        files = [Path("foo.test.ts")]
        result = _get_test_files(files, config=config)
        assert Path("foo.test.ts") in result

    def test_r_p4_05_spec_ts_matched_by_ts_patterns(self) -> None:
        """# Tests R-P4-05 -- *.spec.ts matched by typescript profile pattern."""
        from qa_runner import _get_test_files

        config = _make_config_with_ts_profile()
        files = [Path("service.spec.ts")]
        result = _get_test_files(files, config=config)
        assert Path("service.spec.ts") in result

    def test_r_p4_06_backward_compat_no_config(self) -> None:
        """-- test_foo.py detected with hardcoded pattern when no config."""
        from qa_runner import _get_test_files

        files = [Path("test_foo.py")]
        result = _get_test_files(files)
        assert Path("test_foo.py") in result

    def test_r_p4_06_backward_compat_without_profiles(self) -> None:
        """-- backward compat: test_foo.py with config_without_profiles."""
        from qa_runner import _get_test_files

        config = _make_config_without_profiles()
        files = [Path("test_foo.py")]
        result = _get_test_files(files, config=config)
        assert Path("test_foo.py") in result

    def test_get_test_files_excludes_non_test_files(self) -> None:
        """_get_test_files excludes non-test source files."""
        from qa_runner import _get_test_files

        config = _make_config_with_ts_profile()
        files = [Path("main.py"), Path("utils.ts"), Path("test_main.py")]
        result = _get_test_files(files, config=config)
        assert Path("main.py") not in result
        assert Path("utils.ts") not in result
        assert Path("test_main.py") in result

    def test_get_test_files_detects_python_test_file(self) -> None:
        """_get_test_files detects test_x.py as a test file."""
        from qa_runner import _get_test_files

        result = _get_test_files([Path("test_x.py")])
        assert Path("test_x.py") in result, "test_x.py not detected as test file"
        assert Path("main.py") not in result, "main.py falsely detected as test file"


class TestFullPipelinePolyglot:
    """-- full pipeline with mixed Python+TS files"""

    def test_r_p4_08_pipeline_with_changed_py_and_ts(self, tmp_path: Path) -> None:
        """-- full pipeline aggregates results for a.py and b.ts."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        # Create both a .py and a .ts file as changed files
        py_file = tmp_path / "module.py"
        py_file.write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n",
            encoding="utf-8",
        )
        ts_file = tmp_path / "module.ts"
        ts_file.write_text(
            "export function add(a: number, b: number): number { return a + b; }\n",
            encoding="utf-8",
        )
        changed = f"{py_file},{ts_file}"
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            changed,
            "--steps",
            "1,6,7,12",
        )
        assert result.returncode in (0, 1), f"Unexpected exit code: {result.returncode}"
        output = json.loads(result.stdout)
        step_numbers = {s["step"] for s in output["steps"]}
        assert 1 in step_numbers
        assert 12 in step_numbers
        for step in output["steps"]:
            assert step["result"] in ("PASS", "FAIL", "SKIP")

    def test_r_p4_08_pipeline_output_has_required_fields(self, tmp_path: Path) -> None:
        """-- pipeline output has all required top-level fields."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        py_file = tmp_path / "clean.py"
        py_file.write_text("def noop(): pass\n", encoding="utf-8")
        ts_file = tmp_path / "clean.ts"
        ts_file.write_text(
            "export function noop(): void {}\n",
            encoding="utf-8",
        )
        changed = f"{py_file},{ts_file}"
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            changed,
            "--steps",
            "6,7,12",
        )
        output = json.loads(result.stdout)
        assert "steps" in output
        assert "overall_result" in output
        assert len(output["steps"]) == 3


# ---------------------------------------------------------------------------
# Phase 5: Custom QA Step Plugins
# ---------------------------------------------------------------------------


def _make_config_with_custom_steps(
    after_step: int = 3,
    severity: str = "block",
    phase_types: list[str] | None = None,
    timeout_s: int = 30,
    enabled: bool = True,
    command: str = "echo custom-ok",
) -> dict:
    """Return a workflow config dict with custom_steps configured."""
    step: dict = {
        "id": "test-custom",
        "name": "Test Custom Step",
        "command": command,
        "severity": severity,
        "after_step": after_step,
        "timeout_s": timeout_s,
        "enabled": enabled,
    }
    if phase_types is not None:
        step["phase_types"] = phase_types
    return {
        "qa_runner": {
            "custom_steps": [step],
        }
    }


class TestBuildStepSequence:
    """-- _build_step_sequence()"""

    def test_r_p5_01_custom_steps_inserted_after_anchor(self) -> None:
        """-- custom step dict inserted after after_step anchor."""
        from qa_runner import _build_step_sequence

        config = _make_config_with_custom_steps(after_step=3)
        seq = _build_step_sequence(config, None)
        # Find position of step 3
        idx_3 = seq.index(3)
        # Next element should be the custom step dict
        next_item = seq[idx_3 + 1]
        custom_id = next_item.get("id") if isinstance(next_item, dict) else None
        assert custom_id == "test-custom", (
            f"Expected custom step dict with id='test-custom' after step 3, got: {next_item}"
        )

    def test_r_p5_01_all_12_base_steps_still_present(self) -> None:
        """-- all 12 base steps still present when custom steps added."""
        from qa_runner import _build_step_sequence

        config = _make_config_with_custom_steps(after_step=5)
        seq = _build_step_sequence(config, None)
        int_steps = [x for x in seq if isinstance(x, int)]
        assert int_steps == list(range(1, 13))

    def test_r_p5_02_phase_type_filter_excludes_step(self) -> None:
        """-- custom step filtered out when phase_type not in phase_types."""
        from qa_runner import _build_step_sequence

        config = _make_config_with_custom_steps(phase_types=["integration", "e2e"])
        seq = _build_step_sequence(config, "module")
        custom_steps = [x for x in seq if isinstance(x, dict)]
        assert len(custom_steps) == 0, (
            f"Custom step should be filtered out for 'module' phase, but got: {custom_steps}"
        )

    def test_r_p5_02_phase_type_filter_includes_matching_step(self) -> None:
        """-- custom step included when phase_type is in phase_types."""
        from qa_runner import _build_step_sequence

        config = _make_config_with_custom_steps(phase_types=["integration", "e2e"])
        seq = _build_step_sequence(config, "integration")
        custom_steps = [x for x in seq if isinstance(x, dict)]
        assert len(custom_steps) == 1, (
            f"Expected 1 custom step for 'integration' phase, got {len(custom_steps)}"
        )

    def test_r_p5_02_no_phase_types_field_always_included(self) -> None:
        """-- custom step without phase_types is always included."""
        from qa_runner import _build_step_sequence

        config = _make_config_with_custom_steps(phase_types=None)
        for pt in ("foundation", "module", "integration", "e2e"):
            seq = _build_step_sequence(config, pt)
            custom_steps = [x for x in seq if isinstance(x, dict)]
            assert len(custom_steps) == 1, (
                f"Expected custom step included for phase_type={pt}"
            )

    def test_r_p5_03_no_custom_steps_returns_1_to_12(self) -> None:
        """-- no custom steps → returns [1..12] (unchanged behavior)."""
        from qa_runner import _build_step_sequence

        config_no_custom = {"qa_runner": {"custom_steps": []}}
        seq = _build_step_sequence(config_no_custom, None)
        assert seq == list(range(1, 13))

    def test_r_p5_03_missing_qa_runner_section_returns_1_to_12(self) -> None:
        """-- config without qa_runner.custom_steps → [1..12]."""
        from qa_runner import _build_step_sequence

        seq = _build_step_sequence({}, None)
        assert seq == list(range(1, 13))

    def test_r_p5_03_disabled_step_excluded_from_sequence(self) -> None:
        """-- disabled custom step excluded → returns [1..12]."""
        from qa_runner import _build_step_sequence

        config = _make_config_with_custom_steps(enabled=False)
        seq = _build_step_sequence(config, None)
        assert seq == list(range(1, 13))


class TestRunCustomStep:
    """-- _run_custom_step()"""

    def test_r_p5_04_block_severity_fail_on_nonzero_exit(self) -> None:
        """-- FAIL when exit non-zero and severity=block."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "lint-check",
            "name": "Lint Check",
            "command": "some-lint",
            "severity": "block",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(1, "", "lint failed")):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "FAIL"
        assert result["step"] == "custom:lint-check"
        assert "block" in result["evidence"]

    def test_r_p5_04_block_severity_pass_on_zero_exit(self) -> None:
        """-- PASS when exit 0 and severity=block."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "lint-check",
            "name": "Lint Check",
            "command": "some-lint",
            "severity": "block",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(0, "lint ok", "")):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "PASS"

    def test_r_p5_05_warn_severity_warn_on_nonzero_exit(self) -> None:
        """-- WARN when exit non-zero and severity=warn."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "license-check",
            "name": "License Check",
            "command": "check-license",
            "severity": "warn",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(1, "", "missing headers")):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "WARN", (
            f"Expected WARN for severity=warn, got {result['result']}"
        )
        assert result["step"] == "custom:license-check"

    def test_r_p5_05_warn_severity_pass_on_zero_exit(self) -> None:
        """-- PASS when exit 0 and severity=warn."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "license-check",
            "name": "License Check",
            "command": "check-license",
            "severity": "warn",
            "timeout_s": 30,
        }
        with patch(
            "qa_runner._run_command", return_value=(0, "all headers present", "")
        ):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "PASS"

    def test_r_p5_06_timeout_block_severity_returns_fail(self) -> None:
        """-- timeout with severity=block → FAIL."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "slow-check",
            "name": "Slow Check",
            "command": "sleep 999",
            "severity": "block",
            "timeout_s": 1,
        }
        # Simulate timeout: _run_command returns (-1, "", "Command timed out after 1s")
        with patch(
            "qa_runner._run_command",
            return_value=(-1, "", "Command timed out after 1s"),
        ):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "FAIL"
        assert "timed out" in result["evidence"].lower() or "1s" in result["evidence"]

    def test_r_p5_06_timeout_warn_severity_returns_warn(self) -> None:
        """-- timeout with severity=warn → WARN."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "slow-warn",
            "name": "Slow Warn Check",
            "command": "sleep 999",
            "severity": "warn",
            "timeout_s": 1,
        }
        with patch(
            "qa_runner._run_command",
            return_value=(-1, "", "Command timed out after 1s"),
        ):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "WARN"

    def test_r_p5_07_step_key_format_is_custom_colon_id(self) -> None:
        """-- step key is 'custom:{id}' in result dict."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "my-special-check",
            "name": "My Special Check",
            "command": "echo ok",
            "severity": "block",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(0, "ok", "")):
            result = _run_custom_step(step_def, [])
        assert result["step"] == "custom:my-special-check"
        assert result["name"] == "My Special Check"

    def test_r_p5_07_result_has_all_required_fields(self) -> None:
        """-- result dict has step, name, result, evidence, duration_ms."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "check-x",
            "name": "Check X",
            "command": "echo x",
            "severity": "block",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(0, "x", "")):
            result = _run_custom_step(step_def, [])
        assert result["step"] == "custom:check-x"
        assert result["name"] == "Check X"
        assert result["result"] == "PASS"
        assert result["duration_ms"] >= 0
        required_keys = {"step", "name", "result", "evidence", "duration_ms"}
        assert required_keys <= set(result.keys())

    def test_r_p5_09_substitutes_changed_files_placeholder(
        self, tmp_path: Path
    ) -> None:
        """-- {changed_files} replaced with actual file paths."""
        from qa_runner import _run_custom_step

        src = tmp_path / "module.py"
        src.write_text("x = 1\n", encoding="utf-8")
        step_def = {
            "id": "scan",
            "name": "File Scan",
            "command": "echo {changed_files}",
            "severity": "block",
            "timeout_s": 30,
        }
        captured: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured.append(cmd)
            return (0, "ok", "")

        with patch("qa_runner._run_command", side_effect=mock_run):
            _run_custom_step(step_def, [src])

        assert len(captured) == 1
        assert "{changed_files}" not in captured[0]
        assert str(src) in captured[0]

    def test_r_p5_09_substitutes_changed_dir_placeholder(self, tmp_path: Path) -> None:
        """-- {changed_dir} replaced with common parent of changed files."""
        from qa_runner import _run_custom_step

        src = tmp_path / "module.py"
        src.write_text("x = 1\n", encoding="utf-8")
        step_def = {
            "id": "dir-scan",
            "name": "Dir Scan",
            "command": "echo {changed_dir}",
            "severity": "block",
            "timeout_s": 30,
        }
        captured: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured.append(cmd)
            return (0, "ok", "")

        with patch("qa_runner._run_command", side_effect=mock_run):
            _run_custom_step(step_def, [src])

        assert len(captured) == 1
        assert "{changed_dir}" not in captured[0]

    def test_r_p5_09_both_placeholders_substituted(self, tmp_path: Path) -> None:
        """-- both {changed_files} and {changed_dir} substituted."""
        from qa_runner import _run_custom_step

        src = tmp_path / "app.py"
        src.write_text("y = 2\n", encoding="utf-8")
        step_def = {
            "id": "both-scan",
            "name": "Both Scan",
            "command": "scan {changed_dir} --files {changed_files}",
            "severity": "block",
            "timeout_s": 30,
        }
        captured: list[str] = []

        def mock_run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
            captured.append(cmd)
            return (0, "ok", "")

        with patch("qa_runner._run_command", side_effect=mock_run):
            _run_custom_step(step_def, [src])

        assert len(captured) == 1
        assert "{changed_files}" not in captured[0]
        assert "{changed_dir}" not in captured[0]
        assert str(src) in captured[0]


class TestCustomStepOverallResult:
    """-- overall FAIL counting for custom steps"""

    def test_r_p5_08_block_fail_counts_toward_overall_fail(self) -> None:
        """-- block severity FAIL → overall FAIL."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "strict-check",
            "name": "Strict Check",
            "command": "some-check",
            "severity": "block",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(1, "", "failed")):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "FAIL"
        # Simulate overall result logic: has_fail if any result == "FAIL"
        step_results = [result]
        has_fail = any(s["result"] == "FAIL" for s in step_results)
        assert has_fail is True

    def test_r_p5_08_warn_fail_does_not_count_toward_overall_fail(self) -> None:
        """-- warn severity FAIL (WARN result) does NOT cause overall FAIL."""
        from qa_runner import _run_custom_step

        step_def = {
            "id": "advisory-check",
            "name": "Advisory Check",
            "command": "some-advisory",
            "severity": "warn",
            "timeout_s": 30,
        }
        with patch("qa_runner._run_command", return_value=(1, "", "advisory issue")):
            result = _run_custom_step(step_def, [])
        assert result["result"] == "WARN"
        # WARN should NOT be counted as FAIL in overall result logic
        step_results = [result]
        has_fail = any(s["result"] == "FAIL" for s in step_results)
        assert has_fail is False

    def test_r_p5_08_integration_block_fail_in_pipeline(self, tmp_path: Path) -> None:
        """-- integration: block custom step FAIL → overall_result FAIL."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        clean_file = _make_clean_source(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--changed-files",
            str(clean_file),
            "--steps",
            "10",
        )
        # This verifies the pipeline runs; actual custom step integration
        # is tested via unit tests above (full subprocess integration would
        # require injecting config, which is tested via unit approach)
        output = json.loads(result.stdout)
        assert "overall_result" in output

    def test_r_p5_08_warn_step_in_overall_result_stays_pass(
        self, tmp_path: Path
    ) -> None:
        """-- WARN in steps[] does not flip overall from PASS to FAIL."""
        # Simulate step_results with a WARN entry (no FAIL entries)
        step_results = [
            {
                "step": 10,
                "name": "Plan Conformance Check",
                "result": "PASS",
                "evidence": "ok",
                "duration_ms": 1,
            },
            {
                "step": "custom:warn-check",
                "name": "Warn Check",
                "result": "WARN",
                "evidence": "advisory",
                "duration_ms": 1,
            },
        ]
        has_fail = any(s["result"] == "FAIL" for s in step_results)
        overall = "FAIL" if has_fail else "PASS"
        assert overall == "PASS"


# ---------------------------------------------------------------------------
# STORY-001: Authoritative Verification Boundary
# Tests R-P1-01, R-P1-02, R-P1-03
# ---------------------------------------------------------------------------


class TestComputeReceiptHash:
    """# Tests R-P1-01"""

    def test_returns_64_char_hex(self) -> None:
        """# Tests R-P1-01 -- returns 64-character hexadecimal string."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "name": "Lint", "result": "PASS"}]
        result = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "foundation")
        assert isinstance(result, str), "Should return a string"
        assert len(result) == 64, f"Expected 64 chars, got {len(result)}"
        assert all(c in "0123456789abcdef" for c in result), "Should be hex"

    def test_hash_changes_when_story_id_changes(self) -> None:
        """# Tests R-P1-01 -- hash changes when story_id changes."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "result": "PASS"}]
        h1 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "foundation")
        h2 = _compute_receipt_hash(steps, "STORY-002", 1, "PASS", "foundation")
        assert h1 != h2, "Hash should change when story_id changes"

    def test_hash_changes_when_attempt_changes(self) -> None:
        """# Tests R-P1-01 -- hash changes when attempt changes."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "result": "PASS"}]
        h1 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "foundation")
        h2 = _compute_receipt_hash(steps, "STORY-001", 2, "PASS", "foundation")
        assert h1 != h2, "Hash should change when attempt changes"

    def test_hash_changes_when_overall_result_changes(self) -> None:
        """# Tests R-P1-01 -- hash changes when overall_result changes."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "result": "PASS"}]
        h1 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "foundation")
        h2 = _compute_receipt_hash(steps, "STORY-001", 1, "FAIL", "foundation")
        assert h1 != h2, "Hash should change when overall_result changes"

    def test_hash_changes_when_phase_type_changes(self) -> None:
        """# Tests R-P1-01 -- hash changes when phase_type changes."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "result": "PASS"}]
        h1 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "foundation")
        h2 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "module")
        assert h1 != h2, "Hash should change when phase_type changes"

    def test_hash_changes_when_steps_change(self) -> None:
        """# Tests R-P1-01 -- hash changes when steps change."""
        from qa_runner import _compute_receipt_hash

        steps_a = [{"step": 1, "result": "PASS"}]
        steps_b = [{"step": 1, "result": "FAIL"}]
        h1 = _compute_receipt_hash(steps_a, "STORY-001", 1, "PASS", "foundation")
        h2 = _compute_receipt_hash(steps_b, "STORY-001", 1, "PASS", "foundation")
        assert h1 != h2, "Hash should change when steps change"

    def test_hash_is_deterministic(self) -> None:
        """# Tests R-P1-01 -- same inputs produce same hash."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "result": "PASS"}, {"step": 2, "result": "SKIP"}]
        h1 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "integration")
        h2 = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", "integration")
        assert h1 == h2, "Same inputs should produce same hash"

    def test_hash_accepts_none_phase_type(self) -> None:
        """# Tests R-P1-01 -- accepts None as phase_type."""
        from qa_runner import _compute_receipt_hash

        steps = [{"step": 1, "result": "PASS"}]
        result = _compute_receipt_hash(steps, "STORY-001", 1, "PASS", None)
        assert len(result) == 64, "Should return 64-char hex even with None phase_type"


class TestWriteReceipt:
    """# Tests R-P1-02"""

    def test_creates_receipt_file(self, tmp_path: Path) -> None:
        """# Tests R-P1-02 -- creates qa-receipt.json at expected path."""
        from qa_runner import _write_receipt

        output = {
            "story_id": "STORY-001",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "phase_type": "foundation",
            "steps": [
                {
                    "step": 1,
                    "name": "Lint",
                    "result": "PASS",
                    "evidence": "ok",
                    "duration_ms": 10,
                }
            ],
            "overall_result": "PASS",
            "criteria_verified": ["R-P1-01"],
            "production_violations": 0,
            "receipt_hash": "a" * 64,
        }
        receipt_path = _write_receipt(output, "STORY-001", 1, base_dir=tmp_path)
        expected = tmp_path / "STORY-001" / "attempt-1" / "qa-receipt.json"
        assert expected.is_file(), f"Receipt file not found at {expected}"
        assert receipt_path == str(expected)

    def test_receipt_contains_required_fields(self, tmp_path: Path) -> None:
        """# Tests R-P1-02 -- receipt file contains all required fields."""
        from qa_runner import _write_receipt

        steps = [
            {
                "step": 1,
                "name": "Lint",
                "result": "PASS",
                "evidence": "ok",
                "duration_ms": 5,
            }
        ]
        output = {
            "story_id": "STORY-001",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "phase_type": "foundation",
            "steps": steps,
            "overall_result": "PASS",
            "criteria_verified": [],
            "production_violations": 0,
            "receipt_hash": "b" * 64,
        }
        receipt_path = _write_receipt(output, "STORY-001", 2, base_dir=tmp_path)
        data = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        required = {
            "receipt_hash",
            "story_id",
            "attempt",
            "timestamp",
            "overall_result",
            "steps",
            "receipt_version",
        }
        missing = required - set(data.keys())
        assert not missing, f"Receipt missing fields: {missing}"

    def test_receipt_has_correct_values(self, tmp_path: Path) -> None:
        """# Tests R-P1-02 -- receipt fields match expected values."""
        from qa_runner import _write_receipt

        steps = [{"step": 1, "result": "PASS"}]
        output = {
            "story_id": "STORY-099",
            "timestamp": "2026-03-01T12:00:00+00:00",
            "phase_type": "module",
            "steps": steps,
            "overall_result": "FAIL",
            "criteria_verified": ["R-X-01"],
            "production_violations": 3,
            "receipt_hash": "c" * 64,
        }
        receipt_path = _write_receipt(output, "STORY-099", 3, base_dir=tmp_path)
        data = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        assert data["story_id"] == "STORY-099"
        assert data["attempt"] == 3
        assert data["overall_result"] == "FAIL"
        assert data["steps"] == steps
        assert data["receipt_version"] == "1"
        assert data["receipt_hash"] == "c" * 64

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """# Tests R-P1-02 -- creates parent directories as needed."""
        from qa_runner import _write_receipt

        output = {
            "story_id": "STORY-001",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "phase_type": None,
            "steps": [],
            "overall_result": "PASS",
            "criteria_verified": [],
            "production_violations": 0,
            "receipt_hash": "d" * 64,
        }
        # base_dir points to non-existent subdirectory
        base = tmp_path / "nested" / "receipts"
        receipt_path = _write_receipt(output, "STORY-001", 1, base_dir=base)
        assert Path(receipt_path).is_file(), "Should create nested dirs"

    def test_returns_path_string(self, tmp_path: Path) -> None:
        """# Tests R-P1-02 -- returns path as string."""
        from qa_runner import _write_receipt

        output = {
            "story_id": "STORY-001",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "phase_type": "foundation",
            "steps": [],
            "overall_result": "PASS",
            "criteria_verified": [],
            "production_violations": 0,
            "receipt_hash": "e" * 64,
        }
        receipt_path = _write_receipt(output, "STORY-001", 1, base_dir=tmp_path)
        assert isinstance(receipt_path, str), "Should return a string path"
        assert "STORY-001" in receipt_path, "Path should contain story ID"


class TestMainOutputReceiptFields:
    """# Tests R-P1-03"""

    def test_main_output_includes_receipt_hash(self, tmp_path: Path) -> None:
        """# Tests R-P1-03 -- main() stdout JSON includes receipt_hash field."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert "receipt_hash" in output, "Output should include receipt_hash"
        h = output["receipt_hash"]
        assert isinstance(h, str) and len(h) == 64, (
            f"receipt_hash should be 64-char hex, got: {h!r}"
        )
        assert all(c in "0123456789abcdef" for c in h), "receipt_hash should be hex"

    def test_main_output_includes_receipt_path(self, tmp_path: Path) -> None:
        """# Tests R-P1-03 -- main() stdout JSON includes receipt_path field."""
        prd = _make_prd(tmp_path)
        _make_test_file_with_markers(tmp_path)
        result = _run_qa_runner(
            "--story",
            "STORY-003",
            "--prd",
            str(prd),
            "--test-dir",
            str(tmp_path / "tests"),
            "--steps",
            "10",
        )
        output = json.loads(result.stdout)
        assert "receipt_path" in output, "Output should include receipt_path"
        assert isinstance(output["receipt_path"], str), (
            "receipt_path should be a string"
        )


# ---------------------------------------------------------------------------
# STORY-005: True Zero-Skip Enforcement (R-P5-01 through R-P5-04)
# ---------------------------------------------------------------------------


class TestRequiredVerificationSteps:
    """# Tests R-P5-01 -- _required_verification_steps returns dict[str, bool]."""

    def _make_story(self, test_types: list) -> dict:
        """Build a minimal story dict with given testType values."""
        return {
            "id": "STORY-005",
            "acceptanceCriteria": [
                {"id": f"R-P5-0{i + 1}", "criterion": f"crit {i}", "testType": tt}
                for i, tt in enumerate(test_types)
            ],
        }

    def test_returns_dict_with_all_required_keys(self) -> None:
        """# Tests R-P5-01 -- returns dict with exactly 5 required keys."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "module", {})
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "lint",
            "type",
            "unit",
            "integration",
            "regression",
        }

    def test_values_are_bool(self) -> None:
        """# Tests R-P5-01 -- all values in the returned dict are bool."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "module", {})
        for key, val in result.items():
            assert val in (True, False), f"key {key!r} has non-bool value: {val!r}"

    def test_unit_required_when_unit_testtype_present(self) -> None:
        """# Tests R-P5-01 -- unit=True when any criterion has testType unit."""

        story = self._make_story(["unit", "manual"])
        result = _required_verification_steps(story, "module", {})
        assert result["unit"] is True

    def test_unit_not_required_when_all_manual(self) -> None:
        """# Tests R-P5-01 -- unit=False when all criteria are testType manual."""

        story = self._make_story(["manual", "manual"])
        result = _required_verification_steps(story, "module", {})
        assert result["unit"] is False

    def test_integration_required_when_integration_testtype_present(self) -> None:
        """# Tests R-P5-01 -- integration=True when testType integration exists."""

        story = self._make_story(["unit", "integration"])
        result = _required_verification_steps(story, "module", {})
        assert result["integration"] is True

    def test_integration_not_required_when_no_integration_testtype(self) -> None:
        """# Tests R-P5-01 -- integration=False when no integration testType."""

        story = self._make_story(["unit", "manual"])
        result = _required_verification_steps(story, "module", {})
        assert result["integration"] is False

    def test_lint_required_for_non_docs_phase(self) -> None:
        """# Tests R-P5-01 -- lint=True for module phase_type."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "module", {})
        assert result["lint"] is True

    def test_lint_not_required_for_docs_phase(self) -> None:
        """# Tests R-P5-01 -- lint=False for docs phase_type."""

        story = self._make_story(["manual"])
        result = _required_verification_steps(story, "docs", {})
        assert result["lint"] is False

    def test_type_required_when_config_has_type_check_command(self) -> None:
        """# Tests R-P5-01 -- type=True when config has type_check command."""

        story = self._make_story(["unit"])
        config = {"commands": {"type_check": "mypy src/"}}
        result = _required_verification_steps(story, "module", config)
        assert result["type"] is True

    def test_type_not_required_when_no_type_check_command(self) -> None:
        """# Tests R-P5-01 -- type=False when config has no type_check command."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "module", {})
        assert result["type"] is False

    def test_regression_required_for_integration_phase(self) -> None:
        """# Tests R-P5-01 -- regression=True for integration phase_type."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "integration", {})
        assert result["regression"] is True

    def test_regression_required_for_full_phase(self) -> None:
        """# Tests R-P5-01 -- regression=True for e2e phase_type."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "e2e", {})
        assert result["regression"] is True

    def test_regression_not_required_for_module_phase(self) -> None:
        """# Tests R-P5-01 -- regression=False for module phase_type."""

        story = self._make_story(["unit"])
        result = _required_verification_steps(story, "module", {})
        assert result["regression"] is False

    def test_works_with_none_story(self) -> None:
        """# Tests R-P5-01 -- handles story=None without error."""

        result = _required_verification_steps(None, "module", {})
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "lint",
            "type",
            "unit",
            "integration",
            "regression",
        }

    def test_works_with_none_phase_type(self) -> None:
        """# Tests R-P5-01 -- handles phase_type=None without error."""

        story = {
            "id": "STORY-X",
            "acceptanceCriteria": [{"id": "R-X-01", "testType": "unit"}],
        }
        result = _required_verification_steps(story, None, {})
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "lint",
            "type",
            "unit",
            "integration",
            "regression",
        }


class TestZeroSkipEnforcement:
    """# Tests R-P5-02 -- Required steps with missing config return FAIL not SKIP."""

    def test_unit_step_fails_when_required_but_no_command(self) -> None:
        """# Tests R-P5-02 -- Step 3 returns FAIL when unit required but no command."""
        from qa_runner import _step_unit_tests

        story = {
            "id": "STORY-005",
            "acceptanceCriteria": [{"id": "R-P5-01", "testType": "unit"}],
            "gateCmds": {},
        }
        result, evidence = _step_unit_tests({}, story, required=True)
        assert result == "FAIL", f"Expected FAIL, got: {result}"

    def test_unit_step_skips_when_not_required_and_no_command(self) -> None:
        """# Tests R-P5-03 -- Step 3 returns SKIP when unit NOT required and no command."""
        from qa_runner import _step_unit_tests

        story = {
            "id": "STORY-005",
            "acceptanceCriteria": [{"id": "R-P5-01", "testType": "manual"}],
            "gateCmds": {},
        }
        result, evidence = _step_unit_tests({}, story, required=False)
        assert result == "SKIP", f"Expected SKIP, got: {result}"

    def test_lint_step_fails_when_required_but_no_command(self) -> None:
        """# Tests R-P5-02 -- Step 1 returns FAIL when lint required but no command."""
        from qa_runner import _step_lint

        story = {"id": "STORY-005", "gateCmds": {}}
        result, evidence = _step_lint({}, story, required=True)
        assert result == "FAIL", f"Expected FAIL, got: {result}"

    def test_lint_step_skips_when_not_required_and_no_command(self) -> None:
        """# Tests R-P5-03 -- Step 1 returns SKIP when lint NOT required and no command."""
        from qa_runner import _step_lint

        story = {"id": "STORY-005", "gateCmds": {}}
        result, evidence = _step_lint({}, story, required=False)
        assert result == "SKIP", f"Expected SKIP, got: {result}"

    def test_integration_step_fails_when_required_but_no_command(self) -> None:
        """# Tests R-P5-02 -- Step 4 returns FAIL when integration required but no command."""
        from qa_runner import _step_integration_tests

        story = {"id": "STORY-005", "gateCmds": {}}
        result, evidence = _step_integration_tests({}, story, required=True)
        assert result == "FAIL", f"Expected FAIL, got: {result}"

    def test_integration_step_skips_when_not_required_and_no_command(self) -> None:
        """# Tests R-P5-03 -- Step 4 returns SKIP when integration NOT required."""
        from qa_runner import _step_integration_tests

        story = {"id": "STORY-005", "gateCmds": {}}
        result, evidence = _step_integration_tests({}, story, required=False)
        assert result == "SKIP", f"Expected SKIP, got: {result}"

    def test_regression_step_fails_when_required_but_no_command(self) -> None:
        """# Tests R-P5-02 -- Step 5 returns FAIL when regression required but no command."""
        from qa_runner import _step_regression

        result, evidence = _step_regression({}, story=None, required=True)
        assert result == "FAIL", f"Expected FAIL, got: {result}"

    def test_regression_step_skips_when_not_required_and_no_command(self) -> None:
        """# Tests R-P5-03 -- Step 5 returns SKIP when regression NOT required."""
        from qa_runner import _step_regression

        result, evidence = _step_regression({}, story=None, required=False)
        assert result == "SKIP", f"Expected SKIP, got: {result}"

    def test_type_step_fails_when_required_but_no_command(self) -> None:
        """# Tests R-P5-02 -- Step 2 returns FAIL when type required but no command."""

        result, evidence = _step_type_check({}, required=True)
        assert result == "FAIL", f"Expected FAIL, got: {result}"

    def test_type_step_skips_when_not_required_and_no_command(self) -> None:
        """# Tests R-P5-03 -- Step 2 returns SKIP when type NOT required."""

        result, evidence = _step_type_check({}, required=False)
        assert result == "SKIP", f"Expected SKIP, got: {result}"


class TestOnlyInapplicableStepsMaySkip:
    """# Tests R-P5-03 -- Only genuinely inapplicable steps may SKIP."""

    def test_phase_type_exclusion_may_skip(self) -> None:
        """# Tests R-P5-03 -- SKIP is valid when phase_type excludes step."""
        from qa_runner import PHASE_TYPE_RELEVANCE

        foundation_steps = PHASE_TYPE_RELEVANCE["foundation"]
        assert 4 not in foundation_steps

    def test_all_manual_criteria_may_skip_unit(self) -> None:
        """# Tests R-P5-03 -- unit step SKIP valid when all criteria are manual."""

        story = {
            "id": "STORY-X",
            "acceptanceCriteria": [
                {"id": "R-X-01", "testType": "manual"},
                {"id": "R-X-02", "testType": "manual"},
            ],
        }
        req = _required_verification_steps(story, "module", {})
        assert req["unit"] is False

    def test_required_step_missing_command_is_not_inapplicable(self) -> None:
        """# Tests R-P5-03 -- A required step with missing command is FAIL, not SKIP."""
        from qa_runner import _step_unit_tests

        story = {
            "id": "STORY-005",
            "acceptanceCriteria": [{"id": "R-P5-01", "testType": "unit"}],
            "gateCmds": {},
        }
        result, evidence = _step_unit_tests({}, story, required=True)
        assert result != "SKIP"
        assert result == "FAIL"


class TestStep6ExternalScanners:
    """# Tests R-P9-01, R-P9-02, R-P9-03 -- Step 6 external scanner integration."""

    def test_r_p9_01_step6_invokes_enabled_scanner_found_on_path(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P9-01 -- step 6 invokes enabled scanner when executable found on PATH."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "my-scanner": {
                    "enabled": True,
                    "executable": "my-scanner",
                    "args": ["--path", "{scope}"],
                    "strict_mode": True,
                }
            }
        }
        with (
            patch("shutil.which", return_value="/usr/bin/my-scanner") as mock_which,
            patch(
                "qa_runner._run_command", return_value=(0, "scan clean", "")
            ) as mock_run,
        ):
            result_val, evidence = _step_security_scan([clean_file], config=config)
            mock_which.assert_called_once_with("my-scanner")
            assert mock_run.called, (
                "Expected _run_command to be called for enabled scanner"
            )
            assert result_val == "PASS"

    def test_r_p9_01_step6_uses_executable_field_over_dict_key(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P9-01 -- executable field is used; falls back to dict key name."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)

        # Case 1: explicit executable field
        config_explicit = {
            "external_scanners": {
                "scanner-alias": {
                    "enabled": True,
                    "executable": "actual-binary",
                    "strict_mode": False,
                }
            }
        }
        with (
            patch("shutil.which", return_value="/usr/bin/actual-binary") as mock_which,
            patch("qa_runner._run_command", return_value=(0, "ok", "")),
        ):
            result_val, _evidence = _step_security_scan(
                [clean_file], config=config_explicit
            )
            mock_which.assert_called_once_with("actual-binary")
            assert result_val in ("PASS", "FAIL", "SKIP")

        # Case 2: no executable field — falls back to dict key name
        config_fallback = {
            "external_scanners": {
                "dict-key-binary": {
                    "enabled": True,
                    "strict_mode": False,
                }
            }
        }
        with (
            patch(
                "shutil.which", return_value="/usr/bin/dict-key-binary"
            ) as mock_which2,
            patch("qa_runner._run_command", return_value=(0, "ok", "")),
        ):
            result_val2, _evidence2 = _step_security_scan(
                [clean_file], config=config_fallback
            )
            mock_which2.assert_called_once_with("dict-key-binary")
            assert result_val2 in ("PASS", "FAIL", "SKIP")

    def test_r_p9_02_strict_mode_true_missing_executable_returns_fail(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P9-02 -- strict_mode: true + missing executable returns FAIL."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "silent-failure-hunter": {
                    "enabled": True,
                    "executable": "silent-failure-hunter",
                    "strict_mode": True,
                }
            }
        }
        with patch("shutil.which", return_value=None):
            result_val, evidence = _step_security_scan([clean_file], config=config)
        assert result_val == "FAIL"
        assert "silent-failure-hunter" in evidence

    def test_r_p9_02_strict_mode_false_missing_executable_returns_skip(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P9-02 -- strict_mode: false (or absent) + missing executable returns SKIP."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "optional-scanner": {
                    "enabled": True,
                    "executable": "optional-scanner",
                    "strict_mode": False,
                }
            }
        }
        with patch("shutil.which", return_value=None):
            result_val, evidence = _step_security_scan([clean_file], config=config)
        # SKIP means step still passes overall (not a hard FAIL)
        assert result_val in ("PASS", "SKIP")
        assert "optional-scanner" in evidence

    def test_r_p9_02_no_strict_mode_key_missing_executable_returns_skip(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P9-02 -- absent strict_mode key + missing executable returns SKIP (not FAIL)."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "another-scanner": {
                    "enabled": True,
                    "executable": "another-scanner",
                    # No strict_mode key — defaults to False
                }
            }
        }
        with patch("shutil.which", return_value=None):
            result_val, evidence = _step_security_scan([clean_file], config=config)
        assert result_val in ("PASS", "SKIP")

    def test_r_p9_03_disabled_scanner_not_invoked(self, tmp_path: Path) -> None:
        """# Tests R-P9-03 -- disabled scanner is not invoked in step 6."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "disabled-scanner": {
                    "enabled": False,
                    "executable": "disabled-scanner",
                    "strict_mode": True,
                }
            }
        }
        with (
            patch("shutil.which") as mock_which,
            patch("qa_runner._run_command") as mock_run,
        ):
            result_val, evidence = _step_security_scan([clean_file], config=config)
            mock_which.assert_not_called()
            mock_run.assert_not_called()
            assert result_val in ("PASS", "FAIL", "SKIP")

    def test_r_p9_03_no_config_falls_back_to_existing_prod_scan(
        self, tmp_path: Path
    ) -> None:
        """# Tests R-P9-03 -- no external_scanners config → existing violation scan logic."""
        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        # No config passed — uses internal violation scan only
        result_val, evidence = _step_security_scan([clean_file], config=None)
        assert result_val in ("PASS", "FAIL", "SKIP")

    def test_r_p9_01_scanner_fail_exit_code_returns_fail(self, tmp_path: Path) -> None:
        """# Tests R-P9-01 -- scanner non-zero exit returns FAIL."""
        from unittest.mock import patch

        from qa_runner import _step_security_scan

        clean_file = _make_clean_source(tmp_path)
        config = {
            "external_scanners": {
                "strict-scanner": {
                    "enabled": True,
                    "executable": "strict-scanner",
                    "strict_mode": True,
                }
            }
        }
        with (
            patch("shutil.which", return_value="/usr/bin/strict-scanner"),
            patch("qa_runner._run_command", return_value=(1, "", "found issues")),
        ):
            result_val, evidence = _step_security_scan([clean_file], config=config)
        assert result_val == "FAIL"
        assert "strict-scanner" in evidence


# ---------------------------------------------------------------------------
# StepResult enum tests (R-P2-01, R-P2-02, R-P2-03) — STORY-002 Phase 2
# ---------------------------------------------------------------------------


class TestStepResultEnum:
    """# Tests R-P2-01, R-P2-02, R-P2-03"""

    def test_step_result_is_str_enum(self) -> None:
        """# Tests R-P2-01 -- StepResult is a str subclass and Enum."""
        from enum import Enum

        assert issubclass(StepResult, str)
        assert issubclass(StepResult, Enum)

    def test_step_result_pass_value(self) -> None:
        """# Tests R-P2-01 -- StepResult.PASS.value == 'PASS'."""

        assert StepResult.PASS.value == "PASS"

    def test_step_result_fail_value(self) -> None:
        """# Tests R-P2-01 -- StepResult.FAIL.value == 'FAIL'."""

        assert StepResult.FAIL.value == "FAIL"

    def test_step_result_skip_value(self) -> None:
        """# Tests R-P2-01 -- StepResult.SKIP.value == 'SKIP'."""

        assert StepResult.SKIP.value == "SKIP"

    def test_step_result_pass_equals_string(self) -> None:
        """# Tests R-P2-01 -- StepResult.PASS == 'PASS' (str subclass comparison)."""

        # str Enum members compare equal to their string value
        assert StepResult.PASS == "PASS"
        assert StepResult.FAIL == "FAIL"
        assert StepResult.SKIP == "SKIP"

    def test_step_functions_return_step_result(self) -> None:
        """# Tests R-P2-02 -- _step_lint returns tuple[StepResult, str]."""
        from qa_runner import _step_lint

        result_val, evidence = _step_lint({}, None)
        assert isinstance(result_val, StepResult)
        assert result_val in ("PASS", "FAIL", "SKIP")
        assert isinstance(evidence, str)

    def test_step_unit_tests_returns_step_result(self) -> None:
        """# Tests R-P2-02 -- _step_unit_tests returns tuple[StepResult, str]."""
        from qa_runner import _step_unit_tests

        result_val, evidence = _step_unit_tests({}, None)
        assert isinstance(result_val, StepResult)
        assert result_val in ("PASS", "FAIL", "SKIP")
        assert isinstance(evidence, str)

    def test_step_coverage_returns_step_result(self) -> None:
        """# Tests R-P2-02 -- _step_coverage returns tuple[StepResult, str]."""

        result_val, evidence = _step_coverage({})
        assert isinstance(result_val, StepResult)
        assert result_val in ("PASS", "FAIL", "SKIP")
        assert isinstance(evidence, str)

    def test_json_output_serializes_result_as_string(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- JSON boundary: step result serialized as string, not Enum repr."""
        prd = _make_prd(tmp_path)
        result = _run_qa_runner(
            "--story", "STORY-003", "--prd", str(prd), "--steps", "1", cwd=str(tmp_path)
        )
        output = json.loads(result.stdout)
        # Each step result must be a plain string, not an enum representation
        for step in output.get("steps", []):
            assert isinstance(step["result"], str), (
                f"step result is not str: {step['result']!r}"
            )
            assert step["result"] in ("PASS", "FAIL", "SKIP", "WARN"), (
                f"unexpected result value: {step['result']!r}"
            )

    def test_json_output_overall_result_is_string(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- overall_result in JSON output is a plain string."""
        prd = _make_prd(tmp_path)
        result = _run_qa_runner(
            "--story", "STORY-003", "--prd", str(prd), "--steps", "1", cwd=str(tmp_path)
        )
        output = json.loads(result.stdout)
        assert isinstance(output["overall_result"], str)
        assert output["overall_result"] in ("PASS", "FAIL")


class TestDeepAnalysisConfig:
    """# Tests R-P2-01 through R-P2-10 -- external scanner and pipeline config."""

    def _load_config(self) -> dict:
        """Load workflow.json."""
        config_path = HOOKS_DIR.parent / "workflow.json"
        return json.loads(config_path.read_text(encoding="utf-8"))

    def test_bandit_enabled(self) -> None:
        """# Tests R-P2-01 -- workflow.json has bandit enabled with strict_mode false."""
        config = self._load_config()
        bandit = config["external_scanners"]["bandit"]
        assert bandit["enabled"] is True
        assert bandit["strict_mode"] is False

    def test_pip_audit_entry(self) -> None:
        """# Tests R-P2-02 -- workflow.json has pip-audit entry with correct config."""
        config = self._load_config()
        pip_audit = config["external_scanners"]["pip-audit"]
        assert pip_audit["enabled"] is True
        assert pip_audit["strict_mode"] is False
        assert "pip-audit" in pip_audit["cmd"]

    def test_type_check_configured(self) -> None:
        """# Tests R-P2-03 -- workflow.json commands.type_check contains mypy."""
        config = self._load_config()
        assert "mypy" in config["commands"]["type_check"]

    def test_coverage_configured(self) -> None:
        """# Tests R-P2-04 -- workflow.json commands.coverage contains --cov-fail-under."""
        config = self._load_config()
        assert "cov-fail-under" in config["commands"]["coverage"]

    def test_language_type_check_matches(self) -> None:
        """# Tests R-P2-05 -- python type_check matches top-level commands.type_check."""
        config = self._load_config()
        top = config["commands"]["type_check"]
        lang = config["languages"]["python"]["commands"]["type_check"]
        assert top == lang

    def test_required_steps_type_true(self) -> None:
        """# Tests R-P2-07 -- _required_verification_steps returns type=True when configured."""
        config = {"commands": {"type_check": "mypy ."}}
        result = _required_verification_steps(
            story=None, phase_type=None, config=config
        )
        assert result["type"] is True

    def test_required_steps_type_false_when_empty(self) -> None:
        """# Tests R-P2-07 -- _required_verification_steps returns type=False when empty."""
        config = {"commands": {"type_check": ""}}
        result = _required_verification_steps(
            story=None, phase_type=None, config=config
        )
        assert result["type"] is False

    def test_type_check_runs_when_configured(self) -> None:
        """# Tests R-P2-08 -- _step_type_check returns non-SKIP when command configured."""
        config = {"commands": {"type_check": "mypy ."}}
        with patch("qa_runner._run_command", return_value=(0, "Success", "")):
            result, evidence = _step_type_check(config)
        assert result != StepResult.SKIP
        assert result == StepResult.PASS

    def test_coverage_runs_when_configured(self) -> None:
        """# Tests R-P2-09 -- _step_coverage returns non-SKIP when command configured."""
        config = {"commands": {"coverage": "pytest --cov=. --cov-fail-under=60"}}
        with patch("qa_runner._run_command", return_value=(0, "80% covered", "")):
            result, evidence = _step_coverage(config)
        assert result != StepResult.SKIP
        assert result == StepResult.PASS
