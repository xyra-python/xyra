from unittest.mock import MagicMock

from xyra.application import App


def test_404_middleware_applied():
    """
    Test that the 404 handler now correctly applies middleware (Security Fix).
    """
    app = App()

    # We patch the instance method to spy on it
    app._create_final_handler = MagicMock(wraps=app._create_final_handler)

    # Mock _app to avoid errors and inspect calls
    app._app = MagicMock()

    # Register routes
    app._register_routes()

    # Check calls to _create_final_handler
    # Expected signature: _create_final_handler(route_handler, param_names, middlewares, parsed_path)
    called_for_404 = False
    for call in app._create_final_handler.call_args_list:
        args, _ = call
        # args[3] corresponds to parsed_path
        if len(args) >= 4 and args[3] == "/*":
            called_for_404 = True
            break

    # FIXED BEHAVIOR: Middleware IS applied to 404 handler,
    # so _create_final_handler IS called for "/*".
    assert called_for_404, (
        "Middleware NOT applied to 404 handler! Security headers missing on 404."
    )
