import os
import re
from datetime import datetime
from smartmailer.utils.new_logger import Logger

def test_log_directory_created(tmp_path):
    logger = Logger(log_to_file=True, log_level="INFO")
    assert os.path.exists("smartmailer_logs")
    logger.log_file_handle.close()

def test_invalid_log_level_defaults_to_info(capsys):
    logger = Logger(log_to_file=False, log_level="INVALID")
    logger.info("Hello world")
    captured = capsys.readouterr()
    assert "INFO" in captured.out

def test_console_logging_with_colored_output(capsys):
    logger = Logger(log_to_file=False, log_level="INFO")
    logger.warning("Watch out!")
    captured = capsys.readouterr()
    # Should have ANSI color codes for yellow
    assert "\033" in captured.out
    assert "WARNING" in captured.out

def test_file_logging():
    logger = Logger(log_to_file=True, log_level="INFO")
    logger.info("File log test")
    logger.log_file_handle.close()

    # Find the latest log file inside smartmailer_logs
    log_files = os.listdir("smartmailer_logs")
    assert log_files, "No log files created"
    latest_log = max(
        [os.path.join("smartmailer_logs", f) for f in log_files],
        key=os.path.getctime
    )
    with open(latest_log, "r") as f:
        content = f.read()
    assert "File log test" in content

def test_log_format_contains_timestamp_and_context(capsys):
    logger = Logger(log_to_file=False, log_level="INFO")
    logger.info("Format check")
    captured = capsys.readouterr()

    # Regex: YYYY-MM-DD HH:MM:SS | LEVEL | file:line | message
    pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| INFO \| .* \| Format check"
    assert re.search(pattern, captured.out)
