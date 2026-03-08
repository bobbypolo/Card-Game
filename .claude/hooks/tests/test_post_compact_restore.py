"""Tests for post_compact_restore.py SessionStart hook."""

import json
import os
import subprocess
import sys
import unittest.mock as mock
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).resolve().parent.parent / "post_compact_restore.py"


def run_hook(cwd: str = None, stdin_data: str = "") -> subprocess.CompletedProcess:
    """Run the post_compact_restore.py hook as a subprocess."""
    env = {}
    for key in ("PATH", "SYSTEMROOT", "PYTHONPATH", "HOME", "USERPROFILE"):
        if key in os.environ:
            env[key] = os.environ[key]
    # Redirect _lib.py paths to tmp_path so hooks write to the temp dir
    if cwd:
        env["CLAUDE_PROJECT_ROOT"] = cwd
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=cwd,
    )


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _lib import (  # noqa: E402
    clear_marker,
    clear_stop_block_count,
    get_stop_block_count,
    increment_stop_block_count,
    read_marker,
    write_marker,
)


# ── TestRulesReminder ─────────────────────────────────────────────────────


class TestRulesReminder:
    """-- rules reminder always appears in stdout."""

    def test_stdout_contains_workflow_rules_reminder(self, tmp_path: Path) -> None:
        """-- output includes WORKFLOW RULES REMINDER header."""
        result = run_hook(cwd=str(tmp_path))
        assert "WORKFLOW RULES REMINDER" in result.stdout

    def test_stdout_contains_run_tests(self, tmp_path: Path) -> None:
        """-- output includes run tests bullet."""
        result = run_hook(cwd=str(tmp_path))
        assert "Run tests" in result.stdout

    def test_stdout_contains_verify(self, tmp_path: Path) -> None:
        """-- output includes /verify reference."""
        result = run_hook(cwd=str(tmp_path))
        assert "/verify" in result.stdout

    def test_stdout_contains_stop_hook(self, tmp_path: Path) -> None:
        """-- output includes Stop hook mention."""
        result = run_hook(cwd=str(tmp_path))
        assert "Stop hook" in result.stdout

    def test_stdout_contains_plan_md(self, tmp_path: Path) -> None:
        """-- output includes PLAN.md reference."""
        result = run_hook(cwd=str(tmp_path))
        assert "PLAN.md" in result.stdout

    def test_reminder_has_four_bullet_points(self, tmp_path: Path) -> None:
        """-- reminder contains exactly 4 bullet points."""
        result = run_hook(cwd=str(tmp_path))
        bullet_lines = [
            line for line in result.stdout.splitlines() if line.strip().startswith("- ")
        ]
        assert len(bullet_lines) == 4


# ── TestMarkerWarning ─────────────────────────────────────────────────────


class TestMarkerWarning:
    """-- WARNING behavior based on marker presence."""

    def test_warning_when_marker_exists(self, tmp_path: Path) -> None:
        """-- prints WARNING when needs_verify is set in state."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        state_file = claude_dir / ".workflow-state.json"
        state_file.write_text(
            json.dumps(
                {
                    "needs_verify": "post_format: edited file.py",
                    "stop_block_count": 0,
                    "prod_violations": None,
                }
            ),
            encoding="utf-8",
        )

        result = run_hook(cwd=str(tmp_path))
        assert "WARNING" in result.stdout

    def test_warning_contains_marker_content(self, tmp_path: Path) -> None:
        """-- WARNING line includes marker content text."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        state_file = claude_dir / ".workflow-state.json"
        state_file.write_text(
            json.dumps(
                {
                    "needs_verify": "post_format: edited file.py",
                    "stop_block_count": 0,
                    "prod_violations": None,
                }
            ),
            encoding="utf-8",
        )

        result = run_hook(cwd=str(tmp_path))
        assert "post_format: edited file.py" in result.stdout

    def test_no_warning_when_marker_absent(self, tmp_path: Path) -> None:
        """-- no WARNING when .needs_verify does not exist."""
        result = run_hook(cwd=str(tmp_path))
        assert "WARNING" not in result.stdout

    def test_no_warning_when_marker_empty(self, tmp_path: Path) -> None:
        """-- no WARNING when needs_verify is null in state."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        state_file = claude_dir / ".workflow-state.json"
        state_file.write_text(
            json.dumps(
                {
                    "needs_verify": None,
                    "stop_block_count": 0,
                    "prod_violations": None,
                }
            ),
            encoding="utf-8",
        )

        result = run_hook(cwd=str(tmp_path))
        assert "WARNING" not in result.stdout


# ── TestExitCode ──────────────────────────────────────────────────────────


class TestExitCode:
    """-- hook always exits 0."""

    def test_exit_0_without_marker(self, tmp_path: Path) -> None:
        """-- exits 0 when no marker exists."""
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0

    def test_exit_0_with_marker(self, tmp_path: Path) -> None:
        """-- exits 0 even when marker exists in state."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        state_file = claude_dir / ".workflow-state.json"
        state_file.write_text(
            json.dumps(
                {
                    "needs_verify": "some change tracked",
                    "stop_block_count": 0,
                    "prod_violations": None,
                }
            ),
            encoding="utf-8",
        )

        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0


# ── TestMarkerIO ──────────────────────────────────────────────────────────


class TestMarkerIO:
    """-- _lib marker I/O round-trip tests (via .workflow-state.json)."""

    def test_write_then_read_returns_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """-- write_marker then read_marker returns content."""
        import _lib

        state_path = tmp_path / ".workflow-state.json"
        monkeypatch.setattr(_lib, "WORKFLOW_STATE_PATH", state_path)
        write_marker("edited src/main.py")
        result = read_marker()
        assert result == "edited src/main.py"

    def test_clear_then_read_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """-- clear_marker then read_marker returns None."""
        import _lib

        state_path = tmp_path / ".workflow-state.json"
        monkeypatch.setattr(_lib, "WORKFLOW_STATE_PATH", state_path)
        write_marker("something")
        assert state_path.exists()
        clear_marker()
        result = read_marker()
        assert result is None

    def test_read_nonexistent_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """-- read_marker returns None when state file does not exist."""
        import _lib

        monkeypatch.setattr(_lib, "WORKFLOW_STATE_PATH", tmp_path / "nonexistent.json")
        result = read_marker()
        assert result is None

    def test_stop_block_counter_lifecycle(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """-- get/increment/clear stop block counter round-trip."""
        import _lib

        state_path = tmp_path / ".workflow-state.json"
        monkeypatch.setattr(_lib, "WORKFLOW_STATE_PATH", state_path)

        # Initially 0
        assert get_stop_block_count() == 0

        # Increment to 1
        new_count = increment_stop_block_count()
        assert new_count == 1
        assert get_stop_block_count() == 1

        # Increment to 2
        new_count = increment_stop_block_count()
        assert new_count == 2
        assert get_stop_block_count() == 2

        # Clear resets
        clear_stop_block_count()
        assert get_stop_block_count() == 0

    def test_clear_marker_also_clears_stop_counter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """-- clear_marker resets both needs_verify and stop_block_count."""
        import _lib

        state_path = tmp_path / ".workflow-state.json"
        monkeypatch.setattr(_lib, "WORKFLOW_STATE_PATH", state_path)

        write_marker("test")
        increment_stop_block_count()

        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["needs_verify"] == "test"
        assert state["stop_block_count"] >= 1

        clear_marker()
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state["needs_verify"] is None
        assert state["stop_block_count"] == 0


# ── TestNoProdViolationsOutput (R-P1-07) ────────────────────────────────


class TestNoProdViolationsOutput:
    """-- no prod_violations WARNING in post_compact_restore output."""

    def test_no_prod_violations_reference_in_source(self) -> None:
        """-- source contains no reference to prod_violations."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "prod_violations" not in source

    def test_no_prod_warning_output(self, tmp_path: Path) -> None:
        """-- no prod violations warning in output."""
        result = run_hook(cwd=str(tmp_path))
        assert "production violations" not in result.stdout.lower()
        assert result.returncode == 0


# ── TestRalphContextRestore (Phase 4) ───────────────────────────────────


class TestRalphContextRestore:
    """Tests for Ralph context restore -- Phase 4."""

    def _write_state(self, tmp_path, ralph_overrides=None):
        """Helper: write workflow state with ralph section."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        ralph_defaults = {
            "consecutive_skips": 0,
            "stories_passed": 2,
            "stories_skipped": 0,
            "feature_branch": "ralph/test-sprint",
            "current_story_id": "STORY-003",
            "current_attempt": 1,
            "max_attempts": 4,
            "prior_failure_summary": "",
        }
        if ralph_overrides:
            ralph_defaults.update(ralph_overrides)
        state = {
            "needs_verify": None,
            "stop_block_count": 0,
            "ralph": ralph_defaults,
        }
        state_file = claude_dir / ".workflow-state.json"
        state_file.write_text(json.dumps(state), encoding="utf-8")

    def _write_prd(self, tmp_path, stories=None):
        """Helper: write prd.json with stories."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        if stories is None:
            stories = [
                {
                    "id": "STORY-001",
                    "description": "First story",
                    "passed": True,
                    "acceptanceCriteria": [],
                },
                {
                    "id": "STORY-002",
                    "description": "Second story",
                    "passed": True,
                    "acceptanceCriteria": [],
                },
                {
                    "id": "STORY-003",
                    "description": "Third story -- the current one",
                    "passed": False,
                    "acceptanceCriteria": [
                        {
                            "id": "R-P3-01",
                            "criterion": "Function exists and works",
                            "testType": "unit",
                        },
                        {
                            "id": "R-P3-02",
                            "criterion": "Tests pass",
                            "testType": "unit",
                        },
                    ],
                },
                {
                    "id": "STORY-004",
                    "description": "Fourth story",
                    "passed": False,
                    "acceptanceCriteria": [],
                },
            ]
        prd = {"version": "2.0", "stories": stories}
        prd_file = claude_dir / "prd.json"
        prd_file.write_text(json.dumps(prd), encoding="utf-8")

    def test_compact_restore_ralph_context(self, tmp_path):
        """# Tests R-P4-01 -- prints RALPH CONTEXT RESTORE when ralph_active with story_id."""
        self._write_state(tmp_path)
        self._write_prd(tmp_path)
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" in result.stdout
        assert "STORY-003" in result.stdout
        assert "Remaining stories: 2" in result.stdout

    def test_compact_restore_no_ralph(self, tmp_path):
        """# Tests R-P4-01 -- no RALPH CONTEXT RESTORE when ralph is not active."""
        # Default state has empty current_story_id
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" not in result.stdout

    def test_compact_restore_missing_prd(self, tmp_path):
        """# Tests R-P4-02 -- graceful fallback when prd.json is missing."""
        self._write_state(tmp_path)
        # Don't write prd.json
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" in result.stdout
        assert "prd.json unavailable" in result.stdout

    def test_compact_restore_corrupt_prd(self, tmp_path):
        """# Tests R-P4-02 -- graceful fallback when prd.json is corrupt."""
        self._write_state(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "prd.json").write_text("{{not valid json!!", encoding="utf-8")
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" in result.stdout
        assert "prd.json unavailable" in result.stdout

    def test_compact_restore_prints_story_details(self, tmp_path):
        """# Tests R-P4-03 -- prints current story description and acceptance criteria."""
        self._write_state(tmp_path)
        self._write_prd(tmp_path)
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "Third story" in result.stdout
        assert "R-P3-01" in result.stdout
        assert "Function exists and works" in result.stdout

    def test_compact_restore_null_story_id_skips(self, tmp_path):
        """# Tests R-P4-04 -- skips context restore when current_story_id is empty."""
        self._write_state(tmp_path, ralph_overrides={"current_story_id": ""})
        self._write_prd(tmp_path)
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" not in result.stdout

    def test_compact_restore_step_aware_resume(self, tmp_path):
        """R-P4B-04: Prints step-aware resume when current_step is set."""
        self._write_state(tmp_path, ralph_overrides={"current_step": "STEP_5_DISPATCH"})
        self._write_prd(tmp_path)
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "Last step: STEP_5_DISPATCH" in result.stdout
        assert "worker result is pending" in result.stdout

    def test_compact_restore_step7_resume(self, tmp_path):
        """R-P4B-04: STEP_7 resume points to STEP 2."""
        self._write_state(tmp_path, ralph_overrides={"current_step": "STEP_7_CLEANUP"})
        self._write_prd(tmp_path)
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "Last step: STEP_7_CLEANUP" in result.stdout
        assert "STEP 2" in result.stdout


# ── TestProtocolCardRestore ──────────────────────────────────────────────


class TestProtocolCardRestore:
    """Tests for Protocol Card inline printing in SessionStart hook."""

    def _write_state(self, tmp_path, ralph_overrides=None):
        """Helper: write workflow state with ralph section."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        ralph_defaults = {
            "consecutive_skips": 0,
            "stories_passed": 1,
            "stories_skipped": 0,
            "feature_branch": "ralph/test",
            "current_story_id": "STORY-002",
            "current_attempt": 1,
            "max_attempts": 4,
            "prior_failure_summary": "",
        }
        if ralph_overrides:
            ralph_defaults.update(ralph_overrides)
        state = {
            "needs_verify": None,
            "stop_block_count": 0,
            "ralph": ralph_defaults,
        }
        (claude_dir / ".workflow-state.json").write_text(
            json.dumps(state), encoding="utf-8"
        )

    def _write_prd(self, tmp_path):
        """Helper: write minimal prd.json."""

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        prd = {
            "version": "2.0",
            "stories": [
                {
                    "id": "STORY-001",
                    "description": "Done",
                    "passed": True,
                    "acceptanceCriteria": [],
                },
                {
                    "id": "STORY-002",
                    "description": "Current",
                    "passed": False,
                    "acceptanceCriteria": [
                        {"id": "R-P1-01", "criterion": "test", "testType": "unit"}
                    ],
                },
            ],
        }
        (claude_dir / "prd.json").write_text(json.dumps(prd), encoding="utf-8")

    def _write_protocol_card(self, tmp_path, content="# Protocol Card\nStep loop"):
        """Helper: write PROTOCOL_CARD.md."""
        card_dir = tmp_path / ".claude" / "skills" / "ralph"
        card_dir.mkdir(parents=True, exist_ok=True)
        (card_dir / "PROTOCOL_CARD.md").write_text(content, encoding="utf-8")

    def test_protocol_card_printed_when_present(self, tmp_path):
        """# Tests R-PCM-01 -- card content appears in output when file exists."""
        self._write_state(tmp_path)
        self._write_prd(tmp_path)
        self._write_protocol_card(tmp_path, "# Protocol Card\nSTEP 2 loop info")
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "PROTOCOL CARD (inline)" in result.stdout
        assert "STEP 2 loop info" in result.stdout

    def test_protocol_card_graceful_when_missing(self, tmp_path):
        """# Tests R-PCM-02 -- no error when file absent, existing restore works."""
        self._write_state(tmp_path)
        self._write_prd(tmp_path)
        # No protocol card file written
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" in result.stdout
        assert "PROTOCOL CARD" not in result.stdout

    def test_protocol_card_not_printed_when_ralph_inactive(self, tmp_path):
        """# Tests R-PCM-03 -- card only printed when Ralph is active."""
        # No ralph state at all — ralph_active will be False
        self._write_protocol_card(tmp_path)
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "PROTOCOL CARD" not in result.stdout

    def test_protocol_card_in_fallback_mode(self, tmp_path):
        """# Tests R-PCM-04 -- card printed even when prd.json is missing."""
        self._write_state(tmp_path)
        # No prd.json — triggers fallback path
        self._write_protocol_card(tmp_path, "# Fallback card\nCircuit breaker rule")
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "prd.json unavailable" in result.stdout
        assert "PROTOCOL CARD (inline)" in result.stdout
        assert "Circuit breaker rule" in result.stdout

    def test_protocol_card_empty_file_skipped(self, tmp_path):
        """# Tests R-PCM-05 -- empty file treated as absent."""
        self._write_state(tmp_path)
        self._write_prd(tmp_path)
        self._write_protocol_card(tmp_path, "")
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "PROTOCOL CARD" not in result.stdout

    def test_protocol_card_corrupt_file_no_crash(self, tmp_path):
        """# Tests R-PCM-06 -- binary/corrupt file doesn't crash hook."""
        self._write_state(tmp_path)
        self._write_prd(tmp_path)
        card_dir = tmp_path / ".claude" / "skills" / "ralph"
        card_dir.mkdir(parents=True, exist_ok=True)
        # Write binary content
        (card_dir / "PROTOCOL_CARD.md").write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        result = run_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        assert "RALPH CONTEXT RESTORE" in result.stdout


# ── TestGenerateFileManifest ─────────────────────────────────────────────


def _import_hook_module():
    """Import post_compact_restore with sys.exit patched to avoid SystemExit."""
    import importlib
    import unittest.mock as _mock

    hooks_dir = str(Path(__file__).resolve().parent.parent)
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)

    # If already loaded, reload to get fresh module
    mod_name = "post_compact_restore"
    with _mock.patch("sys.exit"):
        if mod_name in sys.modules:
            import importlib as _il

            mod = _il.reload(sys.modules[mod_name])
        else:
            mod = importlib.import_module(mod_name)
    return mod


class TestGenerateFileManifest:
    """Tests for _generate_file_manifest() -- R-P2-01, R-P2-02, R-P2-03."""

    @pytest.fixture
    def hook_mod(self):
        """Load post_compact_restore module with sys.exit neutralized."""
        return _import_hook_module()

    def test_manifest_writes_json_with_required_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-01 -- writes .file-manifest.json with all required keys."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        git_output = "src/main.py\nsrc/utils.py\ntests/test_main.py\nREADME.md\n"
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = git_output

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            hook_mod._generate_file_manifest()

        manifest_path = tmp_path / ".claude" / ".file-manifest.json"
        assert manifest_path.exists(), "Manifest file should be written"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert "total_tracked_files" in data
        assert "generated_at" in data
        assert "top_directories" in data
        assert "language_distribution" in data

    def test_manifest_total_tracked_files_is_int(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-01 -- total_tracked_files is an integer."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        git_output = "src/main.py\nsrc/utils.py\ntests/test_main.py\n"
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = git_output

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            hook_mod._generate_file_manifest()

        data = json.loads(
            (tmp_path / ".claude" / ".file-manifest.json").read_text(encoding="utf-8")
        )
        total = data["total_tracked_files"]
        assert isinstance(total, int)
        assert total == 3

    def test_manifest_top_directories_at_most_30(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-01 -- top_directories contains at most 30 entries."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        # Generate 40 unique directories
        lines = [f"dir{i}/file.py" for i in range(40)]
        git_output = "\n".join(lines) + "\n"
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = git_output

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            hook_mod._generate_file_manifest()

        data = json.loads(
            (tmp_path / ".claude" / ".file-manifest.json").read_text(encoding="utf-8")
        )
        dirs = data["top_directories"]
        assert isinstance(dirs, dict)
        dir_count = len(dirs)
        assert dir_count <= 30

    def test_manifest_language_distribution_at_most_15(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-01 -- language_distribution contains at most 15 entries."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        # Generate 20 unique extensions
        extensions = [
            ".py",
            ".js",
            ".ts",
            ".go",
            ".rs",
            ".rb",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".php",
            ".swift",
            ".kt",
            ".scala",
            ".r",
            ".m",
            ".lua",
            ".pl",
            ".sh",
        ]
        lines = [f"src/file{ext}" for ext in extensions]
        git_output = "\n".join(lines) + "\n"
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = git_output

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            hook_mod._generate_file_manifest()

        data = json.loads(
            (tmp_path / ".claude" / ".file-manifest.json").read_text(encoding="utf-8")
        )
        langs = data["language_distribution"]
        assert isinstance(langs, dict)
        lang_count = len(langs)
        assert lang_count <= 15

    def test_manifest_generated_at_is_iso_timestamp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-01 -- generated_at is an ISO timestamp string."""
        from datetime import datetime

        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        git_output = "src/main.py\n"
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = git_output

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            hook_mod._generate_file_manifest()

        data = json.loads(
            (tmp_path / ".claude" / ".file-manifest.json").read_text(encoding="utf-8")
        )
        ts = data["generated_at"]
        assert isinstance(ts, str)
        assert ts != ""
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(ts)
        assert parsed.year >= 2020

    def test_manifest_silent_on_git_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-02 -- returns silently when git ls-files fails."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        fake_result = mock.MagicMock()
        fake_result.returncode = 128
        fake_result.stdout = ""

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            # Should not raise
            hook_mod._generate_file_manifest()

        manifest_path = tmp_path / ".claude" / ".file-manifest.json"
        assert not manifest_path.exists(), (
            "Manifest should not be written on git failure"
        )

    def test_manifest_silent_on_empty_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-02 -- returns silently when git ls-files returns empty output."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = ""

        with mock.patch.object(hook_mod.subprocess, "run", return_value=fake_result):
            # Should not raise
            hook_mod._generate_file_manifest()

        manifest_path = tmp_path / ".claude" / ".file-manifest.json"
        assert not manifest_path.exists(), (
            "Manifest should not be written for empty output"
        )

    def test_manifest_silent_on_subprocess_exception(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_mod
    ) -> None:
        """# Tests R-P2-02 -- returns silently when subprocess raises an exception."""
        monkeypatch.setattr(hook_mod, "PROJECT_ROOT", tmp_path)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)

        with mock.patch.object(
            hook_mod.subprocess, "run", side_effect=OSError("git not found")
        ):
            # Should not raise
            hook_mod._generate_file_manifest()

        manifest_path = tmp_path / ".claude" / ".file-manifest.json"
        assert not manifest_path.exists(), "Manifest should not be written on exception"

    def test_manifest_called_by_hook_via_subprocess(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- _generate_file_manifest() is invoked when hook runs."""
        # Verify manifest generation is called during SessionStart by checking
        # that the hook source references _generate_file_manifest at module level
        source = HOOK_PATH.read_text(encoding="utf-8")
        # Must be called (not just defined) outside of any class/function
        lines = source.splitlines()
        call_lines = [
            line
            for line in lines
            if "_generate_file_manifest()" in line
            and not line.strip().startswith("def ")
        ]
        assert len(call_lines) >= 1, (
            "_generate_file_manifest() must be called in main flow"
        )
