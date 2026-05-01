"""
DOCX parser — extracts requirements from Word documents.
Handles the most common HIL requirements format.
"""
from __future__ import annotations
from pathlib import Path
from docx import Document
from hil_testgen.parser.base_parser import BaseParser


class DocxParser(BaseParser):
    """
    Parses .docx requirements documents.

    Supports two common formats:

    Format A — Heading + bullet points (like your GPS doc):
        HIL-RQ1: System Initialization
        • Objective: Verify correct initialization...
        • Test Method: Load known values...
        • Pass Criteria: Output matches within ±0.00001°

    Format B — Bold labels inline:
        HIL-RQ1
        Objective: Verify correct initialization...
        Test Method: Load known values...
        Pass Criteria: Output matches within ±0.00001°
    """

    # Keywords we look for when extracting fields
    OBJECTIVE_KEYS    = ["objective"]
    TEST_METHOD_KEYS  = ["test method", "test procedure", "method", "procedure"]
    PASS_CRITERIA_KEYS = ["pass criteria", "pass/fail", "acceptance criteria",
                          "expected result", "expected output", "criteria"]

    def parse(self) -> list[dict]:
        """
        Parse the Word document and return list of requirement dicts.
        """
        self._log(f"Opening {self.file_path.name}")
        doc = Document(self.file_path)

        requirements = []
        current_req  = None

        for para in doc.paragraphs:
            text = self._clean(para.text)

            if not text:
                continue

            # ── Detect requirement heading ───────────────────────────────
            if self._is_requirement_heading(para, text):
                # Save previous requirement before starting new one
                if current_req:
                    req = self._finalise(current_req)
                    if req:
                        requirements.append(req)

                req_id = self._extract_id(text)
                self._log(f"Found requirement: {req_id}")

                current_req = {
                    "id"           : req_id,
                    "title"        : text,
                    "objective"    : "",
                    "test_method"  : "",
                    "pass_criteria": "",
                    "raw_text"     : text + "\n",
                    "_current_field": None
                }
                continue

            # ── If we're inside a requirement, extract fields ────────────
            if current_req is not None:
                current_req["raw_text"] += text + "\n"
                self._extract_field(current_req, text)

        # Don't forget the last requirement
        if current_req:
            req = self._finalise(current_req)
            if req:
                requirements.append(req)

        self._log(f"Parsed {len(requirements)} requirements")
        return requirements

    # ── Private helpers ──────────────────────────────────────────────────

    def _is_requirement_heading(self, para, text: str) -> bool:
        """
        Detect if this paragraph is a requirement heading.
        Checks:
          1. Paragraph style is a Heading
          2. Text starts with a known requirement ID pattern
          3. Text is bold
        """
        # Check heading style
        if para.style and "heading" in para.style.name.lower():
            return True

        # Check if text starts with requirement ID pattern
        # e.g. "HIL-RQ1:", "HIL-RQ1 -", "HIL-RQ1 System..."
        import re
        if re.match(r'^(HIL|SIL|MIL|PIL|RQ|REQ)[-_]?(RQ)?[-_]?\d+', 
                    text, re.IGNORECASE):
            return True

        # Check if entire paragraph is bold
        if para.runs and all(run.bold for run in para.runs if run.text.strip()):
            if re.match(r'^(HIL|SIL|MIL|PIL|RQ|REQ)', text, re.IGNORECASE):
                return True

        return False

    def _extract_id(self, text: str) -> str:
        """
        Pull requirement ID from heading text.
        'HIL-RQ1: System Initialization' → 'HIL-RQ1'
        """
        import re
        match = re.match(
            r'^((?:HIL|SIL|MIL|PIL|RQ|REQ)[-_]?(?:RQ)?[-_]?\d+)',
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).upper()
        # Fallback — use first word
        return text.split()[0].upper()

    def _extract_field(self, req: dict, text: str):
        """
        Detect which field this line belongs to and append to it.
        Handles both 'Label: value' and continuation lines.
        """
        lower = text.lower()

        # Check if this line starts a known field
        for key in self.OBJECTIVE_KEYS:
            if lower.startswith(key):
                req["_current_field"] = "objective"
                value = self._after_colon(text)
                if value:
                    req["objective"] += value + " "
                return

        for key in self.TEST_METHOD_KEYS:
            if lower.startswith(key):
                req["_current_field"] = "test_method"
                value = self._after_colon(text)
                if value:
                    req["test_method"] += value + " "
                return

        for key in self.PASS_CRITERIA_KEYS:
            if lower.startswith(key):
                req["_current_field"] = "pass_criteria"
                value = self._after_colon(text)
                if value:
                    req["pass_criteria"] += value + " "
                return

        # Continuation line — append to whatever field we're in
        if req.get("_current_field"):
            field = req["_current_field"]
            req[field] += text + " "

    def _after_colon(self, text: str) -> str:
        """
        Extract value after colon.
        'Objective: Verify initialization' → 'Verify initialization'
        'Objective' → ''
        """
        if ":" in text:
            return self._clean(text.split(":", 1)[1])
        return ""

    def _finalise(self, req: dict) -> dict | None:
        """
        Clean up and validate a completed requirement.
        Returns None if requirement should be skipped.
        """
        # Remove internal tracking field
        req.pop("_current_field", None)

        # Clean all fields
        req["objective"]     = self._clean(req.get("objective", ""))
        req["test_method"]   = self._clean(req.get("test_method", ""))
        req["pass_criteria"] = self._clean(req.get("pass_criteria", ""))

        # Validate
        is_valid, reason, missing = self._validate_requirement(req)

        if not is_valid:
            self._log(f"Skipping {req['id']}: {reason}")
            req["status"]  = "skipped"
            req["reason"]  = reason
            req["missing"] = missing
        else:
            req["status"] = "ok"

        return req
