import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import queue
import os
import psutil
import GPUtil
import logging
try:
    import torch
    GPU_AVAILABLE = torch.cuda.is_available()
except Exception:
    GPU_AVAILABLE = False
from datetime import datetime
from config import MODEL_LIST, TRANSCRIPT_FOLDER, MODEL_REQUIREMENTS
from transcriber import (
    check_requirements,
    install_requirements,
    transcribe,
    get_installed_models,
    download_model,
)

# Dil cevirileri
translations = {
    "tr": {
        "title": "Whisper GUI Çevirici",
        "system_info": "Sistem Bilgisi",
        "select_file": "Dosya Seç",
        "no_file_selected": "Dosya seçilmedi",
        "select_model": "Model Seç:",
        "start_transcription": "Transkripsiyonu Başlat",
        "stop": "Durdur",
        "save_transcription": "Transkripsiyonu Kaydet",
        "install_requirements": "Gereksinimleri Yükle",
        "theme": "Tema:",
        "language": "Dil:",
        "transcription": "Transkripsiyon",
        "character_count": "Karakter Sayısı: {count}",
        "log": "Log:",
        "warning": "Uyarı",
        "missing_packages": "Eksik paketler: {packages}",
        "please_select_file": "Lütfen bir dosya seçin.",
        "installation_complete": "Kurulum tamamlandı. Uygulamayı yeniden başlatın.",
        "info": "Bilgi",
        "save_txt": "TXT",
        "save_pdf": "PDF",
        "completion_time": "Tamamlanma süresi: {duration:.2f} saniye",
        "cpu_loading": "CPU Kullanımı: Yükleniyor...",
        "cpu_usage": "CPU Kullanımı: {value:.1f}%",
        "ram_loading": "RAM Kullanımı: Yükleniyor...",
        "ram_usage": "RAM Kullanımı: {value:.1f}%",
        "gpu_loading": "GPU: Yükleniyor...",
        "gpu_load_loading": "GPU Yükü: Yükleniyor...",
        "gpu_mem_loading": "GPU Bellek: Yükleniyor...",
        "no_gpu": "GPU algılanamadı",
        "gpu_load_na": "GPU Yükü: N/A",
        "gpu_mem_na": "GPU Bellek: N/A",
        "fpdf_missing": "FPDF modülü eksik, PDF kaydetme seçeneği çalışmayacaktır.",
        "fpdf_error": "FPDF kütüphanesi yüklü mü?",
        "download_model": "Model İndir:",
        "download": "İndir",
        "model_requirements": "Model Gereksinimleri",
    },
    "en": {
        "title": "Whisper GUI Transcriber",
        "system_info": "System Info",
        "select_file": "Select File",
        "no_file_selected": "No file selected",
        "select_model": "Select Model:",
        "start_transcription": "Start Transcription",
        "stop": "Stop",
        "save_transcription": "Save Transcription",
        "install_requirements": "Install Requirements",
        "theme": "Theme:",
        "language": "Language:",
        "transcription": "Transcription",
        "character_count": "Character Count: {count}",
        "log": "Log:",
        "warning": "Warning",
        "missing_packages": "Missing packages: {packages}",
        "please_select_file": "Please select a file.",
        "installation_complete": "Installation complete. Restart the application.",
        "info": "Info",
        "save_txt": "TXT",
        "save_pdf": "PDF",
        "completion_time": "Completion time: {duration:.2f} seconds",
        "cpu_loading": "CPU Usage: Loading...",
        "cpu_usage": "CPU Usage: {value:.1f}%",
        "ram_loading": "RAM Usage: Loading...",
        "ram_usage": "RAM Usage: {value:.1f}%",
        "gpu_loading": "GPU: Loading...",
        "gpu_load_loading": "GPU Load: Loading...",
        "gpu_mem_loading": "GPU Memory: Loading...",
        "no_gpu": "No GPU detected",
        "gpu_load_na": "GPU Load: N/A",
        "gpu_mem_na": "GPU Memory: N/A",
        "fpdf_missing": "FPDF module is missing; saving as PDF will not work.",
        "fpdf_error": "Is the FPDF library installed?",
        "download_model": "Download Model:",
        "download": "Download",
        "model_requirements": "Model Requirements",
    },
}

# Tema renklerini tutan sozluk
themes = {
    "shadow": {
        "bg": "#1E1E2E",
        "fg": "white",
        "text_bg": "#282A36",
        "progress": "#5A5A5A",
    },
    "white": {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "text_bg": "#FFFFFF",
        "progress": "#007ACC",
    },
}


class TextHandler(logging.Handler):
    """Log handler to redirect logs to the Tk text widget."""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.see(tk.END)


def create_main_window():
    root = tk.Tk()
    language_var = tk.StringVar(value="en")
    lang = translations[language_var.get()]
    root.title(lang["title"])
    root.geometry("1200x800")
    root.configure(bg="#1E1E2E")
    style = ttk.Style(root)

    # Logging setup
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = TextHandler(None)  # placeholder, will assign widget later
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    missing_modules = check_requirements()
    if missing_modules:
        warn_msg = lang["missing_packages"].format(packages=", ".join(missing_modules))
        if "fpdf" in missing_modules:
            warn_msg += "\n" + lang["fpdf_missing"]
        messagebox.showwarning(lang["warning"], warn_msg)
    global selected_file
    selected_file = ""
    global transcribe_thread
    transcribe_thread = None
    global stop_event
    stop_event = threading.Event()
    global q
    q = queue.Queue()

    # Requirement info labels will be assigned later
    req_ram_label = None
    req_notes_label = None
    req_size_label = None
    requirements_frame = None
    bottom_frame = None

    def select_file():
        global selected_file
        selected_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.flac")])
        if selected_file:
            file_label.config(text=selected_file)
        else:
            file_label.config(text=lang["no_file_selected"])

    def start_transcription():
        if not selected_file:
            messagebox.showwarning(lang["warning"], lang["please_select_file"])
            return
        logging.info("Starting transcription")
        transcribe(q, stop_event, model_var.get(), selected_file)
        check_queue()

    def check_queue():
        try:
            while True:
                msg = q.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                if isinstance(msg, tuple):
                    if msg[0] == "Error":
                        messagebox.showerror(lang["warning"], msg[1])
                    elif msg[0] == "Warning":
                        messagebox.showwarning(lang["warning"], msg[1])
                    elif msg[0] == "Result":
                        transcription_area.insert(tk.END, msg[1]["text"])
                        update_transcription_char_count()
                        logging.info(f"{timestamp} - " + lang["completion_time"].format(duration=msg[2]))
                    elif msg[0] == "Log":
                        logging.info(f"{timestamp} - {msg[1]}")
                else:
                    logging.info(f"{timestamp} - {msg}")
        except queue.Empty:
            pass
        root.after(100, check_queue)

    def update_transcription_char_count():
        text_content = transcription_area.get("1.0", tk.END).strip()
        char_count_label.config(text=lang["character_count"].format(count=len(text_content)))
        transcription_area.edit_modified(False)

    def install_missing():
        install_requirements(missing_modules)
        messagebox.showinfo(lang["info"], lang["installation_complete"])

    def update_system_info():
        try:
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent

            cpu_label.config(text=lang["cpu_usage"].format(value=cpu_usage))
            cpu_bar['value'] = cpu_usage

            ram_label.config(text=lang["ram_usage"].format(value=ram_usage))
            ram_bar['value'] = ram_usage

            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_label.config(text=f"GPU: {gpu.name}")
                gpu_load = gpu.load * 100
                gpu_mem = (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal else 0
                gpu_load_label.config(text=f"GPU Load: {gpu_load:.1f}%")
                gpu_load_bar['value'] = gpu_load
                gpu_mem_label.config(text=f"GPU Memory: {gpu.memoryUsed:.1f}/{gpu.memoryTotal:.1f} MB")
                gpu_mem_bar['value'] = gpu_mem
            else:
                gpu_label.config(text=lang["no_gpu"])
                gpu_load_label.config(text=lang["gpu_load_na"])
                gpu_load_bar['value'] = 0
                gpu_mem_label.config(text=lang["gpu_mem_na"])
                gpu_mem_bar['value'] = 0
        except Exception as e:
            gpu_label.config(text=f"Error retrieving system info: {str(e)}")
        root.after(2000, update_system_info)

    def update_requirements(selected_model=None):
        if req_ram_label is None:
            return
        model = selected_model or model_var.get() or download_var.get()
        req = MODEL_REQUIREMENTS.get(model, {})
        req_ram_label.config(text=f"RAM: {req.get('ram', 'N/A')}")
        req_notes_label.config(text=f"Notes: {req.get('notes', 'N/A')}")
        req_size_label.config(text=f"Size: {req.get('size', 'N/A')}")

    # Frames
    left_frame = tk.Frame(root, bg="#1E1E2E")
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    system_info_frame = tk.LabelFrame(left_frame, text=lang["system_info"], bg="#1E1E2E", fg="white", padx=5, pady=5)
    system_info_frame.pack(fill=tk.X, padx=5, pady=5)

    cpu_label = tk.Label(system_info_frame, text=lang["cpu_loading"], bg="#1E1E2E", fg="white")
    cpu_label.pack(anchor="w")
    cpu_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    cpu_bar.pack(fill=tk.X, pady=(0, 5))

    ram_label = tk.Label(system_info_frame, text=lang["ram_loading"], bg="#1E1E2E", fg="white")
    ram_label.pack(anchor="w")
    ram_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    ram_bar.pack(fill=tk.X, pady=(0, 5))

    gpu_label = tk.Label(system_info_frame, text=lang["gpu_loading"], bg="#1E1E2E", fg="white")
    gpu_label.pack(anchor="w")
    gpu_load_label = tk.Label(system_info_frame, text=lang["gpu_load_loading"], bg="#1E1E2E", fg="white")
    gpu_load_label.pack(anchor="w")
    gpu_load_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    gpu_load_bar.pack(fill=tk.X, pady=(0, 5))
    gpu_mem_label = tk.Label(system_info_frame, text=lang["gpu_mem_loading"], bg="#1E1E2E", fg="white")
    gpu_mem_label.pack(anchor="w")
    gpu_mem_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    gpu_mem_bar.pack(fill=tk.X, pady=(0, 5))

    # File Selection
    file_button = tk.Button(left_frame, text=lang["select_file"], command=select_file, width=20)
    file_button.pack(pady=5)
    file_label = tk.Label(left_frame, text=lang["no_file_selected"], bg="#1E1E2E", fg="white", wraplength=200)
    file_label.pack(pady=5)

    # Model Selection
    installed_models = get_installed_models()
    model_label = tk.Label(left_frame, text=lang["select_model"], bg="#1E1E2E", fg="white")
    model_label.pack(pady=5)
    model_var = tk.StringVar(value=installed_models[0] if installed_models else "")
    model_menu = ttk.Combobox(left_frame, textvariable=model_var, values=installed_models, width=18, state="readonly")
    model_menu.pack(pady=5)
    model_menu.bind("<<ComboboxSelected>>", lambda e: update_requirements(model_var.get()))

    download_label = tk.Label(left_frame, text=lang["download_model"], bg="#1E1E2E", fg="white")
    download_label.pack(pady=5)
    not_installed = [m for m in MODEL_LIST if m not in installed_models]
    download_var = tk.StringVar(value=not_installed[0] if not_installed else "")
    download_menu = ttk.Combobox(left_frame, textvariable=download_var, values=not_installed, width=18, state="readonly")
    download_menu.pack(pady=5)
    download_menu.bind("<<ComboboxSelected>>", lambda e: update_requirements(download_var.get()))

    def refresh_model_lists():
        installed = get_installed_models()
        model_menu['values'] = installed
        if installed:
            model_var.set(installed[0])
        else:
            model_var.set("")
        remaining = [m for m in MODEL_LIST if m not in installed]
        download_menu['values'] = remaining
        if remaining:
            download_var.set(remaining[0])
        else:
            download_var.set("")
        update_requirements(model_var.get() if installed else (download_var.get() if remaining else None))

    def download_selected_model():
        model = download_var.get()
        if not model:
            return
        size = MODEL_REQUIREMENTS.get(model, {}).get("size", "N/A")
        if not messagebox.askyesno(
            "Onay",
            f"'{model}' modeli (~{size}) indirilecek. Onaylıyor musunuz?",
        ):
            return
        def worker():
            logging.info(f"Downloading model: {model}")
            try:
                download_model(model)
                logging.info(f"Model downloaded: {model}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            refresh_model_lists()
        threading.Thread(target=worker, daemon=True).start()

    download_button = tk.Button(left_frame, text=lang["download"], command=download_selected_model, width=20)
    download_button.pack(pady=5)
    refresh_model_lists()

    # Transcription Buttons
    transcribe_button = tk.Button(left_frame, text=lang["start_transcription"], command=start_transcription, width=20)
    if not GPU_AVAILABLE:
        transcribe_button.config(state=tk.DISABLED)
    transcribe_button.pack(pady=10)
    stop_button = tk.Button(left_frame, text=lang["stop"], command=lambda: stop_event.set(), width=20)
    stop_button.pack(pady=5)
    def save_transcription():
        text = transcription_area.get("1.0", tk.END).strip()
        if not text:
            return
        os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(TRANSCRIPT_FOLDER, f"transcription_{timestamp}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        pdf_path = os.path.join(TRANSCRIPT_FOLDER, f"transcription_{timestamp}.pdf")
        try:
            from fpdf import FPDF
        except Exception:
            messagebox.showerror("Error", lang["fpdf_error"])
            return
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)
        pdf.output(pdf_path)
        messagebox.showinfo(lang["info"], "PDF ve TXT dosyaları program klasörüne kaydedildi")

    save_transcription_button = tk.Button(left_frame, text=lang["save_transcription"], command=save_transcription, width=20)
    save_transcription_button.pack(pady=5)

    # Install Button
    if missing_modules:
        install_button = tk.Button(left_frame, text=lang["install_requirements"], command=install_missing, width=20)
        install_button.pack(pady=10)

    # Tema Secimi
    theme_label = tk.Label(left_frame, text=lang["theme"], bg="#1E1E2E", fg="white")
    theme_label.pack(pady=5)
    theme_var = tk.StringVar(value="shadow")
    theme_menu = ttk.Combobox(left_frame, textvariable=theme_var, values=list(themes.keys()), width=18, state="readonly")
    theme_menu.pack(pady=5)

    language_label = tk.Label(left_frame, text=lang["language"], bg="#1E1E2E", fg="white")
    language_label.pack(pady=5)
    language_menu = ttk.Combobox(left_frame, textvariable=language_var, values=["tr", "en"], width=18, state="readonly")
    language_menu.pack(pady=5)

    def apply_theme(event=None):
        theme = themes[theme_var.get()]
        root.configure(bg=theme["bg"])
        left_frame.configure(bg=theme["bg"])
        right_frame.configure(bg=theme["bg"])
        system_info_frame.configure(bg=theme["bg"], fg=theme["fg"])

        label_list = [cpu_label, ram_label, gpu_label, gpu_load_label, gpu_mem_label,
                    file_label, model_label, download_label, transcription_label,
                    char_count_label, log_label, theme_label]
        if req_ram_label is not None:
            label_list.extend([req_ram_label, req_notes_label, req_size_label])
        for lbl in label_list:
            lbl.configure(bg=theme["bg"], fg=theme["fg"])

        if bottom_frame is not None:
            bottom_frame.configure(bg=theme["bg"])
        if requirements_frame is not None:
            requirements_frame.configure(bg=theme["bg"], fg=theme["fg"])
        transcription_area.configure(bg=theme["text_bg"], fg=theme["fg"])
        log_area.configure(bg=theme["text_bg"], fg=theme["fg"])

        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor=theme["bg"], background=theme["progress"])
        for bar in [cpu_bar, ram_bar, gpu_load_bar, gpu_mem_bar]:
            bar.configure(style="Custom.Horizontal.TProgressbar")

    theme_menu.bind("<<ComboboxSelected>>", apply_theme)

    def apply_language(event=None):
        nonlocal lang
        lang = translations[language_var.get()]
        root.title(lang["title"])
        system_info_frame.configure(text=lang["system_info"])
        file_button.configure(text=lang["select_file"])
        if not selected_file:
            file_label.configure(text=lang["no_file_selected"])
        model_label.configure(text=lang["select_model"])
        download_label.configure(text=lang["download_model"])
        download_button.configure(text=lang["download"])
        transcribe_button.configure(text=lang["start_transcription"])
        stop_button.configure(text=lang["stop"])
        save_transcription_button.configure(text=lang["save_transcription"])
        if missing_modules:
            install_button.configure(text=lang["install_requirements"])
        theme_label.configure(text=lang["theme"])
        language_label.configure(text=lang["language"])
        transcription_label.configure(text=lang["transcription"])
        char_count_label.configure(text=lang["character_count"].format(count=len(transcription_area.get("1.0", tk.END).strip())))
        log_label.configure(text=lang["log"])
        cpu_label.configure(text=lang["cpu_loading"])
        ram_label.configure(text=lang["ram_loading"])
        gpu_label.configure(text=lang["gpu_loading"])
        gpu_load_label.configure(text=lang["gpu_load_loading"])
        gpu_mem_label.configure(text=lang["gpu_mem_loading"])
        requirements_frame.configure(text=lang["model_requirements"])

    language_menu.bind("<<ComboboxSelected>>", apply_language)

    # Transcription Area
    right_frame = tk.Frame(root, bg="#1E1E2E")
    right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    transcription_label = tk.Label(right_frame, text=lang["transcription"], bg="#1E1E2E", fg="white")
    transcription_label.pack(anchor="w", pady=(0, 5))
    transcription_area = tk.Text(right_frame, wrap=tk.WORD, bg="#282A36", fg="white", height=30)
    transcription_area.pack(expand=True, fill=tk.BOTH)
    transcription_area.bind("<<Modified>>", lambda e: update_transcription_char_count())

    char_count_label = tk.Label(right_frame, text=lang["character_count"].format(count=0), bg="#1E1E2E", fg="white")
    char_count_label.pack(anchor="e", pady=(0, 5))

    # Log Area
    log_label = tk.Label(right_frame, text=lang["log"], bg="#1E1E2E", fg="white")
    log_label.pack(anchor="w", pady=(0, 5))

    bottom_frame = tk.Frame(right_frame, bg="#1E1E2E")
    bottom_frame.pack(fill=tk.BOTH, expand=True)

    log_area = tk.Text(bottom_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white")
    log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    requirements_frame = tk.LabelFrame(bottom_frame, text=translations[language_var.get()]["model_requirements"], bg="#1E1E2E", fg="white", padx=5, pady=5)
    requirements_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

    req_ram_label = tk.Label(requirements_frame, text="")
    req_ram_label.pack(anchor="w")
    req_notes_label = tk.Label(requirements_frame, text="")
    req_notes_label.pack(anchor="w")
    req_size_label = tk.Label(requirements_frame, text="")
    req_size_label.pack(anchor="w")

    # Logging handler now knows text widget
    handler.text_widget = log_area

    # Varsayilan temayi uygula
    apply_theme()
    apply_language()
    update_requirements()

    # Start System Monitoring
    update_system_info()

    return root
