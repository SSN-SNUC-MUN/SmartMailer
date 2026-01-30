from smartmailer.core.template.parser import JinjaTemplateParser
from jinja2 import Environment

def test_parser_extracts_variables():
    env = Environment()
    parser = JinjaTemplateParser(env)

    template = "Hello {{ name }}, welcome to {{ college }}"

    vars = parser.extract_variables(template)

    assert vars == {"name", "college"}


def test_parser_empty_string():
    env = Environment()
    parser = JinjaTemplateParser(env)
    template = ""
    vars = parser.extract_variables(template)
    assert vars == set()

def test_parser_strips_spaces():
    env = Environment()
    parser = JinjaTemplateParser(env)
    template = "Hi {{   name   }}"
    vars = parser.extract_variables(template)
    assert vars == {"name"}