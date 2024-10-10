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

# Eksik modülleri takip etmek için bir liste oluşturun
missing_modules = []

# Modülleri yüklemeye çalışın ve hata olursa missing_modules listesine ekleyin
try:
    import whisper
except ImportError:
    missing_modules.append('whisper')

try:
    import torch
except ImportError:
    missing_modules.append('torch')

try:
    import psutil
except ImportError:
    missing_modules.append('psutil')

try:
    import GPUtil
except ImportError:
    missing_modules.append('GPUtil')

try:
    from googletrans import Translator, LANGUAGES as GT_LANGUAGES
except ImportError:
    missing_modules.append('googletrans')

# Eksik modüller varsa, ilgili fonksiyonları devre dışı bırakmak için bir flag oluşturun
can_transcribe = 'whisper' not in missing_modules and 'torch' not in missing_modules
can_translate = 'googletrans' not in missing_modules

def resource_path(relative_path):
    """ Kaynağa mutlak yol alır, geliştirme ve PyInstaller için çalışır """
    try:
        # PyInstaller, temp klasörde bir _MEIPASS klasörü oluşturur
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def select_file():
    global selected_file
    filetypes = (
        (UI_TEXT['file_types_audio'], "*.mp3 *.mp4 *.wav *.m4a *.ogg *.flac"),
        (UI_TEXT['file_types_all'], "*.*")
    )
    selected_file = filedialog.askopenfilename(title=UI_TEXT['select_file'], filetypes=filetypes)
    if selected_file:
        file_label.config(text=selected_file)
        log_message(f"{UI_TEXT['file_selected']}: {selected_file}")
    else:
        file_label.config(text=UI_TEXT['no_file_selected'])
        log_message(UI_TEXT['file_selection_cancelled'])

def update_system_info():
    while True:
        if 'psutil' in missing_modules:
            system_info_label.config(text=UI_TEXT['missing_modules_system_info'])
            time.sleep(1)
            continue
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        if 'GPUtil' not in missing_modules and torch.cuda.is_available():
            gpu = GPUtil.getGPUs()[0]
            gpu_usage = gpu.load * 100
            gpu_memory = gpu.memoryUsed
            gpu_info = f"{UI_TEXT['gpu_usage']}: {gpu_usage:.2f}% - {UI_TEXT['memory']}: {gpu_memory:.2f}MB"
        else:
            gpu_info = UI_TEXT['gpu_not_available']

        system_info = f"{UI_TEXT['cpu_usage']}: {cpu_usage}%\n{UI_TEXT['ram_usage']}: {ram_usage}%\n{gpu_info}"
        system_info_label.config(text=system_info)
        time.sleep(1)

def log_message(message):
    log_area.insert(tk.END, message + "\n")
    log_area.see(tk.END)

def update_requirements():
    model_option = model_var.get()
    requirements = MODEL_REQUIREMENTS.get(model_option, {})
    if requirements:
        requirements_text = f"{UI_TEXT['model_requirements']}: {model_option}\n"
        requirements_text += f"- GPU VRAM: {requirements['gpu_vram']}\n"
        requirements_text += f"- RAM: {requirements['ram']}\n"
        requirements_text += f"- CPU: {requirements['cpu']}\n"
    else:
        requirements_text = UI_TEXT['requirements_not_available']

    requirements_area.config(state='normal')
    requirements_area.delete(1.0, tk.END)
    requirements_area.insert(tk.END, requirements_text)
    requirements_area.config(state='disabled')

def run_transcription(queue_obj, model_option, options, selected_file, use_gpu_value):
    start_time = time.time()
    try:
        queue_obj.put(UI_TEXT['model_loading'])
        if use_gpu_value and torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
        # Modeli yüklerken resource_path kullanımı
        model = whisper.load_model(model_option, device=device)
        queue_obj.put(f"{UI_TEXT['model_loaded']}: {model_option} ({device})")
        queue_obj.put(UI_TEXT['transcription_starting'])
        result = model.transcribe(selected_file, **options)
        queue_obj.put(UI_TEXT['transcription_finished'])

        end_time = time.time()
        duration = end_time - start_time
        queue_obj.put(("Result", result, duration))
    except Exception as e:
        queue_obj.put(("Error", str(e)))

def transcribe():
    global transcribe_thread
    if not selected_file:
        messagebox.showwarning(UI_TEXT['warning'], UI_TEXT['please_select_file'])
        return
    if not can_transcribe:
        messagebox.showwarning(UI_TEXT['warning'], UI_TEXT['missing_modules_transcription'])
        log_message(UI_TEXT['missing_modules_transcription_log'])
        return
    transcribe_button.config(state="disabled")
    stop_button.config(state="normal")
    save_transcription_button.config(state="disabled")
    save_translation_button.config(state="disabled")
    translate_button.config(state="disabled")
    model_option = model_var.get()
    log_message(f"{UI_TEXT['model_selected']}: {model_option}")
    log_message(f"{UI_TEXT['gpu_usage_option']}: {'Yes' if use_gpu.get() else 'No'}")

    queue_obj = queue.Queue()
    use_gpu_value = use_gpu.get()

    options = {
        "verbose": False,
        "task": "transcribe",
        "beam_size": 5,
        "best_of": 5,
        "temperature": 0.0,
        "language": None  # Otomatik dil tespiti
    }

    log_message(UI_TEXT['input_language_auto'])

    transcribe_thread = threading.Thread(target=run_transcription, args=(queue_obj, model_option, options, selected_file, use_gpu_value))
    transcribe_thread.start()
    check_queue(queue_obj)

def check_queue(queue_obj):
    try:
        while True:
            msg = queue_obj.get_nowait()
            if isinstance(msg, str):
                # Log mesajı
                log_message(msg)
            elif isinstance(msg, tuple):
                if msg[0] == "Error":
                    log_message(f"{UI_TEXT['error_occurred']}: {msg[1]}")
                    messagebox.showerror(UI_TEXT['error'], msg[1])
                    transcribe_button.config(state="normal")
                    stop_button.config(state="disabled")
                    save_transcription_button.config(state="normal")
                    translate_button.config(state="normal")
                elif msg[0] == "Result":
                    result = msg[1]
                    duration = msg[2]
                    detected_lang = result["language"]
                    # Whisper'ın dil sözlüğünü kullanarak dil adını alıyoruz
                    lang_name = LANGUAGES.get(detected_lang, UI_TEXT['unknown']).capitalize()
                    language_label.config(text=f"{UI_TEXT['detected_language']}: {lang_name}")
                    duration_label.config(text=f"{UI_TEXT['processing_time']}: {duration:.2f} {UI_TEXT['seconds']}")
                    log_message(f"{UI_TEXT['detected_language']}: {lang_name}")
                    log_message(UI_TEXT['process_completed'])

                    # Transkripsiyon alanına metni ekliyoruz
                    transcription_area.delete(1.0, tk.END)
                    transcription_area.insert(tk.END, result["text"])
                    transcribe_button.config(state="normal")
                    stop_button.config(state="disabled")
                    save_transcription_button.config(state="normal")
                    translate_button.config(state="normal")
                    save_translation_button.config(state="normal")
                    # Harf sayısını güncelle
                    update_transcription_char_count()
    except queue.Empty:
        pass
    except Exception as e:
        # Hataları logla
        log_message(f"{UI_TEXT['error_in_check_queue']}: {str(e)}")
    finally:
        if transcribe_thread.is_alive():
            root.after(100, check_queue, queue_obj)
        else:
            transcribe_button.config(state="normal")
            stop_button.config(state="disabled")
            save_transcription_button.config(state="normal")
            translate_button.config(state="normal")
            save_translation_button.config(state="normal")

def stop_transcription():
    global transcribe_thread
    if transcribe_thread.is_alive():
        # Doğrudan thread'i durduramayız.
        messagebox.showinfo(UI_TEXT['info'], UI_TEXT['cannot_stop_thread'])
        log_message(UI_TEXT['transcription_not_stopped'])
    else:
        log_message(UI_TEXT['transcription_already_stopped'])
    transcribe_button.config(state="normal")
    stop_button.config(state="disabled")
    save_transcription_button.config(state="normal")
    translate_button.config(state="normal")
    save_translation_button.config(state="normal")

def save_transcription():
    if transcription_area.get(1.0, tk.END).strip():
        file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[(UI_TEXT['text_files'], "*.txt")])
        if file:
            with open(file, "w", encoding="utf-8") as f:
                f.write(transcription_area.get(1.0, tk.END))
            messagebox.showinfo(UI_TEXT['info'], UI_TEXT['text_saved'])
            log_message(f"{UI_TEXT['text_saved']}: {file}")
        else:
            log_message(UI_TEXT['save_cancelled'])
    else:
        messagebox.showwarning(UI_TEXT['warning'], UI_TEXT['no_text_to_save'])
        log_message(UI_TEXT['no_text_to_save_log'])

def save_translation():
    if translation_area.get(1.0, tk.END).strip():
        file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[(UI_TEXT['text_files'], "*.txt")])
        if file:
            with open(file, "w", encoding="utf-8") as f:
                f.write(translation_area.get(1.0, tk.END))
            messagebox.showinfo(UI_TEXT['info'], UI_TEXT['text_saved'])
            log_message(f"{UI_TEXT['text_saved']}: {file}")
        else:
            log_message(UI_TEXT['save_cancelled'])
    else:
        messagebox.showwarning(UI_TEXT['warning'], UI_TEXT['no_text_to_save'])
        log_message(UI_TEXT['no_text_to_save_log'])

def translate_text():
    if 'googletrans' in missing_modules:
        messagebox.showwarning(UI_TEXT['warning'], UI_TEXT['missing_modules_translation'])
        log_message(UI_TEXT['missing_modules_translation_log'])
        return

    text = transcription_area.get(1.0, tk.END).strip()
    if not text:
        messagebox.showwarning(UI_TEXT['warning'], UI_TEXT['no_text_to_translate'])
        log_message(UI_TEXT['no_text_to_translate_log'])
        return

    selected_target_language = target_language_var.get()
    target_language_code = GOOGLE_LANGUAGES_SHORT.get(selected_target_language)

    if not target_language_code:
        # Hedef dil geçersizse varsayılan olarak İngilizce'yi kullan
        target_language_code = 'en'
        selected_target_language = 'English'

    translate_button.config(state="disabled")
    log_message(f"{UI_TEXT['translating_text']} {selected_target_language}...")

    try:
        translator = Translator()
        translated_text = translator.translate(text, dest=target_language_code).text
        translation_area.delete(1.0, tk.END)
        translation_area.insert(tk.END, translated_text)
        log_message(UI_TEXT['translation_completed'])
        # Harf sayısını güncelle
        update_translation_char_count()
    except Exception as e:
        messagebox.showerror(UI_TEXT['error'], f"{UI_TEXT['error_during_translation']}: {e}")
        log_message(f"{UI_TEXT['translation_error']}: {e}")
    finally:
        translate_button.config(state="normal")

def install_requirements():
    install_button.config(state="disabled")
    log_message(UI_TEXT['installing_packages'])
    install_thread = threading.Thread(target=run_installation)
    install_thread.start()

def run_installation():
    try:
        # Gerekli paketler listesi
        requirements = ["openai-whisper", "torch", "psutil", "gputil", "googletrans==4.0.0-rc1"]
        for package in requirements:
            log_message(f"{UI_TEXT['installing_package']}: {package}")
            result = subprocess.run(["pip", "install", package], capture_output=True, text=True)
            if result.returncode == 0:
                log_message(f"{UI_TEXT['package_installed']}: {package}")
                if package in missing_modules:
                    missing_modules.remove(package)
            else:
                log_message(f"{UI_TEXT['package_install_error']} ({package}): {result.stderr}")
        log_message(UI_TEXT['all_packages_installed'])
        messagebox.showinfo(UI_TEXT['info'], UI_TEXT['all_components_installed'])
        messagebox.showinfo(UI_TEXT['info'], UI_TEXT['restart_required'])
    except Exception as e:
        log_message(f"{UI_TEXT['package_installation_error']}: {e}")
        messagebox.showerror(UI_TEXT['error'], f"{UI_TEXT['package_installation_error']}: {e}")
    finally:
        install_button.config(state="normal")

def change_language(lang_code):
    global UI_TEXT
    if lang_code in LANGUAGES_UI:
        UI_TEXT = LANGUAGES_UI[lang_code]
        update_ui_texts()
        create_menus()  # Menüleri yeniden oluştur
        update_requirements()  # Gereksinimleri güncelle
    else:
        messagebox.showwarning(UI_TEXT['warning'], "Language not supported.")

def update_ui_texts():
    # Tüm UI metinlerini güncelle
    root.title(UI_TEXT['app_title'])
    select_button.config(text=UI_TEXT['select_file'])
    file_label.config(text=UI_TEXT['no_file_selected'])
    model_label.config(text=UI_TEXT['select_model'])
    gpu_check.config(text=UI_TEXT['use_gpu'])
    target_language_label.config(text=UI_TEXT['select_target_language'])
    transcribe_button.config(text=UI_TEXT['start_transcription'])
    translate_button.config(text=UI_TEXT['translate'])
    stop_button.config(text=UI_TEXT['stop'])
    save_transcription_button.config(text=UI_TEXT['save_transcription'])
    save_translation_button.config(text=UI_TEXT['save_translation'])
    install_button.config(text=UI_TEXT['install_requirements'])
    language_label.config(text=f"{UI_TEXT['detected_language']}: ")
    duration_label.config(text=f"{UI_TEXT['processing_time']}: ")
    transcription_label.config(text=UI_TEXT['transcription'])
    translation_label.config(text=UI_TEXT['translation'])
    log_label.config(text=UI_TEXT['log'])
    credits_label.config(text=UI_TEXT['credits'])
    requirements_label.config(text=UI_TEXT['model_requirements_title'])
    transcription_char_count_label.config(text=f"{UI_TEXT['character_count']}: 0")
    translation_char_count_label.config(text=f"{UI_TEXT['character_count']}: 0")
    # Menüleri güncellemeye gerek yok çünkü yeniden oluşturuyoruz

def set_theme(theme):
    if theme == 'dark':
        # Koyu tema ayarları
        root.configure(bg="#1E1E2E")
        left_frame.configure(bg="#1E1E2E")
        right_frame.configure(bg="#1E1E2E")
        file_label.configure(bg="#1E1E2E", fg="white")
        model_label.configure(bg="#1E1E2E", fg="white")
        gpu_check.configure(bg="#1E1E2E", fg="white", selectcolor="#1E1E2E")
        target_language_label.configure(bg="#1E1E2E", fg="white")
        language_label.configure(bg="#1E1E2E", fg="white")
        duration_label.configure(bg="#1E1E2E", fg="white")
        system_info_label.configure(bg="#1E1E2E", fg="white")
        log_label.configure(bg="#1E1E2E", fg="white")
        transcription_label.configure(bg="#1E1E2E", fg="white")
        translation_label.configure(bg="#1E1E2E", fg="white")
        credits_label.configure(bg="#1E1E2E", fg="white")
        requirements_label.configure(bg="#1E1E2E", fg="white")
        transcription_char_count_label.configure(bg="#1E1E2E", fg="white")
        translation_char_count_label.configure(bg="#1E1E2E", fg="white")
        transcription_area.configure(bg="#282A36", fg="white")
        translation_area.configure(bg="#282A36", fg="white")
        log_area.configure(bg="#282A36", fg="white")
        requirements_area.configure(bg="#282A36", fg="white")
    elif theme == 'light':
        # Açık tema ayarları
        root.configure(bg="#FFFFFF")
        left_frame.configure(bg="#FFFFFF")
        right_frame.configure(bg="#FFFFFF")
        file_label.configure(bg="#FFFFFF", fg="black")
        model_label.configure(bg="#FFFFFF", fg="black")
        gpu_check.configure(bg="#FFFFFF", fg="black", selectcolor="#FFFFFF")
        target_language_label.configure(bg="#FFFFFF", fg="black")
        language_label.configure(bg="#FFFFFF", fg="black")
        duration_label.configure(bg="#FFFFFF", fg="black")
        system_info_label.configure(bg="#FFFFFF", fg="black")
        log_label.configure(bg="#FFFFFF", fg="black")
        transcription_label.configure(bg="#FFFFFF", fg="black")
        translation_label.configure(bg="#FFFFFF", fg="black")
        credits_label.configure(bg="#FFFFFF", fg="black")
        requirements_label.configure(bg="#FFFFFF", fg="black")
        transcription_char_count_label.configure(bg="#FFFFFF", fg="black")
        translation_char_count_label.configure(bg="#FFFFFF", fg="black")
        transcription_area.configure(bg="#FFFFFF", fg="black")
        translation_area.configure(bg="#FFFFFF", fg="black")
        log_area.configure(bg="#FFFFFF", fg="black")
        requirements_area.configure(bg="#FFFFFF", fg="black")

def show_about():
    messagebox.showinfo(UI_TEXT['about'], UI_TEXT['about_text'])

def create_menus():
    global menubar, settings_menu, language_menu, theme_menu, help_menu
    # Mevcut menüyü yok et
    if menubar:
        root.config(menu=None)
        menubar.destroy()

    menubar = tk.Menu(root)
    root.config(menu=menubar)

    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=UI_TEXT['settings'], menu=settings_menu)

    language_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_cascade(label=UI_TEXT['language'], menu=language_menu)

    # Dil seçeneklerini ekle
    language_menu.add_command(label="English", command=lambda: change_language('en'))
    language_menu.add_command(label="Türkçe", command=lambda: change_language('tr'))

    # Tema seçenekleri
    theme_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_cascade(label=UI_TEXT['theme'], menu=theme_menu)
    theme_menu.add_command(label="Dark", command=lambda: set_theme('dark'))
    theme_menu.add_command(label="Light", command=lambda: set_theme('light'))

    # Yardım menüsü
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=UI_TEXT['help'], menu=help_menu)
    help_menu.add_command(label=UI_TEXT['about'], command=show_about)

# Transkripsiyon için harf sayısını güncelleme fonksiyonu
def update_transcription_char_count(event=None):
    text = transcription_area.get(1.0, tk.END)
    char_count = len(text.strip())
    transcription_char_count_label.config(text=f"{UI_TEXT['character_count']}: {char_count}")

# Çeviri için harf sayısını güncelleme fonksiyonu
def update_translation_char_count(event=None):
    text = translation_area.get(1.0, tk.END)
    char_count = len(text.strip())
    translation_char_count_label.config(text=f"{UI_TEXT['character_count']}: {char_count}")

# Otomatik tamamlama fonksiyonu
def autocomplete(event, combobox, value_list):
    value = combobox.get()
    if value == '':
        combobox['values'] = value_list
    else:
        data = []
        for item in value_list:
            if item.lower().startswith(value.lower()):
                data.append(item)
        combobox['values'] = data

if __name__ == "__main__":
    selected_file = ""
    transcribe_thread = None
    menubar = None  # Menüleri global olarak tanımla

    root = tk.Tk()
    root.geometry("1200x800")
    root.configure(bg="#1E1E2E")  # Koyu mavi arka plan

    # Çok dilli UI metinleri
    LANGUAGES_UI = {
        "en": {
            "app_title": "Whisper Transcriber",
            "select_file": "Select File",
            "no_file_selected": "No file selected",
            "select_model": "Select Model:",
            "use_gpu": "Use GPU",
            # Giriş dili seçeneği kaldırıldı
            "select_target_language": "Select Target Language:",
            "start_transcription": "Start Transcription",
            "translate": "Translate",
            "stop": "Stop",
            "save_transcription": "Save Transcription",
            "save_translation": "Save Translation",
            "install_requirements": "Install Requirements",
            "detected_language": "Detected Language",
            "processing_time": "Processing Time",
            "transcription": "Transcription",
            "translation": "Translation",
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
            "gpu_usage_option": "GPU usage",
            "input_language_selected": "Input language selected",
            "input_language_auto": "Input language will be auto-detected.",
            "info": "Info",
            "cannot_stop_thread": "Cannot stop the transcription process (Thread).",
            "transcription_not_stopped": "Transcription process could not be stopped.",
            "transcription_already_stopped": "Transcription process already completed or stopped.",
            "text_files": "Text Files",
            "text_saved": "Text saved successfully.",
            "save_cancelled": "Text save operation cancelled.",
            "no_text_to_save": "No text to save.",
            "no_text_to_save_log": "Text save failed: No text to save.",
            "no_text_to_translate": "No text to translate.",
            "no_text_to_translate_log": "Translation failed: No text to translate.",
            "please_select_valid_target_language": "Please select a valid target language.",
            "invalid_target_language": "Translation failed: Invalid target language.",
            "translating_text": "Translating text to",
            "translation_completed": "Translation completed.",
            "error": "Error",
            "error_during_translation": "An error occurred during translation",
            "translation_error": "Translation error",
            "installing_packages": "Installing required packages...",
            "installing_package": "Installing package",
            "package_installed": "Package installed",
            "package_install_error": "Package install error",
            "all_packages_installed": "All packages installed.",
            "all_components_installed": "All required components have been installed.",
            "package_installation_error": "An error occurred during package installation",
            "cpu_usage": "CPU Usage",
            "ram_usage": "RAM Usage",
            "gpu_usage": "GPU Usage",
            "memory": "Memory",
            "gpu_not_available": "GPU Not Available",
            "error_in_check_queue": "Error (check_queue)",
            "unknown": "Unknown",
            "seconds": "seconds",
            "language": "Language",
            "theme": "Theme",
            "settings": "Settings",
            "help": "Help",
            "about": "About",
            "about_text": "Whisper Transcriber\nVersion 1.0\nThis application is used to transcribe audio files to text and perform translations.",
            "credits": "PrensCin (with the help of ChatGPT)",
            "character_count": "Character Count",
            "missing_modules": "Missing Modules",
            "missing_modules_transcription": "Required modules for transcription are missing. Please install them using the 'Install Requirements' button.",
            "missing_modules_transcription_log": "Transcription failed: Required modules are missing.",
            "missing_modules_translation": "Required modules for translation are missing. Please install them using the 'Install Requirements' button.",
            "missing_modules_translation_log": "Translation failed: Required modules are missing.",
            "missing_modules_system_info": "Required modules for system info are missing.",
            "restart_required": "Required components have been installed. Please restart the application.",
        },
        "tr": {
            "app_title": "Whisper Çevirici",
            "select_file": "Dosya Seç",
            "no_file_selected": "Hiçbir dosya seçilmedi",
            "select_model": "Model Seç:",
            "use_gpu": "GPU Kullan",
            # Giriş dili seçeneği kaldırıldı
            "select_target_language": "Hedef Dil Seç:",
            "start_transcription": "Transkripsiyon Başlat",
            "translate": "Çevir",
            "stop": "Durdur",
            "save_transcription": "Transkripsiyonu Kaydet",
            "save_translation": "Çeviriyi Kaydet",
            "install_requirements": "Gerekli Bileşenleri Kur",
            "detected_language": "Tespit edilen dil",
            "processing_time": "İşlem Süresi",
            "transcription": "Transkripsiyon",
            "translation": "Çeviri",
            "log": "Log:",
            "model_requirements_title": "Model Gereksinimleri:",
            "model_requirements": "Model gereksinimleri",
            "requirements_not_available": "Gereksinimler mevcut değil.",
            "file_types_audio": "Ses/Video Dosyaları",
            "file_types_all": "Tüm Dosyalar",
            "file_selected": "Dosya seçildi",
            "file_selection_cancelled": "Dosya seçimi iptal edildi.",
            "model_loading": "Model yükleniyor...",
            "model_loaded": "Model yüklendi",
            "transcription_starting": "Transkripsiyon başlatılıyor...",
            "transcription_finished": "Transkripsiyon tamamlandı.",
            "error_occurred": "Hata oluştu",
            "process_completed": "İşlem tamamlandı.",
            "warning": "Uyarı",
            "please_select_file": "Lütfen bir dosya seçin.",
            "model_selected": "Seçilen model",
            "gpu_usage_option": "GPU kullanımı",
            "input_language_selected": "Giriş dili seçildi",
            "input_language_auto": "Giriş dili otomatik algılanacak.",
            "info": "Bilgi",
            "cannot_stop_thread": "Transkripsiyon işlemi durdurulamıyor (Thread).",
            "transcription_not_stopped": "Transkripsiyon işlemi durdurulamadı.",
            "transcription_already_stopped": "Transkripsiyon işlemi zaten tamamlandı veya durduruldu.",
            "text_files": "Metin Dosyaları",
            "text_saved": "Metin başarıyla kaydedildi.",
            "save_cancelled": "Metin kaydetme işlemi iptal edildi.",
            "no_text_to_save": "Kaydedilecek metin yok.",
            "no_text_to_save_log": "Metin kaydetme işlemi başarısız: Kaydedilecek metin yok.",
            "no_text_to_translate": "Çevrilecek metin yok.",
            "no_text_to_translate_log": "Çeviri işlemi başarısız: Çevrilecek metin yok.",
            "please_select_valid_target_language": "Lütfen geçerli bir hedef dil seçin.",
            "invalid_target_language": "Çeviri işlemi başarısız: Geçersiz hedef dil.",
            "translating_text": "Metin çevriliyor...",
            "translation_completed": "Çeviri tamamlandı.",
            "error": "Hata",
            "error_during_translation": "Çeviri işlemi sırasında hata oluştu",
            "translation_error": "Çeviri hatası",
            "installing_packages": "Gerekli paketler yükleniyor...",
            "installing_package": "Paket yükleniyor",
            "package_installed": "Paket yüklendi",
            "package_install_error": "Paket yükleme hatası",
            "all_packages_installed": "Tüm paketler yüklendi.",
            "all_components_installed": "Gerekli tüm bileşenler yüklendi.",
            "package_installation_error": "Paket yükleme sırasında hata oluştu",
            "cpu_usage": "CPU Kullanımı",
            "ram_usage": "RAM Kullanımı",
            "gpu_usage": "GPU Kullanımı",
            "memory": "Bellek",
            "gpu_not_available": "GPU Mevcut Değil",
            "error_in_check_queue": "Hata (check_queue)",
            "unknown": "Bilinmiyor",
            "seconds": "saniye",
            "language": "Dil",
            "theme": "Tema",
            "settings": "Ayarlar",
            "help": "Yardım",
            "about": "Hakkında",
            "about_text": "Whisper Çevirici\nSürüm 1.0\nBu uygulama, ses dosyalarını metne dönüştürmek ve çeviri yapmak için kullanılır.",
            "credits": "PrensCin (ChatGPT yardımıyla)",
            "character_count": "Harf Sayısı",
            "missing_modules": "Eksik modüller",
            "missing_modules_transcription": "Transkripsiyon için gerekli modüller yüklü değil. Lütfen 'Gerekli Bileşenleri Kur' butonunu kullanın.",
            "missing_modules_transcription_log": "Transkripsiyon işlemi başarısız: Gerekli modüller eksik.",
            "missing_modules_translation": "Çeviri için gerekli modüller yüklü değil. Lütfen 'Gerekli Bileşenleri Kur' butonunu kullanın.",
            "missing_modules_translation_log": "Çeviri işlemi başarısız: Gerekli modüller eksik.",
            "missing_modules_system_info": "Sistem bilgisi için gerekli modüller eksik.",
            "restart_required": "Gerekli bileşenler yüklendi. Lütfen uygulamayı yeniden başlatın.",
        }
    }

    # Model gereksinimleri
    MODEL_REQUIREMENTS = {
        'tiny': {
            'gpu_vram': '1GB',
            'ram': '2GB',
            'cpu': 'Minimal'
        },
        'base': {
            'gpu_vram': '1GB',
            'ram': '2GB',
            'cpu': 'Minimal'
        },
        'small': {
            'gpu_vram': '2GB',
            'ram': '4GB',
            'cpu': 'Moderate'
        },
        'medium': {
            'gpu_vram': '5GB',
            'ram': '8GB',
            'cpu': 'High'
        },
        'large': {
            'gpu_vram': '10GB',
            'ram': '16GB',
            'cpu': 'Very High'
        }
    }

    # Varsayılan dili İngilizce yapıyoruz
    UI_TEXT = LANGUAGES_UI['en']

    # Menüleri oluştur
    create_menus()

    # Sol panel
    left_frame = tk.Frame(root, bg="#1E1E2E")
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    select_button = tk.Button(left_frame, text=UI_TEXT['select_file'], command=select_file, width=20)
    select_button.pack(pady=5)

    file_label = tk.Label(left_frame, text=UI_TEXT['no_file_selected'], bg="#1E1E2E", fg="white", wraplength=200)
    file_label.pack(pady=5)

    model_label = tk.Label(left_frame, text=UI_TEXT['select_model'], bg="#1E1E2E", fg="white")
    model_label.pack(pady=5)

    models = ["tiny", "base", "small", "medium", "large"]
    model_var = tk.StringVar(value="base")
    model_menu = ttk.Combobox(left_frame, textvariable=model_var, values=models, width=18, state="readonly")
    model_menu.pack(pady=5)
    model_menu.bind('<<ComboboxSelected>>', lambda event: update_requirements())

    use_gpu = tk.BooleanVar(value=torch.cuda.is_available() if 'torch' not in missing_modules else False)
    gpu_check = tk.Checkbutton(left_frame, text=UI_TEXT['use_gpu'], variable=use_gpu, bg="#1E1E2E", fg="white", selectcolor="#1E1E2E")
    gpu_check.pack(pady=5)

    target_language_label = tk.Label(left_frame, text=UI_TEXT['select_target_language'], bg="#1E1E2E", fg="white")
    target_language_label.pack(pady=5)

    # Varsayılan hedef dili 'English' olarak ayarla
    target_language_var = tk.StringVar(value="English")
    target_language_menu = ttk.Combobox(left_frame, textvariable=target_language_var, values=[], width=18, state="normal")
    target_language_menu.pack(pady=5)

    transcribe_button = tk.Button(left_frame, text=UI_TEXT['start_transcription'], command=transcribe, width=20, state="disabled" if not can_transcribe else "normal")
    transcribe_button.pack(pady=10)

    translate_button = tk.Button(left_frame, text=UI_TEXT['translate'], command=translate_text, width=20, state="disabled" if not can_translate else "normal")
    translate_button.pack(pady=5)

    stop_button = tk.Button(left_frame, text=UI_TEXT['stop'], command=stop_transcription, width=20, state="disabled")
    stop_button.pack(pady=5)

    save_transcription_button = tk.Button(left_frame, text=UI_TEXT['save_transcription'], command=save_transcription, width=20)
    save_transcription_button.pack(pady=5)

    save_translation_button = tk.Button(left_frame, text=UI_TEXT['save_translation'], command=save_translation, width=20, state="disabled")
    save_translation_button.pack(pady=5)

    # "Gerekli Bileşenleri Kur" butonunun durumu
    install_button_state = "normal" if missing_modules else "disabled"
    install_button = tk.Button(left_frame, text=UI_TEXT['install_requirements'], command=install_requirements, width=20, state=install_button_state)
    install_button.pack(pady=10)

    language_label = tk.Label(left_frame, text=f"{UI_TEXT['detected_language']}: ", bg="#1E1E2E", fg="white")
    language_label.pack(pady=5)

    duration_label = tk.Label(left_frame, text=f"{UI_TEXT['processing_time']}: ", bg="#1E1E2E", fg="white")
    duration_label.pack(pady=5)

    system_info_label = tk.Label(left_frame, text="", bg="#1E1E2E", fg="white")
    system_info_label.pack(pady=5)

    # Alt tarafta kredi etiketi
    credits_label = tk.Label(left_frame, text=UI_TEXT['credits'], bg="#1E1E2E", fg="white")
    credits_label.pack(side=tk.BOTTOM, pady=10)

    # Sağ çerçeve
    right_frame = tk.Frame(root, bg="#1E1E2E")
    right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10, pady=10)

    # Transkripsiyon alanı
    transcription_label = tk.Label(right_frame, text=UI_TEXT['transcription'], bg="#1E1E2E", fg="white")
    transcription_label.pack(anchor="w", pady=(0, 5))

    transcription_area = tk.Text(right_frame, wrap=tk.WORD, bg="#282A36", fg="white", height=15)
    transcription_area.pack(expand=True, fill=tk.BOTH)
    transcription_area.bind("<<Modified>>", update_transcription_char_count)

    transcription_char_count_label = tk.Label(right_frame, text=f"{UI_TEXT['character_count']}: 0", bg="#1E1E2E", fg="white")
    transcription_char_count_label.pack(anchor="e", pady=(0, 5))

    # Çeviri alanı
    translation_label = tk.Label(right_frame, text=UI_TEXT['translation'], bg="#1E1E2E", fg="white")
    translation_label.pack(anchor="w", pady=(10, 5))

    translation_area = tk.Text(right_frame, wrap=tk.WORD, bg="#282A36", fg="white", height=15)
    translation_area.pack(expand=True, fill=tk.BOTH)
    translation_area.bind("<<Modified>>", update_translation_char_count)

    translation_char_count_label = tk.Label(right_frame, text=f"{UI_TEXT['character_count']}: 0", bg="#1E1E2E", fg="white")
    translation_char_count_label.pack(anchor="e", pady=(0, 5))

    # Log ve gereksinimler için alt çerçeve
    bottom_frame = tk.Frame(right_frame, bg="#1E1E2E")
    bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # Log çerçevesi
    log_frame = tk.Frame(bottom_frame, bg="#1E1E2E")
    log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

    log_label = tk.Label(log_frame, text=UI_TEXT['log'], bg="#1E1E2E", fg="white")
    log_label.pack(anchor="w", pady=(0, 5))

    log_area = tk.Text(log_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white")
    log_area.pack(fill=tk.BOTH, expand=True)

    # Gereksinimler çerçevesi
    requirements_frame = tk.Frame(bottom_frame, bg="#1E1E2E")
    requirements_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

    requirements_label = tk.Label(requirements_frame, text=UI_TEXT['model_requirements_title'], bg="#1E1E2E", fg="white")
    requirements_label.pack(anchor="w", pady=(0, 5))

    requirements_area = tk.Text(requirements_frame, height=10, wrap=tk.WORD, bg="#282A36", fg="white", state='disabled')
    requirements_area.pack(fill=tk.BOTH, expand=True)

    # Sistem bilgisi thread'i başlat
    if 'psutil' not in missing_modules:
        system_thread = threading.Thread(target=update_system_info, daemon=True)
        system_thread.start()

    # Desteklenen dilleri yükle
    def load_language_lists():
        global target_language_list, LANGUAGES, LANGUAGES_SHORT, GOOGLE_LANGUAGES, GOOGLE_LANGUAGES_SHORT
        if 'whisper' not in missing_modules:
            LANGUAGES = whisper.tokenizer.LANGUAGES
            LANGUAGES_SHORT = {v: k for k, v in LANGUAGES.items()}

        if 'googletrans' not in missing_modules:
            GOOGLE_LANGUAGES = {value.capitalize(): key for key, value in GT_LANGUAGES.items()}
            GOOGLE_LANGUAGES_SHORT = {name: code for name, code in GOOGLE_LANGUAGES.items()}
            target_language_list = sorted(GOOGLE_LANGUAGES.keys())
            target_language_menu['values'] = target_language_list
            target_language_menu.bind('<KeyRelease>', lambda event: autocomplete(event, target_language_menu, target_language_list))

    load_language_lists()
    update_ui_texts()
    update_requirements()

    # Eksik modülleri kontrol edin ve kullanıcıya bildirin
    if missing_modules:
        missing_modules_str = ', '.join(missing_modules)
        messagebox.showwarning(UI_TEXT['warning'], f"{UI_TEXT['missing_modules']}: {missing_modules_str}")
        log_message(f"{UI_TEXT['missing_modules']}: {missing_modules_str}")
    else:
        # Butonların durumunu güncelleyin
        pass

    root.mainloop()
