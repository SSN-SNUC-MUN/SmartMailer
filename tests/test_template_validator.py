import pytest
from src.smartmailer.core.template.validator import TemplateValidator

def test_validate_schema_valid_data():
    validator = TemplateValidator()
    data = {"username": "abc", "email": "a@b.com"}
    validator.validate_schema(data)


def test_validate_schema_invalid_key():
    validator = TemplateValidator()
    data = {"UserName": "abc"}
    with pytest.raises(ValueError):
        validator.validate_schema(data)

def test_validate_schema_empty_data():
    validator = TemplateValidator()
    data = {}
    validator.validate_schema(data)




def test_validate_template_match():
    validator = TemplateValidator()
    template_vars = {"username", "email"}
    data_keys = {"username", "email", "age"}
    validator.validate_template(template_vars, data_keys)

def test_validate_template_missing_variable():
    validator = TemplateValidator()
    template_vars = {"username", "email"}
    data_keys = {"username"}
    with pytest.raises(ValueError):
        validator.validate_template(template_vars, data_keys)


def test_validate_template_empty_template():
    validator = TemplateValidator()
    template_vars = set()
    data_keys = {"a", "b"}
    validator.validate_template(template_vars, data_keys)


