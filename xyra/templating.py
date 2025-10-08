import os
from collections.abc import Callable
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class Templating:
    """Template rendering engine using Jinja2."""

    def __init__(self, directory: str = "templates", auto_reload: bool = True):
        """
        Initialize the templating engine.

        Args:
            directory: Directory containing template files
            auto_reload: Whether to auto-reload templates when they change
        """
        self.directory = directory
        self.auto_reload = auto_reload

        # Check if templates directory exists
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(directory),
            auto_reload=auto_reload,
            enable_async=True,  # Enable async template rendering
        )

        # Simple render cache for performance
        self._render_cache: dict[str, str] = {}
        self._cache_enabled = True

        # Add custom filters and globals
        self._setup_environment()

    def _setup_environment(self):
        """Setup custom filters and global functions for templates."""
        # Add custom filters
        self.env.filters["currency"] = self._currency_filter
        self.env.filters["datetime"] = self._datetime_filter

        # Add global functions
        self.env.globals["url_for"] = self._url_for
        self.env.globals["static"] = self._static_url

    def _currency_filter(self, value: float, currency: str = "USD") -> str:
        """Format a number as currency."""
        if currency.upper() == "USD":
            return f"${value:,.2f}"
        elif currency.upper() == "EUR":
            return f"€{value:,.2f}"
        else:
            return f"{value:,.2f} {currency}"

    def _datetime_filter(self, value, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a datetime object."""
        if hasattr(value, "strftime"):
            return value.strftime(format)
        return str(value)

    def _url_for(self, route_name: str, **kwargs) -> str:
        """Generate URL for a route (placeholder implementation)."""
        # This would be enhanced to work with actual routing
        return f"/{route_name}"

    def _static_url(self, filename: str) -> str:
        """Generate URL for static files."""
        return f"/static/{filename}"

    def render(self, template_name: str, **context) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file
            **context: Variables to pass to the template

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If the template file doesn't exist
            Exception: If there's an error rendering the template
        """
        # Simple caching for performance (disabled in development with auto_reload)
        if self._cache_enabled and not self.auto_reload:
            cache_key = f"{template_name}:{hash(frozenset(context.items()))}"
            if cache_key in self._render_cache:
                return self._render_cache[cache_key]

        try:
            template = self.env.get_template(template_name)
            result = template.render(**context)

            # Cache the result
            if self._cache_enabled and not self.auto_reload:
                cache_key = f"{template_name}:{hash(frozenset(context.items()))}"
                self._render_cache[cache_key] = result

            return result
        except TemplateNotFound:
            raise TemplateNotFound(
                f"Template '{template_name}' not found in directory '{self.directory}'"
            ) from None
        except Exception as e:
            raise Exception(
                f"Error rendering template '{template_name}': {str(e)}"
            ) from e

    async def render_async(self, template_name: str, **context) -> str:
        """
        Render a template asynchronously with the given context.

        Args:
            template_name: Name of the template file
            **context: Variables to pass to the template

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If the template file doesn't exist
            Exception: If there's an error rendering the template
        """
        # Simple caching for performance (disabled in development with auto_reload)
        if self._cache_enabled and not self.auto_reload:
            cache_key = f"{template_name}:{hash(frozenset(context.items()))}"
            if cache_key in self._render_cache:
                return self._render_cache[cache_key]

        try:
            template = self.env.get_template(template_name)
            result = await template.render_async(**context)

            # Cache the result
            if self._cache_enabled and not self.auto_reload:
                cache_key = f"{template_name}:{hash(frozenset(context.items()))}"
                self._render_cache[cache_key] = result

            return result
        except TemplateNotFound:
            raise TemplateNotFound(
                f"Template '{template_name}' not found in directory '{self.directory}'"
            ) from None
        except Exception as e:
            raise Exception(
                f"Error rendering template '{template_name}': {str(e)}"
            ) from e

    def render_string(self, template_string: str, **context) -> str:
        """
        Render a template from a string instead of a file.

        Args:
            template_string: Template content as string
            **context: Variables to pass to the template

        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            raise Exception(f"Error rendering template string: {str(e)}") from e

    def add_global(self, name: str, value: Any):
        """Add a global variable or function to all templates."""
        self.env.globals[name] = value

    def add_filter(self, name: str, func: Callable[..., Any]):
        """Add a custom filter to the template environment."""
        self.env.filters[name] = func

    def list_templates(self) -> list:
        """List all available templates."""
        return self.env.list_templates()

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False

    def get_template_source(self, template_name: str) -> tuple:
        """Get the source code of a template (for debugging)."""
        assert self.env.loader is not None
        return self.env.loader.get_source(self.env, template_name)
