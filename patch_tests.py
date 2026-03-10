import re

with open("tests/test_request.py", "r") as f:
    content = f.read()

# Make sure indentation is exactly preserved.
# The group 2 in match contains the exact spacing before 'request = '
content = re.sub(
    r"(res\.get_json = AsyncMock\(return_value=\{\}\)\n)(\s+)(request = Request\(req, res\))",
    r"\1\2req.get_header = Mock(return_value='application/json')\n\2\3",
    content
)

content = re.sub(
    r"(res\.get_data = AsyncMock\(return_value=b'\{\"key\": \"value\"\}'\)\n)(\s+)(request = Request\(req, res\))",
    r"\1\2req.get_header = Mock(return_value='application/json')\n\2\3",
    content
)

content = re.sub(
    r"(res\.get_data = AsyncMock\(return_value=b\"invalid json\"\)\n)(\s+)(request = Request\(req, res\))",
    r"\1\2req.get_header = Mock(return_value='application/json')\n\2\3",
    content
)

with open("tests/test_request.py", "w") as f:
    f.write(content)
