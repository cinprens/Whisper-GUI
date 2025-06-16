# Whisper-GUI

Bu uygulama ses dosyalarını yazıya döken basit bir arayüz sunar. Projeyi GitHub'dan `Code > Download ZIP` diyerek indirip klasörü dışarı çıkararak başlayabilirsiniz.

🚀 Proje Hedefleri
Ses dosyalarını (mp3, mp4, wav, vb.) yazıya dökme.
Oluşan metni farklı dillere çevirme.
GPU (CUDA) desteğiyle işlemleri hızlandırma.
Kullanımı kolay bir Python arayüzü sunma.
CPU, RAM ve varsa GPU kullanımını anlık gösterme.
Toplam karakter sayısını ve detaylı günlükleri görüntüleme.



🌟 Öne Çıkan Özellikler
OpenAI'nin Whisper modeliyle ses dosyalarını yazıya çevirme.
Çeviri özelliğiyle çoklu dil desteği.
Büyük dosyaları daha hızlı işlemek için GPU (CUDA) kullanımı.
Gerçek zamanlı sistem istatistikleri ve log takibi.
Çıktıları .txt veya .pdf olarak kaydetme.





⚙️ Gereksinimler
Python 3.10+
pip paket yöneticisi
FFmpeg kurulu ve PATH'e eklenmiş olmalı
Gerekli kütüphaneler `requirements.txt` içinde listelenmiştir




📁 Repository Contents
main.py: Application entry point; launches the GUI and controls transcription.
ui.py: Defines the interface components and handles user interactions.
transcriber.py: Helper module that uses Whisper models to transcribe and translate audio files.

## Nasıl Çalıştırılır?

1. Bilgisayarınızda Python yüklü değilse <https://www.python.org/downloads/> adresinden indirin ve kurulum sırasında **"Add Python to PATH"** seçeneğini işaretleyin.
2. Proje klasöründe boş bir alana sağ tıklayıp **"Komut İstemcisini burada aç"** deyin.
3. Sırayla şu komutları çalıştırın:

```bash
pip install -r requirements.txt
python main.py
```

Program açıldığında modelinizi seçip **Transcribe** butonuna basmanız yeterli. Çıktıyı TXT veya PDF olarak kaydedebilirsiniz.
Uygun ekran kartı olan sistemlerde GPU desteği otomatik olarak devreye girer ve işlem daha hızlı tamamlanır.
🎉 Katkıda Bulunun
Hata bildirmek veya geliştirme önerisinde bulunmak için çekme isteği veya issue açabilirsiniz.
Her türlü desteğe açığım, katkılarınızı beklerim!
İyi eğlenceler!


