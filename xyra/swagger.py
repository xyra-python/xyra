import inspect
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .application import App


def extract_parameter_info(docstring: str) -> dict[str, dict[str, Any]]:
    """Extract parameter information from docstring."""
    params = {}
    if not docstring:
        return params

    lines = docstring.split("\n")
    current_param = None

    for line in lines:
        line = line.strip()

        # Look for parameter patterns like "param_name (type): description"
        param_match = re.match(r"(\w+)\s*\(([^)]+)\):\s*(.+)", line)
        if param_match:
            param_name, param_type, description = param_match.groups()
            params[param_name] = {
                "type": param_type.strip(),
                "description": description.strip(),
            }
            current_param = param_name
        elif current_param and line.startswith("-"):
            # Continue description on next line
            params[current_param]["description"] += " " + line[1:].strip()

    return params


def infer_response_schema(handler_func) -> dict[str, Any]:
    """Infer response schema from function annotations and docstring."""
    responses = {
        "200": {
            "description": "Successful response",
            "content": {"application/json": {"schema": {"type": "object"}}},
        }
    }

    # Try to get return type annotation
    signature = inspect.signature(handler_func)
    return_annotation = signature.return_annotation

    if return_annotation is not inspect.Signature.empty:
        # Convert Python types to OpenAPI types
        if return_annotation is dict:
            responses["200"]["content"]["application/json"]["schema"] = {
                "type": "object"
            }
        elif return_annotation is list:
            responses["200"]["content"]["application/json"]["schema"] = {
                "type": "array",
                "items": {"type": "object"},
            }
        elif return_annotation is str:
            responses["200"]["content"]["text/plain"]["schema"] = {"type": "string"}

    return responses


def extract_request_body_schema(handler_func, method: str) -> dict[str, Any] | None:
    """Extract request body schema for POST/PUT/PATCH methods."""
    if method.upper() not in ["POST", "PUT", "PATCH"]:
        return None

    request_body = {
        "content": {
            "application/json": {
                "schema": {"type": "object", "properties": {}, "required": []}
            }
        }
    }

    # Try to infer from docstring
    docstring = inspect.getdoc(handler_func)
    if docstring:
        # Look for JSON body descriptions
        if "json" in docstring.lower() or "body" in docstring.lower():
            # Extract field mentions from docstring
            field_matches = re.findall(r'"(\w+)"', docstring)
            for field in field_matches:
                request_body["content"]["application/json"]["schema"]["properties"][
                    field
                ] = {"type": "string", "description": f"The {field} field"}

    return request_body


def parse_docstring(docstring: str | None) -> dict[str, str]:
    """Parse docstring into summary and description."""
    if not docstring:
        return {"summary": "", "description": ""}

    lines = [line.strip() for line in docstring.strip().split("\n") if line.strip()]

    if not lines:
        return {"summary": "", "description": ""}

    summary = lines[0]
    description = ""

    if len(lines) > 1:
        # Skip empty lines after summary
        desc_lines = []
        start_desc = False

        for line in lines[1:]:
            if not start_desc and not line:
                continue
            start_desc = True
            desc_lines.append(line)

        description = "\n".join(desc_lines)

    return {"summary": summary, "description": description}


def convert_path_to_openapi(path: str) -> str:
    """Convert Flask-style path parameters to OpenAPI format."""
    # Convert {param} to {param} (already in correct format)
    # Handle typed parameters like {param:int} -> {param}
    openapi_path = re.sub(r"\{(\w+):[^}]+\}", r"{\1}", path)
    return openapi_path


def extract_path_parameters(path: str) -> list[dict[str, Any]]:
    """Extract path parameters from route path."""
    parameters = []

    # Find all {param} patterns
    param_matches = re.findall(r"\{(\w+)(?::[^}]+)?\}", path)

    for param_name in param_matches:
        parameters.append(
            {
                "name": param_name,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"The {param_name} parameter",
            }
        )

    return parameters


def generate_swagger(
    app: "App",
    title: str = "Xyra API",
    version: str = "1.0.0",
    description: str = "API documentation for Xyra application",
    contact: dict[str, str] | None = None,
    license_info: dict[str, str] | None = None,
    servers: list[dict[str, str]] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification from Xyra app routes.

    Args:
        app: The Xyra application instance
        title: API title
        version: API version
        description: API description
        contact: Contact information dict with 'name', 'email', 'url'
        license_info: License information dict with 'name', 'url'
        servers: list of server objects with 'url' and optional 'description'
        **kwargs: Additional OpenAPI specification fields

    Returns:
        OpenAPI specification dictionary
    """
    # Base OpenAPI structure
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
        },
        "paths": {},
        "components": {
            "schemas": {},
            "responses": {},
            "parameters": {},
            "examples": {},
            "requestBodies": {},
            "headers": {},
            "securitySchemes": {},
            "links": {},
            "callbacks": {},
        },
    }

    # Add optional info fields
    if contact:
        swagger_spec["info"]["contact"] = contact

    if license_info:
        swagger_spec["info"]["license"] = license_info

    # Add servers
    if servers:
        swagger_spec["servers"] = servers
    else:
        swagger_spec["servers"] = [
            {"url": "http://localhost:8000", "description": "Development server"}
        ]

    # Process routes
    if hasattr(app, "router") and hasattr(app.router, "routes"):
        for route in app.router.routes:
            path = route["path"]
            method = route["method"].lower()
            handler = route["handler"]

            # Convert path to OpenAPI format
            openapi_path = convert_path_to_openapi(path)

            # Initialize path object if not exists
            if openapi_path not in swagger_spec["paths"]:
                swagger_spec["paths"][openapi_path] = {}

            # Parse handler docstring
            docstring_info = parse_docstring(inspect.getdoc(handler))

            # Extract path parameters
            path_parameters = extract_path_parameters(path)

            # Build operation object
            operation = {
                "summary": docstring_info["summary"] or f"{method.upper()} {path}",
                "description": docstring_info["description"],
                "parameters": path_parameters,
                "responses": infer_response_schema(handler),
                "tags": [extract_tag_from_path(path)],
            }

            request_body = extract_request_body_schema(handler, method)
            if request_body:
                operation["requestBody"] = request_body

            # Add query parameters if detected
            query_params = extract_query_parameters(handler)
            if query_params:
                operation["parameters"].extend(query_params)

            swagger_spec["paths"][openapi_path][method] = operation

    # Add any additional kwargs to the spec
    for key, value in kwargs.items():
        if key not in swagger_spec:
            swagger_spec[key] = value

    return swagger_spec


def extract_tag_from_path(path: str) -> str:
    """Extract a tag name from the route path."""
    # Remove leading slash and get first path segment
    clean_path = path.lstrip("/")
    segments = clean_path.split("/")

    if segments and segments[0]:
        # Capitalize first letter and remove parameter markers
        tag = segments[0].replace("{", "").replace("}", "")
        return tag.capitalize()

    return "Default"


def extract_query_parameters(handler_func) -> list[dict[str, Any]]:
    """Extract query parameters from function signature or docstring."""
    parameters = []

    try:
        # Get function signature
        signature = inspect.signature(handler_func)

        # Look for parameters beyond req and res
        for param_name, param in signature.parameters.items():
            if param_name not in ["req", "res", "request", "response"]:
                param_schema = {"type": "string"}

                # Try to infer type from annotation
                if param.annotation is not inspect.Parameter.empty:
                    if param.annotation is int:
                        param_schema["type"] = "integer"
                    elif param.annotation is float:
                        param_schema["type"] = "number"
                    elif param.annotation is bool:
                        param_schema["type"] = "boolean"

                parameters.append(
                    {
                        "name": param_name,
                        "in": "query",
                        "required": param.default == inspect.Parameter.empty,
                        "schema": param_schema,
                    }
                )

    except Exception:
        # If signature inspection fails, just return empty list
        pass

    return parameters


def add_common_responses(swagger_spec: dict[str, Any]) -> dict[str, Any]:
    """Add common HTTP response definitions."""
    common_responses = {
        "400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                        },
                    }
                }
            },
        },
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                        },
                    }
                }
            },
        },
        "404": {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                        },
                    }
                }
            },
        },
        "500": {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "message": {"type": "string"},
                        },
                    }
                }
            },
        },
    }

    swagger_spec["components"]["responses"].update(common_responses)
    return swagger_spec


def validate_swagger_spec(spec: dict[str, Any]) -> bool:
    """Basic validation of OpenAPI specification."""
    required_fields = ["openapi", "info", "paths"]

    for field in required_fields:
        if field not in spec:
            return False

    if "title" not in spec["info"] or "version" not in spec["info"]:
        return False

    return True
