class Param:
    def __init__(self, name: str, type: str = "string"):
        self.name = name
        self.type = type

    def __repr__(self):
        return f"<Param {self.name}>"


def parse_path(path: str) -> tuple[str, list[str]]:
    """
    Parses a path and extracts parameters.
    Returns a socketify-compatible path and a list of parameter names in order.
    """
    param_names = []
    socketify_path = ""
    segments = [s for s in path.split("/") if s]  # Filter empty segments
    for segment in segments:
        if segment.startswith("{") and segment.endswith("}"):
            param_name = segment[1:-1]
            param_names.append(param_name)
            socketify_path += f"/:{param_name}"
        else:
            socketify_path += f"/{segment}"
    if not socketify_path:
        socketify_path = "/"
    return socketify_path, param_names
