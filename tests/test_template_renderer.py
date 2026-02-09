from smartmailer.core.template.renderer import JinjaTemplateRenderer
from jinja2 import Environment
from typing import Dict, Optional
import pytest

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

def test_renderer_invalid_template_syntax():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "Hello {{ name "
    data = {"name": "abc"}

    with pytest.raises(ValueError) as exc:
        renderer.render(template, data)

    assert "Jinja rendering failed" in str(exc.value)


def test_renderer_conditionals():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "{% if premium %}VIP{% else %}Normal{% endif %}"
    out = renderer.render(template, {"premium": True})

    assert out == "VIP"



def test_renderer_loop():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "{% for item in items %}{{ item }} {% endfor %}"
    out = renderer.render(template, {"items": [1,2,3]})

    assert out == "1 2 3 "


def test_renderer_filters():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "{{ name | upper }}"
    out = renderer.render(template, {"name": "abc"})

    assert out == "ABC"


def test_renderer_nested_access():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "{{ user.name }}"
    data = {"user": {"name": "abc"}}

    out = renderer.render(template, data)
    assert out == "abc"


def test_renderer_default_filter():
    env = Environment()
    renderer = JinjaTemplateRenderer(env)

    template = "{{ name | default('Guest') }}"
    out = renderer.render(template, {})

    assert out == "Guest"

