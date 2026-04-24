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
    dt = datetime(2025, 2, 2, 12, 0, 0)
    result = templating.render_string("{{ dt | datetime }}", dt=dt)
    assert result == "2025-02-02 12:00:00"


def test_templating_url_for():
    templating = Templating()
    result = templating.render_string("{{ url_for('users') }}")
    assert result == "/users"


def test_templating_static_url():
    templating = Templating()
    result = templating.render_string("{{ static('style.css') }}")
    assert result == "/static/style.css"


def test_templating_get_template_source(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    source, filename, uptodate = templating.get_template_source("test.html")
    assert source == "<h1>Hello {{ name }}!</h1>"
    assert filename.endswith("test.html")
    assert callable(uptodate)


def test_templating_get_template_source_not_found(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    with pytest.raises(TemplateNotFound):
        templating.get_template_source("nonexistent.html")


def test_templating_get_template_source_no_loader():
    templating = Templating()
    templating.env.loader = None
    with pytest.raises(ValueError, match="Template loader is not set"):
        templating.get_template_source("test.html")

@pytest.mark.asyncio
async def test_templating_render_async(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    result = await templating.render_async("test.html", name="Async World")
    assert result == "<h1>Hello Async World!</h1>"

@pytest.mark.asyncio
async def test_templating_render_async_not_found(temp_templates_dir):
    templating = Templating(temp_templates_dir)
    with pytest.raises(TemplateNotFound):
        await templating.render_async("nonexistent.html")

@pytest.mark.asyncio
async def test_templating_render_async_error(temp_templates_dir):
    from xyra.exceptions import TemplateException
    templating = Templating(temp_templates_dir)

    # Create a mock for get_template that raises an Exception
    def mock_get_template(*args, **kwargs):
        raise Exception("Mock error")

    templating.env.get_template = mock_get_template
    with pytest.raises(TemplateException, match="An internal error occurred while rendering the template."):
        await templating.render_async("test.html")

def test_templating_render_error(temp_templates_dir):
    from xyra.exceptions import TemplateException
    templating = Templating(temp_templates_dir)

    # Create a mock for get_template that raises an Exception
    def mock_get_template(*args, **kwargs):
        raise Exception("Mock error")

    templating.env.get_template = mock_get_template
    with pytest.raises(TemplateException, match="An internal error occurred while rendering the template."):
        templating.render("test.html")

def test_templating_render_string_error():
    from xyra.exceptions import TemplateException
    templating = Templating()

    # Create a mock for from_string that raises an Exception
    def mock_from_string(*args, **kwargs):
        raise Exception("Mock error")

    templating.env.from_string = mock_from_string
    with pytest.raises(TemplateException, match="An internal error occurred while rendering the template string."):
        templating.render_string("Hello {{ name }}!", name="Test")
