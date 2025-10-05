from typing import Dict


class Param:
    def __init__(self, name: str, type: str = "string"):
        self.name = name
        self.type = type

    def __repr__(self):
        return f"<Param {self.name}>"


def parse_path(path: str) -> tuple[str, Dict[str, Param]]:
    """
    Parses a path and extracts parameters.
    Returns a regex-compatible path and a dictionary of parameters.
    """
    params = {}
    regex_path = ""
    for segment in path.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            param_name = segment[1:-1]
            params[param_name] = Param(param_name)
            regex_path += f"/(?P<{param_name}>[^/]+)"
        else:
            regex_path += f"/{segment}"
    return regex_path, params
