import smtplib
import re
import os
import time
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import json
from typing import Optional, Any

from smartmailer.session_management.session_manager import SessionManager
from smartmailer.utils.new_logger import Logger
from smartmailer.utils.types import TemplateModelType

class MailSender:
    def __init__(self, sender_email: str, password: str, provider: str = "gmail") -> None:
        self.logger = Logger()
        
        self._validate_email(sender_email)
        self.sender_email = sender_email
        self.password = password
        self.smtp_server, self.smtp_port = self._get_settings(provider)

        self.logger.info(f"MailSender initialized for {sender_email} using {provider} provider.")

    def _get_settings(self, provider: str) -> tuple[str, int]:
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        with open(settings_path, 'r') as f:
            settings: dict[str, list[Any]] = json.load(f)

        if provider not in settings:
            self.logger.error(f"Provider '{provider}' not found in settings.")
            raise ValueError("Invalid provider.")
        return tuple(settings[provider])  # type: ignore

    #check email format using regex
    def _is_valid_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_email(self, email: str) -> bool:
        if not self._is_valid_email(email):
            self.logger.error(f"Invalid email address: {email}")
            raise ValueError("Invalid email address format.")
        return True
    
    def prepare_message(
        self,
        to_email: str,
        subject: Optional[str] = None,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None,
        attachment_paths: Optional[list[str]] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> MIMEMultipart:
        
        
        msg = MIMEMultipart("mixed")
        msg["From"] = self.sender_email
        msg["To"] = to_email
        if subject:
            msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)

        if text_content and html_content:
            body = MIMEMultipart("alternative")
            body.attach(MIMEText(text_content, "plain"))
            body.attach(MIMEText(html_content, "html"))
            msg.attach(body)

        elif text_content:
            msg.attach(MIMEText(text_content, "plain"))
        elif html_content:
            msg.attach(MIMEText(html_content, "html"))

        if attachment_paths:
            for file_path in attachment_paths:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                        msg.attach(part)
                except Exception as e:
                    self.logger.warning(f"Couldn't attach file '{file_path}': {e}")
        return msg
        

    def send_individual_mail(
        self,
        server: smtplib.SMTP,
        to_email: str,
        subject: Optional[str] = None,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None,
        attachment_paths: Optional[list[str]] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> bool:
        
        self._validate_email(to_email)

        if not text_content and not html_content:
            self.logger.warning("Attempted to send an email with no content.")
            raise ValueError("At least one content type must be provided.")

        msg = self.prepare_message(
            to_email=to_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            attachment_paths=attachment_paths,
            cc=cc,
            bcc=bcc)

        try:
            server.sendmail(self.sender_email,
                            [to_email] + (cc or []) + (bcc or []), 
                            msg.as_string())
            self.logger.info(f"Email sent to {to_email} successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Couldn't send email to {to_email}: {e}")
            return False
        
    def preview_email(self, example: dict[str, Any], timer:int) -> None:
        print("\nPREVIEW:")
        print(f"To          : {example.get('to_email')}")
        print(f"Subject     : {example.get('subject')}")
        print("\nBODY (TEXT):")
        print(example.get('text_content') or "(no text content)")
        print("\nBODY (HTML):")
        print(example.get('html_content') or "(no HTML content)")
        print("\n\n")
        print(f"Sending will start in {timer} seconds...Press Ctrl+C to cancel.")


    def send_bulk_mail(
        self,
        recipients: list[dict[str, Any]],
        session_manager: SessionManager,
        attachment_paths: Optional[list[str]] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
        show_preview: bool = True,
        preview_timer: int = 5
    ) -> None:
        server = None
        server_closed = False
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.password)
            self.logger.info(f"Connected to SMTP server {self.smtp_server} as {self.sender_email}")
        
            if show_preview and recipients:
                first = recipients[0]
                self.preview_email(first, timer= preview_timer)
                if preview_timer and preview_timer > 0:
                    try:
                        time.sleep(preview_timer)
                    except KeyboardInterrupt:
                        self.logger.info("Email sending canceled by user.")
                        if server and not server_closed:
                            server.quit()
                            self.logger.info("SMTP server connection closed.")
                            server_closed = True
                        sys.exit(0)

            for row in recipients:
                    try:
                        object: TemplateModelType = row['object'] # type: ignore
                        to_email = row.get("to_email")
                        subject = row.get("subject")
                        text = row.get("text_content")
                        html = row.get("html_content")
                        r_attachment_paths = row.get("attachments", attachment_paths)
                        r_cc = row.get("cc", cc)
                        r_bcc = row.get("bcc", bcc)

                        if not to_email:
                            self.logger.error("Recipient email address is missing.")
                            continue

                    
                        sent = self.send_individual_mail(
                                server=server,
                                to_email=to_email,
                                subject=subject,
                                text_content=text,
                                html_content=html,
                                attachment_paths=r_attachment_paths,
                                cc=r_cc,
                                bcc=r_bcc
                        )

                        if sent and session_manager:
                            session_manager.add_recipient(object)

                        if not sent:
                            self.logger.warning(f"Couldn't send email to {to_email}.")

                    except KeyboardInterrupt:
                        self.logger.info("Email sending canceled by user.")
                        if server and not server_closed:
                            server.quit()
                            self.logger.info("SMTP server connection closed.")
                            server_closed = True
                        sys.exit(0)

                    except Exception as e:
                        self.logger.error(f"Error during email sending: {e}")
                        continue

        except KeyboardInterrupt:
            self.logger.info("Email sending canceled by user.")
        except Exception as e:
            self.logger.error(f"Error connecting to server: {e}")
        finally:
            if server and not server_closed:
                try:
                    server.quit()
                    self.logger.info("SMTP server connection closed.")
                except Exception as e:
                    self.logger.error(f"Error closing SMTP server connection: {e}")
                finally:
                    sys.exit(0)
