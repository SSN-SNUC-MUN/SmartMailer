from abc import ABC, abstractmethod
from typing import Dict, Type, Optional
from pydantic import BaseModel, model_validator, computed_field
import re
import json
import keyword

class AbstractTemplateModel(BaseModel, ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, object]:
        pass
    
    @property
    @abstractmethod
    def hash_string(self)-> str:
        pass

class TemplateModel(AbstractTemplateModel):
    """
    Concrete TemplateModel used by SmartMailer.
    Defines the schema for allowed template variables.
    """

    @model_validator(mode='after')
    def check_lowercase_identifier(self):
        for name in self.__dict__:
            if (
                not name.isidentifier()
                or not name.islower()
                or keyword.iskeyword(name)
            ):
                raise ValueError(
                    f"Field '{name}' must be a lowercase Python identifier."
                )
        return self
    
    def to_dict(self) -> Dict[str, object]:
        return self.model_dump()

    @computed_field
    @property
    def hash_string(self) -> str:
        """
        Returns a hash of the model's fields.
        This is used to uniquely identify the template model.
        """
        # we cant do model_dump because it keeps recursively calling this computed field
        dump = self.model_json_schema()
        res = {}
        for key in dump["properties"].keys():
            res[key] = self.__dict__.get(key, None)
        return json.dumps(res)