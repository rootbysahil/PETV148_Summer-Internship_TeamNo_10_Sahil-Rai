import csv
import datetime
import json
from abc import ABC, abstractmethod
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.logger import setup_logger
from src.models import ScanResult

logger = setup_logger("smft.exporter")


class BaseExporter(ABC):
    """Abstract base class establishing interface for report exporters."""

    @abstractmethod
    def export(self, scan_result: ScanResult, output_path: Path) -> None:
        """Saves a scan result report in the format target.

        Args:
            scan_result: The finished scan result data model.
            output_path: Path to write the output report file.
        """
        pass


class JsonExporter(BaseExporter):
    """Generates structured JSON reports for programmatic API consumption."""

    def export(self, scan_result: ScanResult, output_path: Path) -> None:
        try:
            # Pydantic dump model
            data = json.loads(scan_result.model_dump_json())
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Successfully exported JSON report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export JSON report to {output_path}: {e}")
            raise OSError(f"Could not save JSON report: {e}") from e


class CsvExporter(BaseExporter):
    """Generates flat CSV tabular files for spreadsheet analysis."""

    def export(self, scan_result: ScanResult, output_path: Path) -> None:
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write metadata header rows
                writer.writerow(["SMFT Scan Report Summary"])
                writer.writerow(["Target Username", scan_result.summary.username])
                writer.writerow(["Scan Timestamp", scan_result.summary.timestamp.isoformat()])
                writer.writerow(["Total Checked", scan_result.summary.total_checked])
                writer.writerow(["Profiles Found", scan_result.summary.total_found])
                writer.writerow(["Success Rate (%)", scan_result.summary.success_rate_pct])
                writer.writerow([])

                # Write detail fields
                writer.writerow(
                    [
                        "Platform Name",
                        "Category",
                        "Profile URL",
                        "Status",
                        "HTTP Status",
                        "Response Time (ms)",
                    ]
                )
                for hit in scan_result.hits:
                    writer.writerow(
                        [
                            hit.platform_name,
                            hit.category,
                            hit.profile_url,
                            hit.status,
                            hit.http_status if hit.http_status is not None else "",
                            hit.response_time_ms,
                        ]
                    )
            logger.info(f"Successfully exported CSV report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export CSV report to {output_path}: {e}")
            raise OSError(f"Could not save CSV report: {e}") from e


class TxtExporter(BaseExporter):
    """Generates clean plaintext summaries for standard terminal views."""

    def export(self, scan_result: ScanResult, output_path: Path) -> None:
        try:
            s = scan_result.summary
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("        SOCIAL MEDIA FOOTPRINTING TOOL (SMFT) REPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Target Username    : {s.username}\n")
                f.write(f"Scan Time (UTC)    : {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Scan Duration      : {s.total_duration_seconds} seconds\n\n")
                f.write("-" * 40 + "\n")
                f.write("Scan Summary Statistics\n")
                f.write("-" * 40 + "\n")
                f.write(f"Platforms Checked  : {s.total_checked}\n")
                f.write(f"Profiles Found     : {s.total_found}\n")
                f.write(f"Profiles Not Found : {s.total_not_found}\n")
                f.write(f"Errors/Timeouts    : {s.total_errors}\n")
                f.write(f"Success Rate       : {s.success_rate_pct}%\n")
                if s.fastest_platform:
                    f.write(f"Fastest Response   : {s.fastest_platform} ({s.fastest_time_ms} ms)\n")
                if s.slowest_platform:
                    f.write(f"Slowest Response   : {s.slowest_platform} ({s.slowest_time_ms} ms)\n")

                f.write("\n" + "-" * 40 + "\n")
                f.write("Category Distribution\n")
                f.write("-" * 40 + "\n")
                for cat, count in s.category_breakdown.items():
                    f.write(f"  {cat.capitalize():18}: {count}\n")

                f.write("\n" + "-" * 40 + "\n")
                f.write("Detailed Profile Hits\n")
                f.write("-" * 40 + "\n")
                found_hits = [h for h in scan_result.hits if h.status == "FOUND"]
                if found_hits:
                    for hit in found_hits:
                        f.write(f"[+] {hit.platform_name} ({hit.category}): {hit.profile_url}\n")
                else:
                    f.write("No profiles identified.\n")

                err_hits = [h for h in scan_result.hits if h.status not in ("FOUND", "NOT_FOUND")]
                if err_hits:
                    f.write("\nWarnings / Errors:\n")
                    for hit in err_hits:
                        reason = (
                            hit.error_message if hit.error_message else f"HTTP {hit.http_status}"
                        )
                        f.write(f"  [!] {hit.platform_name}: {hit.status} ({reason})\n")

            logger.info(f"Successfully exported TXT report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export TXT report to {output_path}: {e}")
            raise OSError(f"Could not save TXT report: {e}") from e


class HtmlExporter(BaseExporter):
    """Renders highly styled HTML reports using Jinja2 templates."""

    def __init__(self, template_dir: Path | None = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        self.template_dir = template_dir

    def export(self, scan_result: ScanResult, output_path: Path) -> None:
        try:
            env = Environment(loader=FileSystemLoader(self.template_dir))
            template = env.get_template("report_template.html.j2")

            # Map statuses to css indicator classes
            status_classes = {
                "FOUND": "badge-found",
                "NOT_FOUND": "badge-notfound",
                "ERROR": "badge-error",
                "UNKNOWN": "badge-warning",
                "SKIPPED": "badge-skipped",
            }

            rendered_html = template.render(
                summary=scan_result.summary,
                hits=scan_result.hits,
                status_classes=status_classes,
                export_date=datetime_now_formatted(),
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered_html)
            logger.info(f"Successfully exported HTML report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export HTML report to {output_path}: {e}")
            raise OSError(f"Could not save HTML report: {e}") from e


def datetime_now_formatted() -> str:
    """Returns local human-readable timestamp."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
