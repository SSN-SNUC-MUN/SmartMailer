from abc import ABC, abstractmethod
from typing import Set


class AbstractTemplateParser(ABC):
    @abstractmethod
    def extract_variables(self, template: str) -> Set[str]:
        pass
