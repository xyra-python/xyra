import os
import tempfile

import pytest
from jinja2 import TemplateNotFound

from xyra.templating import Templating


@pytest.fixture
def temp_templates_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test template
        template_path = os.path.join(tmpdir, "test.html")
        with open(template_path, "w") as f:
            f.write("<h1>Hello {{ name }}!</h1>")
        yield tmpdir


def test_templating_init(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    assert templating.directory == temp_templates_dir
    assert templating.auto_reload is True


def test_templating_render(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    result = templating.render("test.html", name="World")
    assert result == "<h1>Hello World!</h1>"


def test_templating_render_not_found(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    with pytest.raises(TemplateNotFound):
        templating.render("nonexistent.html")


def test_templating_render_string():
    templating = Templating()
    result = templating.render_string("Hello {{ name }}!", name="Test")
    assert result == "Hello Test!"


def test_templating_add_global():
    templating = Templating()
    templating.add_global("site_name", "My Site")
    result = templating.render_string("{{ site_name }}", site_name="Override")
    assert result == "Override"  # Context overrides global


def test_templating_add_filter():
    templating = Templating()

    def uppercase(value):
        return value.upper()

    templating.add_filter("upper", uppercase)
    result = templating.render_string("{{ 'hello' | upper }}")
    assert result == "HELLO"


def test_templating_list_templates(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    templates = templating.list_templates()
    assert "test.html" in templates


def test_templating_template_exists(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    assert templating.template_exists("test.html") is True
    assert templating.template_exists("nonexistent.html") is False


def test_templating_currency_filter():
    templating = Templating()
    result = templating.render_string("{{ 1234.56 | currency }}")
    assert result == "$1,234.56"

    result = templating.render_string("{{ 1234.56 | currency('EUR') }}")
    assert result == "€1,234.56"


def test_templating_datetime_filter():
    from datetime import datetime

    templating = Templating()
    dt = datetime(2023, 1, 1, 12, 0, 0)
    result = templating.render_string("{{ dt | datetime }}", dt=dt)
    assert result == "2023-01-01 12:00:00"


def test_templating_url_for():
    templating = Templating()
    result = templating.render_string("{{ url_for('users') }}")
    assert result == "/users"


def test_templating_static_url():
    templating = Templating()
    result = templating.render_string("{{ static('style.css') }}")
    assert result == "/static/style.css"
