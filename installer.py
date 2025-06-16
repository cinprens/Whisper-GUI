import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from config import missing_modules

PACKAGE_TO_MODULE = {
    "openai-whisper": "whisper",
    "torch": "torch",
    "psutil": "psutil",
    "gputil": "GPUtil",
    "fpdf": "fpdf",
}

def install_requirements(log_func, button_widget):
    """
    Gereksiz tekrarları kaldırılmış, optimize edilmiş kurulum fonksiyonu.
    - log_func: Log paneline yazmak için kullanılacak fonksiyon
    - button_widget: Kurulum bitince butonun tekrar aktif edilmesi vb.
    """
    button_widget.config(state="disabled")
    log_func("Installing required packages...")
    
    t = threading.Thread(target=run_installation, args=(log_func, button_widget), daemon=True)
    t.start()

def run_installation(log_func, button_widget):
    try:
        packages = ["openai-whisper", "torch", "psutil", "gputil", "fpdf"]

        for pkg in packages:
            log_func(f"Installing: {pkg}")
            result = subprocess.run([
                sys.executable,
                "-m",
                "pip",
                "install",
                pkg,
            ], capture_output=True, text=True)

            if result.returncode == 0:
                log_func(f"Successfully installed: {pkg}")
                if pkg in missing_modules:
                    missing_modules.remove(pkg)
            else:
                log_func(f"Failed to install {pkg}: {result.stderr}")

        log_func("All required packages have been installed.")
        messagebox.showinfo("Installation Complete", "Restart the application to apply changes.")
    except Exception as e:
        log_func(f"Error during installation: {e}")
        messagebox.showerror("Installation Error", f"An error occurred: {e}")
    finally:
        button_widget.config(state="normal")
