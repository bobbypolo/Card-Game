"""Tests for ralph-story.md agent file — verifies R-P5-01 through R-P5-05."""

from pathlib import Path

AGENT_FILE = Path(__file__).parent.parent.parent / "agents" / "ralph-story.md"


def get_content() -> str:
    """Read the agent file content."""
    return AGENT_FILE.read_text(encoding="utf-8")


class TestRalphStoryAgent:
    """Positive tests for ralph-story.md existence and frontmatter."""

    def test_file_exists(self) -> None:
        """ -- ralph-story.md must exist at the expected path."""
        assert AGENT_FILE.exists(), (
            "ralph-story.md must exist at .claude/agents/ralph-story.md"
        )

    def test_frontmatter_name(self) -> None:
        """ -- frontmatter must contain name: ralph-story."""
        content = get_content()
        assert "name: ralph-story" in content, "Frontmatter must have name: ralph-story"

    def test_frontmatter_max_turns(self) -> None:
        """ -- frontmatter must contain maxTurns: 200."""
        content = get_content()
        assert "maxTurns: 200" in content, "Frontmatter must have maxTurns: 200"

    def test_frontmatter_memory(self) -> None:
        """ -- frontmatter must contain memory: user."""
        content = get_content()
        assert "memory: user" in content, "Frontmatter must have memory: user"

    def test_required_sections_present(self) -> None:
        """ -- all required STEP sections must be present."""
        content = get_content()
        required_sections = ["STEP 4", "STEP 5A", "STEP 5", "STEP 6", "STEP 6A"]
        for section in required_sections:
            assert section in content, f"Agent file must contain section: {section}"


class TestRalphStoryAgentNegative:
    """Negative tests guarding against critical bugs.  R-P5-02 R-P5-03"""

    def test_no_isolation_worktree(self) -> None:
        """ -- frontmatter must NOT contain isolation: worktree.

        ralph-story merges to feature branch directly; worktree isolation would break git merge.
        """
        content = get_content()
        assert "isolation: worktree" not in content, (
            "Frontmatter must NOT have isolation: worktree — "
            "ralph-story performs git merges and must not run in a worktree"
        )

    def test_dispatch_contains_checkpoint_hash(self) -> None:
        """ -- checkpoint_hash must be listed as a required dispatch field."""
        content = get_content()
        assert "checkpoint_hash" in content, (
            "RALPH_STORY_DISPATCH section must include checkpoint_hash as a required field"
        )

    def test_no_ralph_worker_result_in_return_format(self) -> None:
        """ -- return format must use RALPH_STORY_RESULT not RALPH_WORKER_RESULT.

        The return format marker is RALPH_STORY_RESULT. RALPH_WORKER_RESULT: (with colon) is
        the inner worker's output marker and must NOT appear in this agent's return instructions,
        as it would cause the outer loop to mis-parse this agent's output.
        """
        content = get_content()
        # The agent must document RALPH_STORY_RESULT as its return format
        assert "RALPH_STORY_RESULT" in content, (
            "Agent file must document RALPH_STORY_RESULT as the return format"
        )
        # RALPH_WORKER_RESULT: (with colon) is the actual output marker used by ralph-worker.
        # This agent must NOT instruct itself to emit RALPH_WORKER_RESULT: — only RALPH_STORY_RESULT:
        assert "RALPH_WORKER_RESULT:" not in content, (
            "Agent file must not contain RALPH_WORKER_RESULT: marker — "
            "this agent returns RALPH_STORY_RESULT, not RALPH_WORKER_RESULT"
        )


class TestRalphStoryAgentDispatchFormat:
    """Tests for RALPH_STORY_DISPATCH documentation."""

    def test_dispatch_section_exists(self) -> None:
        """ -- RALPH_STORY_DISPATCH section must exist."""
        content = get_content()
        assert "RALPH_STORY_DISPATCH" in content, (
            "Agent file must document the RALPH_STORY_DISPATCH format"
        )

    def test_dispatch_required_fields(self) -> None:
        """ -- all required dispatch fields must be documented."""
        content = get_content()
        required_fields = [
            "story_id",
            "checkpoint_hash",
            "feature_branch",
            "attempt",
            "acceptanceCriteria",
        ]
        for field in required_fields:
            assert field in content, (
                f"RALPH_STORY_DISPATCH must document required field: {field}"
            )

    def test_step4_reads_checkpoint_from_dispatch(self) -> None:
        """ -- STEP 4 must explicitly read checkpoint_hash from dispatch prompt."""
        content = get_content()
        # Check that STEP 4 references reading from dispatch prompt (not from state)
        assert "NOT from .workflow-state.json" in content, (
            "STEP 4 must explicitly state checkpoint_hash is read from dispatch prompt, "
            "not from .workflow-state.json"
        )


class TestRalphStoryAgentResultFormat:
    """Tests for RALPH_STORY_RESULT documentation."""

    def test_result_section_exists(self) -> None:
        """ -- RALPH_STORY_RESULT section must exist."""
        content = get_content()
        assert "RALPH_STORY_RESULT" in content, (
            "Agent file must document the RALPH_STORY_RESULT format"
        )

    def test_result_required_fields(self) -> None:
        """ -- all required result fields must be documented."""
        content = get_content()
        required_fields = [
            "passed",
            "summary",
            "files_changed",
            "attempt",
            "story_id",
            "worktree_branch",
            "qa_receipt",
            "prod_violations_checked",
        ]
        for field in required_fields:
            assert field in content, (
                f"RALPH_STORY_RESULT must document required field: {field}"
            )
