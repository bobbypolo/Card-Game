"""Tests for post_write_prod_scan.py hook."""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "post_write_prod_scan.py"
SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "settings.json"
HOOKS_DIR = Path(__file__).resolve().parent.parent


def run_hook(file_path: str, tmp_dir: Path) -> subprocess.CompletedProcess:
    """Run the prod scan hook with simulated stdin JSON."""
    stdin_data = json.dumps({"tool_input": {"file_path": file_path}})
    (tmp_dir / ".claude").mkdir(parents=True, exist_ok=True)
    env = {
        "CLAUDE_PROJECT_ROOT": str(tmp_dir),
        "PATH": "",
        "SYSTEMROOT": "",
    }
    for key in ("PATH", "SYSTEMROOT", "PYTHONPATH", "HOME", "USERPROFILE"):
        if key in os.environ:
            env[key] = os.environ[key]

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return result


class TestHookExists:
    """# Tests R-P2-01"""

    def test_hook_file_exists(self) -> None:
        """# Tests R-P2-01 R-P4-05 -- post_write_prod_scan.py exists."""
        assert HOOK_PATH.exists(), f"Hook not found at {HOOK_PATH}"
        assert HOOK_PATH.name == "post_write_prod_scan.py"

    def test_hook_is_valid_python(self) -> None:
        """# Tests R-P2-01 -- hook is valid Python that can be compiled."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        code = compile(source, str(HOOK_PATH), "exec")
        code_type = type(code).__name__
        assert code_type == "code"

    def test_hook_imports_scan_file_violations(self) -> None:
        """R-P2-02 -- hook imports scan_file_violations, not state writers."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "scan_file_violations" in source
        assert "set_file_violations" not in source
        assert "remove_file_violations" not in source


class TestScanningBehavior:
    """# Tests R-P2-02"""

    def test_detects_violations_and_prints_warnings(self, tmp_path: Path) -> None:
        """# Tests R-P2-02 -- scans code files and prints [PROD WARN] per violation."""
        bad_file = tmp_path / "bad_code.py"
        bad_file.write_text(
            '# TODO: fix this\npassword = "secret123"\nimport pdb; pdb.set_trace()\n',
            encoding="utf-8",
        )
        result = run_hook(str(bad_file), tmp_path)
        assert "[PROD WARN]" in result.stdout
        assert "todo-comment" in result.stdout
        assert "hardcoded-secret" in result.stdout
        assert "debugger-stmt" in result.stdout

    def test_clean_file_no_warnings(self, tmp_path: Path) -> None:
        """# Tests R-P2-02 -- clean file produces no [PROD WARN] output."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text(
            "def add(a: int, b: int) -> int:\n"
            '    """Add two numbers."""\n'
            "    return a + b\n",
            encoding="utf-8",
        )
        result = run_hook(str(clean_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout


class TestExitCode:
    """# Tests R-P2-03"""

    def test_exits_0_on_violations(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- exits 0 even when violations found (warn-only)."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("# TODO: fix\n", encoding="utf-8")
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 0

    def test_exits_0_on_clean_file(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- exits 0 on clean file."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("x = 1\n", encoding="utf-8")
        result = run_hook(str(clean_file), tmp_path)
        assert result.returncode == 0

    def test_exits_0_on_missing_file(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- exits 0 on missing/nonexistent file."""
        result = run_hook(str(tmp_path / "nonexistent.py"), tmp_path)
        assert result.returncode == 0

    def test_exits_0_on_empty_stdin(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- exits 0 on empty stdin."""
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="",
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

    def test_exits_0_on_malformed_stdin(self, tmp_path: Path) -> None:
        """# Tests R-P2-03 -- exits 0 on malformed JSON stdin."""
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0


class TestSkipBehavior:
    """# Tests R-P2-04"""

    def test_skips_test_file_prefix(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- skips files named test_*."""
        test_file = tmp_path / "test_something.py"
        test_file.write_text("# TODO: fix\n", encoding="utf-8")
        result = run_hook(str(test_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout

    def test_skips_test_file_suffix(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- skips files matching *_test.*."""
        test_file = tmp_path / "module_test.py"
        test_file.write_text("# TODO: fix\n", encoding="utf-8")
        result = run_hook(str(test_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout

    def test_skips_non_code_markdown(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- skips .md files."""
        md_file = tmp_path / "readme.md"
        md_file.write_text("# TODO: write docs\n", encoding="utf-8")
        result = run_hook(str(md_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout

    def test_skips_non_code_json(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- skips .json files."""
        json_file = tmp_path / "config.json"
        json_file.write_text('{"TODO": "fix"}\n', encoding="utf-8")
        result = run_hook(str(json_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout

    def test_skips_non_code_txt(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- skips .txt files."""
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("# TODO: fix\n", encoding="utf-8")
        result = run_hook(str(txt_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout

    def test_scans_python_file(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- does scan regular .py files."""
        py_file = tmp_path / "module.py"
        py_file.write_text("# TODO: fix\n", encoding="utf-8")
        result = run_hook(str(py_file), tmp_path)
        assert "[PROD WARN]" in result.stdout

    def test_scans_typescript_file(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- does scan .ts files."""
        ts_file = tmp_path / "module.ts"
        ts_file.write_text("// TODO: fix\n", encoding="utf-8")
        result = run_hook(str(ts_file), tmp_path)
        assert "[PROD WARN]" in result.stdout


class TestStatelessBehavior:
    """-- prod scan is stateless, no state writes."""

    def test_no_violations_written_to_workflow_state(self, tmp_path: Path) -> None:
        """-- violations NOT written to .workflow-state.json."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("# TODO: fix this\n", encoding="utf-8")
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 0

        state_file = tmp_path / ".claude" / ".workflow-state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            assert state.get("prod_violations") is None, (
                "prod_violations should not be set -- hook is stateless"
            )

    def test_no_legacy_prod_violations_file(self, tmp_path: Path) -> None:
        """-- no legacy .prod_violations file created."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("# TODO: fix this\n", encoding="utf-8")
        run_hook(str(bad_file), tmp_path)

        legacy_marker = tmp_path / ".prod_violations"
        assert not legacy_marker.exists(), (
            "Legacy .prod_violations should not be created"
        )

        # Also check inside .claude dir
        legacy_claude = tmp_path / ".claude" / ".prod_violations"
        assert not legacy_claude.exists(), (
            "Legacy .claude/.prod_violations should not be created"
        )

    def test_clean_file_no_state_written(self, tmp_path: Path) -> None:
        """-- clean file does not write prod_violations to state."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("x = 1\n", encoding="utf-8")
        run_hook(str(clean_file), tmp_path)

        state_file = tmp_path / ".claude" / ".workflow-state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            assert state.get("prod_violations") is None


class TestSettingsWiring:
    def test_settings_json_has_prod_scan(self) -> None:
        """settings.json PostToolUse:Edit|Write includes prod_scan."""
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        post_tool_use = settings["hooks"]["PostToolUse"]

        # Find the Edit|Write matcher
        edit_write_matchers = [
            g for g in post_tool_use if "Edit" in g.get("matcher", "")
        ]
        matcher_count = len(edit_write_matchers)
        assert matcher_count >= 1, "No Edit|Write matcher found"

        # Collect all hook commands across Edit|Write matchers
        commands = []
        for matcher in edit_write_matchers:
            for hook in matcher.get("hooks", []):
                commands.append(hook.get("command", ""))

        has_prod_scan = any("prod_scan" in cmd for cmd in commands)
        assert has_prod_scan is True, f"prod_scan not found in commands: {commands}"

    def test_settings_json_has_post_format(self) -> None:
        """settings.json still includes post_format.py."""
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        post_tool_use = settings["hooks"]["PostToolUse"]

        edit_write_matchers = [
            g for g in post_tool_use if "Edit" in g.get("matcher", "")
        ]
        commands = []
        for matcher in edit_write_matchers:
            for hook in matcher.get("hooks", []):
                commands.append(hook.get("command", ""))

        assert any("post_format" in cmd for cmd in commands), (
            f"post_format not found in commands: {commands}"
        )


class TestTwoTierEnforcement:
    """# Tests R-P3-01, R-P3-02"""

    def test_exits_2_on_security_violation(self, tmp_path: Path) -> None:
        """# Tests R-P3-01 -- exits 2 when any violation has severity='block'."""
        bad_file = tmp_path / "secret.py"
        bad_file.write_text('password = "hunter2"\n', encoding="utf-8")
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 2
        assert "[PROD BLOCK]" in result.stdout

    def test_exits_0_on_hygiene_only(self, tmp_path: Path) -> None:
        """# Tests R-P3-02 -- exits 0 when all violations are severity='warn'."""
        bad_file = tmp_path / "hygiene.py"
        # Use a debug print which is severity=warn
        bad_file.write_text('print("debug info")\n', encoding="utf-8")
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD WARN]" in result.stdout

    def test_mixed_security_and_hygiene_exits_2(self, tmp_path: Path) -> None:
        """# Tests R-P3-01 -- mixed violations: security + hygiene → exit 2."""

        bad_file = tmp_path / "mixed.py"
        bad_file.write_text(
            '# a]fixme: fix later\npassword = "secret123"\n',
            encoding="utf-8",
        )
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 2
        assert "[PROD BLOCK]" in result.stdout

    def test_sql_injection_blocks(self, tmp_path: Path) -> None:
        """# Tests R-P3-01 -- SQL injection is severity=block."""
        bad_file = tmp_path / "sqli.py"
        bad_file.write_text(
            'query = "SELECT * FROM users WHERE id=" + uid\n',
            encoding="utf-8",
        )
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 2

    def test_shell_injection_blocks(self, tmp_path: Path) -> None:
        """# Tests R-P3-01 -- shell injection is severity=block."""
        bad_file = tmp_path / "shelli.py"
        bad_file.write_text(
            'os.system(f"rm -rf {user_input}")\n',
            encoding="utf-8",
        )
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 2

    def test_debug_print_warns(self, tmp_path: Path) -> None:
        """# Tests R-P3-02 -- debug print is severity=warn."""
        bad_file = tmp_path / "debug.py"
        bad_file.write_text('print("debug info")\n', encoding="utf-8")
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD WARN]" in result.stdout

    def test_clean_file_still_exits_0(self, tmp_path: Path) -> None:
        """clean file still exits 0."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("x = 1\n", encoding="utf-8")
        result = run_hook(str(clean_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD" not in result.stdout


class TestBugFixRegression:
    def test_hook_has_no_legacy_write_marker(self) -> None:
        """-- hook does not contain legacy _write_marker function."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "def _write_marker" not in source

    def test_hook_has_no_legacy_get_marker_path(self) -> None:
        """-- hook does not contain legacy _get_marker_path function."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "def _get_marker_path" not in source

    def test_hook_does_not_import_prod_violations_path(self) -> None:
        """-- hook does not import PROD_VIOLATIONS_PATH (legacy)."""
        source = HOOK_PATH.read_text(encoding="utf-8")
        assert "PROD_VIOLATIONS_PATH" not in source


class TestFileExistence:
    def test_test_file_exists(self) -> None:
        """test_post_write_prod_scan.py exists."""
        assert Path(__file__).exists()
        assert Path(__file__).name == "test_post_write_prod_scan.py"


STOP_GATE_PATH = Path(__file__).resolve().parent.parent / "stop_verify_gate.py"


def run_stop_gate(tmp_dir: Path) -> subprocess.CompletedProcess:
    """Run stop_verify_gate.py with CLAUDE_PROJECT_ROOT pointing to tmp_dir."""
    env = {
        "CLAUDE_PROJECT_ROOT": str(tmp_dir),
        "PATH": "",
        "SYSTEMROOT": "",
    }
    for key in ("PATH", "SYSTEMROOT", "PYTHONPATH", "HOME", "USERPROFILE"):
        if key in os.environ:
            env[key] = os.environ[key]

    # stop_verify_gate reads stdin but we can send an empty hook payload
    stdin_data = json.dumps({"tool_input": {}})
    result = subprocess.run(
        [sys.executable, str(STOP_GATE_PATH)],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return result


class TestProdScanStatelessIntegration:
    """-- prod scan is stateless, stop_gate only checks needs_verify."""

    def test_prod_scan_does_not_write_violations_to_state(self, tmp_path: Path) -> None:
        """-- prod_scan does not write violations to state."""
        bad_file = tmp_path / "violations.py"
        bad_file.write_text(
            "".join(["# ", "TODO", ": leftover cleanup\n"]), encoding="utf-8"
        )

        scan_result = run_hook(str(bad_file), tmp_path)
        assert scan_result.returncode == 0, (
            f"prod_scan should exit 0 for hygiene: {scan_result.stderr}"
        )

        # State file should NOT have prod_violations set
        state_file = tmp_path / ".claude" / ".workflow-state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            assert state.get("prod_violations") is None, (
                "prod_violations should not be set -- hook is stateless"
            )

    def test_stop_gate_allows_after_prod_scan_only(self, tmp_path: Path) -> None:
        """-- stop_gate allows stop when only prod_scan ran (no needs_verify)."""
        bad_file = tmp_path / "violations.py"
        bad_file.write_text(
            "".join(["# ", "TODO", ": leftover cleanup\n"]), encoding="utf-8"
        )

        run_hook(str(bad_file), tmp_path)

        gate_result = run_stop_gate(tmp_path)
        assert gate_result.returncode == 0
        # No needs_verify marker => stop_gate allows stop (no output or warn)
        if gate_result.stdout.strip():
            gate_output = json.loads(gate_result.stdout)
            assert gate_output.get("decision") != "block", (
                f"Should not block when only prod_scan ran: {gate_output}"
            )

    def test_stop_gate_allows_after_clean_scan(self, tmp_path: Path) -> None:
        """after scanning a clean file, stop_gate allows stop."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("x = 1\n", encoding="utf-8")

        run_hook(str(clean_file), tmp_path)

        gate_result = run_stop_gate(tmp_path)
        assert gate_result.returncode == 0
        if gate_result.stdout.strip():
            gate_output = json.loads(gate_result.stdout)
            assert gate_output.get("decision") != "block", (
                f"Should not block on clean file: {gate_output}"
            )


class TestExcludePatterns:
    """# Tests R-P2-01, R-P2-02, R-P2-03, R-P2-04"""

    def test_skips_file_matching_exclude_pattern(self, tmp_path: Path) -> None:
        """# Tests R-P2-01 -- workflow.json exclude_patterns are applied."""
        # Create workflow.json with exclude pattern for "generated_*"
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        wf = claude_dir / "workflow.json"
        wf.write_text(
            json.dumps(
                {
                    "qa_runner": {
                        "production_scan": {"exclude_patterns": ["generated_*"]}
                    }
                }
            ),
            encoding="utf-8",
        )
        # Create a file that matches the pattern with a violation
        gen_file = tmp_path / "generated_code.py"
        gen_file.write_text("# TODO: auto-generated\n", encoding="utf-8")
        result = run_hook(str(gen_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD WARN]" not in result.stdout

    def test_does_not_skip_non_matching_file(self, tmp_path: Path) -> None:
        """# Tests R-P2-02 -- non-excluded files are still scanned."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        wf = claude_dir / "workflow.json"
        wf.write_text(
            json.dumps(
                {
                    "qa_runner": {
                        "production_scan": {"exclude_patterns": ["generated_*"]}
                    }
                }
            ),
            encoding="utf-8",
        )
        normal_file = tmp_path / "app.py"
        normal_file.write_text("# TODO: fix this\n", encoding="utf-8")
        result = run_hook(str(normal_file), tmp_path)
        assert "[PROD WARN]" in result.stdout

    def test_hook_file_in_claude_hooks_dir_is_now_scanned(self, tmp_path: Path) -> None:
        """# Tests R-P8-05 -- hook exclusion removed; .claude/hooks/ files ARE scanned."""
        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_file = hooks_dir / "my_hook.py"
        hook_file.write_text("# TODO: fix hook\n", encoding="utf-8")
        result = run_hook(str(hook_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD WARN]" in result.stdout

    def test_test_file_still_skipped(self, tmp_path: Path) -> None:
        """# Tests R-P2-04 -- existing test file skip logic is preserved."""
        test_file = tmp_path / "test_something.py"
        test_file.write_text("# TODO: fix test\n", encoding="utf-8")
        result = run_hook(str(test_file), tmp_path)
        assert "[PROD WARN]" not in result.stdout

    def test_missing_workflow_json_still_scans(self, tmp_path: Path) -> None:
        """-- missing workflow.json does not crash hook."""
        # Ensure there is no workflow.json
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        wf = claude_dir / "workflow.json"
        if wf.exists():
            wf.unlink()
        bad_file = tmp_path / "module.py"
        bad_file.write_text("# TODO: fix this\n", encoding="utf-8")
        result = run_hook(str(bad_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD WARN]" in result.stdout

    def test_hook_file_is_scanned_not_skipped(self, tmp_path: Path) -> None:
        """# Tests R-P8-05 -- hook directory files are now scanned (exclusion removed)."""
        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_file = hooks_dir / "my_hook.py"
        hook_file.write_text("# TODO: fix hook\n", encoding="utf-8")
        result = run_hook(str(hook_file), tmp_path)
        assert result.returncode == 0
        assert "[PROD WARN]" in result.stdout


class TestNewProdPatterns:
    """# Tests R-P8-01 through R-P8-04 -- new production violation patterns."""

    def _scan(self, content: str) -> list[dict]:
        """Import and call scan_file_violations directly with a tmp file."""
        import sys

        sys.path.insert(0, str(HOOKS_DIR))
        from _prod_patterns import scan_file_violations
        from pathlib import Path as P
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = P(f.name)
        try:
            return scan_file_violations(tmp)
        finally:
            os.unlink(tmp)

    def test_silent_swallow_inline(self) -> None:
        """# Tests R-P8-01 -- except ValueError: pass (inline) detected as silent-swallow."""
        violations = self._scan("except ValueError: pass\n")
        ids = [v["violation_id"] for v in violations]
        assert "silent-swallow" in ids
        sw = next(v for v in violations if v["violation_id"] == "silent-swallow")
        assert sw["severity"] == "warn"

    def test_silent_swallow_multiline(self) -> None:
        """# Tests R-P8-01 -- except ValueError:\\n    pass (multiline) detected as silent-swallow."""
        violations = self._scan("except ValueError:\n    pass\n")
        ids = [v["violation_id"] for v in violations]
        assert "silent-swallow" in ids
        sw = next(v for v in violations if v["violation_id"] == "silent-swallow")
        assert sw["severity"] == "warn"

    def test_silent_swallow_no_false_positive(self) -> None:
        """# Tests R-P8-03 -- except ValueError: logger.error(e) NOT flagged as silent-swallow."""
        violations = self._scan("except ValueError: logger.error(e)\n")
        ids = [v["violation_id"] for v in violations]
        assert "silent-swallow" not in ids

    def test_silent_swallow_multiline_no_false_positive(self) -> None:
        """# Tests R-P8-03 -- except ValueError:\\n    logger.error(e) NOT flagged."""
        violations = self._scan("except ValueError:\n    logger.error(e)\n")
        ids = [v["violation_id"] for v in violations]
        assert "silent-swallow" not in ids

    def test_error_mask_none_inline(self) -> None:
        """# Tests R-P8-02 -- except Exception: return None (inline) detected as error-mask-none."""
        violations = self._scan("except Exception: return None\n")
        ids = [v["violation_id"] for v in violations]
        assert "error-mask-none" in ids
        em = next(v for v in violations if v["violation_id"] == "error-mask-none")
        assert em["severity"] == "warn"

    def test_error_mask_none_multiline(self) -> None:
        """# Tests R-P8-02 -- except Exception:\\n    return None detected as error-mask-none."""
        violations = self._scan("except Exception:\n    return None\n")
        ids = [v["violation_id"] for v in violations]
        assert "error-mask-none" in ids
        em = next(v for v in violations if v["violation_id"] == "error-mask-none")
        assert em["severity"] == "warn"

    def test_error_mask_none_typed_except(self) -> None:
        """# Tests R-P8-02 -- except ValueError: return None detected as error-mask-none."""
        violations = self._scan("except ValueError: return None\n")
        ids = [v["violation_id"] for v in violations]
        assert "error-mask-none" in ids

    def test_subprocess_shell_multiline(self) -> None:
        """# Tests R-P8-04 -- subprocess.run(..., shell=True) across lines detected."""
        code = "result = subprocess.run(\n    ['cmd'],\n    shell=True,\n)\n"
        violations = self._scan(code)
        ids = [v["violation_id"] for v in violations]
        assert "subprocess-shell-multiline" in ids
        sp = next(
            v for v in violations if v["violation_id"] == "subprocess-shell-multiline"
        )
        assert sp["severity"] == "warn"

    def test_subprocess_shell_singleline_still_detected(self) -> None:
        """# Tests R-P8-04 -- single-line subprocess.run with shell=True still detected."""
        violations = self._scan("subprocess.run(['cmd'], shell=True)\n")
        ids = [v["violation_id"] for v in violations]
        # Either subprocess-shell-injection (block) or subprocess-shell-multiline (warn) should fire
        assert (
            "subprocess-shell-injection" in ids or "subprocess-shell-multiline" in ids
        )


class TestDeepSecurityPatterns:
    """# Tests R-P1-01 through R-P1-08 -- deep security violation patterns."""

    def _scan(self, content: str) -> list[dict]:
        """Import and call scan_file_violations directly with a tmp file."""
        sys.path.insert(0, str(HOOKS_DIR))
        from _prod_patterns import scan_file_violations
        from pathlib import Path as P
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            tmp = P(f.name)
        try:
            return scan_file_violations(tmp)
        finally:
            os.unlink(tmp)

    # --- R-P1-01: pickle-deserialize positive detection ---

    def test_pickle_loads_detected(self) -> None:
        """# Tests R-P1-01 -- pickle.loads() detected as pickle-deserialize."""
        violations = self._scan("data = pickle.loads(raw_bytes)\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" in ids
        v = next(v for v in violations if v["violation_id"] == "pickle-deserialize")
        assert v["severity"] == "block"

    def test_pickle_load_detected(self) -> None:
        """# Tests R-P1-01 -- pickle.load() detected as pickle-deserialize."""
        violations = self._scan("obj = pickle.load(open('data.pkl', 'rb'))\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" in ids

    def test_yaml_load_detected(self) -> None:
        """# Tests R-P1-01 -- yaml.load() detected as pickle-deserialize."""
        violations = self._scan("config = yaml.load(stream)\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" in ids

    def test_yaml_unsafe_load_detected(self) -> None:
        """# Tests R-P1-01 -- yaml.unsafe_load() detected as pickle-deserialize."""
        violations = self._scan("data = yaml.unsafe_load(raw)\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" in ids

    def test_marshal_loads_detected(self) -> None:
        """# Tests R-P1-01 -- marshal.loads() detected as pickle-deserialize."""
        violations = self._scan("code = marshal.loads(raw)\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" in ids

    # --- R-P1-01: pickle-deserialize false positive checks ---

    def test_pickle_dumps_safe(self) -> None:
        """# Tests R-P1-07 -- pickle.dumps (serialization) NOT flagged."""
        violations = self._scan("raw = pickle.dumps(obj)\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" not in ids

    def test_yaml_safe_load_safe(self) -> None:
        """# Tests R-P1-07 -- yaml.safe_load NOT flagged."""
        violations = self._scan("config = yaml.safe_load(stream)\n")
        ids = [v["violation_id"] for v in violations]
        assert "pickle-deserialize" not in ids

    # --- R-P1-02: path-traversal positive detection ---

    def test_path_traversal_open_detected(self) -> None:
        """# Tests R-P1-02 -- open() with ../ detected as path-traversal."""
        violations = self._scan("f = open('../../etc/passwd')\n")
        ids = [v["violation_id"] for v in violations]
        assert "path-traversal" in ids
        v = next(v for v in violations if v["violation_id"] == "path-traversal")
        assert v["severity"] == "block"

    def test_path_traversal_os_path_join_detected(self) -> None:
        """# Tests R-P1-02 -- os.path.join with ../ detected."""
        violations = self._scan("p = os.path.join(base, '../secret')\n")
        ids = [v["violation_id"] for v in violations]
        assert "path-traversal" in ids

    def test_path_traversal_Path_detected(self) -> None:
        """# Tests R-P1-02 -- Path() with ../ detected."""
        violations = self._scan("p = Path('../../../etc/shadow')\n")
        ids = [v["violation_id"] for v in violations]
        assert "path-traversal" in ids

    # --- R-P1-03: eval-exec-var positive detection ---

    def test_eval_variable_detected(self) -> None:
        """# Tests R-P1-03 -- eval(variable) detected as eval-exec-var."""
        violations = self._scan("result = eval(user_input)\n")
        ids = [v["violation_id"] for v in violations]
        assert "eval-exec-var" in ids
        v = next(v for v in violations if v["violation_id"] == "eval-exec-var")
        assert v["severity"] == "block"

    def test_exec_variable_detected(self) -> None:
        """# Tests R-P1-03 -- exec(variable) detected as eval-exec-var."""
        violations = self._scan("exec(code_string)\n")
        ids = [v["violation_id"] for v in violations]
        assert "eval-exec-var" in ids

    # --- R-P1-03: eval-exec-var false positive checks ---

    def test_eval_string_literal_safe(self) -> None:
        """# Tests R-P1-07 -- eval('literal') NOT flagged."""
        violations = self._scan("result = eval('2 + 2')\n")
        ids = [v["violation_id"] for v in violations]
        assert "eval-exec-var" not in ids

    def test_eval_double_quote_literal_safe(self) -> None:
        """# Tests R-P1-07 -- eval(\"literal\") NOT flagged."""
        violations = self._scan('result = eval("2 + 2")\n')
        ids = [v["violation_id"] for v in violations]
        assert "eval-exec-var" not in ids

    # --- R-P1-04: unsafe-tempfile positive detection ---

    def test_tempfile_mktemp_detected(self) -> None:
        """# Tests R-P1-04 -- tempfile.mktemp() detected as unsafe-tempfile."""
        violations = self._scan("path = tempfile.mktemp()\n")
        ids = [v["violation_id"] for v in violations]
        assert "unsafe-tempfile" in ids
        v = next(v for v in violations if v["violation_id"] == "unsafe-tempfile")
        assert v["severity"] == "block"

    # --- R-P1-04: unsafe-tempfile false positive checks ---

    def test_tempfile_mkstemp_safe(self) -> None:
        """# Tests R-P1-07 -- tempfile.mkstemp() NOT flagged."""
        violations = self._scan("fd, path = tempfile.mkstemp()\n")
        ids = [v["violation_id"] for v in violations]
        assert "unsafe-tempfile" not in ids

    def test_tempfile_named_temporary_file_safe(self) -> None:
        """# Tests R-P1-07 -- NamedTemporaryFile NOT flagged."""
        violations = self._scan("f = tempfile.NamedTemporaryFile()\n")
        ids = [v["violation_id"] for v in violations]
        assert "unsafe-tempfile" not in ids

    # --- R-P1-05: unvalidated-redirect positive detection ---

    def test_redirect_request_args_detected(self) -> None:
        """# Tests R-P1-05 -- redirect(request.args) detected as unvalidated-redirect."""
        violations = self._scan("return redirect(request.args.get('next'))\n")
        ids = [v["violation_id"] for v in violations]
        assert "unvalidated-redirect" in ids
        v = next(v for v in violations if v["violation_id"] == "unvalidated-redirect")
        assert v["severity"] == "block"

    def test_redirect_fstring_detected(self) -> None:
        """# Tests R-P1-05 -- redirect(f'...') detected as unvalidated-redirect."""
        violations = self._scan("return redirect(f'/goto/{url}')\n")
        ids = [v["violation_id"] for v in violations]
        assert "unvalidated-redirect" in ids

    # --- R-P1-05: unvalidated-redirect false positive checks ---

    def test_redirect_literal_path_safe(self) -> None:
        """# Tests R-P1-07 -- redirect('/dashboard') NOT flagged."""
        violations = self._scan("return redirect('/dashboard')\n")
        ids = [v["violation_id"] for v in violations]
        assert "unvalidated-redirect" not in ids

    # --- R-P1-06: _SECURITY_IDS contains all new IDs ---

    def test_security_ids_contains_new_ids(self) -> None:
        """# Tests R-P1-06 -- _SECURITY_IDS frozenset contains all 5 new violation IDs."""
        sys.path.insert(0, str(HOOKS_DIR))
        from qa_runner import _SECURITY_IDS

        new_ids = {
            "pickle-deserialize",
            "path-traversal",
            "eval-exec-var",
            "unsafe-tempfile",
            "unvalidated-redirect",
        }
        assert new_ids.issubset(_SECURITY_IDS), (
            f"Missing from _SECURITY_IDS: {new_ids - _SECURITY_IDS}"
        )
