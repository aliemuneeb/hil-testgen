from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def generate(
    requirements_file: str,
    output: str = None,
    export_format: str = "excel",
    engine: str = "ollama",
    model: str = "llama3",
    verbose: bool = False
):
    """
    Generate structured HIL/SIL/MIL test cases from a requirements document.

    Args:
        requirements_file : Path to requirements doc (.docx, .xlsx, .csv, .pdf)
        output            : Output file path (auto-named if not provided)
        export_format     : "excel", "csv", or "html" (default: "excel")
        engine            : AI engine to use — "ollama" only for now
        model             : Ollama model to use (default: "llama3")
        verbose           : Print detailed logs

    Example:
        from hil_testgen import generate
        generate("requirements.docx")
    """

    input_path = Path(requirements_file)

    # ── 1. Validate input file ──────────────────────────────────────────
    if not input_path.exists():
        console.print(f"[red]Error:[/red] File not found: {input_path.name}")
        raise FileNotFoundError(f"File not found: {requirements_file}")

    supported = [".docx", ".xlsx", ".csv", ".pdf"]
    if input_path.suffix.lower() not in supported:
        console.print(
            f"[red]Error:[/red] Unsupported file type: {input_path.suffix}\n"
            f"Supported formats: {', '.join(supported)}\n"
            f"[yellow]Tip:[/yellow] Convert your file to .docx and try again."
        )
        raise ValueError(f"Unsupported file type: {input_path.suffix}")

    # ── 2. Auto-name output file ────────────────────────────────────────
    ext_map = {"excel": ".xlsx", "csv": ".csv", "html": ".html"}
    ext = ext_map.get(export_format, ".xlsx")
    if output is None:
        output = input_path.stem + "_test_cases" + ext
    output_path = Path(output)

    console.print(f"\n[bold]hil-testgen[/bold] v0.1.0")
    console.print(f"Processing: [cyan]{input_path.name}[/cyan]")
    console.print(f"Engine:     [cyan]{engine} / {model}[/cyan]")
    console.print(f"Output:     [cyan]{output_path.name}[/cyan]\n")

    # ── 3. Check Ollama is running ──────────────────────────────────────
    _check_ollama(model)

    # ── 4. Parse requirements document ─────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Parsing requirements document...", total=None)
        requirements = _parse(input_path, verbose)

    if not requirements:
        console.print("[red]Error:[/red] No requirements found in document.")
        console.print(
            "[yellow]Tip:[/yellow] Ensure your document has clear requirement "
            "sections with objectives and pass criteria."
        )
        return

    console.print(f"[green]Found {len(requirements)} requirements[/green]")

    # ── 5. Generate test cases via AI ───────────────────────────────────
    test_cases = []
    skipped = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Generating test cases...", total=len(requirements))

        for req in requirements:
            progress.update(task, description=f"Generating: {req.get('id', 'REQ')}...")
            result = _generate_test_case(req, model, verbose)

            if result["status"] == "skipped":
                skipped.append(result)
            else:
                test_cases.append(result)

            progress.advance(task)

    # ── 6. Export results ───────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Exporting results...", total=None)
        _export(test_cases, skipped, output_path, export_format)

    # ── 7. Summary ──────────────────────────────────────────────────────
    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"─────────────────────────────────────")
    console.print(f"[green]Generated:[/green] {len(test_cases)} test cases")

    if skipped:
        console.print(f"[yellow]Skipped:  [/yellow] {len(skipped)} requirements")
        console.print(f"\n[yellow]Skipped requirements (missing context):[/yellow]")
        for s in skipped:
            console.print(f"  [yellow]⚠[/yellow]  {s['req_id']} — {s['reason']}")
            if s.get("missing"):
                console.print(f"      Missing: {s['missing']}")

    console.print(f"\nSaved to: [cyan]{output_path.name}[/cyan]\n")
    return str(output_path)


# ── Internal helpers ────────────────────────────────────────────────────────


def _check_ollama(model: str):
    """Check Ollama is installed and model is available."""
    try:
        import ollama
        ollama.show(model)
    except Exception:
        console.print(
            f"\n[red]Ollama not running or model '{model}' not found.[/red]\n"
            f"Fix this in 2 steps:\n\n"
            f"  1. Install Ollama → [link]https://ollama.ai[/link]\n"
            f"  2. Run: [bold]ollama pull {model}[/bold]\n"
            f"\nOllama is free, runs locally, and keeps your data 100% private.\n"
        )
        raise RuntimeError(f"Ollama not available. See instructions above.")


def _parse(input_path: Path, verbose: bool) -> list:
    """Route to correct parser based on file extension."""
    suffix = input_path.suffix.lower()

    if suffix == ".docx":
        from hil_testgen.parser.docx_parser import DocxParser
        return DocxParser(input_path, verbose).parse()

    elif suffix in [".xlsx"]:
        from hil_testgen.parser.excel_parser import ExcelParser
        return ExcelParser(input_path, verbose).parse()

    elif suffix == ".csv":
        from hil_testgen.parser.excel_parser import ExcelParser
        return ExcelParser(input_path, verbose).parse()

    elif suffix == ".pdf":
        from hil_testgen.parser.pdf_parser import PdfParser
        return PdfParser(input_path, verbose).parse()


def _generate_test_case(req: dict, model: str, verbose: bool) -> dict:
    """Send requirement to AI engine and get structured test case back."""
    from hil_testgen.generator.ai_engine import AIEngine
    return AIEngine(model=model, verbose=verbose).generate(req)


def _export(test_cases: list, skipped: list, output_path: Path, fmt: str):
    """Route to correct exporter."""
    if fmt == "excel":
        from hil_testgen.exporters.excel_exporter import ExcelExporter
        ExcelExporter(test_cases, skipped, output_path).export()

    elif fmt == "csv":
        from hil_testgen.exporters.csv_exporter import CsvExporter
        CsvExporter(test_cases, skipped, output_path).export()

    elif fmt == "html":
        from hil_testgen.exporters.html_exporter import HtmlExporter
        HtmlExporter(test_cases, skipped, output_path).export()
