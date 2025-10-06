import os


def get_real_path(path: str) -> str:
    return os.path.realpath(path)


def get_file_info(path: str) -> os.stat_result:
    return os.stat(path)
