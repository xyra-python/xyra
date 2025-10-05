import json
import inspect
import re

def generate_swagger(app, title="Xyra API", version="1.0.0", **kwargs):
    swagger = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
        },
        "paths": {},
    }

    for route in app.router.routes:
        path = route["path"]
        method = route["method"].lower()
        handler = route["handler"]

        if path not in swagger["paths"]:
            swagger["paths"][path] = {}

        summary = f"{method.upper()} {path}"
        description = ""
        docstring = inspect.getdoc(handler)
        if docstring:
            lines = docstring.strip().split('\n')
            summary = lines[0]
            if len(lines) > 1:
                description = '\n'.join(lines[1:]).strip()

        parameters = []
        path_params = re.findall(r'\{(\w+)\}', path)
        for param in path_params:
            parameters.append({
                "name": param,
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string"
                }
            })

        swagger["paths"][path][method] = {
            "summary": summary,
            "description": description,
            "parameters": parameters,
            "responses": {
                "200": {
                    "description": "Successful response"
                }
            }
        }

    return swagger