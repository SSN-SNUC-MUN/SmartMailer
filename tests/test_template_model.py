from pydantic import ValidationError
import pytest
from smartmailer.core.template.model import TemplateModel

def test_template_model_valid():
    class UserTemplate(TemplateModel):
        name: str
        age: int

    model = UserTemplate(name="ABC", age=20)

    assert model.name == "ABC"
    assert model.age == 20
    assert isinstance(model.hash_string, str)


def test_template_model_invalid_field_name():
    with pytest.raises(ValidationError):
        class BadTemplate(TemplateModel):
            Name: str

        BadTemplate(Name="test")

def test_template_model_to_dict():
    class UserTemplate(TemplateModel):
        name: str
        age: int

    model = UserTemplate(name="ABC", age=20)
    data = model.to_dict()

    assert data == {"name": "ABC", "age": 20}
