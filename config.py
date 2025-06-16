import os
import warnings

# 🔹 Uyarıları kapatma
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# 🔹 Model klasörü ayarı
MODEL_FOLDER = os.path.join(os.path.expanduser("~"), "Desktop", "WhisperPy", "Models")
os.makedirs(MODEL_FOLDER, exist_ok=True)  # Eğer klasör yoksa oluştur

# 🔹 Kullanılabilir modeller listesi
MODEL_LIST = [
    "tiny", "tiny.en", "base", "base.en",
    "small", "small.en", "medium", "medium.en",
    "large", "large-v2", "large-v3", "whisper-turbo"
]

# 🔹 Model gereksinimleri
MODEL_REQUIREMENTS = {
    "tiny":       {"ram": "2GB+",  "notes": "Fast, lower accuracy"},
    "tiny.en":    {"ram": "2GB+",  "notes": "English-only version"},
    "base":       {"ram": "4GB+",  "notes": "Base model"},
    "base.en":    {"ram": "4GB+",  "notes": "English-only version"},
    "small":      {"ram": "5GB+",  "notes": "Smaller, higher accuracy"},
    "small.en":   {"ram": "6GB+",  "notes": "English-only version"},
    "medium":     {"ram": "8GB+",  "notes": "Medium model"},
    "large":      {"ram": "12GB+", "notes": "Large model"},
    "large-v2":   {"ram": "15GB+", "notes": "Latest large model"},
    "large-v3":   {"ram": "16GB+", "notes": "Newest large model"},
    "whisper-turbo": {"ram": "8GB+", "notes": "Optimized for fast transcription"}
}

# 🔹 Eksik modülleri kontrol et
missing_modules = set()
for module in ["whisper", "torch", "psutil", "GPUtil"]:
    try:
        __import__(module)
    except ImportError:
        missing_modules.add(module)

# 🔹 Transkripsiyon için gerekli modüller var mı?
can_transcribe = "whisper" not in missing_modules and "torch" not in missing_modules