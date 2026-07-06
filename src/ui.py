from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from src.models import ScanResult, ScanSummary

console = Console()


class RichUI:
    """Handles Rich rendering and user interactive screens."""

    @staticmethod
    def render_error(title: str, message: str) -> None:
        """Displays a red error card block.

        Args:
            title: Title text.
            message: Accompanying detail message.
        """
        panel = Panel(
            f"[bold white]{message}[/bold white]",
            title=f"[bold red]❌ {title}[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def render_warning(title: str, message: str) -> None:
        """Displays a yellow warning card block.

        Args:
            title: Title text.
            message: Details.
        """
        panel = Panel(
            f"[bold white]{message}[/bold white]",
            title=f"[bold yellow]⚠️ {title}[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def render_info(title: str, message: str) -> None:
        """Displays a blue informational block.

        Args:
            title: Title.
            message: Details.
        """
        panel = Panel(
            message, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan", padding=(1, 2)
        )
        console.print(panel)

    @staticmethod
    def render_results_table(scan_result: ScanResult) -> None:
        """Renders the final platforms checker hits table.

        Args:
            scan_result: Target scan details.
        """
        table = Table(
            title=f"[bold cyan]Platform Scan Results for '{scan_result.summary.username}'[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            box=None,
        )

        table.add_column("Platform", style="bold white", width=20)
        table.add_column("Category", style="dim", width=15)
        table.add_column("Status", width=15)
        table.add_column("Profile URL", style="blue")
        table.add_column("Response Time", justify="right", style="green")

        for hit in scan_result.hits:
            status_text = f"[bold green]{hit.status}[/bold green]"
            url_text = hit.profile_url

            if hit.status == "NOT_FOUND":
                status_text = "[bold red]NOT FOUND[/bold red]"
                url_text = "[dim]N/A[/dim]"
            elif hit.status == "ERROR":
                reason = hit.error_message if hit.error_message else f"HTTP {hit.http_status}"
                status_text = f"[bold yellow]ERROR ({reason})[/bold yellow]"
                url_text = "[dim]N/A[/dim]"
            elif hit.status == "UNKNOWN":
                status_text = "[bold yellow]TIMEOUT[/bold yellow]"
                url_text = "[dim]N/A[/dim]"
            elif hit.status == "SKIPPED":
                status_text = "[dim]SKIPPED[/dim]"
                url_text = "[dim]N/A[/dim]"

            time_text = f"{hit.response_time_ms} ms" if hit.response_time_ms > 0 else "-"

            table.add_row(hit.platform_name, hit.category, status_text, url_text, time_text)

        console.print(table)
        console.print("\n")

    @staticmethod
    def render_summary_panel(summary: ScanSummary) -> None:
        """Displays cards metrics summary.

        Args:
            summary: Results metrics analytics.
        """
        fastest_info = (
            f"[green]{summary.fastest_platform} ({summary.fastest_time_ms} ms)[/green]"
            if summary.fastest_platform
            else "[dim]N/A[/dim]"
        )
        slowest_info = (
            f"[red]{summary.slowest_platform} ({summary.slowest_time_ms} ms)[/red]"
            if summary.slowest_platform
            else "[dim]N/A[/dim]"
        )

        stats_text = (
            f"• [bold]Target Username:[/bold] {summary.username}\n"
            f"• [bold]Platforms Checked:[/bold] {summary.total_checked}\n"
            f"• [bold]Profiles Identified:[/bold] [green]{summary.total_found}[/green]\n"
            f"• [bold]Success/Match Rate:[/bold] [cyan]{summary.success_rate_pct}%[/cyan]\n"
            f"• [bold]Scan Duration:[/bold] {summary.total_duration_seconds} seconds\n"
            f"• [bold]Response Speeds:[/bold] Fastest: {fastest_info} | Slowest: {slowest_info}"
        )

        categories_text = ""
        for cat, count in summary.category_breakdown.items():
            categories_text += f"• [bold]{cat.capitalize()}:[/bold] {count}\n"
        if not categories_text:
            categories_text = "[dim]No category distributions (no hits).[/dim]"

        panel_stats = Panel(
            stats_text,
            title="[bold green]Scan Metrics & Analytics[/bold green]",
            border_style="green",
            expand=True,
        )

        panel_categories = Panel(
            categories_text.strip(),
            title="[bold green]Category Distribution[/bold green]",
            border_style="green",
            expand=True,
        )

        console.print(Columns([panel_stats, panel_categories]))
        console.print("\n")

    @staticmethod
    def get_progress_renderer() -> Progress:
        """Configures and returns custom Live Rich progress bar task."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )
