from pathlib import Path

from src.models import ScanResult
from src.report_generator import ReportGenerator


def test_report_generator_all_formats(tmp_path: Path, sample_scan_result: ScanResult):
    generator = ReportGenerator(output_dir=tmp_path)

    # Generate all formats
    saved_files = generator.generate_reports(sample_scan_result)

    assert "json" in saved_files
    assert "csv" in saved_files
    assert "txt" in saved_files
    assert "html" in saved_files

    assert saved_files["json"].exists()
    assert saved_files["csv"].exists()
    assert saved_files["txt"].exists()
    assert saved_files["html"].exists()


def test_report_generator_selective_formats(tmp_path: Path, sample_scan_result: ScanResult):
    generator = ReportGenerator(output_dir=tmp_path)

    # Generate only json and txt formats
    saved_files = generator.generate_reports(sample_scan_result, formats=["json", "txt"])

    assert "json" in saved_files
    assert "txt" in saved_files
    assert "csv" not in saved_files
    assert "html" not in saved_files

    assert saved_files["json"].exists()
    assert saved_files["txt"].exists()
