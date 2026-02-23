from unittest.mock import Mock, patch

from xyra.request import Request


def test_query_params_fallback_limit():
    """Test fallback limits number of params."""
    # Create a query string with 1001 params
    # k0=v&k1=v...
    query = "&".join([f"k{i}=v" for i in range(1001)])

    req = Mock(spec=["get_query"])
    req.get_query.return_value = query

    res = Mock()
    request = Request(req, res)

    # We expect empty dict or partial result if logging swallows error
    # Current implementation propagates error.
    # New implementation should swallow and return empty dict.

    # We need to mock logging to avoid noise
    with patch("xyra.request.get_logger") as mock_logger:
        params = request.query_params
        assert params == {}
        # Ensure warning was logged
        mock_logger.return_value.warning.assert_called()

def test_query_params_native_limit_error():
    """Test native get_queries raising ValueError."""
    req = Mock()
    # Simulate native method raising ValueError due to limit
    req.get_queries.side_effect = ValueError("Too many query parameters")

    res = Mock()
    request = Request(req, res)

    with patch("xyra.request.get_logger") as mock_logger:
        params = request.query_params
        assert params == {}
        mock_logger.return_value.warning.assert_called_with(
            "Query params exceeded max fields limit or failed to parse: Too many query parameters. Returning empty dict."
        )
