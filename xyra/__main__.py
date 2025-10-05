import argparse
import importlib.util
import os
import sys


def load_app_from_file(file_path: str):
    """Load an app instance from a Python file."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec is None or spec.loader is None:
            print(f"Error: Could not load module from '{file_path}'")
            sys.exit(1)

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        app = getattr(module, "app", None)
        if app is None:
            print(f"Error: No 'app' instance found in {file_path}")
            print(
                "Make sure your file defines an 'app' variable with your Xyra application."
            )
            sys.exit(1)

        return app

    except Exception as e:
        print(f"Error loading application from '{file_path}': {e}")
        sys.exit(1)


def main():
    """Main entry point for running Xyra applications."""
    parser = argparse.ArgumentParser(
        description="Run a Xyra application.", prog="python -m xyra"
    )
    parser.add_argument(
        "file",
        help="The Python file containing the Xyra app instance (must have an 'app' variable).",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to listen on (default: 8000)."
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on file changes (development mode).",
    )

    args = parser.parse_args()

    # Load and run the application
    app = load_app_from_file(args.file)

    if args.reload:
        print("⚠️  Auto-reload is not implemented yet. Running in normal mode.")

    try:
        app.listen(port=args.port, host=args.host)
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
