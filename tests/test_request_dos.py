from unittest.mock import AsyncMock, Mock

import pytest

from xyra.request import Request


@pytest.mark.asyncio
async def test_form_parsing_dos_protection():
    """Test that Request.form() protects against Hash Collision / Large Payload DoS."""
    req_mock = Mock()
    res_mock = Mock()

    # Create a malicious payload with many fields
    # max_num_fields default in Django/PHP is 1000.
    # We will generate 2000 fields.
    payload = "&".join([f"key{i}=value{i}" for i in range(2000)])

    res_mock.get_data = AsyncMock(return_value=payload.encode())

    request = Request(req_mock, res_mock)

    # This should verify that we limit the fields or handle it gracefully
    form_data = await request.form()

    # Expect empty dict because limit was exceeded and we swallowed the error (logging warning)
    assert form_data == {}, "Form data should be empty when limit is exceeded"


@pytest.mark.asyncio
async def test_form_parsing_unicode_error():
    """Test that Request.form() handles invalid UTF-8 gracefully."""
    req_mock = Mock()
    res_mock = Mock()

    # Invalid UTF-8 sequence
    res_mock.get_data = AsyncMock(return_value=b"\x80\x81")

    request = Request(req_mock, res_mock)

    # Should handle safe
    form_data = await request.form()
    assert form_data == {}, "Form data should be empty on unicode error"
