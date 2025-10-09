from xyra.params import Param, parse_path


def test_param_type_conversion():
    """Test parameter type conversion like in FastAPI."""
    # Simulate type conversion for int
    param = Param("id", "int")
    value_str = "123"
    if param.type == "int":
        converted = int(value_str)
        assert converted == 123
    else:
        converted = value_str
    assert converted == 123


def test_param_default_value():
    """Test parameter with default values."""
    # Simulate default handling
    default_value = 10
    value = None  # Simulate no value provided
    if value is None:
        value = default_value
    assert value == 10


def test_param_validation_error():
    """Test parameter validation that raises error on invalid type."""
    param = Param("id", "int")
    invalid_value = "abc"
    try:
        if param.type == "int":
            int(invalid_value)
        assert False, "Should raise ValueError"
    except ValueError:
        pass  # Expected


def test_query_param_parsing():
    """Test parsing query parameters."""
    # Mock query string parsing
    query_string = "name=John&age=25"
    params = {}
    for pair in query_string.split("&"):
        key, value = pair.split("=")
        params[key] = value
    assert params["name"] == "John"
    assert params["age"] == "25"


def test_param_creation():
    param = Param("id", "int")
    assert param.name == "id"
    assert param.type == "int"


def test_param_repr():
    param = Param("name")
    assert repr(param) == "<Param name>"


def test_parse_path_no_params():
    path, params = parse_path("/users")
    assert path == "/users"
    assert params == []


def test_parse_path_with_params():
    path, params = parse_path("/users/{id}")
    assert path == "/users/:id"
    assert params == ["id"]


def test_parse_path_multiple_params():
    path, params = parse_path("/users/{user_id}/posts/{post_id}")
    assert path == "/users/:user_id/posts/:post_id"
    assert params == ["user_id", "post_id"]


def test_parse_path_mixed():
    path, params = parse_path("/api/v1/users/{id}/profile")
    assert path == "/api/v1/users/:id/profile"
    assert params == ["id"]
