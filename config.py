import os
import warnings

# 🔹 Uyarıları kapatma
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# 🔹 Model klasörü ayarı
# Uygulama dizini altındaki 'WhisperModels' klasörünü kullan
MODEL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WhisperModels")
os.makedirs(MODEL_FOLDER, exist_ok=True)  # Eğer klasör yoksa oluştur

# 🔹 Transkripsiyon klasörü ayarı
# Proje dizinindeki 'Transkriptasyons' klasörünü kullan
TRANSCRIPT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Transkriptasyons")
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)  # Eğer klasör yoksa oluştur

# 🔹 Kullanılabilir modeller listesi
MODEL_LIST = [
    "tiny", "tiny.en", "base", "base.en",
    "small", "small.en", "medium", "medium.en",
    "large", "large-v2", "large-v3"
]

# 🔹 Model gereksinimleri
MODEL_REQUIREMENTS = {
    "tiny": {
        "ram": "2GB+",
        "notes": "Fast, lower accuracy",
        "size": "152MB",
    },
    "tiny.en": {
        "ram": "2GB+",
        "notes": "English-only version",
        "size": "152MB",
    },
    "base": {
        "ram": "4GB+",
        "notes": "Base model",
        "size": "292MB",
    },
    "base.en": {
        "ram": "4GB+",
        "notes": "English-only version",
        "size": "292MB",
    },
    "small": {
        "ram": "5GB+",
        "notes": "Smaller, higher accuracy",
        "size": "1GB",
    },
    "small.en": {
        "ram": "6GB+",
        "notes": "English-only version",
        "size": "1GB",
    },
    "medium": {
        "ram": "8GB+",
        "notes": "Medium model",
        "size": "2.9GB",
    },
    "medium.en": {
        "ram": "8GB+",
        "notes": "English-only version",
        "size": "2.9GB",
    },
    "large": {
        "ram": "12GB+",
        "notes": "Large model",
        "size": "5.8GB",
    },
    "large-v2": {
        "ram": "15GB+",
        "notes": "Latest large model",
        "size": "5.8GB",
    },
    "large-v3": {
        "ram": "16GB+",
        "notes": "Newest large model",
        "size": "6.2GB"
    }
}

# 🔹 Eksik modülleri kontrol et
missing_modules = set()
for module in ["whisper", "torch", "psutil", "GPUtil"]:
    try:
        __import__(module)
    except ImportError:
        missing_modules.add(module)

