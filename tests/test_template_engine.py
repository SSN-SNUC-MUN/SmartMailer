import pytest
from unittest.mock import patch, MagicMock
from src.smartmailer.core.template.engine import TemplateEngine


class DummyModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def model_dump(self):
        return self.__dict__


@pytest.fixture
def engine():
    return TemplateEngine()

@pytest.fixture
def model():
    return DummyModel(name="abc", id=10)


def test_basic_render(engine, model):
    with patch.object(engine.parser, "extract_variables", return_value={"name"}), \
         patch.object(engine.validator, "validate_schema"), \
         patch.object(engine.validator, "validate_template"), \
         patch.object(engine.renderer, "render", return_value="Hello abc"):

        result = engine.render("Hello {{ name }}", model)
        assert result == "Hello abc"

def test_multiple_variables(engine, model):
    with patch.object(engine.parser, "extract_variables", return_value={"name", "id"}), \
         patch.object(engine.validator, "validate_schema"), \
         patch.object(engine.validator, "validate_template"), \
         patch.object(engine.renderer, "render", return_value="User abc 10"):

        result = engine.render("User {{ name }} {{ id }}", model)
        assert result == "User abc 10"

def test_empty_template(engine, model):
    with patch.object(engine.parser, "extract_variables", return_value=set()), \
         patch.object(engine.validator, "validate_schema"), \
         patch.object(engine.validator, "validate_template"), \
         patch.object(engine.renderer, "render", return_value=""):

        result = engine.render("", model)
        assert result == ""

def test_missing_variable_raises(engine, model):
    with patch.object(engine.parser, "extract_variables", return_value={"name", "age"}), \
         patch.object(engine.validator, "validate_schema"), \
         patch.object(engine.validator, "validate_template", side_effect=ValueError("Missing variables")):

        with pytest.raises(ValueError):
            engine.render("Hello {{ name }} {{ age }}", model)


def test_no_placeholders(engine, model):
    with patch.object(engine.parser, "extract_variables", return_value=set()), \
         patch.object(engine.validator, "validate_schema"), \
         patch.object(engine.validator, "validate_template"), \
         patch.object(engine.renderer, "render", return_value="Hello world"):

        result = engine.render("Hello world", model)
        assert result == "Hello world"


def test_validator_called(engine, model):
    with patch.object(engine.parser, "extract_variables", return_value={"name"}), \
         patch.object(engine.validator, "validate_schema") as mock_schema, \
         patch.object(engine.validator, "validate_template") as mock_template, \
         patch.object(engine.renderer, "render", return_value="OK"):

        engine.render("Hello {{ name }}", model)

        mock_schema.assert_called_once()
        mock_template.assert_called_once()
