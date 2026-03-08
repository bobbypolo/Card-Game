# Tests R-P1-01, R-P1-02, R-P1-03, R-P1-04, R-P1-05, R-P1-06
"""Tests for STORY-001: Fix-Log Behavioral Instructions + State Ownership Documentation.

Validates that ralph-story.md contains fix-log read/write/cleanup instructions
and state-ownership.md documents the fix-log file ownership and compaction recovery.
"""

from pathlib import Path

RALPH_STORY = Path(__file__).parent.parent.parent / "agents" / "ralph-story.md"
STATE_OWNERSHIP = (
    Path(__file__).parent.parent.parent / "docs" / "knowledge" / "state-ownership.md"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestFixLogReadInstruction:
    """R-P1-01: ralph-story.md Fix Loop contains read instruction."""

    def test_fix_log_read_before_iteration(self) -> None:
        content = _read(RALPH_STORY)
        assert "fix-log" in content, "ralph-story.md must reference fix-log"
        assert ".claude/runtime/fix-log/{story_id}.md" in content, (
            "Must reference the fix-log file path"
        )
        assert "Read" in content and "fix-log" in content, (
            "Fix Loop must instruct reading fix-log before each iteration"
        )


class TestFixLogWriteInstruction:
    """R-P1-02: ralph-story.md Fix Loop contains append instruction."""

    def test_fix_log_append_after_fix(self) -> None:
        content = _read(RALPH_STORY)
        assert "Append" in content or "append" in content, (
            "Fix Loop must instruct appending to fix-log"
        )
        assert "Failing steps" in content, "Iteration entry must include failing steps"
        assert "Changes made" in content or "changes made" in content, (
            "Iteration entry must include changes made"
        )
        assert "Files touched" in content or "files touched" in content, (
            "Iteration entry must include files touched"
        )
        assert "Outcome" in content or "outcome" in content, (
            "Iteration entry must include outcome"
        )


class TestFixLogCleanup:
    """R-P1-03: ralph-story.md Fix Loop contains cleanup on PASS."""

    def test_fix_log_delete_on_pass(self) -> None:
        content = _read(RALPH_STORY)
        assert "Delete" in content or "delete" in content or "rm -f" in content, (
            "Fix Loop must instruct deleting fix-log on QA pass"
        )
        assert "cleanup" in content.lower(), "Fix Loop must mention cleanup"


class TestFixLogSummaryOnFailure:
    """R-P1-04: RALPH_STORY_RESULT guidance embeds fix-log in summary."""

    def test_fix_log_embedded_in_summary(self) -> None:
        content = _read(RALPH_STORY)
        assert "last 3" in content, "Must instruct embedding last 3 fix-log iterations"
        assert "summary" in content and "fix-log" in content.lower(), (
            "Must instruct embedding fix-log content in summary field"
        )


class TestStateOwnershipFixLogEntry:
    """R-P1-05: state-ownership.md State Files table includes fix-log."""

    def test_fix_log_in_state_files_table(self) -> None:
        content = _read(STATE_OWNERSHIP)
        assert ".claude/runtime/fix-log/{story_id}.md" in content, (
            "State Files table must include fix-log entry"
        )
        assert "ralph-story" in content, "Fix-log owner must be ralph-story"
        # Verify the fix-log row includes mutation rules
        lines = content.split("\n")
        fix_log_lines = [
            line for line in lines if "fix-log" in line and "ralph-story" in line
        ]
        assert len(fix_log_lines) >= 1, (
            "State Files table must have a row with fix-log and ralph-story"
        )


class TestStateOwnershipCompactionRecovery:
    """R-P1-06: state-ownership.md Context-Budget Degradation references fix-log."""

    def test_fix_log_compaction_recovery(self) -> None:
        content = _read(STATE_OWNERSHIP)
        assert "compaction recovery mechanism" in content, (
            "Context-Budget Degradation must reference fix-log as compaction recovery"
        )
        assert "fix-log" in content.lower() and "compaction" in content.lower(), (
            "Must connect fix-log to compaction recovery"
        )
