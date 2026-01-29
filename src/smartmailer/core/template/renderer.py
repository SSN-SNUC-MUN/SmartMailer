from abc import ABC, abstractmethod
from typing import Dict
from jinja2 import Environment, TemplateError


class AbstractTemplateRenderer(ABC):
    @abstractmethod
    def render(self, template: str, data: Dict[str, object]) -> str:
        pass

class JinjaTemplateRenderer(AbstractTemplateRenderer):
    """
    Renders a Jinja2 template using provided data.
    """

    def __init__(self, env: Environment):
        self.env = env

    def render(self, template: str, data: Dict[str, object]) -> str:
        try:
            tmpl = self.env.from_string(template)
            return tmpl.render(data)
        except TemplateError as e:
            raise ValueError(f"Jinja rendering failed: {e}")