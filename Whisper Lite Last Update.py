import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import time
import platform
import queue
import subprocess
import sys
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

####################################
# 1) Define the target model folder
####################################
MODEL_FOLDER = r"C:\Users\Mahmut\Desktop\WhisperGUI\WhisperModels"
os.makedirs(MODEL_FOLDER, exist_ok=True)  # Create folder if it doesn't exist

####################################
# 2) Check Missing Modules
####################################
missing_modules = []
try:
    import whisper
except ImportError:
    missing_modules.append("whisper")

try:
    import torch
except ImportError:
    missing_modules.append("torch")

try:
    import psutil
except ImportError:
    missing_modules.append("psutil")

try:
    import GPUtil
except ImportError:
    missing_modules.append("gputil")

########################
# Flags
########################
can_transcribe = ("whisper" not in missing_modules) and ("torch" not in missing_modules)

########################
# UI TEXT
########################
UI_TEXT = {
    "app_title": "OpenAI Whisper GPU Transcriber",
    "select_file": "Select File",
    "no_file_selected": "No file selected",
    "select_model": "Select Model:",
    "start_transcription": "Start Transcription",
    "stop": "Stop",
    "save_transcription": "Save Transcription",
    "install_requirements": "Install Requirements",
    "detected_language": "Detected Language",
    "processing_time": "Processing Time",
    "transcription": "Transcription",
    "log": "Log:",
    "model_requirements_title": "Model Requirements:",
    "model_requirements": "Model requirements",
    "requirements_not_available": "Requirements not available.",
    "file_types_audio": "Audio/Video Files",
    "file_types_all": "All Files",
    "file_selected": "File selected",
    "file_selection_cancelled": "File selection cancelled.",
    "model_loading": "Loading model...",
    "model_loaded": "Model loaded",
    "transcription_starting": "Starting transcription...",
    "transcription_finished": "Transcription finished.",
    "error_occurred": "An error occurred",
    "process_completed": "Process completed.",
    "warning": "Warning",
    "please_select_file": "Please select a file.",
    "model_selected": "Selected model",
    "input_language_auto": "Input language will be auto-detected.",
    "info": "Info",
    "cannot_stop_thread": "Cannot forcibly kill the transcription thread (no partial stop).",
    "transcription_not_stopped": "Transcription process could not be stopped instantly.",
    "transcription_already_stopped": "Transcription process already completed or stopped.",
    "text_files": "Text Files",
    "text_saved": "Text saved successfully.",
    "save_cancelled": "Save operation cancelled.",
    "no_text_to_save": "No text to save.",
    "no_text_to_save_log": "Save failed: No text to save.",
    "installing_packages": "Installing required packages...",
    "installing_package": "Installing package",
    "package_installed": "Package installed",
    "package_install_error": "Package install error",
    "all_packages_installed": "All required components have been installed. ✓",
    "all_components_installed": "All required components have been installed. ✓",
    "package_installation_error": "An error occurred during package installation",
    "cpu_usage": "CPU Usage",
    "ram_usage": "RAM Usage",
    "gpu_usage": "GPU Usage",
    "gpu_memory": "GPU Memory",
    "error_in_check_queue": "Error (check_queue)",
    "unknown": "Unknown",
    "seconds": "seconds",
    "theme": "Theme",
    "settings": "Settings",
    "help": "Help",
    "about": "About",
    "about_text": (
        "OpenAI Whisper GPU Transcriber\n"
        "Forces GPU usage if available, transcribes audio/video to text.\n"
        "If no compatible CUDA GPU is found, it raises an error.\n"
        "Author: PrensCin & ChatGPT"
    ),
    "credits": "Developed by PrensCin & ChatGPT",
    "character_count": "Character Count",
    "missing_modules": "Missing Modules",
    "missing_modules_transcription": "Required modules for transcription are missing. Please install them.",
    "missing_modules_transcription_log": "Transcription failed: Required modules are missing.",
    "missing_modules_system_info": "psutil/gputil is missing; cannot show system info.",
    "restart_required": "Please restart the application after installation.",
    "stop_in_progress": "Stop requested. Waiting for the ongoing process to finish internally.",
    "insufficient_vram": "Insufficient VRAM for the selected model.",
    "transcription_stopped_no_result": "Transcription was stopped. No result will be shown.",
}

####################################
# 3) Model List & Requirements
####################################
MODEL_LIST = [
    "tiny", "tiny.en",
    "base", "base.en",
    "small", "small.en",
    "medium", "medium.en",
    "large", "large-v2"
]

MODEL_REQUIREMENTS = {
    "tiny":       {"gpu_vram": "1GB+",  "ram": "2GB+",  "notes": "Fast, lower accuracy",  "min_vram": 1.0},
    "tiny.en":    {"gpu_vram": "1GB+",  "ram": "2GB+",  "notes": "English-only version",  "min_vram": 1.0},
    "base":       {"gpu_vram": "1GB+",  "ram": "3GB+",  "notes": "Base model",            "min_vram": 1.0},
    "base.en":    {"gpu_vram": "1GB+",  "ram": "3GB+",  "notes": "English-only version",  "min_vram": 1.0},
    "small":      {"gpu_vram": "2-3GB", "ram": "4GB+",  "notes": "Good trade-off size",   "min_vram": 2.0},
    "small.en":   {"gpu_vram": "2-3GB", "ram": "4GB+",  "notes": "English-only version",  "min_vram": 2.0},
    "medium":     {"gpu_vram": "5GB+",  "ram": "8GB+",  "notes": "More accurate, bigger", "min_vram": 5.0},
    "medium.en":  {"gpu_vram": "5GB+",  "ram": "8GB+",  "notes": "English-only version",  "min_vram": 5.0},
    "large":      {"gpu_vram": "10GB+", "ram": "16GB+", "notes": "Multilingual, large",   "min_vram": 10.0},
    "large-v2":   {"gpu_vram": "10GB+", "ram": "16GB+", "notes": "Newer large variant",   "min_vram": 10.0},
}

####################################
# 4) Global Vars
####################################
selected_file = ""
transcribe_thread = None
menubar = None
stop_event = threading.Event()  # Event to signal stopping

####################################
# 5) Functions
####################################

def log_message(message):
    log_area.insert(tk.END, message + "\n")
    log_area.see(tk.END)

def select_file():
    global selected_file
    filetypes = (
        ("Audio/Video Files", "*.mp3 *.mp4 *.wav *.m4a *.ogg *.flac *.webm *.aac"),
        ("All Files", "*.*")
    )
    selected_file = filedialog.askopenfilename(title="Select File", filetypes=filetypes)
    if selected_file:
        file_label.config(text=selected_file)
        filename_only = os.path.basename(selected_file)
        log_message(f"File selected: {selected_file}")
        log_message(f"{filename_only} dosyası yüklendi ve işleme hazır.")  # Ek mesaj
    else:
        file_label.config(text=UI_TEXT["no_file_selected"])
        log_message("File selection cancelled")

def update_requirements():
    """
    Shows approximate system requirements for the currently selected model.
    """
    model_name = model_var.get()
    req = MODEL_REQUIREMENTS.get(model_name, {})
    if req:
        text = (
            f"{UI_TEXT['model_requirements']}: {model_name}\n"
            f"- GPU VRAM: {req['gpu_vram']}\n"
            f"- RAM: {req['ram']}\n"
            f"- Notes: {req['notes']}\n"
        )
    else:
        text = UI_TEXT["requirements_not_available"]

    requirements_area.config(state="normal")
    requirements_area.delete("1.0", tk.END)
    requirements_area.insert(tk.END, text)
    requirements_area.config(state="disabled")


def run_transcription(q, stop_evt, model_name, audio_file):
    """
    Background thread: forcibly uses GPU, checks VRAM, downloads models to MODEL_FOLDER.
    stop_evt: threading.Event for "stop" signal
    """
    import time
    start_time = time.time()

    try:
        import whisper
        import torch

        # ========== Detailed GPU Check ========== #
        if not torch.cuda.is_available():
            raise RuntimeError(
                "No NVIDIA CUDA GPU found or CUDA is not available!\n"
                "This application strictly requires a CUDA-capable GPU."
            )
        device_idx = 0  # Varsayılan GPU
        device_name = torch.cuda.get_device_name(device_idx)
        
        # Burayı try-except'e aldık:
        try:
            props = torch.cuda.get_device_properties(device_idx)
            total_vram_gb = props.total_memory / (1024**3)
        except RuntimeError as e:
            q.put(("Error", f"GPU properties alınamadı. Sürücü veya CUDA versiyon hatası olabilir: {str(e)}"))
            return

        # Modelin asgari VRAM gereksinimini kontrol et
        req = MODEL_REQUIREMENTS.get(model_name, {})
        min_vram = req.get("min_vram", 1.0)
        if total_vram_gb < min_vram:
            raise RuntimeError(
                f"{UI_TEXT['insufficient_vram']}\n"
                f"Model: {model_name}, Required ~{min_vram}GB, Found ~{total_vram_gb:.2f}GB on [{device_name}]"
            )

        q.put(f"{UI_TEXT['model_loading']} (GPU: {device_name}, {total_vram_gb:.2f}GB VRAM)")
        device = "cuda"

        # Model dosyası indirilmiş mi kontrolü
        model_path = os.path.join(MODEL_FOLDER, f"{model_name}.pt")
        # Bazı modeller tiny.en.pt olarak inebiliyor, vs. ama kabaca kontrol ekliyoruz:
        if not os.path.exists(model_path):
            q.put(f"Model not found locally, will be downloaded: {model_name}")

        model = whisper.load_model(
            model_name,
            device=device,
            download_root=MODEL_FOLDER
        )
        if stop_evt.is_set():
            # Eğer stop_event bu aşamada set edilmişse, model yüklense dahi transkripsiyonu iptal edebiliriz
            q.put(("StoppedBeforeTranscribe", None))
            return

        q.put(f"{UI_TEXT['model_loaded']}: {model_name} ({device})")

        q.put(UI_TEXT["transcription_starting"])
        # Burada transcribe başlıyor, maalesef adım adım durdurma yok
        result = model.transcribe(audio_file)
        
        # Transkripsiyon bitti ama tekrar kontrol edip stop edilmiş mi bakalım
        if stop_evt.is_set():
            # Eğer transkripsiyon bitse bile "kullanıcı durdurdu" ise
            q.put(("StoppedAfterTranscribe", None))
            return

        q.put(UI_TEXT["transcription_finished"])
        end_time = time.time()
        duration = end_time - start_time
        q.put(("Result", result, duration))

    except Exception as e:
        q.put(("Error", str(e)))
    finally:
        # CUDA bellek temizliği
        if 'torch' in sys.modules and torch.cuda.is_available():
            torch.cuda.empty_cache()


def transcribe():
    global transcribe_thread
    stop_event.clear()  # Yeni bir transkripsiyon öncesi 'stop' sinyalini sıfırla

    # 1) Zaten bir transkripsiyon varsa engelle
    if transcribe_thread and transcribe_thread.is_alive():
        messagebox.showwarning("Warning", "Transcription already in progress!")
        return

    # 2) Dosya seçili mi?
    if not selected_file:
        messagebox.showwarning("Warning", UI_TEXT["please_select_file"])
        return
    # 3) Path gerçekten var mı?
    if not os.path.exists(selected_file):
        messagebox.showerror("Error", f"The file does not exist: {selected_file}")
        log_message(f"Error: The file does not exist: {selected_file}")
        return
    # 4) Gerekli modüller kurulu mu?
    if not can_transcribe:
        messagebox.showwarning("Warning", UI_TEXT["missing_modules_transcription"])
        log_message(UI_TEXT["missing_modules_transcription_log"])
        return

    transcribe_button.config(state="disabled")
    stop_button.config(state="normal")
    log_message(f"{UI_TEXT['model_selected']}: {model_var.get()}")
    log_message(f"Processing file: {selected_file}")

    # Start transcription in a separate thread
    q = queue.Queue()
    transcribe_thread = threading.Thread(
        target=run_transcription,
        args=(q, stop_event, model_var.get(), selected_file),
        daemon=True
    )
    transcribe_thread.start()
    check_queue(q)


def check_queue(q):
    """
    Poll messages from the worker thread and update GUI accordingly.
    """
    try:
        while True:
            msg = q.get_nowait()
            if isinstance(msg, str):
                # Düz metin mesajı
                log_message(msg)

            elif isinstance(msg, tuple):
                if msg[0] == "Error":
                    log_message(f"{UI_TEXT['error_occurred']}: {msg[1]}")
                    messagebox.showerror(UI_TEXT["error_occurred"], msg[1])
                    transcribe_button.config(state="normal")
                    stop_button.config(state="disabled")
                    save_transcription_button.config(state="normal")

                elif msg[0] == "Result":
                    result_dict = msg[1]
                    duration = msg[2]

                    detected_lang = result_dict.get("language", UI_TEXT["unknown"])
                    try:
                        from whisper.tokenizer import LANGUAGES
                        lang_name = LANGUAGES.get(detected_lang, UI_TEXT["unknown"]).capitalize()
                    except:
                        lang_name = detected_lang

                    language_label.config(
                        text=f"{UI_TEXT['detected_language']}: {lang_name}"
                    )
                    duration_label.config(
                        text=f"{UI_TEXT['processing_time']}: {duration:.2f} {UI_TEXT['seconds']}"
                    )
                    log_message(f"{UI_TEXT['detected_language']}: {lang_name}")
                    log_message(UI_TEXT["process_completed"])

                    transcription_area.delete("1.0", tk.END)
                    transcription_area.insert(tk.END, result_dict.get("text", ""))

                    transcribe_button.config(state="normal")
                    stop_button.config(state="disabled")
                    save_transcription_button.config(state="normal")
                    update_transcription_char_count()

                elif msg[0] == "StoppedBeforeTranscribe":
                    # Kullanıcı model yüklenirken iptal etti
                    log_message(UI_TEXT["transcription_stopped_no_result"])
                    transcribe_button.config(state="normal")
                    stop_button.config(state="disabled")
                    save_transcription_button.config(state="normal")

                elif msg[0] == "StoppedAfterTranscribe":
                    # Model transcribe'ı bitirdi ama stop_event set ise
                    log_message(UI_TEXT["transcription_stopped_no_result"])
                    transcribe_button.config(state="normal")
                    stop_button.config(state="disabled")
                    save_transcription_button.config(state="normal")

    except queue.Empty:
        pass
    except Exception as e:
        log_message(f"{UI_TEXT['error_in_check_queue']}: {str(e)}")
    finally:
        # Thread devam ediyorsa queue'yu tekrar kontrol et
        if transcribe_thread and transcribe_thread.is_alive():
            root.after(100, check_queue, q)
        else:
            # Thread durdu veya bitti
            transcribe_button.config(state="normal")
            stop_button.config(state="disabled")
            save_transcription_button.config(state="normal")


def stop_transcription():
    """
    Safe-ish stop: set event -> if transcribe() not finished, final results are discarded.
    """
    global transcribe_thread
    if transcribe_thread and transcribe_thread.is_alive():
        stop_event.set()
        # Kullanıcıya bilgi verelim ki hemen durmayabilir:
        log_message(UI_TEXT["stop_in_progress"])
        messagebox.showinfo(UI_TEXT["info"], UI_TEXT["cannot_stop_thread"])
    else:
        log_message(UI_TEXT["transcription_already_stopped"])

    transcribe_button.config(state="normal")
    stop_button.config(state="disabled")
    save_transcription_button.config(state="normal")


def save_transcription():
    text_data = transcription_area.get("1.0", tk.END).strip()
    if text_data:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[(UI_TEXT["text_files"], "*.txt")]
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text_data)
            messagebox.showinfo(UI_TEXT["info"], UI_TEXT["text_saved"])
            log_message(f"{UI_TEXT['text_saved']}: {path}")
        else:
            log_message(UI_TEXT["save_cancelled"])
    else:
        messagebox.showwarning(UI_TEXT["warning"], UI_TEXT["no_text_to_save"])
        log_message(UI_TEXT["no_text_to_save_log"])


def install_requirements():
    install_button.config(state="disabled")
    log_message(UI_TEXT["installing_packages"])
    t = threading.Thread(target=run_installation, daemon=True)
    t.start()


def run_installation():
    """
    Installs all required packages: openai-whisper, torch, psutil, gputil
    """
    try:
        packages = ["openai-whisper", "torch", "psutil", "gputil"]
        for pkg in packages:
            log_message(f"{UI_TEXT['installing_package']}: {pkg}")
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True, text=True
            )
            if proc.returncode == 0:
                log_message(f"{UI_TEXT['package_installed']}: {pkg}")
                if pkg in missing_modules:
                    missing_modules.remove(pkg)
            else:
                log_message(f"{UI_TEXT['package_install_error']} ({pkg}): {proc.stderr}")

        log_message(UI_TEXT["all_packages_installed"])
        messagebox.showinfo(UI_TEXT["info"], UI_TEXT["all_components_installed"])
        messagebox.showinfo(UI_TEXT["info"], UI_TEXT["restart_required"])

    except Exception as e:
        log_message(f"{UI_TEXT['package_installation_error']}: {e}")
        messagebox.showerror(UI_TEXT["error_occurred"], f"{UI_TEXT['package_installation_error']}: {e}")
    finally:
        install_button.config(state="normal")


def update_transcription_char_count(event=None):
    text_content = transcription_area.get("1.0", tk.END).strip()
    count = len(text_content)
    transcription_char_count_label.config(text=f"{UI_TEXT['character_count']}: {count}")
    # Eğer <<Modified>> event'i tekrar tetiklenmesin derseniz:
    if event:
        transcription_area.edit_modified(False)


def set_theme(theme):
    """
    Uyguladığımız tema ile ttk widget'ların da renklerini güncelliyoruz.
    """
    style = ttk.Style()
    if theme == "dark":
        root.configure(bg="#1E1E2E")

        # TTK teması
        style.theme_use("clam")
        style.configure(".", background="#1E1E2E", foreground="white")
        style.configure("TFrame", background="#1E1E2E")
        style.configure("TLabel", background="#1E1E2E", foreground="white")
        style.configure("TButton", background="#282A36", foreground="white")
        style.configure("TCombobox",
                        foreground="white",
                        fieldbackground="#282A36",
                        background="#1E1E2E")
        
        # Normal tk widget'lar
        left_frame.configure(bg="#1E1E2E")
        right_frame.configure(bg="#1E1E2E")
        file_label.configure(bg="#1E1E2E", fg="white")
        model_label.configure(bg="#1E1E2E", fg="white")
        language_label.configure(bg="#1E1E2E", fg="white")
        duration_label.configure(bg="#1E1E2E", fg="white")
        system_info_label.configure(bg="#1E1E2E", fg="white")
        log_label.configure(bg="#1E1E2E", fg="white")
        transcription_label.configure(bg="#1E1E2E", fg="white")
        credits_label.configure(bg="#1E1E2E", fg="white")
        requirements_label.configure(bg="#1E1E2E", fg="white")
        transcription_char_count_label.configure(bg="#1E1E2E", fg="white")
        transcription_area.configure(bg="#282A36", fg="white")
        log_area.configure(bg="#282A36", fg="white")
        requirements_area.configure(bg="#282A36", fg="white")
    else:
        # Light tema
        root.configure(bg="#FFFFFF")

        style.theme_use("default")
        style.configure(".", background="#FFFFFF", foreground="black")
        style.configure("TFrame", background="#FFFFFF")
        style.configure("TLabel", background="#FFFFFF", foreground="black")
        style.configure("TButton", background="#FFFFFF", foreground="black")
        style.configure("TCombobox",
                        foreground="black",
                        fieldbackground="#FFFFFF",
                        background="#FFFFFF")

        left_frame.configure(bg="#FFFFFF")
        right_frame.configure(bg="#FFFFFF")
        file_label.configure(bg="#FFFFFF", fg="black")
        model_label.configure(bg="#FFFFFF", fg="black")
        language_label.configure(bg="#FFFFFF", fg="black")
        duration_label.configure(bg="#FFFFFF", fg="black")
        system_info_label.configure(bg="#FFFFFF", fg="black")
        log_label.configure(bg="#FFFFFF", fg="black")
        transcription_label.configure(bg="#FFFFFF", fg="black")
        credits_label.configure(bg="#FFFFFF", fg="black")
        requirements_label.configure(bg="#FFFFFF", fg="black")
        transcription_char_count_label.configure(bg="#FFFFFF", fg="black")
        transcription_area.configure(bg="#FFFFFF", fg="black")
        log_area.configure(bg="#FFFFFF", fg="black")
        requirements_area.configure(bg="#FFFFFF", fg="black")


def show_about():
    messagebox.showinfo(UI_TEXT["about"], UI_TEXT["about_text"])


def create_menus():
    global menubar
    if menubar:
        root.config(menu=None)
        menubar.destroy()

    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # Settings menu
    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=UI_TEXT["settings"], menu=settings_menu)

    # Theme submenu
    theme_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_cascade(label=UI_TEXT["theme"], menu=theme_menu)
    theme_menu.add_command(label="Dark", command=lambda: set_theme("dark"))
    theme_menu.add_command(label="Light", command=lambda: set_theme("light"))

    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=UI_TEXT["help"], menu=help_menu)
    help_menu.add_command(label=UI_TEXT["about"], command=show_about)


##################################
# System Info Loop
##################################
def system_info_loop():
    """
    Repeatedly updates CPU usage, RAM usage, GPU usage (load/memory).
    """
    import psutil
    import GPUtil

    cpu_name = platform.processor() or "Unknown CPU"
    total_ram = psutil.virtual_memory().total / (1024**3)  # in GB
    gpu_name = "No GPU"
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_name = gpus[0].name
    except Exception as e:
        gpu_name = f"GPU error: {e}"

    while True:
        try:
            # interval=0.5 veya 0 yapabilirsiniz; 1 saniyede bir günceller
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent

            gpu_info_str = ""
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_load = gpu.load * 100
                    gpu_mem_used = gpu.memoryUsed
                    gpu_mem_total = gpu.memoryTotal
                    gpu_info_str = (f"{UI_TEXT['gpu_usage']}: {gpu_load:.1f}% | "
                                    f"{UI_TEXT['gpu_memory']}: {gpu_mem_used:.0f}/{gpu_mem_total:.0f}MB")
                else:
                    gpu_info_str = "No NVIDIA GPU found."
            except Exception as ge:
                gpu_info_str = f"GPU usage error: {ge}"

            info_str = (
                f"CPU: {cpu_name}\n"
                f"{UI_TEXT['cpu_usage']}: {cpu_usage:.1f}%\n\n"
                f"RAM: {total_ram:.1f} GB total\n"
                f"{UI_TEXT['ram_usage']}: {ram_usage:.1f}%\n\n"
                f"GPU: {gpu_name}\n"
                f"{gpu_info_str}"
            )
            system_info_label.config(text=info_str)
        except Exception as e:
            system_info_label.config(text=f"{UI_TEXT['missing_modules_system_info']} ({e})")


########################
# Main
########################
if __name__ == "__main__":
    root = tk.Tk()
    root.title(UI_TEXT["app_title"])
    root.geometry("1200x800")
    root.configure(bg="#1E1E2E")

    create_menus()

    # Frames
    left_frame = tk.Frame(root, bg="#1E1E2E")
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    right_frame = tk.Frame(root, bg="#1E1E2E")
    right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    # LEFT PANEL
    select_button = tk.Button(left_frame, text=UI_TEXT["select_file"], command=select_file, width=20)
    select_button.pack(pady=5)

    file_label = tk.Label(left_frame, text=UI_TEXT["no_file_selected"], bg="#1E1E2E", fg="white", wraplength=200)
    file_label.pack(pady=5)

    model_label = tk.Label(left_frame, text=UI_TEXT["select_model"], bg="#1E1E2E", fg="white")
    model_label.pack(pady=5)

    model_var = tk.StringVar(value="base")
    model_menu = ttk.Combobox(left_frame, textvariable=model_var, values=MODEL_LIST, width=18, state="readonly")
    model_menu.pack(pady=5)
    model_menu.bind("<<ComboboxSelected>>", lambda e: update_requirements())

    transcribe_button = tk.Button(
        left_frame, text=UI_TEXT["start_transcription"], command=transcribe,
        width=20, state="disabled" if not can_transcribe else "normal"
    )
    transcribe_button.pack(pady=10)

    stop_button = tk.Button(left_frame, text=UI_TEXT["stop"], command=stop_transcription, width=20, state="disabled")
    stop_button.pack(pady=5)

    save_transcription_button = tk.Button(left_frame, text=UI_TEXT["save_transcription"], command=save_transcription, width=20)
    save_transcription_button.pack(pady=5)

    # Install button
    install_button_state = "normal" if missing_modules else "disabled"
    install_button = tk.Button(
        left_frame, text=UI_TEXT["install_requirements"], command=install_requirements,
        width=20, state=install_button_state
    )
    install_button.pack(pady=10)

    language_label = tk.Label(left_frame, text=f"{UI_TEXT['detected_language']}: ", bg="#1E1E2E", fg="white")
    language_label.pack(pady=5)

    duration_label = tk.Label(left_frame, text=f"{UI_TEXT['processing_time']}: ", bg="#1E1E2E", fg="white")
    duration_label.pack(pady=5)

    system_info_label = tk.Label(left_frame, text="", bg="#1E1E2E", fg="white", justify="left")
    system_info_label.pack(pady=5)

    credits_label = tk.Label(left_frame, text=UI_TEXT["credits"], bg="#1E1E2E", fg="white")
    credits_label.pack(side=tk.BOTTOM, pady=10)

    # RIGHT PANEL
    transcription_label = tk.Label(right_frame, text=UI_TEXT["transcription"], bg="#1E1E2E", fg="white")
    transcription_label.pack(anchor="w", pady=(0, 5))

    transcription_area = tk.Text(right_frame, wrap=tk.WORD, bg="#282A36", fg="white", height=30)
    transcription_area.pack(expand=True, fill=tk.BOTH)
    transcription_area.bind("<<Modified>>", update_transcription_char_count)

    transcription_char_count_label = tk.Label(
        right_frame, text=f"{UI_TEXT['character_count']}: 0", bg="#1E1E2E", fg="white"
    )
    transcription_char_count_label.pack(anchor="e", pady=(0, 5))

    # Bottom frame for logs & requirements
    bottom_frame = tk.Frame(right_frame, bg="#1E1E2E")
    bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    log_frame = tk.Frame(bottom_frame, bg="#1E1E2E")
    log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

    log_label = tk.Label(log_frame, text=UI_TEXT["log"], bg="#1E1E2E", fg="white")
    log_label.pack(anchor="w", pady=(0, 5))

    log_area = tk.Text(log_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white")
    log_area.pack(fill=tk.BOTH, expand=True)

    requirements_frame = tk.Frame(bottom_frame, bg="#1E1E2E")
    requirements_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

    requirements_label = tk.Label(requirements_frame, text=UI_TEXT["model_requirements_title"], bg="#1E1E2E", fg="white")
    requirements_label.pack(anchor="w", pady=(0, 5))

    requirements_area = tk.Text(requirements_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white", state="disabled")
    requirements_area.pack(fill=tk.BOTH, expand=True)

    # Eksik modüller varsa uyar
    if missing_modules:
        missing_str = ", ".join(missing_modules)
        messagebox.showwarning(UI_TEXT["warning"], f"{UI_TEXT['missing_modules']}: {missing_str}")
        log_message(f"{UI_TEXT['missing_modules']}: {missing_str}")

    # Başlangıçta model gereksinimleri göster
    update_requirements()

    # Sistemi izlemek için thread (CPU, RAM, GPU vb.)
    if ("psutil" not in missing_modules) and ("gputil" not in missing_modules):
        threading.Thread(target=system_info_loop, daemon=True).start()
    else:
        system_info_label.config(text=UI_TEXT["missing_modules_system_info"])

    root.mainloop()
