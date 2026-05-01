"""
PDF parser — best effort extraction from PDF requirements documents.

IMPORTANT: PDF extraction is inherently imperfect.
If you get poor results, convert your PDF to .docx first:
  - Word: File → Save As → .docx
  - Online: smallpdf.com, ilovepdf.com
  - Or simply copy/paste content into a Word doc
"""
from __future__ import annotations
import re
from pathlib import Path
from hil_testgen.parser.base_parser import BaseParser


class PdfParser(BaseParser):
    """
    Parses PDF requirements documents using pdfplumber.

    Works well for:
      ✅ Text-based PDFs (digitally created)
      ✅ PDFs exported from Word
      ✅ PDFs with clear section structure

    Works poorly for:
      ❌ Scanned PDFs (images of paper)
      ❌ Password protected PDFs
      ❌ PDFs with complex multi-column layouts
      ❌ PDFs with requirements inside images/diagrams
    """

    OBJECTIVE_KEYS     = ["objective"]
    TEST_METHOD_KEYS   = ["test method", "test procedure", "method", "procedure"]
    PASS_CRITERIA_KEYS = ["pass criteria", "pass/fail", "acceptance criteria",
                          "expected result", "expected output", "criteria"]

    def parse(self) -> list[dict]:
        """
        Parse PDF and return list of requirement dicts.
        """
        self._log(f"Opening {self.file_path.name}")

        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber not installed.\n"
                "Run: pip install pdfplumber"
            )

        # ── Extract all text from PDF ────────────────────────────────────
        full_text = ""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                self._log(f"PDF has {len(pdf.pages)} pages")

                if not pdf.pages:
                    raise ValueError("PDF has no readable pages.")

                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                    else:
                        self._log(f"Page {i+1}: no text extracted (possibly scanned)")

        except Exception as e:
            # Friendly error with disclaimer
            raise ValueError(
                f"Could not read PDF: {self.file_path.name}\n\n"
                f"This may be because:\n"
                f"  • The PDF is scanned (image-based, not text-based)\n"
                f"  • The PDF is password protected\n"
                f"  • The PDF has an unsupported layout\n\n"
                f"Please convert to .docx and try again.\n"
                f"Error: {e}"
            )

        if not full_text.strip():
            raise ValueError(
                f"No text could be extracted from {self.file_path.name}.\n"
                f"This is likely a scanned PDF.\n"
                f"Please convert to .docx and try again."
            )

        self._log(f"Extracted {len(full_text)} characters from PDF")

        # ── Parse extracted text into requirements ───────────────────────
        requirements = self._parse_text(full_text)
        self._log(f"Found {len(requirements)} requirements")

        return requirements

    # ── Text parsing ─────────────────────────────────────────────────────

    def _parse_text(self, text: str) -> list[dict]:
        """
        Split raw text into individual requirements
        and extract fields from each.
        """
        requirements = []

        # Split text into lines
        lines = [self._clean(line) for line in text.splitlines()]
        lines = [l for l in lines if l]  # remove empty lines

        current_req     = None
        current_field   = None

        for line in lines:
            # ── Detect requirement heading ───────────────────────────────
            if self._is_req_line(line):
                # Save previous requirement
                if current_req:
                    req = self._finalise(current_req)
                    if req:
                        requirements.append(req)

                req_id = self._extract_id_from_line(line)
                self._log(f"Found requirement: {req_id}")

                current_req = {
                    "id"           : req_id,
                    "title"        : line,
                    "objective"    : "",
                    "test_method"  : "",
                    "pass_criteria": "",
                    "raw_text"     : line + "\n",
                    "_current_field": None,
                }
                current_field = None
                continue

            # ── Extract fields from requirement body ─────────────────────
            if current_req is not None:
                current_req["raw_text"] += line + "\n"
                current_field = self._extract_field(
                    current_req, line, current_field
                )

        # Last requirement
        if current_req:
            req = self._finalise(current_req)
            if req:
                requirements.append(req)

        return requirements

    def _is_req_line(self, text: str) -> bool:
        """
        Detect if a line is a requirement heading.
        Matches: HIL-RQ1, SIL-RQ2:, MIL-RQ10 - Title etc.
        """
        pattern = r'^(HIL|SIL|MIL|PIL|RQ|REQ)[-_]?(RQ)?[-_]?\d+'
        return bool(re.match(pattern, text, re.IGNORECASE))

    def _extract_id_from_line(self, text: str) -> str:
        """
        Extract requirement ID from heading line.
        'HIL-RQ1: System Initialization' → 'HIL-RQ1'
        """
        match = re.match(
            r'^((?:HIL|SIL|MIL|PIL|RQ|REQ)[-_]?(?:RQ)?[-_]?\d+)',
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).upper()
        return text.split()[0].upper()

    def _extract_field(
        self,
        req: dict,
        line: str,
        current_field: str
    ) -> str:
        """
        Detect field label and extract value.
        Returns current active field name.
        """
        lower = line.lower()

        # Check for field label at start of line
        for key in self.OBJECTIVE_KEYS:
            if lower.startswith(key):
                value = self._after_colon(line)
                if value:
                    req["objective"] += value + " "
                return "objective"

        for key in self.TEST_METHOD_KEYS:
            if lower.startswith(key):
                value = self._after_colon(line)
                if value:
                    req["test_method"] += value + " "
                return "test_method"

        for key in self.PASS_CRITERIA_KEYS:
            if lower.startswith(key):
                value = self._after_colon(line)
                if value:
                    req["pass_criteria"] += value + " "
                return "pass_criteria"

        # Continuation line — append to current field
        if current_field and current_field in req:
            req[current_field] += line + " "

        return current_field

    def _after_colon(self, text: str) -> str:
        """
        Extract value after colon.
        'Objective: Verify initialization' → 'Verify initialization'
        """
        if ":" in text:
            return self._clean(text.split(":", 1)[1])
        return ""

    def _finalise(self, req: dict) -> dict | None:
        """
        Clean up and validate completed requirement.
        """
        req.pop("_current_field", None)

        req["objective"]     = self._clean(req.get("objective", ""))
        req["test_method"]   = self._clean(req.get("test_method", ""))
        req["pass_criteria"] = self._clean(req.get("pass_criteria", ""))

        is_valid, reason, missing = self._validate_requirement(req)

        if not is_valid:
            self._log(f"Skipping {req['id']}: {reason}")
            req["status"]  = "skipped"
            req["reason"]  = reason
            req["missing"] = missing
        else:
            req["status"] = "ok"

        return req
