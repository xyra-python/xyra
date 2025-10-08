"""
Gzip Middleware for Xyra Framework

This middleware compresses response data using gzip compression.
"""

import gzip

from ..request import Request
from ..response import Response


class GzipMiddleware:
    """Middleware for gzip compression of responses."""

    def __init__(self, minimum_size: int = 1024, compress_level: int = 6):
        """
        Initialize gzip middleware.

        Args:
            minimum_size: Minimum response size to compress (in bytes)
            compress_level: Gzip compression level (1-9)
        """
        self.minimum_size = minimum_size
        self.compress_level = compress_level

    def __call__(self, req: Request, res: Response):
        """Apply gzip compression to the response."""
        # Store original send method
        original_send = res.send

        def compressed_send(data):
            # Check if response should be compressed
            if (
                isinstance(data, (str, bytes))
                and len(data) >= self.minimum_size
                and "gzip" in req.headers.get("Accept-Encoding", "").lower()
                and "Content-Encoding" not in res.headers
            ):
                # Compress the data
                if isinstance(data, str):
                    data = data.encode("utf-8")

                compressed_data = gzip.compress(data, compresslevel=self.compress_level)

                # Set compression headers
                res.header("Content-Encoding", "gzip")
                res.header("Vary", "Accept-Encoding")

                # Send compressed data
                original_send(compressed_data)
            else:
                # Send uncompressed data
                original_send(data)

        # Replace send method
        res.send = compressed_send

        # Compression setup done, continue to next middleware


def gzip_middleware(
    minimum_size: int = 1024, compress_level: int = 6
) -> GzipMiddleware:
    """Create a gzip middleware instance."""
    return GzipMiddleware(minimum_size, compress_level)
