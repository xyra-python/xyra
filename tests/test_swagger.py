from xyra.swagger import (
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
