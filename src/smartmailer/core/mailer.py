import asyncio
import aiosmtplib

import re
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import json
from typing import Optional, Any, Dict, List, Tuple

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

    def _get_settings(self, provider: str) -> Tuple[str, int]:
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        with open(settings_path, 'r') as f:
            settings: Dict[str, List[Any]] = json.load(f)

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
            logger = getattr(self, "logger", None)
            if logger:
                logger.error(f"Invalid email address: {email}")
            raise ValueError("Invalid email address format.")
        return True
    
    def prepare_message(
        self,
        to_email: str,
        subject: Optional[str] = None,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None,
        attachment_paths: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
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
    
    async def _create_smtp_connection(self) -> aiosmtplib.SMTP:
        smtp = aiosmtplib.SMTP(
            hostname=self.smtp_server,
            port=self.smtp_port,
            use_tls=False,
        )
        await smtp.connect()
        await smtp.starttls()
        await smtp.login(self.sender_email, self.password)
        return smtp
        
            
    async def _send_individual_mail(
        self,
        smtp: aiosmtplib.SMTP,
        to_email: str,
        subject: Optional[str] = None,
        text_content: Optional[str] = None,
        html_content: Optional[str] = None,
        attachment_paths: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
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
            await smtp.send_message(msg)
            self.logger.info(f"Email sent to {to_email} successfully.")
            return True
        except Exception as e:
            self.logger.error(f"Couldn't send email to {to_email}: {e}")
            return False
        
    def preview_email(self, example: Dict[str, Any], timer:int=5) -> None:
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
        recipients: List[Dict[str, Any]],
        session_manager: SessionManager,
        attachment_paths: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        show_preview: bool = True,
        preview_timer: int = 5
    ) -> None:
        asyncio.run(
            self._send_bulk_mail_async(
                recipients,
                session_manager,
                attachment_paths,
                cc,
                bcc,
                show_preview,
                preview_timer,
            )
        )


    async def _send_bulk_mail_async(
        self,
        recipients: List[Dict[str, Any]],
        session_manager: SessionManager,
        attachment_paths: Optional[List[str]],
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        show_preview: bool,
        preview_timer: int,
    ) -> None:

        if show_preview and recipients:
            first = recipients[0]
            self.preview_email(first, timer=preview_timer)
            if preview_timer and preview_timer > 0:
                await asyncio.sleep(preview_timer)

        pool_size = 5
        semaphore = asyncio.Semaphore(pool_size)
        connection_queue: asyncio.Queue[aiosmtplib.SMTP] = asyncio.Queue()

        self.logger.info(f"Creating SMTP connection pool of size {pool_size}")

        for _ in range(pool_size):
            smtp = await self._create_smtp_connection()
            await connection_queue.put(smtp)

        self.logger.info("SMTP connection pool ready.")

        async def worker(row: Dict[str, Any]):

            to_email = row.get("to_email")
            if not isinstance(to_email, str):
                self.logger.error(f"Invalid 'to_email': {to_email}. Skipping.")
                return

            async with semaphore:
                smtp = await connection_queue.get()

                try:

                    recipients_list = [to_email]

                    row_cc = row.get("cc", cc)
                    row_bcc = row.get("bcc", bcc)

                    if row_cc:
                        recipients_list.extend(row_cc)
                    if row_bcc:
                        recipients_list.extend(row_bcc)


                    msg = self.prepare_message(
                        to_email=to_email,
                        subject=row.get("subject"),
                        text_content=row.get("text_content"),
                        html_content=row.get("html_content"),
                        attachment_paths=row.get("attachments", attachment_paths),
                        cc=row_cc,
                        bcc=None,
                    )

                    await smtp.send_message(msg, recipients=recipients_list)

                    self.logger.info(f"Email sent to {to_email} successfully.")

                    if session_manager:
                        session_manager.add_recipient(row["object"])

                except Exception as e:
                    self.logger.error(f"Error sending email to {to_email}: {e}")

                    try:
                        await smtp.quit()
                    except Exception:
                        pass

                    smtp = await self._create_smtp_connection()

                finally:
                    await connection_queue.put(smtp)


        tasks = [worker(row) for row in recipients]
        await asyncio.gather(*tasks)


        self.logger.info("Closing SMTP connection pool.")

        while not connection_queue.empty():
            smtp = await connection_queue.get()
            try:
                await smtp.quit()
            except Exception:
                pass

        self.logger.info("All SMTP connections closed.")