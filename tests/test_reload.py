import os
import sys
from unittest.mock import MagicMock, patch

from xyra import App


@patch("subprocess.Popen")
@patch("watchfiles.watch")
def test_app_reload_subprocess_isolation(mock_watch, mock_popen):
    """
    Test that auto-reload uses `-E` with sys.executable to prevent shell injection
    via untrusted environment variables like PYTHONPATH/PYTHONSTARTUP.
    """
    # Arrange
    app = App()

    # Mock watchfiles to yield no changes and just allow the thread to exit gracefully
    mock_watch.return_value = []

    # Ensure XYRA_RELOAD_CHILD is not set so the parent process block is executed
    if "XYRA_RELOAD_CHILD" in os.environ:
        del os.environ["XYRA_RELOAD_CHILD"]

    # Mock Popen to return a mock process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process

    # Run the server in a separate thread so it doesn't block infinitely
    # run_server loops forever if watchfiles is blocking, but our mock_watch is empty
    # so the watcher thread exits, and the main thread sleeps forever.
    # We will start it and then let it run briefly to hit start_server().

    # We need to mock time.sleep so the infinite loop doesn't block the test
    # but allows it to throw a custom exception to exit
    class ExitLoopException(Exception):
        pass

    with patch("time.sleep", side_effect=ExitLoopException):
        try:
            app.run_server(reload=True)
        except ExitLoopException:
            pass

    # Assert
    mock_popen.assert_called_once()

    # Check the arguments passed to Popen
    args, kwargs = mock_popen.call_args

    command = args[0]
    assert command[0] == sys.executable
    assert command[1] == "-E"
    assert command[2:] == sys.argv

    # Ensure the environment was copied and XYRA_RELOAD_CHILD was set
    env = kwargs.get("env")
    assert env is not None
    assert env.get("XYRA_RELOAD_CHILD") == "1"
