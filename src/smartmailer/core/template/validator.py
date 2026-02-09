from abc import ABC, abstractmethod
from typing import Dict, Set
import re
import keyword

class AbstractTemplateValidator(ABC):
    @abstractmethod
    def validate_template(self,template_vars: Set[str],data_keys: Set[str]) -> None:
        pass

class TemplateValidator(AbstractTemplateValidator):
    """
    Validates Template variables against schema keys
    """
    
    def validate_template(self, template_vars: Set[str], data_keys: Set[str]) -> None:
        undefined = template_vars - data_keys
        if undefined:
            raise ValueError(
                f"Template references undefined variables: {sorted(undefined)}"
            )