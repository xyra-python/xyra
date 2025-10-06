from xyra.params import Param, parse_path


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
