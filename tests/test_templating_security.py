
import pytest
import os
from xyra.templating import Templating

@pytest.fixture
def templating_engine(tmp_path):
    # Create a temporary template directory
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    # Create a simple template
    template_file = template_dir / "test.html"
    template_file.write_text("Hello {{ items|join(', ') }}")

    return Templating(directory=str(template_dir), auto_reload=False)

def test_render_with_unhashable_context(templating_engine):
    """Test that rendering with unhashable context (e.g., lists) does not crash."""
    context = {"items": ["Alice", "Bob"]}

    # This should not raise TypeError
    try:
        result = templating_engine.render("test.html", **context)
        assert "Alice, Bob" in result
    except TypeError as e:
        pytest.fail(f"Rendering failed with TypeError: {e}")

@pytest.mark.asyncio
async def test_render_async_with_unhashable_context(templating_engine):
    """Test that async rendering with unhashable context does not crash."""
    context = {"items": ["Alice", "Bob"]}

    # This should not raise TypeError
    try:
        result = await templating_engine.render_async("test.html", **context)
        assert "Alice, Bob" in result
    except TypeError as e:
        pytest.fail(f"Async rendering failed with TypeError: {e}")
