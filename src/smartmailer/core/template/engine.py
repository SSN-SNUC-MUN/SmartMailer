from abc import ABC, abstractmethod
from typing import Optional, Dict

from .parser import AbstractTemplateParser
from .renderer import AbstractTemplateRenderer
from .validator import AbstractTemplateValidator
from .model import AbstractTemplateModel

class AbstractTemplateEngine(ABC):
    @abstractmethod
    def validate(self, model: AbstractTemplateModel) -> None:
        pass

    @abstractmethod
    def render(self, model: AbstractTemplateModel) -> str:
        pass

class TemplateEngine:
    """
    Coordinates parsing, validation, and rendering.
    Validation is mandatory and fail-fast.
    """

    # Public API intentionally matches the old TemplateEngine
    # so SmartMailer does NOT need to change.

    def __init__(
        self,
        parser: AbstractTemplateParser,
        validator: AbstractTemplateValidator,
        renderer: AbstractTemplateRenderer,
        subject: Optional[str] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
    ):
        self.parser = parser
        self.validator = validator
        self.renderer = renderer

        self.subject = subject
        self.text = text
        self.html = html
    
    def _validate_single(self, template: str, model: AbstractTemplateModel) -> None:
        data = model.to_dict()
        template_vars = self.parser.extract_variables(template)

        self.validator.validate_schema(data)
        self.validator.validate_template(template_vars, set(data.keys()))

    def _render_single(self, template: str, model: AbstractTemplateModel) -> str:
        data = model.to_dict()
        return self.renderer.render(template, data)

    def validate(self, model: AbstractTemplateModel) -> None:
        """
        Validate subject, text, and html templates against the model.
        Fail-fast if any template is invalid.
        """

        if self.subject:
            self._validate_single(self.subject, model)

        if self.text:
            self._validate_single(self.text, model)

        if self.html:
            self._validate_single(self.html, model)

    def render(self, model: AbstractTemplateModel) -> Dict[str, str]:
        """
        Validate all templates and render subject, text, and html.
        """

        # Ensure schema & template correctness FIRST
        self.validate(model)

        result = {
            "subject": None,
            "text": None,
            "html": None,
        }

        if self.subject:
            result["subject"] = self._render_single(self.subject, model)

        if self.text:
            result["text"] = self._render_single(self.text, model)

        if self.html:
            result["html"] = self._render_single(self.html, model)

        return result