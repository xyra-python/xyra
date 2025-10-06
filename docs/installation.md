# Installing Xyra Framework

This guide will help you install Xyra on your system.

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Package Manager**: pip (comes with Python)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install Xyra is from PyPI:

```bash
pip install xyra
```

For development or if you want the latest features:

```bash
pip install --pre xyra
```

### Method 2: Install from Source

If you want to contribute to Xyra or need the latest development version:

```bash
git clone https://github.com/xyra-python/xyra.git
cd xyra
pip install -e .
```

This installs Xyra in development mode, so changes to the source code are immediately available.

### Method 3: Using Poetry

If you're using Poetry for dependency management:

```bash
poetry add xyra
```

Or for development:

```bash
git clone https://github.com/xyra-python/xyra.git
cd xyra
poetry install
```

### Method 4: Using uv

For faster package management with uv:

```bash
uv add xyra
```

## Dependencies

Xyra has minimal dependencies to keep it lightweight:

- **socketify**: High-performance networking library
- **jinja2**: Template engine for HTML rendering
- **typing-extensions**: Backport of typing features for older Python versions

These dependencies are automatically installed when you install Xyra.

## Verifying Installation

After installation, verify that Xyra is working correctly:

```python
import xyra
print("Xyra installed successfully!")
print(f"Version: {xyra.__version__}")
```

You can also run a quick test:

```python
from xyra import App, Request, Response

app = App()

@app.get("/")
def hello(req: Request, res: Response):
    res.json({"message": "Xyra is working!"})

if __name__ == "__main__":
    print("Testing Xyra installation...")
    # Just test that the app can be created without errors
    print("✅ Xyra is ready to use!")
```

## Platform-Specific Instructions

### Linux

Xyra works out of the box on most Linux distributions. If you encounter issues with socketify, you may need to install development headers:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel

# Arch Linux
sudo pacman -S base-devel python
```

### macOS

Xyra works on macOS with Xcode command line tools:

```bash
xcode-select --install
```

### Windows

Xyra supports Windows, but for the best experience, consider using WSL (Windows Subsystem for Linux) or a Linux container.

If you must use Windows natively, ensure you have:

- Visual Studio Build Tools (for socketify compilation)
- Windows SDK

## Virtual Environments

It's recommended to use virtual environments to isolate your project dependencies:

### Using venv

```bash
python -m venv xyra_env
source xyra_env/bin/activate  # On Windows: xyra_env\Scripts\activate
pip install xyra
```

### Using conda

```bash
conda create -n xyra_env python=3.11
conda activate xyra_env
pip install xyra
```

## Troubleshooting

### Common Installation Issues

1. **Permission denied**: Use `pip install --user xyra` or use a virtual environment

2. **Compilation errors**: Ensure you have build tools installed (see platform-specific instructions above)

3. **Import errors after installation**: Try reinstalling with `pip install --force-reinstall xyra`

4. **SSL certificate issues**: Update pip and certificates:
   ```bash
   pip install --upgrade pip
   pip install --upgrade certifi
   ```

### Checking Python Version

Ensure you have the correct Python version:

```bash
python --version
# Should show Python 3.11 or higher
```

### Checking pip Version

Make sure pip is up to date:

```bash
pip --version
pip install --upgrade pip
```

### Firewall/Antivirus Issues

If installation fails due to network issues, temporarily disable your firewall/antivirus or configure them to allow pip downloads.

## Upgrading Xyra

To upgrade to the latest version:

```bash
pip install --upgrade xyra
```

For development installations:

```bash
cd /path/to/xyra/source
git pull
pip install -e .
```

## Uninstalling Xyra

To remove Xyra from your system:

```bash
pip uninstall xyra
```

## Next Steps

Now that you have Xyra installed, check out:

- [Getting Started](getting-started.md) - Your first Xyra application
- [Examples](examples.md) - Complete example applications
- [API Reference](api-reference.md) - Detailed API documentation

---

[Back to Table of Contents](../README.md)