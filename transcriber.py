import os
import sys
import queue
import threading
import subprocess
import torch
import whisper
import time  # Eksik import tamamlandı
from tkinter import messagebox, filedialog

from config import MODEL_FOLDER, MODEL_REQUIREMENTS, MODEL_LIST
os.makedirs(MODEL_FOLDER, exist_ok=True)  # Ensure model folder exists


def ensure_model_folder():
    """MODEL_FOLDER klasörünün mevcut olduğundan emin ol."""
    os.makedirs(MODEL_FOLDER, exist_ok=True)


def get_installed_models():
    """MODEL_FOLDER içindeki .pt veya .bin uzantılı dosyalardan model adlarını döndür."""
    models = []
    if os.path.isdir(MODEL_FOLDER):
        for fname in os.listdir(MODEL_FOLDER):
            base, ext = os.path.splitext(fname)
            if ext in {".pt", ".bin"}:
                models.append(base)
    return models



def check_requirements():
    missing_modules = []
    try:
        import psutil
    except ImportError:
        missing_modules.append("psutil")
    try:
        import GPUtil
    except ImportError:
        missing_modules.append("gputil")
    try:
        import fpdf
    except ImportError:
        missing_modules.append("fpdf")
    return missing_modules

def install_requirements(packages=None):
    """Install only the given packages or the ones returned by check_requirements."""
    if packages is None:
        packages = check_requirements()
    for pkg in packages:
        subprocess.run([
            sys.executable,
            "-m",
            "pip",
            "install",
            pkg,
        ], capture_output=True, text=True)

def run_transcription(q, stop_evt, model_name, audio_file):
    start_time = time.time()
    try:
        if not torch.cuda.is_available():
            raise RuntimeError("No NVIDIA CUDA GPU found! GPU is required for this application.")

        device = "cuda"
        model_file_pt = os.path.join(MODEL_FOLDER, f"{model_name}.pt")
        model_file_bin = os.path.join(MODEL_FOLDER, f"{model_name}.bin")

        if not (os.path.isfile(model_file_pt) or os.path.isfile(model_file_bin)):
            q.put(("Warning", "Model bulunamadı, lütfen önce indirin."))
            return

        model = whisper.load_model(model_name, device=device, download_root=MODEL_FOLDER)
        
        if stop_evt.is_set():
            q.put(("StoppedBeforeTranscribe", None))
            return
        
        q.put(("Log", "Model loaded. Starting transcription..."))
        result = model.transcribe(audio_file)
        
        if stop_evt.is_set():
            q.put(("StoppedAfterTranscribe", None))
            return
        
        end_time = time.time()
        duration = end_time - start_time
        q.put(("Result", result, duration))
    except Exception as e:
        q.put(("Error", str(e)))
    finally:
        torch.cuda.empty_cache()

def transcribe(q, stop_event, model_name, selected_file):
    stop_event.clear()
    ensure_model_folder()
    threading.Thread(
        target=run_transcription,
        args=(q, stop_event, model_name, selected_file),
        daemon=True
    ).start()


def download_model(model_name):
    """Download the given Whisper model to MODEL_FOLDER."""
    ensure_model_folder()
    whisper.load_model(model_name, device="cpu", download_root=MODEL_FOLDER)
