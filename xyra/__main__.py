import argparse
import importlib.util
import os
import sys


def load_app_from_file(file_path: str):
    """
    Load a Xyra app instance from a Python file.

    This function dynamically imports a Python module from the given file path
    and extracts the 'app' variable, which should be an instance of the Xyra App class.

    Args:
        file_path: Path to the Python file containing the app instance.

    Returns:
        The Xyra app instance from the file.

    Raises:
        SystemExit: If the file doesn't exist, can't be loaded, or doesn't contain an 'app' variable.
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    try:
        # Extract module name from file path
        module_name = os.path.splitext(os.path.basename(file_path))[0]

        # Create module spec for dynamic loading
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec is None or spec.loader is None:
            print(f"Error: Could not load module from '{file_path}'")
            sys.exit(1)

        # Create and execute the module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Extract the app instance
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
    """
    Main entry point for the Xyra CLI.

    This function parses command-line arguments and runs the specified Xyra application.
    It supports configuration of host, port, and auto-reload mode.
    """
    parser = argparse.ArgumentParser(
        description="Run a Xyra application.", prog="python -m xyra"
    )
    parser.add_argument(
        "file",
        help="The Python file containing the Xyra app instance (must have an 'app' variable).",
    )
    parser.add_argument(
        "--host", default="localhost", help="Host to bind to (default: localhost)."
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

    # Load the application from the specified file
    app = load_app_from_file(args.file)

    # Note: Auto-reload is handled internally by app.listen()

    try:
        # Start the server with the specified configuration
        app.listen(port=args.port, host=args.host, reload=args.reload)
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
