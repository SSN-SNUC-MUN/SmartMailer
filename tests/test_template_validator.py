import pytest
from smartmailer.core.template.validator import TemplateValidator


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


