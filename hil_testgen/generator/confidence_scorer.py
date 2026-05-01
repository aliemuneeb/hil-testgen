"""
Confidence scorer — rates how reliable each generated test case is.
Based on how complete the original requirement was.
"""


class ConfidenceScorer:
    """
    Scores generated test cases based on input requirement quality.

    Levels:
        HIGH    → 80-100%  requirement was complete and explicit
        REVIEW  → 50-79%   some fields were missing or vague  
        LOW     → 0-49%    significant information was missing
    """

    def score(self, req: dict, test_case: dict) -> dict:
        """
        Score a generated test case.

        Returns:
            {
                "level" : "HIGH" | "REVIEW" | "LOW",
                "score" : 0-100,
                "notes" : "human readable explanation"
            }
        """
        score  = 0
        notes  = []

        # ── Check requirement completeness ───────────────────────────────

        # Objective present and substantial
        objective = req.get("objective", "")
        if objective and len(objective.split()) >= 5:
            score += 25
        elif objective:
            score += 10
            notes.append("Objective is brief")
        else:
            notes.append("Objective was missing")

        # Test method present and substantial
        method = req.get("test_method", "")
        if method and len(method.split()) >= 5:
            score += 25
        elif method:
            score += 10
            notes.append("Test method is brief")
        else:
            notes.append("Test method was missing")

        # Pass criteria present
        criteria = req.get("pass_criteria", "")
        if criteria and len(criteria.split()) >= 3:
            score += 30
        elif criteria:
            score += 15
            notes.append("Pass criteria is vague")
        else:
            notes.append("Pass criteria was missing — AI inferred threshold")

        # ── Check test case quality ──────────────────────────────────────

        # Numeric values present in pass criteria
        import re
        tc_criteria = test_case.get("pass_criteria", "")
        if re.search(r'\d+\.?\d*', tc_criteria):
            score += 10
        else:
            notes.append("No numeric threshold in pass criteria")

        # Input signals specified
        inputs = test_case.get("input_signals", "")
        if inputs and inputs != "Not specified in requirement":
            score += 10
        else:
            notes.append("Input signals not explicitly specified")

        # ── Determine level ──────────────────────────────────────────────
        score = min(score, 100)  # cap at 100

        if score >= 80:
            level = "HIGH"
        elif score >= 50:
            level = "REVIEW"
        else:
            level = "LOW"

        # Build notes string
        if not notes:
            notes_str = "Requirement was complete — high confidence output"
        else:
            notes_str = " | ".join(notes)

        return {
            "level" : level,
            "score" : score,
            "notes" : notes_str,
        }
