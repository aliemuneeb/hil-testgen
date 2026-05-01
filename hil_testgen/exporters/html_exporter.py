"""
HTML exporter — generates a clean visual report.
Opens in any browser. No dependencies needed to view.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime


class HtmlExporter:
    """
    Exports test cases to a self-contained HTML report.
    Color coded by confidence. Searchable. Shareable.
    """

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
        """Generate and save HTML report."""
        html = self._build_html()
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _build_html(self) -> str:
        total     = len(self.test_cases) + len(self.skipped)
        generated = len(self.test_cases)
        skipped   = len(self.skipped)
        high      = sum(
            1 for tc in self.test_cases if tc.get("confidence") == "HIGH"
        )
        review    = sum(
            1 for tc in self.test_cases if tc.get("confidence") == "REVIEW"
        )
        low       = sum(
            1 for tc in self.test_cases if tc.get("confidence") == "LOW"
        )
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        tc_cards  = "\n".join(self._tc_card(tc) for tc in self.test_cases)
        skip_rows = "\n".join(self._skip_row(s)  for s in self.skipped)
        skip_section = f"""
        <h2>Needs Review ({skipped})</h2>
        <table class="skip-table">
            <thead>
                <tr>
                    <th>Requirement ID</th>
                    <th>Reason</th>
                    <th>What's Missing</th>
                </tr>
            </thead>
            <tbody>{skip_rows}</tbody>
        </table>
        """ if self.skipped else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>hil-testgen Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #f5f5f5; color: #212121; line-height: 1.6;
  }}
  header {{
    background: #1A237E; color: white;
    padding: 24px 40px; margin-bottom: 32px;
  }}
  header h1 {{ font-size: 24px; font-weight: 600; }}
  header p  {{ font-size: 13px; opacity: 0.8; margin-top: 4px; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 0 24px 48px; }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px; margin-bottom: 32px;
  }}
  .stat {{
    background: white; border-radius: 8px;
    padding: 20px; text-align: center;
    border: 1px solid #e0e0e0;
  }}
  .stat .num {{
    font-size: 32px; font-weight: 700; color: #1A237E;
  }}
  .stat .label {{
    font-size: 12px; color: #757575; margin-top: 4px;
  }}
  h2 {{
    font-size: 18px; font-weight: 600;
    margin: 32px 0 16px; color: #1A237E;
  }}
  .tc-card {{
    background: white; border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin-bottom: 16px; overflow: hidden;
  }}
  .tc-header {{
    padding: 14px 20px;
    display: flex; justify-content: space-between;
    align-items: center; cursor: pointer;
    user-select: none;
  }}
  .tc-header:hover {{ background: #f9f9f9; }}
  .tc-title {{ font-weight: 600; font-size: 14px; }}
  .tc-meta  {{ font-size: 12px; color: #757575; margin-top: 2px; }}
  .badges   {{ display: flex; gap: 8px; align-items: center; }}
  .badge {{
    padding: 3px 10px; border-radius: 12px;
    font-size: 11px; font-weight: 600;
  }}
  .badge-HIGH   {{ background:#E8F5E9; color:#1B5E20; }}
  .badge-REVIEW {{ background:#FFF8E1; color:#E65100; }}
  .badge-LOW    {{ background:#FFEBEE; color:#B71C1C; }}
  .badge-pri-HIGH   {{ background:#FFEBEE; color:#B71C1C; }}
  .badge-pri-MEDIUM {{ background:#FFF8E1; color:#E65100; }}
  .badge-pri-LOW    {{ background:#E8F5E9; color:#1B5E20; }}
  .tc-body {{
    padding: 0 20px 16px; display: none;
    border-top: 1px solid #f0f0f0;
  }}
  .tc-body.open {{ display: block; }}
  .field {{ margin-top: 14px; }}
  .field-label {{
    font-size: 11px; font-weight: 600;
    color: #9E9E9E; text-transform: uppercase;
    letter-spacing: 0.05em; margin-bottom: 4px;
  }}
  .field-value {{ font-size: 13px; color: #212121; }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 24px;
  }}
  .confidence-note {{
    font-size: 11px; color: #757575;
    margin-top: 4px; font-style: italic;
  }}
  .skip-table {{
    width: 100%; border-collapse: collapse;
    background: white; border-radius: 8px;
    overflow: hidden; border: 1px solid #e0e0e0;
    font-size: 13px;
  }}
  .skip-table th {{
    background: #B71C1C; color: white;
    padding: 12px 16px; text-align: left;
    font-weight: 600; font-size: 12px;
  }}
  .skip-table td {{
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top;
  }}
  .skip-table tr:last-child td {{ border-bottom: none; }}
  .skip-table tr:nth-child(even) td {{ background: #fff8f8; }}
  .disclaimer {{
    margin-top: 40px; padding: 16px 20px;
    background: #E3F2FD; border-radius: 8px;
    font-size: 12px; color: #1565C0;
    border-left: 4px solid #1A237E;
  }}
  footer {{
    text-align: center; padding: 24px;
    font-size: 12px; color: #9E9E9E;
    border-top: 1px solid #e0e0e0;
    margin-top: 40px;
  }}
</style>
</head>
<body>
<header>
  <h1>hil-testgen — Test Case Report</h1>
  <p>Generated: {timestamp}</p>
</header>

<div class="container">

  <div class="stats">
    <div class="stat">
      <div class="num">{total}</div>
      <div class="label">Requirements</div>
    </div>
    <div class="stat">
      <div class="num">{generated}</div>
      <div class="label">Generated</div>
    </div>
    <div class="stat">
      <div class="num" style="color:#1B5E20">{high}</div>
      <div class="label">High Confidence</div>
    </div>
    <div class="stat">
      <div class="num" style="color:#E65100">{review}</div>
      <div class="label">Needs Review</div>
    </div>
    <div class="stat">
      <div class="num" style="color:#B71C1C">{low}</div>
      <div class="label">Low Confidence</div>
    </div>
    <div class="stat">
      <div class="num" style="color:#B71C1C">{skipped}</div>
      <div class="label">Skipped</div>
    </div>
  </div>

  <h2>Generated Test Cases ({generated})</h2>
  {tc_cards}

  {skip_section}

  <div class="disclaimer">
    All generated test cases must be reviewed by a qualified engineer
    before use in a validation environment. hil-testgen assists with
    drafting — it does not replace engineering judgment.
  </div>

</div>

<footer>
  hil-testgen v0.1.0 — open source, 100% local, NDA-safe
</footer>

<script>
  document.querySelectorAll('.tc-header').forEach(h => {{
    h.addEventListener('click', () => {{
      h.nextElementSibling.classList.toggle('open');
    }});
  }});
</script>
</body>
</html>"""

    def _tc_card(self, tc: dict) -> str:
        """Generate HTML card for one test case."""
        conf     = tc.get("confidence", "REVIEW")
        priority = tc.get("priority", "MEDIUM")

        return f"""
  <div class="tc-card">
    <div class="tc-header">
      <div>
        <div class="tc-title">{tc.get('tc_id','—')} — {tc.get('title','—')}</div>
        <div class="tc-meta">Req: {tc.get('req_id','—')} &nbsp;|&nbsp; 
             Type: {tc.get('test_type','—')}</div>
      </div>
      <div class="badges">
        <span class="badge badge-pri-{priority}">{priority}</span>
        <span class="badge badge-{conf}">{conf}</span>
      </div>
    </div>
    <div class="tc-body">
      <div class="grid-2">
        <div class="field">
          <div class="field-label">Objective</div>
          <div class="field-value">{tc.get('objective','—')}</div>
        </div>
        <div class="field">
          <div class="field-label">Preconditions</div>
          <div class="field-value">{tc.get('preconditions','—')}</div>
        </div>
        <div class="field">
          <div class="field-label">Input Signals</div>
          <div class="field-value">{tc.get('input_signals','—')}</div>
        </div>
        <div class="field">
          <div class="field-label">Expected Output</div>
          <div class="field-value">{tc.get('expected_output','—')}</div>
        </div>
        <div class="field">
          <div class="field-label">Pass Criteria</div>
          <div class="field-value">{tc.get('pass_criteria','—')}</div>
        </div>
        <div class="field">
          <div class="field-label">Fail Criteria</div>
          <div class="field-value">{tc.get('fail_criteria','—')}</div>
        </div>
      </div>
      <div class="field">
        <div class="field-label">Test Steps</div>
        <div class="field-value">{tc.get('test_steps','—')}</div>
      </div>
      <div class="field">
        <div class="field-label">Notes</div>
        <div class="field-value">{tc.get('notes','—')}</div>
        <div class="confidence-note">{tc.get('confidence_notes','')}</div>
      </div>
    </div>
  </div>"""

    def _skip_row(self, skip: dict) -> str:
        """Generate table row for skipped requirement."""
        return f"""
      <tr>
        <td><strong>{skip.get('req_id','—')}</strong></td>
        <td>{skip.get('reason','—')}</td>
        <td>{skip.get('missing','—')}</td>
      </tr>"""
