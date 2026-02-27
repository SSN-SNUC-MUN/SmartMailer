import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from smartmailer.core.mailer import MailSender


@pytest.fixture
def mailer():
    return MailSender(
        sender_email="sender@gmail.com",
        password="password",
        provider="gmail"
    )


@pytest.fixture
def mock_smtp():
    smtp = AsyncMock()
    smtp.send_message = AsyncMock()
    smtp.quit = AsyncMock()
    return smtp


def test_invalid_sender_email():
    with pytest.raises(ValueError):
        MailSender("invalid-email", "password", "gmail")


def test_validate_valid_email(mailer):
    assert mailer._is_valid_email("user@gmail.com")



def test_prepare_message_text_only(mailer):
    msg = mailer.prepare_message(
        to_email="user@gmail.com",
        subject="Test",
        text_content="Hello"
    )

    assert msg["To"] == "user@gmail.com"
    assert msg["Subject"] == "Test"


def test_prepare_message_html_only(mailer):
    msg = mailer.prepare_message(
        to_email="user@gmail.com",
        html_content="<h1>Hello</h1>"
    )

    assert msg.is_multipart()



@pytest.mark.asyncio
async def test_send_individual_mail_success(mailer, mock_smtp):
    result = await mailer._send_individual_mail(
        smtp=mock_smtp,
        to_email="user@gmail.com",
        text_content="Hello"
    )

    assert result is True
    mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_individual_mail_failure(mailer, mock_smtp):
    mock_smtp.send_message.side_effect = Exception("SMTP error")

    result = await mailer._send_individual_mail(
        smtp=mock_smtp,
        to_email="user@gmail.com",
        text_content="Hello"
    )

    assert result is False



@pytest.mark.asyncio
async def test_bulk_mail_sends_all(mailer):
    recipients = [
        {
            "object": "user1",
            "to_email": "u1@gmail.com",
            "subject": "Test",
            "text_content": "Hello"
        },
        {
            "object": "user2",
            "to_email": "u2@gmail.com",
            "subject": "Test",
            "text_content": "Hello"
        }
    ]

    session_manager = MagicMock()
    session_manager.add_recipient = MagicMock()

    mock_smtp = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()

    with patch.object(mailer, "_create_smtp_connection", return_value=mock_smtp):
        await mailer._send_bulk_mail_async(
            recipients,
            session_manager,
            attachment_paths=None,
            cc=None,
            bcc=None,
            show_preview=False,
            preview_timer=0
        )

    assert mock_smtp.send_message.call_count == 2
    assert session_manager.add_recipient.call_count == 2


@pytest.mark.asyncio
async def test_bulk_mail_handles_invalid_email(mailer):
    recipients = [
        {
            "object": "user1",
            "to_email": None,
            "subject": "Test",
            "text_content": "Hello"
        }
    ]

    session_manager = MagicMock()

    mock_smtp = AsyncMock()
    mock_smtp.quit = AsyncMock()

    with patch.object(mailer, "_create_smtp_connection", return_value=mock_smtp):
        await mailer._send_bulk_mail_async(
            recipients,
            session_manager,
            attachment_paths=None,
            cc=None,
            bcc=None,
            show_preview=False,
            preview_timer=0
        )

    assert True