from abc import ABC, abstractmethod
from typing import Dict, Set

class AbstractTemplateValidator(ABC):
    @abstractmethod
    def validate_schema(self, data: Dict[str, object]) -> None:
        pass

    @abstractmethod
    def validate_template(self,template_vars: Set[str],data_keys: Set[str]) -> None:
        pass