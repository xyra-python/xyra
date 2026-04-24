from xyra.swagger import (
    add_common_responses,
    convert_path_to_openapi,
    extract_parameter_info,
    extract_path_parameters,
    extract_tag_from_path,
    parse_docstring,
    validate_swagger_spec,
)


def test_extract_parameter_info():
    docstring = """
    Test function.

    param_name (string): Description of param
    another_param (int): Another description
    """
    params = extract_parameter_info(docstring)
    assert "param_name" in params
    assert params["param_name"]["type"] == "string"
    assert params["param_name"]["description"] == "Description of param"
    assert params["another_param"]["type"] == "int"


def test_extract_parameter_info_empty():
    params = extract_parameter_info("")
    assert params == {}


def test_parse_docstring():
    docstring = "Summary line\n\nDescription paragraph."
    result = parse_docstring(docstring)
    assert result["summary"] == "Summary line"
    assert result["description"] == "Description paragraph."


def test_parse_docstring_empty():
    result = parse_docstring("")
    assert result["summary"] == ""
    assert result["description"] == ""


def test_convert_path_to_openapi():
    # Test basic conversion
    assert convert_path_to_openapi("/users/{id}") == "/users/{id}"
    # Test typed parameters
    assert convert_path_to_openapi("/users/{id:int}") == "/users/{id}"


def test_extract_path_parameters():
    params = extract_path_parameters("/users/{id}/posts/{post_id}")
    assert len(params) == 2
    assert params[0]["name"] == "id"
    assert params[0]["in"] == "path"
    assert params[0]["required"] is True
    assert params[1]["name"] == "post_id"


def test_extract_path_parameters_typed():
    params = extract_path_parameters("/users/{id:int}")
    assert len(params) == 1
    assert params[0]["name"] == "id"


def test_extract_path_parameters_empty():
    params = extract_path_parameters("/health")
    assert params == []


def test_extract_tag_from_path():
    assert extract_tag_from_path("/users") == "Users"
    assert extract_tag_from_path("/api/users") == "Api"
    assert extract_tag_from_path("/users/{id}") == "Users"
    assert extract_tag_from_path("/") == "Default"


def test_validate_swagger_spec_valid():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }
    assert validate_swagger_spec(spec) is True


def test_validate_swagger_spec_invalid():
    # Missing required fields
    spec = {"info": {"title": "Test"}}
    assert validate_swagger_spec(spec) is False

    # Missing info fields
    spec = {"openapi": "3.0.0", "info": {}, "paths": {}}
    assert validate_swagger_spec(spec) is False


def test_generate_swagger_from_app():
    """Test generating Swagger spec from app routes like FastAPI."""
    from xyra import App
    from xyra.swagger import generate_swagger

    app = App(swagger_options={"title": "Test API", "version": "1.0.0"})

    @app.get("/users")
    def get_users(req, res):
        """Get all users.

        Returns a list of users.
        """
        res.json([])

    @app.post("/users")
    def create_user(req, res):
        """Create a new user.

        body (object): User data
        """
        res.json({"id": 1})

    spec = generate_swagger(app, **app.swagger_options)
    assert "paths" in spec
    assert "/users" in spec["paths"]
    assert "get" in spec["paths"]["/users"]
    assert "post" in spec["paths"]["/users"]
    assert spec["info"]["title"] == "Test API"


def test_swagger_endpoint():
    """Test Swagger UI endpoint."""
    from unittest.mock import Mock

    from xyra.request import Request
    from xyra.response import Response

    # Mock request to /docs
    mock_req = Mock()
    mock_req.get_method.return_value = "GET"
    mock_req.get_url.return_value = "http://localhost:8000/docs"
    mock_req.for_each_header = Mock(side_effect=lambda func: None)
    mock_req.get_header = Mock(return_value=None)

    mock_res = Mock()
    response = Response(mock_res)
    response.html("<html>Swagger UI</html>")
    request = Request(mock_req, mock_res)
    request.is_json()
    mock_res.end.assert_called()


def test_add_common_responses():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "responses": {},
        },
    }
    updated_spec = add_common_responses(spec)

    assert "400" in updated_spec["components"]["responses"]
    assert "401" in updated_spec["components"]["responses"]
    assert "404" in updated_spec["components"]["responses"]
    assert "500" in updated_spec["components"]["responses"]

    assert updated_spec["components"]["responses"]["400"]["description"] == "Bad Request"
    assert (
        updated_spec["components"]["responses"]["500"]["description"]
        == "Internal Server Error"
    )

from xyra.swagger import (
    infer_response_schema,
    extract_request_body_schema,
    extract_query_parameters,
    generate_swagger
)
import inspect

def test_extract_parameter_info_multiline():
    docstring = """
    param_name (string): Description of param
    - continued description on new line
    - and another line
    """
    params = extract_parameter_info(docstring)
    assert "param_name" in params
    assert params["param_name"]["description"] == "Description of param continued description on new line and another line"


def test_infer_response_schema():
    def no_annotation(): pass
    def dict_annotation() -> dict: pass
    def list_annotation() -> list: pass
    def str_annotation() -> str: pass

    res_no = infer_response_schema(no_annotation)
    assert "application/json" in res_no["200"]["content"]
    assert res_no["200"]["content"]["application/json"]["schema"]["type"] == "object"

    res_dict = infer_response_schema(dict_annotation)
    assert res_dict["200"]["content"]["application/json"]["schema"]["type"] == "object"

    res_list = infer_response_schema(list_annotation)
    assert res_list["200"]["content"]["application/json"]["schema"]["type"] == "array"

    res_str = infer_response_schema(str_annotation)
    assert res_str["200"]["content"]["text/plain"]["schema"]["type"] == "string"


def test_extract_request_body_schema():
    def get_handler():
        """No json body here"""
        pass

    def post_handler():
        """
        Receives json body with fields.
        "username"
        "password"
        """
        pass

    assert extract_request_body_schema(get_handler, "GET") is None

    schema = extract_request_body_schema(post_handler, "POST")
    assert schema is not None
    props = schema["content"]["application/json"]["schema"]["properties"]
    assert "username" in props
    assert "password" in props
    assert props["username"]["type"] == "string"


def test_extract_query_parameters():
    def handler(req, res, param_str: str, param_int: int = 1, param_float: float = 1.0, param_bool: bool = False, param_no_type=None):
        pass

    params = extract_query_parameters(handler)
    assert len(params) == 5

    # Check types and required
    p_str = next(p for p in params if p["name"] == "param_str")
    assert p_str["schema"]["type"] == "string"
    assert p_str["required"] is True

    p_int = next(p for p in params if p["name"] == "param_int")
    assert p_int["schema"]["type"] == "integer"
    assert p_int["required"] is False

    p_float = next(p for p in params if p["name"] == "param_float")
    assert p_float["schema"]["type"] == "number"

    p_bool = next(p for p in params if p["name"] == "param_bool")
    assert p_bool["schema"]["type"] == "boolean"

    p_no = next(p for p in params if p["name"] == "param_no_type")
    assert p_no["schema"]["type"] == "string"

    # Test exception block
    import unittest.mock
    with unittest.mock.patch('inspect.signature', side_effect=Exception("mocked error")):
        params_err = extract_query_parameters(handler)
        assert params_err == []


def test_generate_swagger_extras():
    class MockRouter:
        routes = []

    class MockApp:
        def __init__(self):
            self.router = MockRouter()
            self._swagger_cache = None

    app = MockApp()
    contact = {"name": "Test", "email": "test@example.com"}
    license_info = {"name": "MIT"}
    servers = [{"url": "http://test"}]

    spec = generate_swagger(
        app,
        title="Custom",
        version="2.0",
        contact=contact,
        license_info=license_info,
        servers=servers,
        extra_field="extra_value"
    )

    assert spec["info"]["contact"] == contact
    assert spec["info"]["license"] == license_info
    assert spec["servers"] == servers
    assert spec["extra_field"] == "extra_value"

    # Test cache
    assert app._swagger_cache is spec

    # Second call should return cached dict
    spec2 = generate_swagger(app)
    assert spec2 is spec


def test_parse_docstring_empty_lines():
    docstring = """


    """
    result = parse_docstring(docstring)
    assert result["summary"] == ""
    assert result["description"] == ""

    docstring = "   \n  \n"
    result = parse_docstring(docstring)
    assert result["summary"] == ""
    assert result["description"] == ""


def test_generate_swagger_kwargs_overlap():
    class MockRouter:
        routes = []

    class MockApp:
        def __init__(self):
            self.router = MockRouter()
            self._swagger_cache = None

    app = MockApp()

    # Try providing a kwarg that already exists in the base spec, e.g. "openapi"
    # It should not overwrite the existing one.
    spec = generate_swagger(
        app,
        openapi="4.0.0",
        paths={"/should-not-overwrite": {}}
    )

    assert spec["openapi"] == "3.0.0"
    assert "/should-not-overwrite" not in spec["paths"]

def test_generate_swagger_cache():
    class MockApp:
        pass
    app = MockApp()
    app._swagger_cache = {"cached": True}
    spec = generate_swagger(app)
    assert spec == {"cached": True}

def test_generate_swagger_kwargs_new():
    class MockRouter:
        routes = []
    class MockApp:
        def __init__(self):
            self.router = MockRouter()
            self._swagger_cache = None

    app = MockApp()

    spec = generate_swagger(
        app,
        new_field="added"
    )

    assert spec["new_field"] == "added"

def test_generate_swagger_no_query_params():
    class MockRouter:
        routes = [
            {
                "path": "/test",
                "method": "GET",
                "handler": lambda: None  # No params
            }
        ]

    class MockApp:
        def __init__(self):
            self.router = MockRouter()
            self._swagger_cache = None

    app = MockApp()
    spec = generate_swagger(app)
    assert len(spec["paths"]["/test"]["get"]["parameters"]) == 0
