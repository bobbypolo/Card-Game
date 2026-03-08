"""Audit section resolution for the /audit skill.

This module is the authoritative source for which sections each audit mode runs.
The audit/SKILL.md calls get_audit_sections() and does not re-express the logic
inline — keeping section selection in executable Python and out of markdown prose.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import AuditMode

# Authoritative section filter map — edit here, not in SKILL.md.
_SECTION_MAP: dict[AuditMode, list[int]] = {
    AuditMode.QUICK: [1, 2, 6],
    AuditMode.DELIVERY: [1, 2, 3, 4],
    AuditMode.FULL: list(range(1, 10)),
}


def get_audit_sections(mode: AuditMode) -> list[int]:
    """Return the ordered list of section numbers to run for *mode*.

    Parameters
    ----------
    mode:
        A resolved AuditMode enum value.  If an unexpected value is received
        (should not happen given AuditMode.resolve() always returns a valid
        member), the function falls back to FULL and logs a warning.

    Returns
    -------
    list[int]
        Ordered section numbers.  QUICK -> [1, 2, 6], DELIVERY -> [1, 2, 3, 4],
        FULL -> [1, 2, 3, 4, 5, 6, 7, 8, 9].
    """
    if mode not in _SECTION_MAP:
        warnings.warn(f"Unknown mode '{mode}' — defaulting to full", stacklevel=2)
        return list(range(1, 10))  # fallback: all sections
    return _SECTION_MAP[mode]
