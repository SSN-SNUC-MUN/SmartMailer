from src.smartmailer.core.template.parser import TemplateParser

def test_parser_extracts_variables():
    parser = TemplateParser()

    template = "Hello {{ name }}, welcome to {{ college }}"

    vars = parser.extract_variables(template)

    assert vars == {"name", "college"}


def test_parser_empty_string():
    parser = TemplateParser()
    template = ""
    vars = parser.extract_variables(template)
    assert vars == set()

def test_parser_strips_spaces():
    parser = TemplateParser()
    template = "Hi {{   name   }}"
    vars = parser.extract_variables(template)
    assert vars == {"name"}