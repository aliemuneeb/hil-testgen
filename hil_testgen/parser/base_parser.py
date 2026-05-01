"""
Base parser — all parsers inherit from this.
Defines the shared interface and common utilities.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """
    Abstract base class for all requirement parsers.
    
    Every parser (docx, excel, pdf) must:
    1. Accept a file path
    2. Implement parse() 
    3. Return a list of requirement dicts
    
    Each requirement dict looks like:
    {
        "id"          : "HIL-RQ1",
        "objective"   : "Verify correct initialization...",
        "test_method" : "Load known values for Const_Offset...",
        "pass_criteria": "Output GPS coordinates match within ±0.00001°",
        "raw_text"    : "full original text of requirement"
    }
    """

    def __init__(self, file_path: Path, verbose: bool = False):
        self.file_path = Path(file_path)
        self.verbose   = verbose

    @abstractmethod
    def parse(self) -> list[dict]:
        """
        Parse the requirements document.
        Returns list of requirement dicts.
        Must be implemented by every subclass.
        """
        pass

    # ── Shared utilities available to all parsers ───────────────────────

    def _clean(self, text: str) -> str:
        """Strip whitespace and normalize text."""
        if not text:
            return ""
        return " ".join(text.strip().split())

    def _is_requirement_id(self, text: str) -> bool:
        """
        Detect if a line looks like a requirement ID.
        Matches patterns like:
          HIL-RQ1, SIL-RQ2, MIL-RQ10, RQ-001, REQ-004
        """
        import re
        pattern = r'^(HIL|SIL|MIL|PIL|RQ|REQ)[-_]?(RQ)?[-_]?\d+$'
        return bool(re.match(pattern, text.strip(), re.IGNORECASE))

    def _validate_requirement(self, req: dict) -> tuple[bool, str, str]:
        """
        Check if a parsed requirement has enough info to generate a test case.

        Returns:
            (is_valid, reason, missing)
            
            is_valid → True if we can generate a test case
            reason   → why it was skipped (if invalid)
            missing  → what specific field is missing
        """
        req_id = req.get("id", "UNKNOWN")

        if not req.get("objective"):
            return (
                False,
                "Objective not found",
                "Add an 'Objective' section to this requirement"
            )

        if not req.get("test_method"):
            return (
                False,
                "Test method incomplete",
                "Add a 'Test Method' section describing inputs and steps"
            )

        if not req.get("pass_criteria"):
            return (
                False,
                "Pass criteria not found",
                "Add a 'Pass Criteria' section with measurable threshold"
            )

        # Minimum content check — avoid empty or one-word fields
        if len(req.get("objective", "").split()) < 3:
            return (
                False,
                "Objective too vague",
                "Objective needs more detail (at least a full sentence)"
            )

        return (True, "", "")

    def _log(self, message: str):
        """Print only if verbose mode is on."""
        if self.verbose:
            print(f"  [parser] {message}")
