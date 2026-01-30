import pytest
from unittest.mock import patch, MagicMock, mock_open
from smartmailer.core.mailer import MailSender
import smtplib

SETTINGS_JSON = '{"gmail": ["smtp.gmail.com", 587]}'

# ---------- Constructor Tests ----------

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_init_valid_email(mock_path, mock_file):
    sender = MailSender("user@gmail.com", "pass123")
    assert sender.sender_email == "user@gmail.com"
    assert sender.smtp_server == "smtp.gmail.com"
    assert sender.smtp_port == 587

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_init_invalid_email(mock_path, mock_file):
    with pytest.raises(ValueError):
        MailSender("invalid-email", "pass123")

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_invalid_provider(mock_path, mock_file):
    with pytest.raises(ValueError):
        MailSender("user@gmail.com", "pass123", provider="unknown")

# ---------- Message Preparation Tests ----------

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_prepare_message_basic(mock_path, mock_file):
    sender = MailSender("user@gmail.com", "pass")
    msg = sender.prepare_message(
        to_email="target@example.com",
        subject="Test",
        text_content="Hello",
        html_content="<p>Hello</p>",
        cc=["cc@example.com"],
        bcc=["bcc@example.com"]
    )
    msg_str = msg.as_string()
    assert msg["To"] == "target@example.com"
    assert msg["Subject"] == "Test"
    assert "Hello" in msg_str
    assert "<p>Hello</p>" in msg_str

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_prepare_message_html_only(mock_path, mock_file):
    sender = MailSender("user@gmail.com", "pass")
    msg = sender.prepare_message(
        to_email="target@example.com",
        html_content="<b>Only HTML</b>"
    )
    assert "<b>Only HTML</b>" in msg.as_string()

@patch("os.path.join", return_value="settings.json")
@patch("smartmailer.core.mailer.open")
def test_prepare_message_with_attachment(mock_open_func, mock_path):
    def open_side_effect(file, *args, **kwargs):
        if file == "settings.json":
            return mock_open(read_data=SETTINGS_JSON).return_value
        elif file == "/path/to/file.txt":
            return mock_open(read_data="filedata").return_value
        else:
            raise FileNotFoundError()
    mock_open_func.side_effect = open_side_effect

    sender = MailSender("user@gmail.com", "pass")
    msg = sender.prepare_message(
        to_email="target@example.com",
        subject="Test",
        attachment_paths=["/path/to/file.txt"]
    )
    assert "file.txt" in msg.as_string()

@patch("os.path.join", return_value="settings.json")
@patch("smartmailer.core.mailer.open")
def test_prepare_message_attachment_failure(mock_open_func, mock_path):
    def open_side_effect(file, *args, **kwargs):
        if file == "settings.json":
            return mock_open(read_data=SETTINGS_JSON).return_value
        else:
            raise FileNotFoundError()
    mock_open_func.side_effect = open_side_effect

    sender = MailSender("user@gmail.com", "pass")
    msg = sender.prepare_message(
        to_email="target@example.com",
        attachment_paths=["/missing/file.txt"]
    )
    assert "target@example.com" in msg.as_string()

# ---------- Send Individual Tests ----------

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_send_individual_mail_success(mock_path, mock_file):
    sender = MailSender("user@gmail.com", "pass")
    mock_server = MagicMock(spec=smtplib.SMTP)
    result = sender.send_individual_mail(
        server=mock_server,
        to_email="target@example.com",
        text_content="Text",
    )
    assert result is True
    assert mock_server.sendmail.called

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_send_individual_mail_failure(mock_path, mock_file):
    sender = MailSender("user@gmail.com", "pass")
    mock_server = MagicMock(spec=smtplib.SMTP)
    mock_server.sendmail.side_effect = Exception("fail")
    result = sender.send_individual_mail(
        server=mock_server,
        to_email="target@example.com",
        text_content="Text",
    )
    assert result is False

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
def test_send_individual_mail_no_content(mock_path, mock_file):
    sender = MailSender("user@gmail.com", "pass")
    mock_server = MagicMock(spec=smtplib.SMTP)
    with pytest.raises(ValueError):
        sender.send_individual_mail(mock_server, "target@example.com")

# ---------- Internal Validation ----------

def test_validate_invalid_email():
    sender = MailSender.__new__(MailSender)
    with pytest.raises(ValueError):
        sender._validate_email("bad-email")

def test_is_valid_email():
    sender = MailSender.__new__(MailSender)
    assert sender._is_valid_email("abc@example.com")
    assert not sender._is_valid_email("bad-email")

# ---------- Preview Email ----------

def test_preview_email_output(capsys):
    sender = MailSender.__new__(MailSender)
    sender.preview_email({
        "to_email": "test@example.com",
        "subject": "Hello",
        "text_content": "Plain",
        "html_content": "<p>HTML</p>"
    })
    output = capsys.readouterr().out
    assert "PREVIEW:" in output
    assert "Plain" in output
    assert "HTML" in output

# ---------- Send Bulk Mail ----------

@patch("builtins.open", new_callable=mock_open, read_data=SETTINGS_JSON)
@patch("os.path.join", return_value="settings.json")
@patch("smtplib.SMTP")
@patch("time.sleep", return_value=None)
@patch("smartmailer.core.mailer.MailSender.preview_email")
@patch("sys.exit")
def test_send_bulk_mail_basic(mock_exit, mock_preview, mock_sleep, mock_smtp, mock_path, mock_file):
    smtp_instance = mock_smtp.return_value
    smtp_instance.sendmail.return_value = True

    mock_session = MagicMock()
    mock_session.add_recipient = MagicMock()

    sender = MailSender("user@gmail.com", "pass")
    recipients = [
        {
            "object": MagicMock(),
            "to_email": "r1@example.com",
            "text_content": "Hello",
            "attachments": [],
            "cc": [],
            "bcc": [],
        },
        {
            "object": MagicMock(),
            "text_content": "Missing email field"
        }
    ]
    sender.send_bulk_mail(recipients, session_manager=mock_session)

    assert smtp_instance.sendmail.called
    assert mock_session.add_recipient.called
    mock_exit.assert_called_once_with(0)

@patch("smtplib.SMTP")
@patch("time.sleep", return_value=None)
@patch("smartmailer.core.mailer.MailSender.preview_email")
@patch("sys.exit")
def test_keyboard_interrupt_during_loop(mock_exit, mock_preview, mock_sleep, mock_smtp):
    smtp_instance = mock_smtp.return_value
    smtp_instance.sendmail.side_effect = KeyboardInterrupt

    sender = MailSender("user@gmail.com", "pass")
    recipients = [{
        "object": MagicMock(),
        "to_email": "test@example.com",
        "text_content": "Hi"
    }]
    session_manager = MagicMock()
    sender.send_bulk_mail(recipients, session_manager)
    mock_exit.assert_called_once_with(0)

@patch("time.sleep", side_effect=KeyboardInterrupt)
@patch("sys.exit")
def test_keyboard_interrupt_before_loop(mock_exit, mock_sleep):
    sender = MailSender("user@gmail.com", "pass")
    recipients = [{"object": MagicMock(), "to_email": "r@example.com", "text_content": "Hi"}]
    sender.send_bulk_mail(recipients, session_manager=MagicMock())
    mock_exit.assert_called_once_with(0)

@patch("smtplib.SMTP", side_effect=Exception("SMTP error"))
@patch("sys.exit")
def test_smtp_connection_error(mock_exit, mock_smtp):
    sender = MailSender("user@gmail.com", "pass")
    sender.send_bulk_mail([{"object": MagicMock(), "to_email": "x", "text_content": "x"}], session_manager=MagicMock())

@patch("smtplib.SMTP", side_effect=KeyboardInterrupt)
@patch("sys.exit")
def test_keyboard_interrupt_on_connect(mock_exit, mock_smtp):
    sender = MailSender("user@gmail.com", "pass")
    sender.send_bulk_mail([{"object": MagicMock(), "to_email": "x", "text_content": "x"}], session_manager=MagicMock())

@patch("sys.exit")
def test_exit_finally(mock_exit):
    sender = MailSender("user@gmail.com", "pass")
    recipients = [{
        "object": MagicMock(),
        "to_email": "r1@example.com",
        "text_content": "Test message"
    }]
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp_instance = mock_smtp.return_value
        mock_smtp_instance.sendmail.return_value = None
        sender.send_bulk_mail(recipients, session_manager=MagicMock())
    mock_exit.assert_called_once_with(0)