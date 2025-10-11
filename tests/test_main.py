import sys
from unittest.mock import Mock, patch

import pytest

from xyra.__main__ import load_app_from_file, main


def test_load_app_from_file_success(tmp_path):
    """Test that a Xyra app can be loaded from a file."""
    # Create a dummy app file
    app_file = tmp_path / "main.py"
    app_file.write_text("from xyra import App\n\napp = App()")

    # Load the app
    app = load_app_from_file(str(app_file))
    assert app is not None
    assert hasattr(app, "run_server")


def test_load_app_from_file_not_found():
    """Test that loading a non-existent file exits the program."""
    with pytest.raises(SystemExit) as excinfo:
        load_app_from_file("non_existent_file.py")
    assert excinfo.value.code == 1


def test_load_app_from_file_no_app_instance(tmp_path):
    """Test that loading a file without an 'app' instance exits the program."""
    app_file = tmp_path / "main.py"
    app_file.write_text("print('Hello')")

    with pytest.raises(SystemExit) as excinfo:
        load_app_from_file(str(app_file))
    assert excinfo.value.code == 1


@patch("xyra.__main__.load_app_from_file")
@patch("argparse.ArgumentParser.parse_args")
def test_main_runs_app(mock_parse_args, mock_load_app):
    """Test that the main function loads and runs the app."""
    # Mock the app and command-line arguments
    mock_app = Mock()
    mock_load_app.return_value = mock_app
    mock_parse_args.return_value = Mock(
        file="main.py", host="localhost", port=8000, reload=False
    )

    # Mock sys.argv to avoid parsing actual command-line arguments
    with patch.object(sys, "argv", ["xyra", "main.py"]):
        main()

    # Check that the app was loaded and run
    mock_load_app.assert_called_with("main.py")
    mock_app.listen.assert_called_with(port=8000, host="localhost", reload=False)
