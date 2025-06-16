import os
import sys
import queue
import threading
import subprocess
import torch
import whisper
import time  # Eksik import tamamlandı
from tkinter import messagebox, filedialog

from config import MODEL_FOLDER
os.makedirs(MODEL_FOLDER, exist_ok=True)  # Ensure model folder exists


def ensure_model_folder():
    """Check model folder and optionally let the user choose a new one."""
    global MODEL_FOLDER
    if not os.path.isdir(MODEL_FOLDER):
        os.makedirs(MODEL_FOLDER, exist_ok=True)
    if messagebox.askyesno(
        "Model Klasörü",
        f"Model klasörü olarak '{MODEL_FOLDER}' kullanılacak. Değiştirmek ister misiniz?",
    ):
        new_dir = filedialog.askdirectory(initialdir=MODEL_FOLDER)
        if new_dir:
            MODEL_FOLDER = new_dir
            os.makedirs(MODEL_FOLDER, exist_ok=True)


MODEL_LIST = [
    "tiny", "tiny.en",
    "base", "base.en",
    "small", "small.en",
    "medium", "medium.en",
    "large", "large-v2", "large-v3", "whisper-turbo"
]

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
    return missing_modules

def install_requirements():
    packages = ["openai-whisper", "torch", "psutil", "gputil"]
    for pkg in packages:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True, text=True)

def run_transcription(q, stop_evt, model_name, audio_file):
    start_time = time.time()
    try:
        if not torch.cuda.is_available():
            raise RuntimeError("No NVIDIA CUDA GPU found! GPU is required for this application.")

        device = "cuda"
        model_file_pt = os.path.join(MODEL_FOLDER, f"{model_name}.pt")
        model_file_bin = os.path.join(MODEL_FOLDER, f"{model_name}.bin")

        if not (os.path.isfile(model_file_pt) or os.path.isfile(model_file_bin)):
            if not messagebox.askyesno("Eksik Model", "Model indirilsin mi?"):
                q.put(("Warning", f"Model dosyasi bulunamadi: {model_name}."))
                return

        model = whisper.load_model(model_name, device=device, download_root=MODEL_FOLDER)
        
        if stop_evt.is_set():
            q.put(("StoppedBeforeTranscribe", None))
            return
        
        q.put("Model loaded. Starting transcription...")
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
