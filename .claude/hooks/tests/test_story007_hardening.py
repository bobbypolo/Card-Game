"""Tests for STORY-007: State Write and Stop-Gate Hardening.

# Tests R-P7-01, R-P7-02, R-P7-03, R-P7-04
"""

import json
import os
import re
import subprocess
import sys
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HOOKS_DIR = Path(__file__).resolve().parent.parent
HOOK_STOP_PATH = HOOKS_DIR / "stop_verify_gate.py"
HOOK_FORMAT_PATH = HOOKS_DIR / "post_format.py"
LIB_PATH = HOOKS_DIR / "_lib.py"


def _setup_project(tmp_path: Path) -> Path:
    """Create minimal project root with .claude dir."""
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    return tmp_path


def _get_lib(tmp_path: Path):
    """Import _lib rooted at tmp_path via CLAUDE_PROJECT_ROOT."""
    old_root = os.environ.get("CLAUDE_PROJECT_ROOT")
    os.environ["CLAUDE_PROJECT_ROOT"] = str(tmp_path)
    try:
        if "_lib" in sys.modules:
            del sys.modules["_lib"]
        import _lib

        return _lib
    finally:
        if old_root is not None:
            os.environ["CLAUDE_PROJECT_ROOT"] = old_root
        elif "CLAUDE_PROJECT_ROOT" in os.environ:
            del os.environ["CLAUDE_PROJECT_ROOT"]


def _state_path(tmp_path: Path) -> Path:
    return tmp_path / ".claude" / ".workflow-state.json"


def _write_state(tmp_path: Path, state: dict) -> None:
    sp = _state_path(tmp_path)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _read_state(tmp_path: Path) -> dict:
    sp = _state_path(tmp_path)
    if sp.exists():
        try:
            return json.loads(sp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            pass
    return {"needs_verify": None, "stop_block_count": 0, "ralph": {}}


def run_stop_hook(
    stdin_data: str = "{}",
    cwd: str | None = None,
    env_overrides: dict | None = None,
) -> subprocess.CompletedProcess:

    env = {}
    for key in ("PATH", "SYSTEMROOT", "PYTHONPATH", "HOME", "USERPROFILE"):
        if key in os.environ:
            env[key] = os.environ[key]
    if cwd:
        env["CLAUDE_PROJECT_ROOT"] = cwd
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(HOOK_STOP_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
        cwd=cwd,
    )


# ─────────────────────────────────────────────────────────────────────────────
# R-P7-01: write_workflow_state() returns True on success, False on failure
# ─────────────────────────────────────────────────────────────────────────────


class TestWriteWorkflowStateReturnValue:
    """# Tests R-P7-01 -- write_workflow_state() returns True/False."""

    def test_returns_true_on_successful_write(self, tmp_path: Path) -> None:
        """R-P7-01: returns True when write succeeds."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)
        state = lib.read_workflow_state()
        result = lib.write_workflow_state(state)
        assert result is True, f"Expected True, got {result!r}"

    def test_returns_true_creates_file(self, tmp_path: Path) -> None:
        """R-P7-01: returns True AND file is actually created."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)
        state = lib.read_workflow_state()
        result = lib.write_workflow_state(state)
        assert result is True
        assert _state_path(tmp_path).exists()

    def test_returns_false_on_serialization_error(self, tmp_path: Path) -> None:
        """R-P7-01: returns False when state is not JSON-serializable."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)
        result = lib.write_workflow_state({"key": object()})
        assert result is False, f"Expected False on TypeError, got {result!r}"

    def test_returns_false_on_permission_error_exhausted(
        self, tmp_path, monkeypatch
    ) -> None:
        """R-P7-01: returns False when all PermissionError retries are exhausted."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)

        def always_fail(src, dst):
            raise PermissionError("Locked forever")

        monkeypatch.setattr(os, "replace", always_fail)
        result = lib.write_workflow_state(
            {"needs_verify": None, "stop_block_count": 0, "ralph": {}}
        )
        assert result is False, f"Expected False when retries exhausted, got {result!r}"

    def test_return_value_is_bool_not_none(self, tmp_path: Path) -> None:
        """R-P7-01: return value is bool True (not None)."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)
        result = lib.write_workflow_state(lib.read_workflow_state())
        assert result is not None, (
            "write_workflow_state returned None (no explicit return)"
        )
        assert result is True

    def test_sequential_writes_all_return_true(self, tmp_path: Path) -> None:
        """R-P7-01: multiple sequential writes all return True."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)
        for i in range(3):
            state = lib.read_workflow_state()
            state["stop_block_count"] = i
            result = lib.write_workflow_state(state)
            assert result is True, f"Write {i} returned {result!r}"


# ─────────────────────────────────────────────────────────────────────────────
# R-P7-02: stop_verify_gate.py uses ADE_ALLOW_UNVERIFIED_STOP env var
# ─────────────────────────────────────────────────────────────────────────────


def _create_marker(tmp_path: Path, content: str = "test.py modified") -> None:
    state = _read_state(tmp_path)
    state["needs_verify"] = content
    _write_state(tmp_path, state)


def _create_counter(tmp_path: Path, count: int) -> None:
    state = _read_state(tmp_path)
    state["stop_block_count"] = count
    _write_state(tmp_path, state)


class TestEnvVarOverride:
    """# Tests R-P7-02 -- ADE_ALLOW_UNVERIFIED_STOP=1 allows stop, no counter bypass."""

    def test_env_var_allows_stop_with_marker(self, tmp_path: Path) -> None:
        """R-P7-02: ADE_ALLOW_UNVERIFIED_STOP=1 allows stop even with needs_verify set."""
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        _create_marker(tmp_path)
        result = run_stop_hook(
            cwd=str(tmp_path),
            env_overrides={"ADE_ALLOW_UNVERIFIED_STOP": "1"},
        )
        assert result.returncode == 0
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert data.get("decision") != "block", (
                "ADE_ALLOW_UNVERIFIED_STOP=1 should prevent block"
            )

    def test_env_var_not_set_still_blocks(self, tmp_path: Path) -> None:
        """R-P7-02: Without env var, marker triggers block (normal behavior)."""
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        _create_marker(tmp_path)
        result = run_stop_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["decision"] == "block"

    def test_env_var_zero_still_blocks(self, tmp_path: Path) -> None:
        """R-P7-02: ADE_ALLOW_UNVERIFIED_STOP=0 does NOT override (only '1' works)."""
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        _create_marker(tmp_path)
        result = run_stop_hook(
            cwd=str(tmp_path),
            env_overrides={"ADE_ALLOW_UNVERIFIED_STOP": "0"},
        )
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["decision"] == "block", (
            "ADE_ALLOW_UNVERIFIED_STOP=0 should NOT allow stop"
        )

    def test_no_counter_bypass_at_count_two(self, tmp_path: Path) -> None:
        """R-P7-02: counter=2 does NOT automatically allow stop (no hidden counter bypass)."""
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        _create_marker(tmp_path)
        _create_counter(tmp_path, 2)
        result = run_stop_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["decision"] == "block", (
            "Counter-based escape hatch must be removed; counter=2 should still block"
        )

    def test_no_counter_bypass_at_count_ten(self, tmp_path: Path) -> None:
        """R-P7-02: Very high counter value does NOT automatically allow stop."""
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        _create_marker(tmp_path)
        _create_counter(tmp_path, 10)
        result = run_stop_hook(cwd=str(tmp_path))
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert data["decision"] == "block", (
            "Any counter value without env var must still block"
        )

    def test_stop_verify_gate_no_counter_check_in_source(self) -> None:
        """R-P7-02: stop_verify_gate.py source must not contain counter >= N bypass."""
        source = HOOK_STOP_PATH.read_text(encoding="utf-8")
        counter_bypass = re.search(r"count\s*>=\s*\d", source)
        assert counter_bypass is None, (
            f"Old counter-based escape hatch still present: {counter_bypass.group()!r}"
        )

    def test_env_var_check_in_source(self) -> None:
        """R-P7-02: stop_verify_gate.py uses ADE_ALLOW_UNVERIFIED_STOP env var."""
        source = HOOK_STOP_PATH.read_text(encoding="utf-8")
        assert "ADE_ALLOW_UNVERIFIED_STOP" in source, (
            "ADE_ALLOW_UNVERIFIED_STOP env var check must be present in stop_verify_gate.py"
        )

    def test_env_var_allows_stop_exits_0(self, tmp_path: Path) -> None:
        """R-P7-02: env var override exits 0."""
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        _create_marker(tmp_path)
        result = run_stop_hook(
            cwd=str(tmp_path),
            env_overrides={"ADE_ALLOW_UNVERIFIED_STOP": "1"},
        )
        assert result.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# R-P7-03: post_format.py formatter failure writes warning to stderr
# ─────────────────────────────────────────────────────────────────────────────


class TestPostFormatFormatterFailure:
    """# Tests R-P7-03 -- formatter failure writes warning to stderr."""

    def test_post_format_source_has_stderr_on_format_fail(self) -> None:
        """R-P7-03: post_format.py source contains sys.stderr write."""
        source = HOOK_FORMAT_PATH.read_text(encoding="utf-8")
        assert "sys.stderr" in source, (
            "post_format.py must write to sys.stderr on formatter failure (R-P7-03)"
        )

    def test_formatter_failure_branch_has_stderr_write(self) -> None:
        """R-P7-03: The code!=0 branch in post_format writes to stderr."""
        source = HOOK_FORMAT_PATH.read_text(encoding="utf-8")
        assert "code != 0" in source, "post_format.py must check code != 0"
        assert "sys.stderr" in source, "post_format.py must write to sys.stderr"

    def test_needs_verify_not_cleared_by_post_format(self) -> None:
        """R-P7-03: post_format.py does not import or call clear_marker."""
        source = HOOK_FORMAT_PATH.read_text(encoding="utf-8")
        assert "clear_marker" not in source, (
            "post_format.py must not call clear_marker (would clear needs_verify)"
        )

    def test_formatter_writes_to_stderr_on_nonzero_rc_ruff(
        self, tmp_path: Path, capsys
    ) -> None:
        """R-P7-03: post_format main() writes WARNING to stderr when run_formatter returns non-zero."""
        import io

        _setup_project(tmp_path)

        # Create the .py file so hook won't skip due to extension
        py_file = tmp_path / "module.py"
        py_file.write_text("x = 1\n", encoding="utf-8")

        old_root = os.environ.get("CLAUDE_PROJECT_ROOT")
        os.environ["CLAUDE_PROJECT_ROOT"] = str(tmp_path)
        try:
            if "_lib" in sys.modules:
                del sys.modules["_lib"]
            if "post_format" in sys.modules:
                del sys.modules["post_format"]
            import _lib

            # Patch run_formatter to simulate ruff failure
            def failing_formatter(cmd, timeout=30):
                return 1, "ruff: internal error occurred"

            _lib.run_formatter = failing_formatter

            # Patch write_marker to avoid side effects
            _lib.write_marker = lambda content, source_path=None: None

            # Load post_format with our patched _lib already in sys.modules
            sys.modules["_lib"] = _lib

            # Prepare stdin
            stdin_data = json.dumps({"tool_input": {"file_path": str(py_file)}})
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(stdin_data)

            import runpy

            try:
                runpy.run_path(str(HOOK_FORMAT_PATH), run_name="__main__")
            except SystemExit:
                pass
            finally:
                sys.stdin = old_stdin
        finally:
            if old_root is not None:
                os.environ["CLAUDE_PROJECT_ROOT"] = old_root
            elif "CLAUDE_PROJECT_ROOT" in os.environ:
                del os.environ["CLAUDE_PROJECT_ROOT"]
            if "_lib" in sys.modules:
                del sys.modules["_lib"]
            if "post_format" in sys.modules:
                del sys.modules["post_format"]

        captured = capsys.readouterr()
        assert captured.err.strip() != "", (
            f"Expected WARNING on stderr when formatter fails, got empty stderr. "
            f"stdout={captured.out!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# R-P7-04: audit_log() writes warning to stderr on write failure
# ─────────────────────────────────────────────────────────────────────────────


class TestAuditLogStderrOnFailure:
    """# Tests R-P7-04 -- audit_log() writes to stderr when file write fails."""

    def test_audit_log_writes_stderr_on_oserror(self, tmp_path: Path, capsys) -> None:
        """R-P7-04: audit_log writes WARNING to stderr when AUDIT_LOG_PATH write fails."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)

        # Path.open() bypasses builtins.open — patch pathlib.Path.open instead
        original_path_open = Path.open

        def failing_path_open(self_path, *args, **kwargs):
            if "hook_audit.jsonl" in str(self_path):
                raise OSError("Permission denied: hook_audit.jsonl")
            return original_path_open(self_path, *args, **kwargs)

        with unittest.mock.patch.object(Path, "open", failing_path_open):
            lib.audit_log("test_hook", "test_decision", "test detail")

        captured = capsys.readouterr()
        err_lower = captured.err.lower()
        assert (
            "warning" in err_lower or "audit" in err_lower or "failed" in err_lower
        ), (
            f"Expected WARNING on stderr when audit write fails, got stderr={captured.err!r}"
        )

    def test_audit_log_stderr_message_contains_error_info(
        self, tmp_path: Path, capsys
    ) -> None:
        """R-P7-04: stderr message contains useful error information."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)

        # Path.open() bypasses builtins.open — patch pathlib.Path.open instead
        original_path_open = Path.open

        def failing_path_open(self_path, *args, **kwargs):
            if "hook_audit.jsonl" in str(self_path):
                raise OSError("disk full")
            return original_path_open(self_path, *args, **kwargs)

        with unittest.mock.patch.object(Path, "open", failing_path_open):
            lib.audit_log("hook_name", "decision", "detail")

        captured = capsys.readouterr()
        stderr_lower = captured.err.lower()
        assert (
            "warning" in stderr_lower
            or "audit" in stderr_lower
            or "failed" in stderr_lower
        ), f"stderr should contain warning/audit/failed, got: {captured.err!r}"

    def test_audit_log_does_not_raise_on_oserror(self, tmp_path: Path) -> None:
        """R-P7-04: audit_log must never raise even when write fails."""
        _setup_project(tmp_path)
        lib = _get_lib(tmp_path)

        # Path.open() bypasses builtins.open — patch pathlib.Path.open instead
        original_path_open = Path.open

        def failing_path_open(self_path, *args, **kwargs):
            if "hook_audit.jsonl" in str(self_path):
                raise OSError("disk full")
            return original_path_open(self_path, *args, **kwargs)

        try:
            with unittest.mock.patch.object(Path, "open", failing_path_open):
                lib.audit_log("hook_name", "decision", "detail")
        except Exception as exc:
            raise AssertionError(f"audit_log raised {type(exc).__name__}: {exc}")

    def test_audit_log_source_has_stderr_write(self) -> None:
        """R-P7-04: _lib.py audit_log() source contains sys.stderr write on failure."""
        source = LIB_PATH.read_text(encoding="utf-8")
        match = re.search(r"def audit_log\(.+?\n(.*?)(?=\ndef |\Z)", source, re.DOTALL)
        if match:
            func_body = match.group(0)
            assert "sys.stderr" in func_body, (
                "audit_log() must write to sys.stderr when write fails (R-P7-04)"
            )
        else:
            assert "sys.stderr" in source, (
                "_lib.py must contain sys.stderr write for audit_log failure (R-P7-04)"
            )

    def test_audit_log_does_not_silently_pass_on_failure(self) -> None:
        """R-P7-04: audit_log() must not have a bare pass in its exception handler."""
        source = LIB_PATH.read_text(encoding="utf-8")
        silent_pass = re.search(
            r"def audit_log.*?except \([^)]+\):\s*\n\s*pass\s*\n",
            source,
            re.DOTALL,
        )
        assert silent_pass is None, (
            "audit_log() must not silently pass on write failure (R-P7-04)"
        )
