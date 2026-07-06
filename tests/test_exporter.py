import csv
import json
from pathlib import Path

from src.exporter import CsvExporter, HtmlExporter, JsonExporter, TxtExporter
from src.models import ScanResult


def test_json_exporter(tmp_path: Path, sample_scan_result: ScanResult):
    output_file = tmp_path / "test.json"
    exporter = JsonExporter()
    exporter.export(sample_scan_result, output_file)

    assert output_file.exists()
    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)
    assert data["summary"]["username"] == "testuser"
    assert len(data["hits"]) == 3
    assert data["hits"][0]["platform_name"] == "GitHub"


def test_csv_exporter(tmp_path: Path, sample_scan_result: ScanResult):
    output_file = tmp_path / "test.csv"
    exporter = CsvExporter()
    exporter.export(sample_scan_result, output_file)

    assert output_file.exists()
    with open(output_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    assert reader[1] == ["Target Username", "testuser"]
    # Check detail row headers and entries presence
    assert any("GitHub" in row for row in reader)


def test_txt_exporter(tmp_path: Path, sample_scan_result: ScanResult):
    output_file = tmp_path / "test.txt"
    exporter = TxtExporter()
    exporter.export(sample_scan_result, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "SOCIAL MEDIA FOOTPRINTING TOOL" in content
    assert "testuser" in content
    assert "[+] GitHub (coding): https://github.com/testuser" in content


def test_html_exporter(tmp_path: Path, sample_scan_result: ScanResult):
    output_file = tmp_path / "test.html"
    # Resolve default template folder relative to workspace
    templates_dir = Path(__file__).parent.parent / "templates"
    exporter = HtmlExporter(template_dir=templates_dir)
    exporter.export(sample_scan_result, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "SMFT Digital Footprint Scan" in content
    assert "testuser" in content
    assert "https://github.com/testuser" in content
