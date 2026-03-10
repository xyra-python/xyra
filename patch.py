with open("xyra/request.py", "r") as f:
    content = f.read()

import re

old_code = """        content_type = self.get_header("content-type", "")
        content_type_lower = content_type.lower()
        if not content_type_lower or not (
            content_type_lower.startswith("application/json") or
            "+json" in content_type_lower
        ):"""

new_code = """        content_type = self.get_header("content-type", "")
        media_type = content_type.split(";")[0].strip().lower()
        if not media_type or not (
            media_type == "application/json" or
            media_type.endswith("+json")
        ):"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("xyra/request.py", "w") as f:
        f.write(content)
    print("Patched!")
else:
    print("Could not find old code")
