# hil_testgen
Open-source Python package that automatically generates structured test cases from requirements documents.
# hil-testgen

Generate structured HIL/SIL/MIL test cases from requirements documents.
100% local. NDA-safe. No data leaves your machine.

```bash
pip install hil-testgen
```

---

## What it does

HIL test engineers spend hours manually converting requirements documents
into structured test cases in Excel. hil-testgen automates that.

**Input** — a requirements document (.docx, .xlsx, .csv, .pdf)

**Output** — a structured test case document with:
- Test Case ID linked to Requirement ID (traceability)
- Preconditions, Input Signals, Test Steps
- Pass Criteria with exact thresholds preserved
- Fail Criteria
- Priority and Test Type classification
- Confidence scoring (HIGH / REVIEW / LOW)

All processing happens locally using Ollama.
No data is sent to any external server.

---

## Quick start

### 1. Install hil-testgen

```bash
pip install hil-testgen
```

### 2. Install Ollama

Download from [ollama.ai](https://ollama.ai) and install.

```bash
ollama pull llama3
```

### 3. Run

```bash
hil-testgen generate requirements.docx
```

That's it. A test_cases.xlsx file is saved in your current directory.

---

## Usage

### Command line

```bash
# Basic — generates Excel output
hil-testgen generate requirements.docx

# HTML report (visual, opens in browser)
hil-testgen generate requirements.docx --format html

# CSV output
hil-testgen generate requirements.docx --format csv

# Custom output path
hil-testgen generate requirements.docx --output my_tests.xlsx

# Use a different Ollama model
hil-testgen generate requirements.docx --model mistral

# Verbose mode — see detailed logs
hil-testgen generate requirements.docx --verbose

# Check your setup
hil-testgen info
```

### Python API

```python
from hil_testgen import generate

# Minimal — generates Excel in current directory
generate("requirements.docx")

# Full options
generate(
    requirements_file="requirements.docx",
    output="test_cases.xlsx",
    export_format="excel",  # "excel", "csv", "html"
    model="llama3",
    verbose=False
)
```

---

## Output formats

### Excel (.xlsx) — default
Three tabs:
- **Generated Test Cases** — color coded by confidence
- **Needs Review** — skipped requirements with exact reasons
- **Summary** — stats at a glance

### HTML (.html)
- Expandable cards per test case
- Color coded HIGH / REVIEW / LOW confidence badges
- Stats dashboard at top
- Opens in any browser — no dependencies needed

### CSV (.csv)
- Flat file, one row per test case
- Separate `_skipped.csv` for requirements that need attention

---

## Supported input formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Word   | .docx     | Best support — recommended |
| Excel  | .xlsx     | Auto-detects column layout |
| CSV    | .csv      | Simple tabular format |
| PDF    | .pdf      | Best effort — convert to .docx if results are poor |

> **Note:** If your requirements are in a format not listed above
> (IBM DOORS, Polarion, Confluence), export or copy them into a
> .docx file first. Most tools support this in one click.

---

## Supported test environments

hil-testgen was designed for automotive ECU validation but works
for any requirements document structured around objectives,
test methods, and pass criteria:

- HIL (Hardware-in-the-Loop)
- SIL (Software-in-the-Loop)
- MIL (Model-in-the-Loop)
- PIL (Processor-in-the-Loop)

---

## Why local?

Automotive requirements documents contain proprietary ECU designs,
calibration data, and safety-critical specifications covered by NDA.

Sending these to a cloud AI API (ChatGPT, Gemini, Claude) risks:
- NDA violation
- IP exposure
- Company security policy breach

hil-testgen uses Ollama to run AI inference entirely on your machine.
Nothing ever leaves your laptop.

Zero network calls. Zero data exposure.

---

## Confidence scoring

Every generated test case is scored based on how complete
the original requirement was:

| Level  | Score  | Meaning |
|--------|--------|---------|
| HIGH   | 80-100 | Requirement was complete — test case ready to use |
| REVIEW | 50-79  | Some fields were missing — verify before use |
| LOW    | 0-49   | Significant info missing — AI inferred values |

---

## Example

Given this requirement:
HIL-RQ1: System Initialization
Objective: Verify correct initialization of start positions
Test Method: Load known values for Const_Offset_Lat,
Startposition_Latitude. Observe Veh_Pos_Lati output.
Pass Criteria: Output GPS coordinates match within ±0.00001°

hil-testgen generates:
TC ID          → TC_HIL-RQ1_001
Requirement ID → HIL-RQ1
Title          → Initialization of Start Positions
Preconditions  → ECU in default state, no prior test runs
Input Signals  → Const_Offset_Lat, Startposition_Latitude
Test Steps     → 1. Load known values
2. Observe Veh_Pos_Lati and Veh_Pos_Longi outputs
Pass Criteria  → Output GPS coordinates match within ±0.00001°
Fail Criteria  → Output does not match within ±0.00001°
Priority       → MEDIUM
Test Type      → Functional
Confidence     → HIGH

---

## Disclaimer

All generated test cases must be reviewed by a qualified engineer
before use in a validation environment. hil-testgen assists with
drafting — it does not replace engineering judgment.

Generated test cases represent a structured starting point.
Signal values, calibration parameters, and environment-specific
details must be verified and completed by the test engineer.

---

## Roadmap

- [ ] Retry logic for failed AI generations
- [ ] Better numeric value extraction from requirements
- [ ] CAPL script export
- [ ] pytest script export
- [ ] ReqIF / DOORS import support
- [ ] Multi-language requirements support

---

## Contributing

Contributions welcome! Please open an issue first to discuss
what you'd like to change.

---

## License

MIT — free to use, modify, and distribute.

---

*Built for HIL/SIL/MIL test engineers who are tired of
staring at blank Excel sheets. 🚗*

