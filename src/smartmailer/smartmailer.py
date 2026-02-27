from smartmailer.core.template.engine import TemplateEngine
from smartmailer.core.mailer import MailSender
from smartmailer.session_management.session_manager import SessionManager
from typing import List
from smartmailer.utils.new_logger import Logger
from smartmailer.utils.types import TemplateModelType


class SmartMailer:
    def __init__(
        self,
        sender_email: str,
        password: str,
        provider: str,
        session_name: str,
        log_to_file: bool = False,
        log_level: str = 'WARNING'
    ):

        self.logger = Logger(log_to_file=log_to_file, log_level=log_level)

        self.mailer = MailSender(sender_email, password, provider)
        self.session_manager = SessionManager(session_name)

    def send_emails(
        self,
        recipients: List[TemplateModelType],
        email_field: str,
        template: TemplateEngine,
        attachment_paths=None,
        cc=None,
        bcc=None,
        cc_field: str = "cc",
        bcc_field: str = "bcc",
        attachment_field: str = "attachments",
        show_preview: bool = True,
        preview_count: int = 5
    ):

        sent = self.session_manager.filter_sent_recipients(recipients)
        rendered_emails = []

        for recipient in recipients:
            if recipient in sent:
                continue

            try:
                rendered = template.render(recipient)
            except Exception as e:
                email = recipient.__dict__.get(email_field, "unknown")
                self.logger.error(f"Error rendering email for {email}: {e}")
                continue

            rendered_emails.append({
                "object": recipient,
                "to_email": recipient.__dict__[email_field],
                "subject": rendered.get("subject", ""),
                "text_content": rendered.get("text", ""),
                "html_content": rendered.get("html"),
                "attachments": recipient.__dict__.get(attachment_field) or [],
                "cc": recipient.__dict__.get(cc_field) or [],
                "bcc": recipient.__dict__.get(bcc_field) or [],
            })

        self.mailer.send_bulk_mail(
            recipients=rendered_emails,
            session_manager=self.session_manager,
            attachment_paths=attachment_paths,
            cc=cc,
            bcc=bcc,
            show_preview=show_preview,
            preview_timer=preview_count
        )

    def show_sent(self):
        sent = self.session_manager.get_sent_recipients()
        print("Sent Recipients:")
        for entry in sent:
            print(entry)