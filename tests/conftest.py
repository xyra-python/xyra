import sys
from unittest.mock import MagicMock

# Mock native extension if not available
try:
    import xyra.libxyra
except ImportError:
    sys.modules["xyra.libxyra"] = MagicMock()
