import pytest
from xyra.request import Request
from unittest.mock import Mock

def create_request(headers):
    req = Mock()
    res = Mock()

    headers_dict = {k.lower(): v for k, v in headers.items()}
    req.get_header.side_effect = lambda k, default=None: headers_dict.get(k, default)

    return Request(req, res)

def test_websocket_default_upgrade_handler():
    from xyra.application import App
    app = App()

    # We can test the default_upgrade by pulling it out or by triggering it.
    # Since _app.ws is a C++ bound method, we can't easily monkeypatch it.
    # Let's extract the default_upgrade logic from the source by manually
    # invoking _register_websocket but mocking out `self._app` inside App.

    # Create a mock for the native app
    mock_app = Mock()
    app._app = mock_app

    # Call _register_websocket to trigger our mock
    app._register_websocket("/test", {"open": lambda ws: None})

    # Extract the configuration passed to ws
    mock_app.ws.assert_called_once()
    ws_config_passed = mock_app.ws.call_args[0][1]

    assert "upgrade" in ws_config_passed

    upgrade_handler = ws_config_passed["upgrade"]

    # 1. No Origin -> Allow (non-browser client)
    req = create_request({"Host": "example.com"})
    assert upgrade_handler(req) is True

    # 2. Origin matches Host -> Allow
    req = create_request({"Host": "example.com", "Origin": "https://example.com"})
    assert upgrade_handler(req) is True

    req = create_request({"Host": "localhost:8000", "Origin": "http://localhost:8000"})
    assert upgrade_handler(req) is True

    # 3. Origin mismatches Host -> Deny (CSWSH attempt)
    req = create_request({"Host": "example.com", "Origin": "https://evil.com"})
    assert upgrade_handler(req) is False

    # 4. Origin present but no Host -> Deny
    req = create_request({"Origin": "https://example.com"})
    assert upgrade_handler(req) is False
