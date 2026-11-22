from .smartmailer import SmartMailer
from .core.mailer import MailSender
from .core.template import (
    TemplateEngine,
    TemplateModel,
    JinjaTemplateParser,
    JinjaTemplateRenderer,
    TemplateValidator,
)
from .session_management.session_manager import SessionManager

__all__ = [
    "SmartMailer",
    "MailSender",
    "TemplateEngine",
    "TemplateModel",
    "JinjaTemplateParser",
    "JinjaTemplateRenderer",
    "TemplateValidator",
    "SessionManager",
]

__version__ = "1.0.0"
