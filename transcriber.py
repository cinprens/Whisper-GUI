import os
import sys
import queue
import threading
import subprocess
import torch
import whisper
import time  # Eksik import tamamlandı

MODEL_FOLDER = r"C:\Users\Mahmut\Desktop\WhisperGUI\WhisperModels"
os.makedirs(MODEL_FOLDER, exist_ok=True)  # Ensure model folder exists

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
    threading.Thread(
        target=run_transcription,
        args=(q, stop_event, model_name, selected_file),
        daemon=True
    ).start()
