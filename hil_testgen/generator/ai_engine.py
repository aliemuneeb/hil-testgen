"""
AI Engine — sends parsed requirements to Ollama
and gets back structured test cases.
100% local. No data leaves the machine.
"""

import json
import re
from hil_testgen.generator.confidence_scorer import ConfidenceScorer


class AIEngine:
    """
    Wraps Ollama local inference.
    Takes a requirement dict, returns a structured test case dict.
    """

    # The prompt template — this is the core of the tool
    PROMPT_TEMPLATE = """You are an expert HIL/SIL/MIL test engineer 
specializing in automotive ECU validation.

Your task is to generate a structured test case from the requirement below.

REQUIREMENT:
ID: {req_id}
Objective: {objective}
Test Method: {test_method}
Pass Criteria: {pass_criteria}

Generate a structured test case in this EXACT JSON format.
Return ONLY the JSON object. No explanation. No markdown. No extra text.

{{
    "tc_id": "TC_{req_id}_001",
    "req_id": "{req_id}",
    "title": "brief test case title",
    "objective": "what this test verifies",
    "preconditions": "system state before test begins",
    "input_signals": "what signals or values are injected",
    "test_steps": "step by step actions",
    "expected_output": "what the system should produce",
    "pass_criteria": "exact measurable threshold for pass",
    "fail_criteria": "what constitutes a failure",
    "priority": "HIGH or MEDIUM or LOW",
    "test_type": "Functional or Boundary or Stress or Timing",
    "notes": "any additional notes or warnings"
}}

Rules:
- tc_id must always start with TC_{req_id}
- pass_criteria must include specific measurable values if available
- priority is HIGH if safety-critical, MEDIUM for functional, LOW for optional
- test_type: Functional=normal operation, Boundary=edge cases, 
  Stress=prolonged/extreme, Timing=latency/real-time
- If information is missing or ambiguous write "Not specified in requirement"
- Never invent specific numeric values that aren't in the requirement
"""

    def __init__(self, model: str = "llama3", verbose: bool = False):
        self.model   = model
        self.verbose = verbose
        self.scorer  = ConfidenceScorer()

    def generate(self, req: dict) -> dict:
        """
        Generate a structured test case from a requirement dict.

        Returns test case dict with status, confidence, and all fields.
        """
        req_id = req.get("id", "UNKNOWN")

        # ── Skip already-flagged requirements ────────────────────────────
        if req.get("status") == "skipped":
            return {
                "status"  : "skipped",
                "req_id"  : req_id,
                "reason"  : req.get("reason", "Flagged during parsing"),
                "missing" : req.get("missing", ""),
            }

        # ── Build prompt ─────────────────────────────────────────────────
        prompt = self.PROMPT_TEMPLATE.format(
            req_id       = req_id,
            objective    = req.get("objective")    or "Not specified",
            test_method  = req.get("test_method")  or "Not specified",
            pass_criteria= req.get("pass_criteria")or "Not specified",
        )

        if self.verbose:
            print(f"\n  [ai_engine] Sending {req_id} to Ollama ({self.model})")

        # ── Call Ollama ──────────────────────────────────────────────────
        try:
            import ollama
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1},  # low temp = consistent output
            )
            raw_output = response["message"]["content"]

        except Exception as e:
            return self._error_result(req_id, f"Ollama call failed: {e}")

        if self.verbose:
            print(f"  [ai_engine] Raw response length: {len(raw_output)} chars")

        # ── Parse JSON response ──────────────────────────────────────────
        test_case = self._parse_response(raw_output, req_id)

        if not test_case:
            return self._error_result(
                req_id,
                "AI response was not valid JSON. Try again or use --verbose."
            )

        # ── Score confidence ─────────────────────────────────────────────
        confidence = self.scorer.score(req, test_case)
        test_case["confidence"]       = confidence["level"]
        test_case["confidence_score"] = confidence["score"]
        test_case["confidence_notes"] = confidence["notes"]
        test_case["status"]           = "generated"
        test_case["req_id"]           = req_id

        if self.verbose:
            print(
                f"  [ai_engine] {req_id} → "
                f"confidence: {confidence['level']} "
                f"({confidence['score']}%)"
            )

        return test_case

    # ── Private helpers ──────────────────────────────────────────────────

    def _parse_response(self, raw: str, req_id: str) -> dict | None:
        """
        Extract JSON from AI response.
        Handles cases where model wraps JSON in markdown code blocks.
        """
        # Try direct JSON parse first
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code block
        # Model sometimes returns ```json { ... } ```
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}',
        ]

        for pattern in patterns:
            match = re.search(pattern, raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if '`' in pattern else match.group())
                except json.JSONDecodeError:
                    continue

        if self.verbose:
            print(f"  [ai_engine] Could not parse JSON for {req_id}")
            print(f"  [ai_engine] Raw output: {raw[:200]}...")

        return None

    def _error_result(self, req_id: str, reason: str) -> dict:
        """Return a skipped result when AI generation fails."""
        return {
            "status"  : "skipped",
            "req_id"  : req_id,
            "reason"  : reason,
            "missing" : "Check Ollama is running: ollama serve",
        }
