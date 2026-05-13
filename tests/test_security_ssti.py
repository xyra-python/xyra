
import pytest
from xyra.templating import Templating

try:
    from jinja2.sandbox import SandboxedEnvironment, SecurityError
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

@pytest.mark.skipif(not JINJA_AVAILABLE, reason="Jinja2 not installed")
def test_ssti_blocked():
    """
    Verify that SandboxedEnvironment blocks access to dangerous attributes.
    """
    templating = Templating()
    # Ensure it's using SandboxedEnvironment
    assert isinstance(templating.env, SandboxedEnvironment)

    # This payload tries to access __class__ which should be blocked or restricted
    # In Jinja2 SandboxedEnvironment, access to attributes starting with __ is blocked by default.
    payload = "{{ ''.__class__.__mro__[1].__subclasses__() }}"

    with pytest.raises(SecurityError):
        templating.render_string(payload)

@pytest.mark.skipif(not JINJA_AVAILABLE, reason="Jinja2 not installed")
def test_normal_rendering_still_works():
    """
    Verify that normal rendering still works with SandboxedEnvironment.
    """
    templating = Templating()
    result = templating.render_string("Hello {{ name }}!", name="World")
    assert result == "Hello World!"

@pytest.mark.skipif(not JINJA_AVAILABLE, reason="Jinja2 not installed")
def test_sandboxed_environment_inherited_by_render():
    """
    Verify that the render method (from file) also uses the sandboxed environment.
    """
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = os.path.join(tmpdir, "unsafe.html")
        with open(template_path, "w") as f:
            f.write("{{ ''.__class__ }}")

        templating = Templating(tmpdir)
        with pytest.raises(SecurityError):
            templating.render("unsafe.html")
