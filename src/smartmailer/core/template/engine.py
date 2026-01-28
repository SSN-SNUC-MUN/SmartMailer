from abc import ABC, abstractmethod

class AbstractTemplateEngine(ABC):
    @abstractmethod
    def render(self, template: str, model) -> str:
        pass