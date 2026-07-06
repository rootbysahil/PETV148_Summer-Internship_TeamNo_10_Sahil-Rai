import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

from src.banner import print_banner, print_disclaimer
from src.logger import setup_logger
from src.models import PlatformHit
from src.report_generator import ReportGenerator
from src.scanner import Scanner
from src.sherlock_engine import SherlockEngine
from src.ui import RichUI
from src.validators import Validator

app = typer.Typer(
    help="SMFT — Social Media Footprinting Tool (OSINT Username Auditor)", no_args_is_help=True
)
console = Console()
logger = setup_logger("smft.cli")


def check_disclaimer_agreement(accept_disclaimer: bool) -> bool:
    """Forces user to read and accept the safety rules before scanner starts.

    Args:
        accept_disclaimer: If True, bypass interactive screen prompt.

    Returns:
        bool: True if agreed, False otherwise.
    """
    if accept_disclaimer:
        logger.info("Disclaimer automatically accepted via CLI argument.")
        return True

    print_disclaimer()
    ans = typer.confirm("Do you accept the ethical-use terms and wish to proceed?")
    if ans:
        logger.info("User explicitly accepted the ethical disclaimer.")
        return True
    return False


@app.command()
def scan(
    username: str | None = typer.Argument(None, help="Single target username to scan"),
    input_file: Path | None = typer.Option(
        None,
        "--input",
        "-i",
        help="Batch process: path to file containing usernames (one per line)",
    ),
    accept_disclaimer: bool = typer.Option(
        False,
        "--accept-disclaimer",
        "-y",
        help="Bypass and accept mandatory ethical disclaimer automatically",
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Quiet mode: suppresses interactive tables and logs"
    ),
    formats: list[str] | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Specify export formats (json, csv, txt, html). Can be specified multiple times.",
    ),
) -> None:
    """Executes digital footprint username scans."""
    if not quiet:
        print_banner()

    # Step 1: Enforce disclaimer gate
    if not check_disclaimer_agreement(accept_disclaimer):
        if not quiet:
            RichUI.render_error(
                "Execution Halted", "You must accept the ethical disclaimer to run scans."
            )
        sys.exit(1)

    # Step 2: Validate Target Inputs
    usernames_to_scan: list[str] = []

    if input_file:
        if not input_file.exists():
            RichUI.render_error(
                "File Not Found", f"Specified input batch file does not exist: {input_file}"
            )
            sys.exit(1)

        try:
            with open(input_file, encoding="utf-8") as f:
                lines = f.readlines()
            valid, errors = Validator.validate_batch_file(lines)

            if errors and not quiet:
                for err in errors:
                    RichUI.render_warning("Validation Warning", err)

            if not valid:
                RichUI.render_error("Batch Error", "No valid usernames found in batch file.")
                sys.exit(1)

            usernames_to_scan = valid
            logger.info(f"Loaded {len(usernames_to_scan)} usernames for batch scan.")
        except Exception as e:
            RichUI.render_error("Batch File Read Error", f"Could not read file: {e}")
            logger.exception("Failed to read input batch file")
            sys.exit(1)
    else:
        # Check single username
        if not username:
            # Prompt interactively if neither argument nor input file is present
            username = typer.prompt("Enter target username to scan")

        is_valid, reason = Validator.validate_username(username)
        if not is_valid:
            if not quiet:
                RichUI.render_error("Invalid Username", reason or "Format error.")
            sys.exit(1)
        usernames_to_scan = [username]

    # Parse output formats
    target_formats = formats if formats else ["json", "csv", "txt", "html"]
    # Normalize formats list
    target_formats = [fmt.lower() for fmt in target_formats]

    # Initialize Engine components
    try:
        engine = SherlockEngine()
        scanner = Scanner(engine)
        report_generator = ReportGenerator()
    except Exception as e:
        if not quiet:
            RichUI.render_error("Initialization Error", f"Failed to load signature engine: {e}")
        logger.exception("System initialization error")
        sys.exit(1)

    # Step 3: Run the Scan asynchronously
    try:
        asyncio.run(
            run_scans_orchestration(
                usernames_to_scan=usernames_to_scan,
                scanner=scanner,
                report_generator=report_generator,
                formats=target_formats,
                quiet=quiet,
            )
        )
    except KeyboardInterrupt:
        if not quiet:
            console.print("\n")
            RichUI.render_warning(
                "Scan Cancelled", "Process terminated by user request. Saving partial outputs..."
            )
        sys.exit(1)
    except Exception as e:
        if not quiet:
            RichUI.render_error("Unexpected Failure", f"Scanner execution failed: {e}")
        logger.exception("Unexpected exception inside scan run")
        sys.exit(1)


async def run_scans_orchestration(
    usernames_to_scan: list[str],
    scanner: Scanner,
    report_generator: ReportGenerator,
    formats: list[str],
    quiet: bool,
) -> None:
    """Orchestrates async scan tasks and handles CLI live output updates."""
    for idx, user in enumerate(usernames_to_scan, start=1):
        if not quiet:
            console.print(
                f"[bold cyan]({idx}/{len(usernames_to_scan)}) Probing username: '{user}'...[/bold cyan]"
            )

        # We define progress callback to update rich progress bar
        total_platforms = len(scanner.engine.get_supported_platforms())

        if quiet:
            # Quiet mode: no console visual bars
            result = await scanner.scan_username(user)
        else:
            with RichUI.get_progress_renderer() as progress:
                task_id = progress.add_task(
                    "[magenta]Scanning Platforms...[/magenta]", total=total_platforms
                )

                async def progress_cb(hit: PlatformHit) -> None:
                    progress.update(
                        task_id, advance=1, description=f"[cyan]Checked: {hit.platform_name}[/cyan]"
                    )

                result = await scanner.scan_username(user, progress_callback=progress_cb)

        # Generate Reports
        saved_files = report_generator.generate_reports(result, formats=formats)

        if not quiet:
            # Display results in CLI
            console.print("\n")
            RichUI.render_results_table(result)
            RichUI.render_summary_panel(result.summary)

            # Print file paths
            console.print("[bold green]Reports generated successfully:[/bold green]")
            for fmt, path in saved_files.items():
                console.print(f"  • {fmt.upper()}: [blue]{path.resolve()}[/blue]")
            console.print("\n")


@app.command("platforms")
def list_platforms() -> None:
    """Lists all supported social media platforms and their categories."""
    try:
        engine = SherlockEngine()
        platforms = engine.get_supported_platforms()
        console.print(f"[bold cyan]Supported Platforms ({len(platforms)} total):[/bold cyan]")
        sorted_platforms = sorted(platforms)
        for platform in sorted_platforms:
            info = engine.platforms[platform]
            console.print(
                f"  • [bold white]{platform:18}[/bold white] | Category: [magenta]{info.get('category', 'other')}[/magenta]"
            )
    except Exception as e:
        console.print(f"[bold red]Error loading platforms signature database: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
