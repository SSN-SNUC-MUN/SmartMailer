from src.smartmailer.core.template.renderer import TemplateRenderer

def test_renderer_basic_replacement():
    renderer = TemplateRenderer()
    template = "Hello {{ name }}"
    data = {"name": "abc"}
    out = renderer.render(template, data)
    assert out == "Hello abc"

def test_renderer_multiple_vars():
    renderer = TemplateRenderer()
    template = "{{ a }} + {{ b }} = {{ c }}"
    data = {"a": 1, "b": 2, "c": 3}
    out = renderer.render(template, data)
    assert out == "1 + 2 = 3"


def test_renderer_empty_template():
    renderer = TemplateRenderer()
    template = ""
    data = {"a": 1}
    out = renderer.render(template, data)
    assert out == ""
   
