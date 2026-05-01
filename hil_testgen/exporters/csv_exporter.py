"""
CSV exporter — simple flat file export.
One row per test case.
"""
from __future__ import annotations
import csv
from pathlib import Path


class CsvExporter:
    """Exports test cases to CSV format."""

    FIELDS = [
        "tc_id", "req_id", "title", "objective",
        "preconditions", "input_signals", "test_steps",
        "expected_output", "pass_criteria", "fail_criteria",
        "priority", "test_type", "confidence",
        "confidence_score", "notes", "confidence_notes",
    ]

    def __init__(
        self,
        test_cases : list,
        skipped    : list,
        output_path: Path
    ):
        self.test_cases  = test_cases
        self.skipped     = skipped
        self.output_path = output_path

    def export(self):
        """Write test cases to CSV."""
        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self.FIELDS,
                extrasaction="ignore"
            )
            writer.writeheader()

            for tc in self.test_cases:
                writer.writerow(tc)

        # Also write skipped to a separate file
        if self.skipped:
            skip_path = self.output_path.parent / (
                self.output_path.stem + "_skipped.csv"
            )
            with open(skip_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["req_id", "reason", "missing"],
                    extrasaction="ignore"
                )
                writer.writeheader()
                for skip in self.skipped:
                    writer.writerow(skip)
