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
        if hasattr(model, "to_dict"):
            data = model.to_dict()
        elif hasattr(model, "model_dump"):   # pydantic support
            data = model.model_dump()
        else:
            data = model.__dict__

        template_vars = self.parser.extract_variables(template)

        self.validator.validate_template(template_vars, set(data.keys()))

    def _render_single(self, template: str, model: AbstractTemplateModel) -> str:
        if hasattr(model, "to_dict"):
            data = model.to_dict()
        elif hasattr(model, "model_dump"):   # pydantic support
            data = model.model_dump()
        else:
            data = model.__dict__

        return self.renderer.render(template, dict(data))

    def validate(self, model: AbstractTemplateModel) -> None:
        """
        Validate subject, text, and html templates against the model.
        Fail-fast if any template is invalid.
        """

        if self.subject is not None:
            self._validate_single(self.subject, model)

        if self.text is not None:
            self._validate_single(self.text, model)

        if self.html is not None:
            self._validate_single(self.html, model)

    def render(self, model: AbstractTemplateModel, validate: bool = True) -> Dict[str, Optional[str]]:
        """
        Validate all templates and render subject, text, and html.
        """
        if validate:
            self.validate(model)

        result: Dict[str, Optional[str]] = {
            "subject": None,
            "text": None,
            "html": None,
        }

        if self.subject is not None:
            result["subject"] = self._render_single(self.subject, model)

        if self.text is not None:
            result["text"] = self._render_single(self.text, model)
        if self.html is not None:
            result["html"] = self._render_single(self.html, model)

        return result