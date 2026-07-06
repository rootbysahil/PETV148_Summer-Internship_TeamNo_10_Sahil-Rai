from pathlib import Path

from config import settings
from src.exporter import CsvExporter, HtmlExporter, JsonExporter, TxtExporter
from src.models import ScanResult


class ReportGenerator:
    """Manages report compilation, path construction and exporter dispatch."""

    def __init__(self, output_dir: Path | None = None):
        """Initializes ReportGenerator.

        Args:
            output_dir: Directory where reports will be generated.
        """
        self.output_dir = output_dir if output_dir else settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Strategies map
        self.exporters = {
            "json": JsonExporter(),
            "csv": CsvExporter(),
            "txt": TxtExporter(),
            "html": HtmlExporter(),
        }

    def generate_reports(
        self, scan_result: ScanResult, formats: list[str] | None = None
    ) -> dict[str, Path]:
        """Saves scan result to files in requested format styles.

        Args:
            scan_result: The finished scan result data model.
            formats: List of formats to write (e.g. ['json', 'csv']). If None, writes all.

        Returns:
            Dict[str, Path]: Map of format names to created file paths.
        """
        target_formats = formats if formats else ["json", "csv", "txt", "html"]
        generated_files: dict[str, Path] = {}

        username = scan_result.summary.username
        # Safely replace invalid characters in username for file naming
        safe_username = "".join(c for c in username if c.isalnum() or c in ("-", "_")).rstrip()

        timestamp_str = scan_result.summary.timestamp.strftime("%Y%m%d_%H%M%S")
        base_filename = f"{safe_username}_report_{timestamp_str}"

        for fmt in target_formats:
            fmt_lower = fmt.lower()
            exporter = self.exporters.get(fmt_lower)
            if not exporter:
                continue

            # HTML disable gate check
            if fmt_lower == "html" and not settings.ENABLE_HTML_EXPORT:
                continue

            file_path = self.output_dir / f"{base_filename}.{fmt_lower}"
            exporter.export(scan_result, file_path)
            generated_files[fmt_lower] = file_path

        return generated_files
