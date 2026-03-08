"""Tests for _audit_lib.py — audit section resolution.

# Tests R-P3-01
# Tests R-P3-03
# Tests R-P3-04
# Tests R-P3-05
# Tests R-P3-06
# Tests R-P3-08
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import _audit_lib
from _audit_lib import get_audit_sections
from _lib import AuditMode


class TestGetAuditSectionsQuick:
    # Tests R-P3-03
    # Tests R-P3-08
    def test_quick_returns_1_2_6(self) -> None:
        result = get_audit_sections(AuditMode.QUICK)
        assert result == [1, 2, 6]

    def test_quick_excludes_non_structural_sections(self) -> None:
        result = get_audit_sections(AuditMode.QUICK)
        # QUICK omits sections 3-5, 7-9 (heavier analysis)
        assert 3 not in result
        assert 4 not in result
        assert 5 not in result
        assert 7 not in result

    def test_quick_ordered_ascending(self) -> None:
        result = get_audit_sections(AuditMode.QUICK)
        assert result == sorted(result)

    def test_quick_has_exactly_three_sections(self) -> None:
        result = get_audit_sections(AuditMode.QUICK)
        assert len(result) == 3


class TestGetAuditSectionsDelivery:
    # Tests R-P3-04
    # Tests R-P3-08
    def test_delivery_returns_1_2_3_4(self) -> None:
        result = get_audit_sections(AuditMode.DELIVERY)
        assert result == [1, 2, 3, 4]

    def test_delivery_excludes_git_hygiene_and_mock_audit(self) -> None:
        result = get_audit_sections(AuditMode.DELIVERY)
        # DELIVERY omits sections 5 (arch), 7 (git), 8 (mocks), 9 (error handling)
        assert 5 not in result
        assert 7 not in result
        assert 8 not in result
        assert 9 not in result

    def test_delivery_subset_of_full(self) -> None:
        full = get_audit_sections(AuditMode.FULL)
        delivery = get_audit_sections(AuditMode.DELIVERY)
        assert all(s in full for s in delivery)

    def test_delivery_has_exactly_four_sections(self) -> None:
        result = get_audit_sections(AuditMode.DELIVERY)
        assert len(result) == 4


class TestGetAuditSectionsFull:
    # Tests R-P3-05
    # Tests R-P3-08
    def test_full_returns_all_nine_sections(self) -> None:
        result = get_audit_sections(AuditMode.FULL)
        assert result == list(range(1, 10))

    def test_full_returns_exactly_1_through_9(self) -> None:
        result = get_audit_sections(AuditMode.FULL)
        assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_full_contains_nine_sections(self) -> None:
        result = get_audit_sections(AuditMode.FULL)
        assert len(result) == 9

    def test_full_is_superset_of_quick(self) -> None:
        full = get_audit_sections(AuditMode.FULL)
        quick = get_audit_sections(AuditMode.QUICK)
        assert all(s in full for s in quick)

    def test_full_is_superset_of_delivery(self) -> None:
        full = get_audit_sections(AuditMode.FULL)
        delivery = get_audit_sections(AuditMode.DELIVERY)
        assert all(s in full for s in delivery)


class TestGetAuditSectionsSignature:
    # Tests R-P3-01
    def test_all_modes_return_expected_sections(self) -> None:
        """get_audit_sections returns distinct, concrete section lists per mode."""
        assert get_audit_sections(AuditMode.QUICK) == [1, 2, 6]
        assert get_audit_sections(AuditMode.DELIVERY) == [1, 2, 3, 4]
        assert get_audit_sections(AuditMode.FULL) == list(range(1, 10))

    def test_all_sections_in_valid_range(self) -> None:
        for mode in AuditMode:
            result = get_audit_sections(mode)
            assert all(1 <= s <= 9 for s in result), (
                f"Mode {mode}: out-of-range section found in {result}"
            )

    def test_returned_lists_are_ordered(self) -> None:
        for mode in AuditMode:
            result = get_audit_sections(mode)
            assert result == sorted(result), (
                f"Mode {mode}: sections not ordered: {result}"
            )

    def test_modes_have_distinct_section_sets(self) -> None:
        quick = get_audit_sections(AuditMode.QUICK)
        delivery = get_audit_sections(AuditMode.DELIVERY)
        full = get_audit_sections(AuditMode.FULL)
        assert quick != delivery
        assert delivery != full
        assert quick != full


class TestGetAuditSectionsEdgeCases:
    # Tests R-P3-06 — unknown mode fallback via patched map
    def test_invalid_mode_emits_warning(self) -> None:
        """When _SECTION_MAP is missing an entry, a UserWarning is emitted."""
        with patch.object(_audit_lib, "_SECTION_MAP", {}):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _audit_lib.get_audit_sections(AuditMode.FULL)
            assert len(caught) >= 1
            warning_messages = [str(w.message) for w in caught]
            assert any("Unknown mode" in msg for msg in warning_messages)

    def test_invalid_mode_warning_message_contains_defaulting_to_full(self) -> None:
        """Warning message matches the required 'defaulting to full' text."""
        with patch.object(_audit_lib, "_SECTION_MAP", {}):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _audit_lib.get_audit_sections(AuditMode.QUICK)
            assert any("defaulting to full" in str(w.message) for w in caught)

    def test_error_if_audit_mode_missing_from_section_map(self) -> None:
        """Every AuditMode member has an entry in _SECTION_MAP."""
        for mode in AuditMode:
            assert mode in _audit_lib._SECTION_MAP, f"Missing entry for {mode}"
