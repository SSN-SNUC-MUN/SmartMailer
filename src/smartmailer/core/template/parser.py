from abc import ABC, abstractmethod
from typing import Set
from jinja2 import Environment, meta

class AbstractTemplateParser(ABC):
    @abstractmethod
    def extract_variables(self, template: str) -> Set[str]:
        pass

class JinjaTemplateParser(AbstractTemplateParser):
    """
    Extracts undeclared variables from a Jinja2 template.
    """

    def __init__(self, env: Environment):
        self.env = env
    
    def extract_variables(self, template: str) -> Set[str]:
        if not template:
            return set()

        ast = self.env.parse(template)
        return meta.find_undeclared_variables(ast)