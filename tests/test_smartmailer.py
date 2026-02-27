import pytest
from unittest.mock import patch, MagicMock
from smartmailer.smartmailer import SmartMailer


@pytest.fixture
def mock_dependencies():
    with patch("smartmailer.smartmailer.MailSender") as mock_mailer_cls, \
         patch("smartmailer.smartmailer.TemplateEngine") as mock_template_cls, \
         patch("smartmailer.smartmailer.SessionManager") as mock_session_cls:

        mock_mailer = MagicMock()
        mock_mailer_cls.return_value = mock_mailer

        mock_template = MagicMock()
        mock_template_cls.return_value = mock_template

        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        yield {
            "mailer": mock_mailer,
            "template": mock_template,
            "session": mock_session
        }


@pytest.fixture
def dummy_recipients():
    class Dummy:
        def __init__(self, email, hash_):
            self.__dict__["email"] = email
            self.hash_string = hash_
    return [Dummy("a@example.com", "h1"), Dummy("b@example.com", "h2")]


def test_send_emails_filters_and_renders(mock_dependencies, dummy_recipients):
    auto = SmartMailer("sender@example.com", "password", "gmail", "testsession")

    mock_session = mock_dependencies["session"]
    mock_mailer = mock_dependencies["mailer"]
    mock_template = mock_dependencies["template"]

    # Pretend no recipients have been sent
    mock_session.filter_sent_recipients.return_value = []

    mock_template.render.side_effect = lambda r: {
        "subject": f"Hello {r.__dict__['email']}",
        "text": f"Hi {r.__dict__['email']}",
        "html": None
    }

    auto.send_emails(recipients=dummy_recipients, email_field="email", template=mock_template)

    assert mock_template.render.call_count == 2
    assert mock_mailer.send_bulk_mail.called

    args, kwargs = mock_mailer.send_bulk_mail.call_args
    assert len(kwargs["recipients"]) == 2
    assert kwargs["session_manager"] == mock_session


def test_send_emails_skips_sent_recipients(mock_dependencies, dummy_recipients):
    auto = SmartMailer("sender@example.com", "password", "gmail", "testsession")

    mock_session = mock_dependencies["session"]
    mock_mailer = mock_dependencies["mailer"]
    mock_template = mock_dependencies["template"]

    # Pretend first recipient already sent
    mock_session.filter_sent_recipients.return_value = [dummy_recipients[0]]

    auto.send_emails(recipients=dummy_recipients, email_field="email", template=mock_template)

    # render called only once (for second recipient)
    assert mock_template.render.call_count == 1
    sent_to = mock_template.render.call_args[0][0]
    assert sent_to.__dict__["email"] == "b@example.com"


def test_show_sent_prints(mock_dependencies):
    auto = SmartMailer("sender@example.com", "pass", "gmail", "mysession")
    mock_session = mock_dependencies["session"]

    mock_session.get_sent_recipients.return_value = [
        {"recipient_hash": "h1", "sent_time": "time1"},
        {"recipient_hash": "h2", "sent_time": "time2"},
    ]

    auto.show_sent()

    mock_session.get_sent_recipients.assert_called_once()

def test_rendering_exception_is_skipped(mock_dependencies, dummy_recipients):
    auto = SmartMailer("sender@example.com", "password", "gmail", "error-session")

    mock_template = mock_dependencies["template"]
    mock_mailer = mock_dependencies["mailer"]
    mock_session = mock_dependencies["session"]

    def render_side_effect(recipient):
        if recipient.__dict__["email"] == "b@example.com":
            raise ValueError("Template failed")
        return {"subject": "Ok", "text": "Body"}

    mock_template.render.side_effect = render_side_effect
    mock_session.filter_sent_recipients.return_value = []

    auto.send_emails(dummy_recipients, email_field="email", template=mock_template)

    recipients_arg = mock_mailer.send_bulk_mail.call_args[1]["recipients"]

    assert len(recipients_arg) == 1
    assert recipients_arg[0]["to_email"] == "a@example.com"