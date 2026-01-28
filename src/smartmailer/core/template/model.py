from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from pydantic import BaseModel, model_validator
import re

class AbstractTemplateModel(BaseModel, ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, object]:
        pass
    
    @property
    @abstractmethod
    def hash_string(self)-> str:
        pass

