"""
Excel + CSV parser — extracts requirements from .xlsx and .csv files.
Handles tabular requirement formats common in smaller teams.

Supported layouts:

Layout A — named columns (most common):
    | ID      | Objective | Test Method | Pass Criteria |
    | HIL-RQ1 | Verify... | Load known  | Within ±0.001 |

Layout B — single requirement per row with free-form text:
    | Requirement ID | Description                        |
    | HIL-RQ1        | Objective: ... Test Method: ...    |

Layout C — vertical/stacked (less common):
    | Field         | Value                  |
    | ID            | HIL-RQ1                |
    | Objective     | Verify initialization  |
    | Test Method   | Load known values...   |
    | Pass Criteria | Within ±0.00001°       |
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from hil_testgen.parser.base_parser import BaseParser


class ExcelParser(BaseParser):
    """
    Parses .xlsx and .csv requirements documents.
    Auto-detects column layout and extracts requirements.
    """

    # Column name aliases we look for
    ID_COLS = [
        "id", "req id", "requirement id", "req_id",
        "requirement", "no", "number", "#"
    ]
    OBJECTIVE_COLS = [
        "objective", "description", "goal", "purpose"
    ]
    TEST_METHOD_COLS = [
        "test method", "test procedure", "method",
        "procedure", "steps", "test_method"
    ]
    PASS_CRITERIA_COLS = [
        "pass criteria", "pass/fail criteria", "acceptance criteria",
        "expected result", "expected output", "criteria", "pass_criteria"
    ]

    def parse(self) -> list[dict]:
        """
        Parse Excel or CSV file and return list of requirement dicts.
        """
        self._log(f"Opening {self.file_path.name}")

        # ── Load file ────────────────────────────────────────────────────
        try:
            if self.file_path.suffix.lower() == ".csv":
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)
        except Exception as e:
            raise ValueError(
                f"Could not read {self.file_path.name}.\n"
                f"If this is a protected or legacy .xls file, "
                f"please save as .xlsx and try again.\n"
                f"Error: {e}"
            )

        # Clean column names — lowercase, strip whitespace
        df.columns = [str(c).lower().strip() for c in df.columns]
        self._log(f"Columns found: {list(df.columns)}")

        # ── Detect layout ────────────────────────────────────────────────
        layout = self._detect_layout(df)
        self._log(f"Detected layout: {layout}")

        if layout == "A":
            return self._parse_layout_a(df)
        elif layout == "C":
            return self._parse_layout_c(df)
        else:
            # Layout B — try best effort on description column
            return self._parse_layout_b(df)

    # ── Layout detection ─────────────────────────────────────────────────

    def _detect_layout(self, df: pd.DataFrame) -> str:
        """
        Detect which layout the spreadsheet uses.
        """
        cols = set(df.columns)

        # Layout A — has dedicated columns for each field
        has_objective = any(c in cols for c in self.OBJECTIVE_COLS)
        has_method    = any(c in cols for c in self.TEST_METHOD_COLS)
        has_criteria  = any(c in cols for c in self.PASS_CRITERIA_COLS)

        if has_objective and (has_method or has_criteria):
            return "A"

        # Layout C — vertical key/value pairs
        # Usually has exactly 2 columns like "Field" and "Value"
        if len(df.columns) == 2:
            first_col_values = df.iloc[:, 0].astype(str).str.lower().tolist()
            vertical_keys = ["objective", "test method", "pass criteria", "id"]
            matches = sum(1 for v in first_col_values if any(k in v for k in vertical_keys))
            if matches >= 2:
                return "C"

        # Default — Layout B
        return "B"

    # ── Layout A parser ──────────────────────────────────────────────────

    def _parse_layout_a(self, df: pd.DataFrame) -> list[dict]:
        """
        Parse tabular layout with named columns.
        Most common format for structured requirement sheets.
        """
        requirements = []

        id_col        = self._find_col(df, self.ID_COLS)
        obj_col       = self._find_col(df, self.OBJECTIVE_COLS)
        method_col    = self._find_col(df, self.TEST_METHOD_COLS)
        criteria_col  = self._find_col(df, self.PASS_CRITERIA_COLS)

        for idx, row in df.iterrows():
            # Skip empty rows
            if row.isnull().all():
                continue

            req_id = self._clean(str(row[id_col])) if id_col else f"REQ-{idx+1}"

            # Skip header-like rows that snuck into data
            if req_id.lower() in ["id", "req id", "nan", ""]:
                continue

            req = {
                "id"           : req_id.upper(),
                "title"        : req_id,
                "objective"    : self._clean(str(row[obj_col]))    if obj_col    else "",
                "test_method"  : self._clean(str(row[method_col])) if method_col else "",
                "pass_criteria": self._clean(str(row[criteria_col])) if criteria_col else "",
                "raw_text"     : " | ".join(str(v) for v in row.values if pd.notna(v)),
            }

            # Clean "nan" strings from pandas
            req = self._clean_nans(req)

            is_valid, reason, missing = self._validate_requirement(req)
            req["status"]  = "ok" if is_valid else "skipped"
            req["reason"]  = reason
            req["missing"] = missing

            requirements.append(req)
            self._log(f"Parsed row {idx}: {req_id} → {req['status']}")

        return requirements

    # ── Layout B parser ──────────────────────────────────────────────────

    def _parse_layout_b(self, df: pd.DataFrame) -> list[dict]:
        """
        Parse free-form description column.
        Falls back to treating entire row as raw text
        and letting AI engine extract structure.
        """
        requirements = []

        id_col = self._find_col(df, self.ID_COLS)

        for idx, row in df.iterrows():
            if row.isnull().all():
                continue

            req_id   = self._clean(str(row[id_col])) if id_col else f"REQ-{idx+1}"
            raw_text = " ".join(str(v) for v in row.values if pd.notna(v))

            if not raw_text.strip() or req_id.lower() in ["nan", ""]:
                continue

            req = {
                "id"           : req_id.upper(),
                "title"        : req_id,
                "objective"    : "",
                "test_method"  : "",
                "pass_criteria": "",
                "raw_text"     : raw_text,
                "status"       : "ok",
                "reason"       : "",
                "missing"      : "",
            }

            requirements.append(req)

        return requirements

    # ── Layout C parser ──────────────────────────────────────────────────

    def _parse_layout_c(self, df: pd.DataFrame) -> list[dict]:
        """
        Parse vertical key/value layout.
        Groups rows into requirements by ID field.
        """
        requirements = []
        current_req  = None

        for _, row in df.iterrows():
            field = self._clean(str(row.iloc[0])).lower()
            value = self._clean(str(row.iloc[1])) if len(row) > 1 else ""

            if not field or field == "nan":
                continue

            # New requirement starts when we see an ID field
            if any(k in field for k in ["id", "requirement id", "req id"]):
                if current_req:
                    is_valid, reason, missing = self._validate_requirement(current_req)
                    current_req["status"]  = "ok" if is_valid else "skipped"
                    current_req["reason"]  = reason
                    current_req["missing"] = missing
                    requirements.append(current_req)

                current_req = {
                    "id"           : value.upper(),
                    "title"        : value,
                    "objective"    : "",
                    "test_method"  : "",
                    "pass_criteria": "",
                    "raw_text"     : f"ID: {value}\n",
                    "status"       : "ok",
                    "reason"       : "",
                    "missing"      : "",
                }
                continue

            if current_req:
                current_req["raw_text"] += f"{field}: {value}\n"

                if any(k in field for k in self.OBJECTIVE_COLS):
                    current_req["objective"] += value + " "

                elif any(k in field for k in self.TEST_METHOD_COLS):
                    current_req["test_method"] += value + " "

                elif any(k in field for k in self.PASS_CRITERIA_COLS):
                    current_req["pass_criteria"] += value + " "

        # Last requirement
        if current_req:
            is_valid, reason, missing = self._validate_requirement(current_req)
            current_req["status"]  = "ok" if is_valid else "skipped"
            current_req["reason"]  = reason
            current_req["missing"] = missing
            requirements.append(current_req)

        return requirements

    # ── Utilities ────────────────────────────────────────────────────────

    def _find_col(self, df: pd.DataFrame, aliases: list) -> str | None:
        """Find the first column name that matches any alias."""
        for col in df.columns:
            for alias in aliases:
                if alias in col:
                    return col
        return None

    def _clean_nans(self, req: dict) -> dict:
        """Replace pandas 'nan' strings with empty string."""
        for key in ["objective", "test_method", "pass_criteria"]:
            if req.get(key, "").lower() == "nan":
                req[key] = ""
        return req
