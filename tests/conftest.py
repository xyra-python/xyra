import sys
from unittest.mock import MagicMock

# Mock libxyra if not available
try:
    import xyra.libxyra
except ImportError:
    # Create a mock for libxyra
    mock_libxyra = MagicMock()
    # Mock App class
    mock_libxyra.App = MagicMock
    # Mock Request class
    mock_libxyra.Request = MagicMock
    # Mock Response class
    mock_libxyra.Response = MagicMock
    # Mock WebSocket class
    mock_libxyra.WebSocket = MagicMock

    # Inject into sys.modules
    sys.modules["xyra.libxyra"] = mock_libxyra
