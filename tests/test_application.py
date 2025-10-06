from xyra import App


def test_app_creation():
    app = App()
    assert app is not None


def test_app_route():
    app = App()

    @app.get("/")
    def home():
        return "Hello"

    assert len(app.router.routes) == 1


def test_app_run():
    app = App()
    # Mock run to avoid actual server start
    assert hasattr(app, "run_server")
