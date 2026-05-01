"""
CLI — command line interface for hil-testgen.
Allows engineers to run the tool from terminal
without writing any Python.

Usage:
    hil-testgen generate requirements.docx
    hil-testgen generate requirements.docx --format html
    hil-testgen generate requirements.docx --output my_tests.xlsx
    hil-testgen generate requirements.docx --verbose
    hil-testgen info
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="hil-testgen")
def main():
    """
    hil-testgen — Generate structured HIL/SIL/MIL test cases
    from requirements documents. 100% local. NDA-safe.
    """
    pass


@main.command()
@click.argument(
    "requirements_file",
    type=click.Path(exists=True)
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output file path. Auto-named if not provided."
)
@click.option(
    "--format", "-f",
    "export_format",
    type=click.Choice(["excel", "csv", "html"], case_sensitive=False),
    default="excel",
    show_default=True,
    help="Output format."
)
@click.option(
    "--model", "-m",
    default="llama3",
    show_default=True,
    help="Ollama model to use."
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Print detailed logs."
)
def generate(
    requirements_file,
    output,
    export_format,
    model,
    verbose
):
    """
    Generate test cases from a requirements document.

    REQUIREMENTS_FILE: Path to your .docx, .xlsx, .csv or .pdf file.

    Examples:\n
        hil-testgen generate requirements.docx\n
        hil-testgen generate requirements.docx --format html\n
        hil-testgen generate requirements.xlsx --output tests.xlsx\n
        hil-testgen generate requirements.docx --model llama3 --verbose
    """
    try:
        from hil_testgen.core import generate as run

        result = run(
            requirements_file=requirements_file,
            output=output,
            export_format=export_format,
            model=model,
            verbose=verbose,
        )

        if result:
            console.print(
                Panel(
                    f"[bold green]Output saved:[/bold green] {result}\n\n"
                    f"[dim]Review all test cases before use in validation.[/dim]",
                    title="[bold]hil-testgen[/bold]",
                    border_style="green"
                )
            )

    except FileNotFoundError as e:
        console.print(f"[red]File not found:[/red] {e}")
        raise SystemExit(1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    except RuntimeError as e:
        console.print(f"[red]Runtime error:[/red] {e}")
        raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise SystemExit(1)


@main.command()
def info():
    """
    Show system info and check Ollama status.
    Run this first to verify your setup is correct.
    """
    console.print()

    # ── Package info ─────────────────────────────────────────────────────
    console.print(Panel(
        "[bold]hil-testgen[/bold] v0.1.0\n"
        "Generate structured HIL/SIL/MIL test cases from "
        "requirements documents.\n"
        "100% local. NDA-safe. No data leaves your machine.",
        title="About",
        border_style="blue"
    ))

    # ── Supported formats ─────────────────────────────────────────────────
    fmt_table = Table(title="Supported Input Formats", show_header=True)
    fmt_table.add_column("Format", style="cyan", width=10)
    fmt_table.add_column("Extension", width=12)
    fmt_table.add_column("Notes", width=45)

    fmt_table.add_row(
        "Word",  ".docx",
        "Best support — recommended format"
    )
    fmt_table.add_row(
        "Excel", ".xlsx",
        "Auto-detects column layout"
    )
    fmt_table.add_row(
        "CSV",   ".csv",
        "Simple tabular format"
    )
    fmt_table.add_row(
        "PDF",   ".pdf",
        "Best effort — convert to .docx if results are poor"
    )
    console.print(fmt_table)
    console.print()

    # ── Ollama status ─────────────────────────────────────────────────────
    console.print("[bold]Checking Ollama...[/bold]")
    try:
        import ollama
        models = ollama.list()
        model_names = [m["model"] for m in models.get("models", [])]

        if model_names:
            console.print(f"[green]Ollama is running[/green]")
            console.print(f"Available models: {', '.join(model_names)}")

            if "llama3:latest" in model_names or "llama3" in model_names:
                console.print(
                    "[green]llama3 is ready — "
                    "you can run hil-testgen now[/green]"
                )
            else:
                console.print(
                    "[yellow]llama3 not found.[/yellow] "
                    "Run: [bold]ollama pull llama3[/bold]"
                )
        else:
            console.print(
                "[yellow]Ollama is running but no models installed.[/yellow]\n"
                "Run: [bold]ollama pull llama3[/bold]"
            )

    except Exception:
        console.print(
            "[red]Ollama not found or not running.[/red]\n\n"
            "Fix in 2 steps:\n"
            "  1. Install Ollama → [link]https://ollama.ai[/link]\n"
            "  2. Run: [bold]ollama pull llama3[/bold]\n"
        )

    console.print()

    # ── Quick start ───────────────────────────────────────────────────────
    qs_table = Table(title="Quick Start", show_header=False)
    qs_table.add_column("Step", style="bold cyan", width=8)
    qs_table.add_column("Command", width=55)

    qs_table.add_row("1", "pip install hil-testgen")
    qs_table.add_row("2", "Install Ollama → https://ollama.ai")
    qs_table.add_row("3", "ollama pull llama3")
    qs_table.add_row("4", "hil-testgen generate requirements.docx")

    console.print(qs_table)
    console.print()
