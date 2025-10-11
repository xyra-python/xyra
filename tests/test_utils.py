import os
import tempfile

from xyra.utils import get_file_info, get_real_path


def test_get_real_path():
    with tempfile.NamedTemporaryFile() as tmp:
        real_path = get_real_path(tmp.name)
        assert os.path.isabs(real_path)
        assert os.path.exists(real_path)


def test_get_file_info():
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b"test content")
        tmp.flush()
        info = get_file_info(tmp.name)
        assert hasattr(info, "st_size")


def test_get_real_path_with_symlink(tmp_path):
    """Test that get_real_path resolves symbolic links."""
    # Create a file and a symlink to it
    real_file = tmp_path / "real.txt"
    real_file.touch()
    link_file = tmp_path / "link.txt"
    os.symlink(real_file, link_file)

    # Get the real path of the symlink
    real_path = get_real_path(str(link_file))
    assert real_path == str(real_file.resolve())
