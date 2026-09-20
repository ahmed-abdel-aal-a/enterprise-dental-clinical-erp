"""High-performance PDF generation engine using native Microsoft Edge Headless.

Engineered for Native Windows environments without external GTK/Pango dependencies
like WeasyPrint, providing ultra-fast, zero-overhead PDF rendering for low-end hardware.
"""

import asyncio
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_CACHED_EDGE_PATH: str | None = None


def find_edge_binary() -> str | None:
    """Dynamically resolve the executable path of Microsoft Edge or Chromium.

    Checks:
    1. Windows Registry (HKLM & HKCU App Paths for msedge.exe)
    2. Common Windows Program Files directories (x86, 64-bit, and LocalAppData)
    3. System PATH via shutil.which
    4. Fallback to Google Chrome or Chromium binaries if Edge is missing.
    """
    global _CACHED_EDGE_PATH
    if _CACHED_EDGE_PATH and os.path.exists(_CACHED_EDGE_PATH):
        return _CACHED_EDGE_PATH

    # 1. Query Windows Registry
    if sys.platform == "win32":
        try:
            import winreg

            reg_keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ]
            for root_key, sub_key in reg_keys:
                try:
                    with winreg.OpenKey(root_key, sub_key) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val and os.path.isfile(val):
                            _CACHED_EDGE_PATH = val
                            logger.info(f"Resolved browser binary via Windows Registry: {val}")
                            return val
                except (OSError, FileNotFoundError):
                    continue
        except ImportError:
            pass

    # 2. Known physical paths on Windows
    candidate_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    for p in candidate_paths:
        if os.path.isfile(p):
            _CACHED_EDGE_PATH = p
            logger.info(f"Resolved browser binary via standard path: {p}")
            return p

    # 3. Search in system PATH
    for name in ["msedge", "msedge.exe", "microsoft-edge", "chrome", "google-chrome", "chromium"]:
        found = shutil.which(name)
        if found and os.path.isfile(found):
            _CACHED_EDGE_PATH = found
            logger.info(f"Resolved browser binary via PATH search: {found}")
            return found

    logger.warning("No Microsoft Edge or Chromium binary could be located on this machine.")
    return None


def render_html_to_pdf(html_content: str, timeout_seconds: int = 15) -> bytes:
    """Convert HTML string to high-fidelity PDF bytes using Microsoft Edge Headless.

    Args:
        html_content: Complete HTML document string with CSS and UTF-8 encoding.
        timeout_seconds: Maximum allowed time for PDF generation before forcefully killing the process.

    Returns:
        PDF binary content as bytes.

    Raises:
        RuntimeError: If browser binary is not found, PDF generation fails, or timeout occurs.
    """
    browser_bin = find_edge_binary()
    if not browser_bin:
        # Fallback to WeasyPrint if browser is unavailable
        try:
            from weasyprint import HTML
            from io import BytesIO

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            return pdf_buffer.getvalue()
        except ImportError:
            raise RuntimeError(
                "Cannot generate PDF: Microsoft Edge/Chrome is not installed and WeasyPrint is unavailable."
            )

    # Prepare temporary HTML and output PDF files
    temp_dir = tempfile.mkdtemp(prefix="dentapex_pdf_")
    html_file = os.path.join(temp_dir, "document.html")
    pdf_file = os.path.join(temp_dir, "output.pdf")

    try:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        cmd = [
            browser_bin,
            "--headless=new" if "--headless=new" in sys.argv else "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--disable-software-rasterizer",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={pdf_file}",
            html_file,
        ]

        # Execute with strict timeout & zombie process killer
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            logger.error(f"Edge PDF generation timed out after {timeout_seconds}s. Forcefully terminating process.")
            proc.kill()
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            raise RuntimeError(f"Edge PDF generation timed out after {timeout_seconds} seconds.")

        if proc.returncode != 0 and not os.path.exists(pdf_file):
            logger.error(f"Edge headless exited with returncode {proc.returncode}. Stderr: {stderr}")
            raise RuntimeError(f"Edge headless PDF generation failed (code {proc.returncode}): {stderr.strip()}")

        if not os.path.exists(pdf_file) or os.path.getsize(pdf_file) == 0:
            raise RuntimeError("Edge headless completed but no PDF output was produced.")

        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()

        return pdf_bytes

    finally:
        # Guaranteed cleanup of temporary directory and files
        shutil.rmtree(temp_dir, ignore_errors=True)


async def render_html_to_pdf_async(html_content: str, timeout_seconds: int = 15) -> bytes:
    """Async wrapper to offload CPU/process-bound PDF generation to a worker thread."""
    return await asyncio.to_thread(render_html_to_pdf, html_content, timeout_seconds)
