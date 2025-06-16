import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import queue
import os
import psutil
import GPUtil
from transcriber import check_requirements, install_requirements, transcribe

# Translation dictionary for English and Turkish
translations = {
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
        "transcription": "Transcription",
        "character_count": "Character Count: {count}",
        "log": "Log:",
        "warning_select_file": "Please select a file.",
        "warning": "Warning",
        "error": "Error",
        "info": "Info",
        "installation_complete": "Installation complete. Restart the application.",
        "cpu_usage_loading": "CPU Usage: Loading...",
        "ram_usage_loading": "RAM Usage: Loading...",
        "gpu_loading": "GPU: Loading...",
        "gpu_load_loading": "GPU Load: Loading...",
        "gpu_memory_loading": "GPU Memory: Loading...",
        "cpu_usage": "CPU Usage: {usage:.1f}%",
        "ram_usage": "RAM Usage: {usage:.1f}%",
        "gpu": "GPU: {name}",
        "gpu_load": "GPU Load: {load:.1f}%",
        "gpu_memory": "GPU Memory: {used:.1f}/{total:.1f} MB",
        "no_gpu_detected": "No GPU detected",
        "gpu_load_na": "GPU Load: N/A",
        "gpu_memory_na": "GPU Memory: N/A",
        "error_retrieving": "Error retrieving system info: {error}"
    },
    "tr": {
        "title": "Whisper GUI Çevirici",
        "system_info": "Sistem Bilgisi",
        "select_file": "Dosya Seç",
        "no_file_selected": "Dosya seçilmedi",
        "select_model": "Model Seç:",
        "start_transcription": "Çeviriyi Başlat",
        "stop": "Durdur",
        "save_transcription": "Çeviriyi Kaydet",
        "install_requirements": "Gereksinimleri Yükle",
        "transcription": "Metin",
        "character_count": "Karakter Sayısı: {count}",
        "log": "Kayıtlar:",
        "warning_select_file": "Lütfen bir dosya seçin.",
        "warning": "Uyarı",
        "error": "Hata",
        "info": "Bilgi",
        "installation_complete": "Kurulum tamamlandı. Uygulamayı yeniden başlatın.",
        "cpu_usage_loading": "CPU Kullanımı: Yükleniyor...",
        "ram_usage_loading": "RAM Kullanımı: Yükleniyor...",
        "gpu_loading": "GPU: Yükleniyor...",
        "gpu_load_loading": "GPU Yükü: Yükleniyor...",
        "gpu_memory_loading": "GPU Belleği: Yükleniyor...",
        "cpu_usage": "CPU Kullanımı: {usage:.1f}%",
        "ram_usage": "RAM Kullanımı: {usage:.1f}%",
        "gpu": "GPU: {name}",
        "gpu_load": "GPU Yükü: {load:.1f}%",
        "gpu_memory": "GPU Belleği: {used:.1f}/{total:.1f} MB",
        "no_gpu_detected": "GPU tespit edilmedi",
        "gpu_load_na": "GPU Yükü: Yok",
        "gpu_memory_na": "GPU Belleği: Yok",
        "error_retrieving": "Sistem bilgisi alınamadı: {error}"
    }
}

def create_main_window():
    root = tk.Tk()
    current_lang = "en"

    def tr(key, **kwargs):
        text = translations[current_lang][key]
        if kwargs:
            text = text.format(**kwargs)
        return text

    root.title(tr("title"))
    root.geometry("1200x800")
    root.configure(bg="#1E1E2E")
    
    missing_modules = check_requirements()
    global selected_file
    selected_file = ""
    global transcribe_thread
    transcribe_thread = None
    global stop_event
    stop_event = threading.Event()
    global q
    q = queue.Queue()

    def select_file():
        global selected_file
        selected_file = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.flac")])
        file_label.config(text=selected_file if selected_file else tr("no_file_selected"))

    def start_transcription():
        if not selected_file:
            messagebox.showwarning(tr("warning"), tr("warning_select_file"))
            return
        transcribe(q, stop_event, model_var.get(), selected_file)
        check_queue()

    def check_queue():
        try:
            while True:
                msg = q.get_nowait()
                if isinstance(msg, str):
                    log_area.insert(tk.END, msg + "\n")
                    log_area.see(tk.END)
                elif isinstance(msg, tuple):
                    if msg[0] == "Error":
                        messagebox.showerror(tr("error"), msg[1])
                    elif msg[0] == "Warning":
                        messagebox.showwarning(tr("warning"), msg[1])
                    elif msg[0] == "Result":
                        transcription_area.insert(tk.END, msg[1]['text'])
                        update_transcription_char_count()
        except queue.Empty:
            pass
        root.after(100, check_queue)

    def update_transcription_char_count():
        text_content = transcription_area.get("1.0", tk.END).strip()
        char_count_label.config(text=tr("character_count", count=len(text_content)))
        transcription_area.edit_modified(False)

    def install_missing():
        install_requirements()
        messagebox.showinfo(tr("info"), tr("installation_complete"))

    def update_system_info():
        try:
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent

            cpu_label.config(text=tr("cpu_usage", usage=cpu_usage))
            cpu_bar['value'] = cpu_usage

            ram_label.config(text=tr("ram_usage", usage=ram_usage))
            ram_bar['value'] = ram_usage

            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_label.config(text=tr("gpu", name=gpu.name))
                gpu_load = gpu.load * 100
                gpu_mem = (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal else 0
                gpu_load_label.config(text=tr("gpu_load", load=gpu_load))
                gpu_load_bar['value'] = gpu_load
                gpu_mem_label.config(text=tr("gpu_memory", used=gpu.memoryUsed, total=gpu.memoryTotal))
                gpu_mem_bar['value'] = gpu_mem
            else:
                gpu_label.config(text=tr("no_gpu_detected"))
                gpu_load_label.config(text=tr("gpu_load_na"))
                gpu_load_bar['value'] = 0
                gpu_mem_label.config(text=tr("gpu_memory_na"))
                gpu_mem_bar['value'] = 0
        except Exception as e:
            gpu_label.config(text=tr("error_retrieving", error=str(e)))
        root.after(2000, update_system_info)

    # Frames
    left_frame = tk.Frame(root, bg="#1E1E2E")
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    system_info_frame = tk.LabelFrame(left_frame, text=tr("system_info"), bg="#1E1E2E", fg="white", padx=5, pady=5)
    system_info_frame.pack(fill=tk.X, padx=5, pady=5)

    cpu_label = tk.Label(system_info_frame, text=tr("cpu_usage_loading"), bg="#1E1E2E", fg="white")
    cpu_label.pack(anchor="w")
    cpu_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    cpu_bar.pack(fill=tk.X, pady=(0, 5))

    ram_label = tk.Label(system_info_frame, text=tr("ram_usage_loading"), bg="#1E1E2E", fg="white")
    ram_label.pack(anchor="w")
    ram_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    ram_bar.pack(fill=tk.X, pady=(0, 5))

    gpu_label = tk.Label(system_info_frame, text=tr("gpu_loading"), bg="#1E1E2E", fg="white")
    gpu_label.pack(anchor="w")
    gpu_load_label = tk.Label(system_info_frame, text=tr("gpu_load_loading"), bg="#1E1E2E", fg="white")
    gpu_load_label.pack(anchor="w")
    gpu_load_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    gpu_load_bar.pack(fill=tk.X, pady=(0, 5))
    gpu_mem_label = tk.Label(system_info_frame, text=tr("gpu_memory_loading"), bg="#1E1E2E", fg="white")
    gpu_mem_label.pack(anchor="w")
    gpu_mem_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    gpu_mem_bar.pack(fill=tk.X, pady=(0, 5))

    # File Selection
    file_button = tk.Button(left_frame, text=tr("select_file"), command=select_file, width=20)
    file_button.pack(pady=5)
    file_label = tk.Label(left_frame, text=tr("no_file_selected"), bg="#1E1E2E", fg="white", wraplength=200)
    file_label.pack(pady=5)

    # Model Selection
    model_label = tk.Label(left_frame, text=tr("select_model"), bg="#1E1E2E", fg="white")
    model_label.pack(pady=5)
    model_var = tk.StringVar(value="base")
    model_menu = ttk.Combobox(left_frame, textvariable=model_var, values=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "whisper-turbo"], width=18, state="readonly")
    model_menu.pack(pady=5)

    # Language Selection
    lang_map = {"English": "en", "Türkçe": "tr"}
    lang_var = tk.StringVar(value="English")
    language_combo = ttk.Combobox(left_frame, textvariable=lang_var, values=list(lang_map.keys()), width=18, state="readonly")
    language_combo.pack(pady=5, side=tk.BOTTOM)

    # Transcription Buttons
    transcribe_button = tk.Button(left_frame, text=tr("start_transcription"), command=start_transcription, width=20)
    transcribe_button.pack(pady=10)
    stop_button = tk.Button(left_frame, text=tr("stop"), command=lambda: stop_event.set(), width=20)
    stop_button.pack(pady=5)
    save_transcription_button = tk.Button(left_frame, text=tr("save_transcription"), width=20)
    save_transcription_button.pack(pady=5)

    # Install Button
    if missing_modules:
        install_button = tk.Button(left_frame, text=tr("install_requirements"), command=install_missing, width=20)
        install_button.pack(pady=10)

    # Transcription Area
    right_frame = tk.Frame(root, bg="#1E1E2E")
    right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    transcription_label = tk.Label(right_frame, text=tr("transcription"), bg="#1E1E2E", fg="white")
    transcription_label.pack(anchor="w", pady=(0, 5))
    transcription_area = tk.Text(right_frame, wrap=tk.WORD, bg="#282A36", fg="white", height=30)
    transcription_area.pack(expand=True, fill=tk.BOTH)
    transcription_area.bind("<<Modified>>", lambda e: update_transcription_char_count())

    char_count_label = tk.Label(right_frame, text=tr("character_count", count=0), bg="#1E1E2E", fg="white")
    char_count_label.pack(anchor="e", pady=(0, 5))

    # Log Area
    log_label = tk.Label(right_frame, text=tr("log"), bg="#1E1E2E", fg="white")
    log_label.pack(anchor="w", pady=(0, 5))
    log_area = tk.Text(right_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white")
    log_area.pack(fill=tk.BOTH, expand=True)

    def update_texts():
        root.title(tr("title"))
        system_info_frame.config(text=tr("system_info"))
        file_button.config(text=tr("select_file"))
        file_label.config(text=selected_file if selected_file else tr("no_file_selected"))
        model_label.config(text=tr("select_model"))
        transcribe_button.config(text=tr("start_transcription"))
        stop_button.config(text=tr("stop"))
        save_transcription_button.config(text=tr("save_transcription"))
        if missing_modules:
            install_button.config(text=tr("install_requirements"))
        transcription_label.config(text=tr("transcription"))
        char_count_label.config(text=tr("character_count", count=len(transcription_area.get("1.0", tk.END).strip())))
        log_label.config(text=tr("log"))
        cpu_label.config(text=tr("cpu_usage_loading"))
        ram_label.config(text=tr("ram_usage_loading"))
        gpu_label.config(text=tr("gpu_loading"))
        gpu_load_label.config(text=tr("gpu_load_loading"))
        gpu_mem_label.config(text=tr("gpu_memory_loading"))
        update_system_info()

    def change_language(event=None):
        nonlocal current_lang
        current_lang = lang_map[lang_var.get()]
        update_texts()

    language_combo.bind("<<ComboboxSelected>>", change_language)

    # Start System Monitoring
    update_system_info()
    
    return root