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
        assert info.st_size == 12  # "test content" is 12 bytes
