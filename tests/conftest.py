
import sys
from unittest.mock import MagicMock

# Mock libxyra before any test imports xyra
if "xyra.libxyra" not in sys.modules:
    mock_libxyra = MagicMock()
    sys.modules["xyra.libxyra"] = mock_libxyra
