import threading
import time

from xyra.middleware.rate_limiter import RateLimiter


def test_ratelimiter_thread_safety():
    """Test that RateLimiter is thread-safe under concurrent access."""
    limiter = RateLimiter(requests=10, window=1)
    client_key = "127.0.0.1"

    # Track results from multiple threads
    results = []
    errors = []

    def make_requests(thread_id):
        """Make requests from a single thread."""
        try:
            for i in range(5):
                allowed = limiter.is_allowed(client_key)
                results.append((thread_id, i, allowed))
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Create multiple threads making requests simultaneously
    threads = []
    for thread_id in range(5):
        thread = threading.Thread(target=make_requests, args=(thread_id,))
        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that no errors occurred
    assert len(errors) == 0, f"Errors occurred in threads: {errors}"

    # Count total allowed requests
    allowed_count = sum(1 for _, _, allowed in results if allowed)

    # Should not exceed the limit (10), but might be less due to timing
    assert allowed_count <= 10, f"Too many requests allowed: {allowed_count}"


def test_ratelimiter_concurrent_access():
    """Test rate limiter with concurrent access."""
    limiter = RateLimiter(requests=5, window=1)
    client_key = "test_client"

    # Create multiple concurrent operations
    def make_request(task_id):
        allowed = limiter.is_allowed(client_key)
        remaining = limiter.get_remaining_requests(client_key)
        return task_id, allowed, remaining

    # Run operations in multiple threads
    results = []
    threads = []

    for i in range(10):
        thread = threading.Thread(target=lambda i=i: results.append(make_request(i)))
        threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Count allowed requests
    allowed_count = sum(1 for _, allowed, _ in results if allowed)

    # Should not exceed the limit
    assert allowed_count <= 5, f"Too many requests allowed: {allowed_count}"

    # Verify that remaining requests count is consistent
    final_remaining = limiter.get_remaining_requests(client_key)
    assert 0 <= final_remaining <= 5, f"Invalid remaining count: {final_remaining}"


def test_ratelimiter_cleanup_thread_safety():
    """Test that cleanup operation is thread-safe."""
    limiter = RateLimiter(requests=10, window=1)  # Integer window for testing
    client_key = "test_client"

    # Add some old requests
    current_time = time.time()

    # Manually add old timestamps
    with limiter._lock:
        limiter._requests[client_key] = [
            current_time - 10,
            current_time - 5,
        ]  # Old timestamps

    # Concurrently check if allowed and trigger cleanup
    results = []

    def worker(worker_id):
        allowed = limiter.is_allowed(client_key)
        remaining = limiter.get_remaining_requests(client_key)
        results.append((worker_id, allowed, remaining))

    # Run multiple workers concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # All results should be consistent
    assert len(results) == 5
