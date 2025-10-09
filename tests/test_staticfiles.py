import tempfile
from pathlib import Path

from xyra import App


def test_static_files_registration():
    """Test registering static files directory."""
    app = App()

    # Register static files
    app.static_files("/static", "static")

    # Should not raise any errors
    assert app is not None


def test_static_files_with_absolute_path():
    """Test registering static files with absolute path."""
    app = App()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello World")

        # Register static files with absolute path
        app.static_files("/files", temp_dir)

        assert app is not None


def test_static_files_multiple_directories():
    """Test registering multiple static directories."""
    app = App()

    with (
        tempfile.TemporaryDirectory() as temp_dir1,
        tempfile.TemporaryDirectory() as temp_dir2,
    ):
        # Register multiple static directories
        app.static_files("/assets", temp_dir1)
        app.static_files("/media", temp_dir2)

        assert app is not None


def test_static_files_with_nonexistent_directory():
    """Test registering static files with nonexistent directory."""
    app = App()

    # This should not raise an error during registration
    # The error would occur during actual file serving
    app.static_files("/static", "/nonexistent/path")

    assert app is not None


def test_static_files_path_patterns():
    """Test different path patterns for static files."""
    app = App()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test various path patterns
        test_cases = [
            "/static",
            "/assets/",
            "/files/v1",
            "/media/images",
        ]

        for path in test_cases:
            app.static_files(path, temp_dir)

        assert app is not None


def test_static_files_directory_creation():
    """Test that static directory can be created and used."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subdirectory structure
        static_dir = Path(temp_dir) / "static"
        static_dir.mkdir()

        css_dir = static_dir / "css"
        css_dir.mkdir()

        # Create test files
        (static_dir / "index.html").write_text("<html><body>Hello</body></html>")
        (css_dir / "style.css").write_text("body { color: blue; }")

        app = App()
        app.static_files("/static", str(static_dir))

        assert app is not None
        assert static_dir.exists()
        assert (static_dir / "index.html").exists()
        assert (css_dir / "style.css").exists()


def test_static_files_empty_directory():
    """Test registering empty directory for static files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        app = App()
        app.static_files("/empty", temp_dir)

        assert app is not None


def test_static_files_nested_paths():
    """Test static files with nested URL paths."""
    app = App()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested directory structure
        deep_dir = Path(temp_dir) / "deep" / "nested" / "path"
        deep_dir.mkdir(parents=True)

        (deep_dir / "file.txt").write_text("nested file")

        app.static_files("/api/v1/static", str(deep_dir))

        assert app is not None
        assert (deep_dir / "file.txt").exists()


def test_static_files_special_characters():
    """Test static files with special characters in paths."""
    app = App()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files with special characters
        (Path(temp_dir) / "file with spaces.txt").write_text("content")
        (Path(temp_dir) / "file-with-dashes.txt").write_text("content")
        (Path(temp_dir) / "file_with_underscores.txt").write_text("content")

        app.static_files("/files", temp_dir)

        assert app is not None


def test_static_files_large_directory():
    """Test static files with many files."""
    app = App()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create many test files
        for i in range(100):
            (Path(temp_dir) / f"file_{i}.txt").write_text(f"content {i}")

        app.static_files("/many", temp_dir)

        assert app is not None
        assert len(list(Path(temp_dir).glob("*.txt"))) == 100
