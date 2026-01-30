import pytest
from unittest.mock import patch, MagicMock
from smartmailer.core.template.engine import TemplateEngine


class DummyModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def model_dump(self):
        return self.__dict__


@pytest.fixture
def parser():
    p = MagicMock()
    return p

@pytest.fixture
def validator():
    v = MagicMock()
    return v

@pytest.fixture
def renderer():
    r = MagicMock()
    return r

@pytest.fixture
def model():
    return DummyModel(name="abc", id=10)


def test_basic_render(parser, validator, renderer, model):
    parser.extract_variables.return_value = {"name"}
    renderer.render.return_value = "Hello abc"

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        text="Hello {{ name }}"
    )

    result = engine.render(model)

    assert result["text"] == "Hello abc"
    assert result["subject"] is None
    assert result["html"] is None


def test_multiple_variables(parser, validator, renderer, model):
    parser.extract_variables.return_value = {"name", "id"}
    renderer.render.return_value = "User abc 10"

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        text="User {{ name }} {{ id }}"
    )

    result = engine.render(model)

    assert result["text"] == "User abc 10"


def test_missing_variable_raises(parser, validator, renderer, model):
    parser.extract_variables.return_value = {"name", "age"}
    validator.validate_template.side_effect = ValueError("Missing variables")

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        text="Hello {{ name }} {{ age }}"
    )

    with pytest.raises(ValueError):
        engine.render(model)


def test_empty_template(parser, validator, renderer, model):
    parser.extract_variables.return_value = set()
    renderer.render.return_value = ""

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        text=""
    )

    result = engine.render(model)

    assert result["text"] == ""


def test_no_placeholders(parser, validator, renderer, model):
    parser.extract_variables.return_value = set()
    renderer.render.return_value = "Hello world"

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        text="Hello world"
    )

    result = engine.render(model)

    assert result["text"] == "Hello world"


def test_render_with_subject_and_html(parser, validator, renderer, model):
    parser.extract_variables.return_value = {"name"}
    renderer.render.side_effect = lambda t, d: f"Rendered {t}"

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        subject="Subject {{ name }}",
        text="Text {{ name }}",
        html="HTML {{ name }}"
    )

    result = engine.render(model)

    assert result["subject"] == "Rendered Subject {{ name }}"
    assert result["text"] == "Rendered Text {{ name }}"
    assert result["html"] == "Rendered HTML {{ name }}"


class ToDictModel:
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"name": self.name}


def test_validate_single_with_to_dict(parser, validator, renderer):
    parser.extract_variables.return_value = {"name"}
    model = ToDictModel("abc")
    engine = TemplateEngine(parser, validator, renderer, text="Hello {{ name }}")
    result = engine.render(model)
    assert result["text"] == renderer.render.return_value


def test_validator_called(parser, validator, renderer, model):
    parser.extract_variables.return_value = {"name"}
    renderer.render.return_value = "OK"

    engine = TemplateEngine(
        parser=parser,
        validator=validator,
        renderer=renderer,
        text="Hello {{ name }}"
    )

    engine.render(model)

    validator.validate_schema.assert_called_once()
    validator.validate_template.assert_called_once()