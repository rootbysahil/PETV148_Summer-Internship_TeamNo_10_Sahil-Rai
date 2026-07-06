from src.banner import print_banner, print_disclaimer
from src.models import ScanResult
from src.ui import RichUI


def test_banner_printing():
    # Verify banner prints run without exceptions
    print_banner()
    print_disclaimer()


def test_ui_panels(sample_scan_result: ScanResult):
    # Verify Rich UI methods render without raising exceptions
    RichUI.render_error("Test Error", "This is a test error panel")
    RichUI.render_warning("Test Warning", "This is a test warning panel")
    RichUI.render_info("Test Info", "This is a test info panel")

    RichUI.render_results_table(sample_scan_result)
    RichUI.render_summary_panel(sample_scan_result.summary)


def test_ui_progress():
    progress = RichUI.get_progress_renderer()
    assert progress is not None
