from abc import ABC, abstractmethod
from typing import Dict, Set
import re
import keyword

class AbstractTemplateValidator(ABC):
    @abstractmethod
    def validate_schema(self, data: Dict[str, object]) -> None:
        pass

    @abstractmethod
    def validate_template(self,template_vars: Set[str],data_keys: Set[str]) -> None:
        pass

class TemplateValidator(AbstractTemplateValidator):
    """
    Validates:
    1. Schema correctness
    2. Template variables against schema keys
    """

    def validate_schema(self, data: Dict[str, object]) -> None:
        for key in data.keys():
            if not key.isidentifier() or not key.islower() or keyword.iskeyword(key):
                raise ValueError(
                    f"Invalid schema field '{key}'. Must be a lowercase Python identifier."
                )
    
    def validate_template(self, template_vars: Set[str], data_keys: Set[str]) -> None:
        undefined = template_vars - data_keys
        if undefined:
            raise ValueError(
                f"Template references undefined variables: {sorted(undefined)}"
            )