Hello there! I'm an entry-level developer, and I'd like to share my exciting Transcriber & Translator project that uses OpenAI Whisper.

🚀 Project Goals
Convert audio files (mp3, mp4, wav, etc.) into text transcriptions.
Use Google Translate to translate the generated text into multiple languages.
Enable GPU (CUDA) acceleration for faster transcription and translation.
Provide a Python GUI for ease of use and real-time system monitoring.
Show CPU, RAM, and GPU usage (if available) in real time.
Display total character counts and detailed logs.
🌟 Key Features
OpenAI's Whisper for audio-to-text transcription.
Google Translate integration for multi-language support.
GPU (CUDA) acceleration for processing larger audio files faster.
Real-time system stats and log outputs in the GUI.
Option to save transcriptions and translations as .txt.
In-app automatic installation for missing libraries.
⚙️ Requirements
Python 3.10+
pip package manager
FFmpeg (A must-have for handling various audio/video formats! Download & install)
openai-whisper, torch, psutil, GPUtil, googletrans (install in-app or via pip)
📁 Repository Contents
WhisperGUI.py: Main GUI application with advanced features, real-time resource monitoring, and GPU acceleration.
WhisperTranslator.py: Alternative or simpler version handling transcription and translation logic; feel free to tweak it.

![Screenshot 2025-01-27 195702](https://github.com/user-attachments/assets/932a7e37-0fd9-40d8-9a64-e4cc64eec556)



🏁 How to Run
Clone or download this repository.
Make sure you have Python 3.10+ installed.
Verify that FFmpeg is installed and added to your system PATH.

Open a terminal in the project folder:
cd WhisperTranscriberProject


If you lack the required packages (e.g., first time user), use the “Install Requirements” button in the app or run:

pip install openai-whisper torch psutil GPUtil googletrans==4.0.0-rc1

In the GUI, select an audio file, choose a model, click “Start Transcription,” then use “Translate” to get text in your preferred language!
🎉 Contribute
Feel free to open a pull request or issue for any bug reports or improvements.
As an entry-level developer, I’m completely open to any kind of suggestion or help!
Have fun! 🙌![Screenshot 2025-01-27 202626](https://github.com/user-attachments/assets/7159e13d-08dd-4015-a985-fd50ca97beac)

