
## 2023-10-27 - [TOCTOU in Static File Handler]
**Vulnerability:** A Time-of-Check to Time-of-Use (TOCTOU) vulnerability existed in `xyra/application.py` where `os.path.exists()`, `os.path.isfile()`, and `os.path.getsize()` were checked sequentially before the file was opened with `open(..., "rb")`. An attacker could potentially swap a benign file for a malicious symlink between the check and the open.
**Learning:** Checking file properties and then opening it creates a race condition window.
**Prevention:** Open the file first, then use `os.fstat(f.fileno())` to check its properties (size, type) using the file descriptor. This ensures the properties checked belong to the exact file being read.
