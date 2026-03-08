"""Tests for lean ralph/SKILL.md outer loop — verifies R-P6-01 through R-P6-04, R-P1-05, R-P1-06."""

from pathlib import Path

SKILL_FILE = Path(__file__).parent.parent.parent / "skills" / "ralph" / "SKILL.md"
PLAN_SKILL_FILE = Path(__file__).parent.parent.parent / "skills" / "plan" / "SKILL.md"


def get_content() -> str:
    """Read the SKILL.md file content."""
    return SKILL_FILE.read_text(encoding="utf-8")


def get_line_count() -> int:
    """Count lines in SKILL.md."""
    return sum(1 for _ in SKILL_FILE.open(encoding="utf-8"))


class TestLeanSkillLineCount:
    """Enforce the lean line count constraint."""

    def test_file_exists(self) -> None:
        """ -- SKILL.md must exist at expected path."""
        assert SKILL_FILE.exists(), (
            "SKILL.md must exist at .claude/skills/ralph/SKILL.md"
        )

    def test_line_count_at_most_200(self) -> None:
        """ -- SKILL.md must contain 200 lines or fewer."""
        count = get_line_count()
        assert count <= 200, (
            f"SKILL.md must be ≤200 lines (lean outer loop), got {count} lines. "
            "Per-story protocol belongs in ralph-story.md, not SKILL.md."
        )


class TestLeanSkillDispatch:
    """Verify dispatch targets ralph-story via Agent tool."""

    def test_dispatches_ralph_story(self) -> None:
        """ -- outer loop must dispatch ralph-story via Agent tool."""
        content = get_content()
        assert "ralph-story" in content, (
            "SKILL.md must reference ralph-story as the dispatch target"
        )

    def test_dispatch_uses_agent_tool(self) -> None:
        """ -- dispatch must use the Agent tool."""
        content = get_content()
        # The dispatch step must mention Agent tool explicitly
        assert "Agent tool" in content, (
            "SKILL.md must reference the Agent tool for dispatching ralph-story"
        )

    def test_subagent_type_ralph_story(self) -> None:
        """ -- dispatch must specify subagent_type: ralph-story."""
        content = get_content()
        assert "subagent_type" in content, (
            "SKILL.md dispatch step must specify subagent_type for Agent tool call"
        )


class TestLeanSkillResultParsing:
    """Verify SKILL.md parses RALPH_STORY_RESULT."""

    def test_parses_ralph_story_result(self) -> None:
        """ -- outer loop must parse RALPH_STORY_RESULT."""
        content = get_content()
        assert "RALPH_STORY_RESULT" in content, (
            "SKILL.md must reference RALPH_STORY_RESULT as the result marker to parse"
        )

    def test_no_ralph_worker_result_reference(self) -> None:
        """ -- RALPH_WORKER_RESULT must NOT appear in outer loop.

        RALPH_WORKER_RESULT is the inner worker's format. The lean outer loop
        only sees RALPH_STORY_RESULT from ralph-story agents.
        """
        content = get_content()
        assert "RALPH_WORKER_RESULT" not in content, (
            "SKILL.md outer loop must NOT reference RALPH_WORKER_RESULT — "
            "only RALPH_STORY_RESULT is returned by ralph-story agents"
        )


class TestLeanSkillCoreRule:
    """Verify Core Rule section exists."""

    def test_core_rule_section_exists(self) -> None:
        """ -- ## Core Rule section must be present."""
        content = get_content()
        assert "## Core Rule" in content, "SKILL.md must contain a ## Core Rule section"

    def test_core_rule_mentions_ralph_story(self) -> None:
        """ -- Core Rule must reference ralph-story delegation."""
        content = get_content()
        assert "## Core Rule" in content, "## Core Rule section must exist"
        # Extract the Core Rule section (text after ## Core Rule up to next ##)
        core_rule_start = content.index("## Core Rule")
        after_core_rule = content[core_rule_start:]
        next_section = after_core_rule.find("\n## ", 4)
        if next_section != -1:
            core_rule_text = after_core_rule[:next_section]
        else:
            core_rule_text = after_core_rule
        assert "ralph-story" in core_rule_text, (
            "## Core Rule section must mention delegation to ralph-story"
        )

    def test_core_rule_mentions_agent_tool(self) -> None:
        """ -- Core Rule must state delegation via Agent tool is mandatory."""
        content = get_content()
        assert "## Core Rule" in content, "## Core Rule section must exist"
        core_rule_start = content.index("## Core Rule")
        after_core_rule = content[core_rule_start:]
        next_section = after_core_rule.find("\n## ", 4)
        if next_section != -1:
            core_rule_text = after_core_rule[:next_section]
        else:
            core_rule_text = after_core_rule
        assert "Agent tool" in core_rule_text, (
            "## Core Rule section must state delegation via Agent tool is mandatory"
        )


class TestLeanSkillStructure:
    """Verify all required STEP sections are present."""

    def test_step_1_present(self) -> None:
        """ -- STEP 1 (Initialize) must be present."""
        content = get_content()
        assert "STEP 1" in content, "SKILL.md must contain STEP 1 (Initialize)"

    def test_step_1_5_present(self) -> None:
        """ -- STEP 1.5 (Feature Branch Setup) must be present."""
        content = get_content()
        assert "STEP 1.5" in content, (
            "SKILL.md must contain STEP 1.5 (Feature Branch Setup)"
        )

    def test_step_2_present(self) -> None:
        """ -- STEP 2 (Find Next Story) must be present."""
        content = get_content()
        assert "STEP 2" in content, "SKILL.md must contain STEP 2 (Find Next Story)"

    def test_step_3_present(self) -> None:
        """ -- STEP 3 (Checkpoint + Dispatch) must be present."""
        content = get_content()
        assert "STEP 3" in content, "SKILL.md must contain STEP 3"

    def test_step_4_present(self) -> None:
        """ -- STEP 4 (Dispatch) must be present."""
        content = get_content()
        assert "STEP 4" in content, "SKILL.md must contain STEP 4 (Dispatch)"

    def test_step_5_present(self) -> None:
        """ -- STEP 5 (Handle Result) must be present."""
        content = get_content()
        assert "STEP 5" in content, "SKILL.md must contain STEP 5 (Handle Result)"

    def test_step_6_present(self) -> None:
        """ -- STEP 6 (End of Session) must be present."""
        content = get_content()
        assert "STEP 6" in content, "SKILL.md must contain STEP 6 (End of Session)"


def _get_step4_text(content: str) -> str:
    """Extract STEP 4 section text (up to STEP 5)."""
    start = content.find("## STEP 4:")
    if start == -1:
        return ""
    end = content.find("\n## STEP 5:", start)
    return content[start:end] if end != -1 else content[start:]


def _get_step5_text(content: str) -> str:
    """Extract STEP 5 section text (up to STEP 6)."""
    start = content.find("## STEP 5:")
    if start == -1:
        return ""
    end = content.find("\n## STEP 6:", start)
    return content[start:end] if end != -1 else content[start:]


class TestParallelDispatch:
    """Verify STEP 4 documents parallel dispatch via same parallelGroup."""

    def test_step4_documents_parallel_dispatch(self) -> None:
        """ -- STEP 4 must document simultaneous dispatch for same parallelGroup."""
        content = get_content()
        step4 = _get_step4_text(content)
        assert "parallelGroup" in step4, (
            "SKILL.md STEP 4 must reference parallelGroup for grouping parallel stories"
        )

    def test_step4_dispatches_simultaneously(self) -> None:
        """ -- STEP 4 must state stories are dispatched simultaneously."""
        content = get_content()
        step4 = _get_step4_text(content)
        assert "simultaneously" in step4 or "same message" in step4, (
            "SKILL.md STEP 4 must document simultaneous dispatch in a single message"
        )

    def test_step4_multiple_agent_calls(self) -> None:
        """ -- STEP 4 must document multiple Agent tool calls for parallel group."""
        content = get_content()
        step4 = _get_step4_text(content)
        assert "multiple Agent tool calls" in step4 or "multiple" in step4, (
            "SKILL.md STEP 4 must mention multiple Agent tool calls for parallel dispatch"
        )

    def test_step4_dependson_met_required(self) -> None:
        """ -- STEP 4 must check dependsOn are met before dispatching."""
        content = get_content()
        step4 = _get_step4_text(content)
        assert "dependsOn" in step4, (
            "SKILL.md STEP 4 must document checking dependsOn before dispatch"
        )


class TestParallelResultCollection:
    """Verify STEP 5 documents collecting results in memory then atomic write."""

    def test_step5_collects_results_in_memory(self) -> None:
        """ -- STEP 5 must document collecting results in memory first."""
        content = get_content()
        step5 = _get_step5_text(content)
        assert "memory" in step5.lower(), (
            "SKILL.md STEP 5 must document collecting results into memory before writing"
        )

    def test_step5_story_id_order(self) -> None:
        """ -- STEP 5 must document merging results in story-ID order."""
        content = get_content()
        step5 = _get_step5_text(content)
        assert "story-ID order" in step5 or "story-id order" in step5.lower(), (
            "SKILL.md STEP 5 must document merging in story-ID order"
        )

    def test_step5_atomic_prd_write(self) -> None:
        """ -- STEP 5 must document a single atomic prd.json write."""
        content = get_content()
        step5 = _get_step5_text(content)
        assert "atomic" in step5 or ("single" in step5 and "prd.json" in step5), (
            "SKILL.md STEP 5 must document a single atomic prd.json write"
        )


class TestDependsOnDefer:
    """Verify SKILL.md documents deferring stories with unmet dependsOn."""

    def test_unmet_dependson_deferred(self) -> None:
        """ -- stories with unmet dependsOn must be deferred to next iteration."""
        content = get_content()
        assert "defer" in content.lower() or "next loop" in content.lower(), (
            "SKILL.md must document deferring stories with unmet dependsOn to next loop iteration"
        )

    def test_dependson_checks_passed_true(self) -> None:
        """ -- dependsOn check must require referenced story passed: true."""
        content = get_content()
        step4 = _get_step4_text(content)
        assert "passed: true" in step4 or "passed:true" in step4 or "passed" in step4, (
            "SKILL.md STEP 4 must reference checking if dependsOn stories are passed"
        )


class TestMissingResultFail:
    """Verify SKILL.md documents missing RALPH_STORY_RESULT treated as FAIL."""

    def test_missing_result_treated_as_fail(self) -> None:
        """ -- missing RALPH_STORY_RESULT for parallel story treated as FAIL."""
        content = get_content()
        assert "Missing" in content or "missing" in content, (
            "SKILL.md must document handling missing RALPH_STORY_RESULT"
        )

    def test_other_results_still_processed(self) -> None:
        """ -- other parallel stories' results must still be processed on failure."""
        content = get_content()
        step5 = _get_step5_text(content)
        assert "still processed" in step5 or "other" in step5, (
            "SKILL.md STEP 5 must document that other stories' results are still processed "
            "even when one story's result is missing"
        )


def _get_step2_text(content: str) -> str:
    """Extract STEP 2 section text (up to STEP 3)."""
    start = content.find("## STEP 2:")
    if start == -1:
        return ""
    end = content.find("\n## STEP 3:", start)
    return content[start:end] if end != -1 else content[start:]


def _get_step6_text(content: str) -> str:
    """Extract STEP 6 section text (up to next ## section or end of file)."""
    start = content.find("## STEP 6:")
    if start == -1:
        return ""
    end = content.find("\n## ", start + 4)
    return content[start:end] if end != -1 else content[start:]


class TestSprintEndRegressionGate:
    """Verify STEP 6 contains sprint-end full regression gate."""

    def test_r_p1_05_step6_contains_sprint_end_gate(self) -> None:
        """ -- STEP 6 must contain sprint-end regression gate."""
        content = get_content()
        step6 = _get_step6_text(content)
        assert "sprint-end" in step6.lower() or "Sprint-end" in step6, (
            "SKILL.md STEP 6 must contain a sprint-end regression gate"
        )

    def test_r_p1_05_step6_reads_full_tier(self) -> None:
        """ -- STEP 6 sprint-end gate reads regression_tiers.full.cmd."""
        content = get_content()
        step6 = _get_step6_text(content)
        assert "regression_tiers" in step6 and "full" in step6, (
            "SKILL.md STEP 6 must reference regression_tiers.full.cmd for sprint-end gate"
        )

    def test_r_p1_05_step6_runs_before_pr_creation(self) -> None:
        """ -- sprint-end gate must appear before PR creation in STEP 6."""
        content = get_content()
        step6 = _get_step6_text(content)
        # Gate should appear before "Create Pull Request"
        gate_pos = step6.lower().find("sprint-end")
        pr_pos = step6.lower().find("create pull request")
        assert gate_pos != -1, "sprint-end gate not found in STEP 6"
        assert pr_pos != -1, "PR creation not found in STEP 6"
        assert gate_pos < pr_pos, (
            "Sprint-end regression gate must appear before PR creation in STEP 6"
        )


class TestPhaseBoundaryDetection:
    """Verify STEP 2 contains phase-boundary detection."""

    def test_r_p1_06_step2_contains_phase_boundary_detection(self) -> None:
        """ -- STEP 2 must contain phase-boundary detection."""
        content = get_content()
        step2 = _get_step2_text(content)
        assert (
            "phase" in step2
            and "boundary" in step2.lower()
            or "phase-boundary" in step2
        ), "SKILL.md STEP 2 must contain phase-boundary detection logic"

    def test_r_p1_06_step2_compares_next_story_phase(self) -> None:
        """ -- STEP 2 must compare next_story.phase against previous phase."""
        content = get_content()
        step2 = _get_step2_text(content)
        assert (
            "next_story" in step2 or "next story" in step2.lower() or "phase" in step2
        ), (
            "SKILL.md STEP 2 must reference comparing next story's phase for boundary detection"
        )

    def test_r_p1_06_step2_runs_unit_tier_on_transition(self) -> None:
        """ -- STEP 2 must run unit tier regression on phase transition."""
        content = get_content()
        step2 = _get_step2_text(content)
        assert "unit" in step2, (
            "SKILL.md STEP 2 phase-boundary detection must reference running unit tier regression"
        )

    def test_r_p1_06_step2_reads_regression_tiers_unit_cmd(self) -> None:
        """ -- STEP 2 reads regression_tiers.unit.cmd from workflow.json."""
        content = get_content()
        step2 = _get_step2_text(content)
        assert "regression_tiers" in step2, (
            "SKILL.md STEP 2 must reference regression_tiers for phase-boundary gate"
        )


def _get_plan_skill_content() -> str:
    """Read the plan/SKILL.md file content."""
    return PLAN_SKILL_FILE.read_text(encoding="utf-8")


def _get_plan_step7a_text(content: str) -> str:
    """Extract Step 7a section text from plan/SKILL.md."""
    # Look for "7a." section header
    start = content.find("#### 7a.")
    if start == -1:
        return ""
    # Find next section at same or higher level
    end = content.find("\n#### 7b.", start)
    if end == -1:
        end = content.find("\n### 8.", start)
    return content[start:end] if end != -1 else content[start:]


class TestPlanSkillScopeInference:
    """Verify plan/SKILL.md Step 7a contains scope inference logic."""

    def test_r_p3_09_plan_skill_exists(self) -> None:
        """ -- plan/SKILL.md must exist at expected path."""
        assert PLAN_SKILL_FILE.exists(), (
            "plan/SKILL.md must exist at .claude/skills/plan/SKILL.md"
        )

    def test_r_p3_09_step7a_contains_scope_inference(self) -> None:
        """ -- Step 7a must contain scope inference logic."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        assert "scope" in step7a, (
            "plan/SKILL.md Step 7a must contain scope inference logic"
        )

    def test_r_p3_09_step7a_extracts_directories_from_changes_table(self) -> None:
        """ -- Step 7a must extract directories from Changes table files."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        assert "Changes table" in step7a or "Changes" in step7a, (
            "plan/SKILL.md Step 7a scope inference must reference extracting directories "
            "from the Changes table"
        )

    def test_r_p3_09_step7a_populates_scope_field(self) -> None:
        """ -- Step 7a must populate scope field per story."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        assert "story.scope" in step7a or "scope[]" in step7a or "scope:" in step7a, (
            "plan/SKILL.md Step 7a must describe populating story.scope field"
        )


class TestPlanSkillComplexityEstimation:
    """Verify plan/SKILL.md Step 7a contains complexity estimation logic."""

    def test_r_p3_10_step7a_contains_complexity_estimation(self) -> None:
        """ -- Step 7a must contain complexity estimation."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        assert "complexity" in step7a.lower(), (
            "plan/SKILL.md Step 7a must contain complexity estimation logic"
        )

    def test_r_p3_10_step7a_uses_file_count_in_score(self) -> None:
        """ -- complexity score must include file/scope count."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        # Score should reference scope (directory count) or file count
        assert "len(scope)" in step7a or "directories" in step7a, (
            "plan/SKILL.md Step 7a complexity estimation must compute score from "
            "file/scope count"
        )

    def test_r_p3_10_step7a_uses_criteria_count_in_score(self) -> None:
        """ -- complexity score must include criteria count."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        assert "acceptanceCriteria" in step7a or "criteria" in step7a, (
            "plan/SKILL.md Step 7a complexity estimation must reference criteria count "
            "in score computation"
        )

    def test_r_p3_10_step7a_uses_cross_package_detection(self) -> None:
        """ -- complexity score must use cross-package detection."""
        content = _get_plan_skill_content()
        step7a = _get_plan_step7a_text(content)
        step7a_lower = step7a.lower()
        assert "cross-package" in step7a_lower or "cross_package" in step7a_lower, (
            "plan/SKILL.md Step 7a complexity estimation must include cross-package detection"
        )


# ---------------------------------------------------------------------------
# Enforcement Matrix tests (Phase 4 — R-P4-01 through R-P4-05)
# ---------------------------------------------------------------------------

ARCH_FILE = Path(__file__).parent.parent.parent / "docs" / "ARCHITECTURE.md"


def _get_arch_content() -> str:
    """Read ARCHITECTURE.md content."""
    return ARCH_FILE.read_text(encoding="utf-8")


class TestEnforcementMatrixExists:
    """R-P4-01: ARCHITECTURE.md contains an Enforcement Matrix section with a table."""

    def test_enforcement_section_exists(self) -> None:
        """R-P4-01 — ARCHITECTURE.md must have ## Enforcement Matrix heading."""
        content = _get_arch_content()
        assert "## Enforcement Matrix" in content, (
            "ARCHITECTURE.md must contain a '## Enforcement Matrix' section"
        )

    def test_enforcement_section_has_table(self) -> None:
        """R-P4-01 — Enforcement Matrix section must contain a markdown table."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1, "Enforcement Matrix section not found"
        section = content[start:]
        next_h2 = section.find("\n## ", 4)
        if next_h2 != -1:
            section = section[:next_h2]
        # A markdown table has pipe-delimited rows and a separator row
        assert "|" in section, "Enforcement Matrix must contain a markdown table"
        assert "---" in section, "Enforcement Matrix table must have a separator row"


class TestEnforcementHookDetectors:
    """R-P4-02: Matrix has rows for hook detectors."""

    def test_enforcement_pre_bash_guard(self) -> None:
        """R-P4-02 — pre_bash_guard must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "pre_bash_guard" in section

    def test_enforcement_post_write_prod_scan(self) -> None:
        """R-P4-02 — post_write_prod_scan must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "post_write_prod_scan" in section

    def test_enforcement_post_format(self) -> None:
        """R-P4-02 — post_format must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "post_format" in section

    def test_enforcement_stop_verify_gate(self) -> None:
        """R-P4-02 — stop_verify_gate must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "stop_verify_gate" in section


class TestEnforcementQADetectors:
    """R-P4-03: Matrix has rows for QA step detectors."""

    def test_enforcement_mock_audit(self) -> None:
        """R-P4-03 — mock_audit must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "mock_audit" in section

    def test_enforcement_assertion_check(self) -> None:
        """R-P4-03 — assertion_check must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "assertion_check" in section

    def test_enforcement_heavy_mock(self) -> None:
        """R-P4-03 — heavy_mock must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "heavy_mock" in section

    def test_enforcement_negative_test(self) -> None:
        """R-P4-03 — negative_test must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "negative_test" in section

    def test_enforcement_happy_path_only(self) -> None:
        """R-P4-03 — happy_path_only must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "happy_path_only" in section


class TestEnforcementPlanValidation:
    """R-P4-04: Matrix has rows for plan validation detectors."""

    def test_enforcement_vague_criteria(self) -> None:
        """R-P4-04 — vague_criteria must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "vague_criteria" in section

    def test_enforcement_r_id_format(self) -> None:
        """R-P4-04 — r_id_format must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "r_id_format" in section

    def test_enforcement_test_file_coverage(self) -> None:
        """R-P4-04 — test_file_coverage must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "test_file_coverage" in section

    def test_enforcement_placeholder_commands(self) -> None:
        """R-P4-04 — placeholder_commands must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "placeholder_commands" in section


class TestEnforcementProdScanPatterns:
    """R-P4-05: Matrix has rows for production scan patterns."""

    def test_enforcement_hardcoded_secret(self) -> None:
        """R-P4-05 — hardcoded-secret must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "hardcoded-secret" in section

    def test_enforcement_sql_injection(self) -> None:
        """R-P4-05 — sql-injection must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "sql-injection" in section

    def test_enforcement_shell_injection(self) -> None:
        """R-P4-05 — shell-injection must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "shell-injection" in section

    def test_enforcement_debug_print(self) -> None:
        """R-P4-05 — debug-print must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "debug-print" in section

    def test_enforcement_bare_except(self) -> None:
        """R-P4-05 — bare-except must appear in the enforcement matrix."""
        content = _get_arch_content()
        start = content.find("## Enforcement Matrix")
        assert start != -1
        section = content[start:]
        assert "bare-except" in section
