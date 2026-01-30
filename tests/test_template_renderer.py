from smartmailer.core.template.renderer import JinjaTemplateRenderer
from jinja2 import Environment
from typing import Dict, Optional

def test_renderer_basic_replacement():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)
    template = "Hello {{ name }}"
    data: Dict[str, object] = {"name": "abc"}
    out = renderer.render(template, data)
    assert out == "Hello abc"

def test_renderer_multiple_vars():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)
    template = "{{ a }} + {{ b }} = {{ c }}"
    data: Dict[str, object] = {"a": 1, "b": 2, "c": 3}
    out = renderer.render(template, data)
    assert out == "1 + 2 = 3"


def test_renderer_empty_template():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)
    template = ""
    data: Dict[str, object] = {"a": 1}
    out = renderer.render(template, data)
    assert out == ""
   
import pytest
from jinja2 import Environment
from smartmailer.core.template.renderer import JinjaTemplateRenderer

def test_renderer_invalid_template_syntax():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "Hello {{ name "
    data = {"name": "abc"}

    with pytest.raises(ValueError) as exc:
        renderer.render(template, data)

    assert "Jinja rendering failed" in str(exc.value)
