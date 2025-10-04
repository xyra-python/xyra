import argparse
import importlib.util
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Run a Xyra application.")
    parser.add_argument("file", help="The file containing the Xyra app instance.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    args = parser.parse_args()

    module_name = os.path.splitext(os.path.basename(args.file))[0]
    spec = importlib.util.spec_from_file_location(module_name, args.file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    app = getattr(module, "app", None)
    if app is None:
        print(f"Error: No 'app' instance found in {args.file}")
        sys.exit(1)

    app.listen(port=args.port, host=args.host)

if __name__ == "__main__":
    main()