from abc import ABC, abstractmethod
from typing import Dict

class AbstractTemplateRenderer(ABC):
    @abstractmethod
    def render(self, template: str, data: Dict[str, object]) -> str:
        pass