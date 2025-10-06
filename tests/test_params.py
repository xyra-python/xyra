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
    assert params == {}


def test_parse_path_with_params():
    path, params = parse_path("/users/{id}")
    assert path == "/users/(?P<id>[^/]+)"
    assert "id" in params
    assert isinstance(params["id"], Param)
    assert params["id"].name == "id"


def test_parse_path_multiple_params():
    path, params = parse_path("/users/{user_id}/posts/{post_id}")
    assert path == "/users/(?P<user_id>[^/]+)/posts/(?P<post_id>[^/]+)"
    assert len(params) == 2
    assert "user_id" in params
    assert "post_id" in params


def test_parse_path_mixed():
    path, params = parse_path("/api/v1/users/{id}/profile")
    assert path == "/api/v1/users/(?P<id>[^/]+)/profile"
    assert len(params) == 1
    assert params["id"].name == "id"
