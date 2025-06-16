import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import threading
import queue
import os
import psutil
import GPUtil
from fpdf import FPDF
from transcriber import check_requirements, install_requirements, transcribe

def create_main_window():
    root = tk.Tk()
    root.title("Whisper GUI Transcriber")
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
        file_label.config(text=selected_file if selected_file else "No file selected")

    def start_transcription():
        if not selected_file:
            messagebox.showwarning("Warning", "Please select a file.")
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
                        messagebox.showerror("Error", msg[1])
                    elif msg[0] == "Warning":
                        messagebox.showwarning("Warning", msg[1])
                    elif msg[0] == "Result":
                        transcription_area.insert(tk.END, msg[1]['text'])
                        update_transcription_char_count()
        except queue.Empty:
            pass
        root.after(100, check_queue)

    def update_transcription_char_count():
        text_content = transcription_area.get("1.0", tk.END).strip()
        char_count_label.config(text=f"Character Count: {len(text_content)}")
        transcription_area.edit_modified(False)

    def save_transcription():
        text = transcription_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Uyarı", "Kaydedilecek bir transkripsiyon yok.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf")]
        )
        if not file_path:
            return
        try:
            if file_path.lower().endswith(".pdf"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=12)
                for line in text.splitlines():
                    pdf.multi_cell(0, 10, line)
                pdf.output(file_path)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
            messagebox.showinfo("Bilgi", f"Dosya kaydedildi:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilemedi: {e}")

    def install_missing():
        install_requirements()
        messagebox.showinfo("Info", "Installation complete. Restart the application.")

    def update_system_info():
        try:
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent

            cpu_label.config(text=f"CPU Usage: {cpu_usage:.1f}%")
            cpu_bar['value'] = cpu_usage

            ram_label.config(text=f"RAM Usage: {ram_usage:.1f}%")
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
                gpu_label.config(text="No GPU detected")
                gpu_load_label.config(text="GPU Load: N/A")
                gpu_load_bar['value'] = 0
                gpu_mem_label.config(text="GPU Memory: N/A")
                gpu_mem_bar['value'] = 0
        except Exception as e:
            gpu_label.config(text=f"Error retrieving system info: {str(e)}")
        root.after(2000, update_system_info)

    # Frames
    left_frame = tk.Frame(root, bg="#1E1E2E")
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    system_info_frame = tk.LabelFrame(left_frame, text="System Info", bg="#1E1E2E", fg="white", padx=5, pady=5)
    system_info_frame.pack(fill=tk.X, padx=5, pady=5)

    cpu_label = tk.Label(system_info_frame, text="CPU Usage: Loading...", bg="#1E1E2E", fg="white")
    cpu_label.pack(anchor="w")
    cpu_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    cpu_bar.pack(fill=tk.X, pady=(0, 5))

    ram_label = tk.Label(system_info_frame, text="RAM Usage: Loading...", bg="#1E1E2E", fg="white")
    ram_label.pack(anchor="w")
    ram_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    ram_bar.pack(fill=tk.X, pady=(0, 5))

    gpu_label = tk.Label(system_info_frame, text="GPU: Loading...", bg="#1E1E2E", fg="white")
    gpu_label.pack(anchor="w")
    gpu_load_label = tk.Label(system_info_frame, text="GPU Load: Loading...", bg="#1E1E2E", fg="white")
    gpu_load_label.pack(anchor="w")
    gpu_load_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    gpu_load_bar.pack(fill=tk.X, pady=(0, 5))
    gpu_mem_label = tk.Label(system_info_frame, text="GPU Memory: Loading...", bg="#1E1E2E", fg="white")
    gpu_mem_label.pack(anchor="w")
    gpu_mem_bar = ttk.Progressbar(system_info_frame, orient="horizontal", length=180, mode="determinate")
    gpu_mem_bar.pack(fill=tk.X, pady=(0, 5))

    # File Selection
    file_button = tk.Button(left_frame, text="Select File", command=select_file, width=20)
    file_button.pack(pady=5)
    file_label = tk.Label(left_frame, text="No file selected", bg="#1E1E2E", fg="white", wraplength=200)
    file_label.pack(pady=5)

    # Model Selection
    model_label = tk.Label(left_frame, text="Select Model:", bg="#1E1E2E", fg="white")
    model_label.pack(pady=5)
    model_var = tk.StringVar(value="base")
    model_menu = ttk.Combobox(left_frame, textvariable=model_var, values=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "whisper-turbo"], width=18, state="readonly")
    model_menu.pack(pady=5)

    # Transcription Buttons
    transcribe_button = tk.Button(left_frame, text="Start Transcription", command=start_transcription, width=20)
    transcribe_button.pack(pady=10)
    stop_button = tk.Button(left_frame, text="Stop", command=lambda: stop_event.set(), width=20)
    stop_button.pack(pady=5)
    save_transcription_button = tk.Button(left_frame, text="Save Transcription", command=save_transcription, width=20)
    save_transcription_button.pack(pady=5)

    # Install Button
    if missing_modules:
        install_button = tk.Button(left_frame, text="Install Requirements", command=install_missing, width=20)
        install_button.pack(pady=10)

    # Transcription Area
    right_frame = tk.Frame(root, bg="#1E1E2E")
    right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    transcription_label = tk.Label(right_frame, text="Transcription", bg="#1E1E2E", fg="white")
    transcription_label.pack(anchor="w", pady=(0, 5))
    transcription_area = tk.Text(right_frame, wrap=tk.WORD, bg="#282A36", fg="white", height=30)
    transcription_area.pack(expand=True, fill=tk.BOTH)
    transcription_area.bind("<<Modified>>", lambda e: update_transcription_char_count())

    char_count_label = tk.Label(right_frame, text="Character Count: 0", bg="#1E1E2E", fg="white")
    char_count_label.pack(anchor="e", pady=(0, 5))

    # Log Area
    log_label = tk.Label(right_frame, text="Log:", bg="#1E1E2E", fg="white")
    log_label.pack(anchor="w", pady=(0, 5))
    log_area = tk.Text(right_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white")
    log_area.pack(fill=tk.BOTH, expand=True)

    # Start System Monitoring
    update_system_info()
    
    return root
