import os
import sys
import queue
import threading
import subprocess
import torch
import whisper
from huggingface_hub import snapshot_download
import time  # Eksik import tamamlandı
from tkinter import messagebox, filedialog

from config import MODEL_FOLDER, MODEL_REQUIREMENTS, HUGGINGFACE_REPOS, HF_TOKEN, MODEL_LIST
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

def install_requirements():
    packages = ["openai-whisper", "torch", "psutil", "gputil", "fpdf"]
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
            size = MODEL_REQUIREMENTS.get(model_name, {}).get("size", "bilinmiyor")
            if not messagebox.askyesno(
                "Eksik Model",
                f"{model_name} modeli (~{size}) indirilecek. Onaylıyor musunuz?",
            ):
                q.put(("Warning", f"Model dosyasi bulunamadi: {model_name}."))
                return

        if model_name == "whisper-turbo":
            repo_id = HUGGINGFACE_REPOS.get(model_name)
            if not repo_id:
                q.put(("Error", f"'{model_name}' modeli icin repo bulunamadi."))
                return
            download_args = dict(
                repo_id=repo_id,
                local_dir=MODEL_FOLDER,
                local_dir_use_symlinks=False,
            )
            if HF_TOKEN:
                download_args["token"] = HF_TOKEN
            try:
                model_path = snapshot_download(**download_args)
            except Exception as e:
                q.put(("Error", f"Repo indirilemedi: {e}"))
                return
            model = whisper.load_model(model_path, device=device)
        else:
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
