import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import logging
from config import missing_modules

PACKAGE_TO_MODULE = {
    "openai-whisper": "whisper",
    "torch": "torch",
    "psutil": "psutil",
    "gputil": "GPUtil",
}

logger = logging.getLogger(__name__)

def install_requirements(button_widget):
    """Gereksiz tekrarları kaldırılmış, optimize edilmiş kurulum fonksiyonu."""
    button_widget.config(state="disabled")
    logger.info("Installing required packages...")
    
    t = threading.Thread(target=run_installation, args=(button_widget,), daemon=True)
    t.start()

def run_installation(button_widget):
    try:
        packages = ["openai-whisper", "torch", "psutil", "gputil", "fpdf"]

        for pkg in packages:
            logger.info(f"Installing: {pkg}")
            result = subprocess.run([
                sys.executable,
                "-m",
                "pip",
                "install",
                pkg,
            ], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Successfully installed: {pkg}")
                if pkg in missing_modules:
                    missing_modules.remove(pkg)
            else:
                logger.error(f"Failed to install {pkg}: {result.stderr}")

        logger.info("All required packages have been installed.")
        messagebox.showinfo("Installation Complete", "Restart the application to apply changes.")
    except Exception as e:
        logger.error(f"Error during installation: {e}")
        messagebox.showerror("Installation Error", f"An error occurred: {e}")
    finally:
        button_widget.config(state="normal")
