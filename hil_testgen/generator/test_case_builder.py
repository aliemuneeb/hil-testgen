"""
Test case builder — lightweight post-processor.
Cleans and standardises AI output before export.
"""


class TestCaseBuilder:
    """
    Cleans and standardises generated test cases.
    Ensures consistent field names and values across all outputs.
    """

    # Fields every test case must have
    REQUIRED_FIELDS = [
        "tc_id", "req_id", "title", "objective",
        "preconditions", "input_signals", "test_steps",
        "expected_output", "pass_criteria", "fail_criteria",
        "priority", "test_type", "notes",
        "confidence", "confidence_score", "confidence_notes",
        "status",
    ]

    DEFAULT_VALUES = {
        "title"            : "Test case",
        "objective"        : "Not specified",
        "preconditions"    : "System in normal operating state",
        "input_signals"    : "Not specified in requirement",
        "test_steps"       : "Not specified in requirement",
        "expected_output"  : "Not specified in requirement",
        "pass_criteria"    : "Not specified in requirement",
        "fail_criteria"    : "Any deviation from pass criteria",
        "priority"         : "MEDIUM",
        "test_type"        : "Functional",
        "notes"            : "",
        "confidence"       : "REVIEW",
        "confidence_score" : 50,
        "confidence_notes" : "",
        "status"           : "generated",
    }

    def build(self, test_case: dict) -> dict:
        """
        Ensure test case has all required fields.
        Fill missing ones with sensible defaults.
        """
        result = {}

        for field in self.REQUIRED_FIELDS:
            value = test_case.get(field)

            # Use default if missing or empty
            if not value and value != 0:
                value = self.DEFAULT_VALUES.get(field, "")

            result[field] = value

        # Normalise priority to uppercase
        result["priority"] = str(result["priority"]).upper()
        if result["priority"] not in ["HIGH", "MEDIUM", "LOW"]:
            result["priority"] = "MEDIUM"

        # Normalise test type
        valid_types = ["Functional", "Boundary", "Stress", "Timing"]
        if result["test_type"] not in valid_types:
            result["test_type"] = "Functional"

        return result
