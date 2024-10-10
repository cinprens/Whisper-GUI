# Whisper Transcriber & Translator

This project is a Python-based GUI application that uses OpenAI's Whisper model for audio transcription and Google Translate for text translation. It supports multiple languages, GPU acceleration, and allows users to save transcriptions and translations as text files.

## Features

- **Audio Transcription**: Transcribe audio files (e.g., `.mp3`, `.mp4`, `.wav`) into text using the Whisper model.
- **Text Translation**: Translate the transcribed text into multiple languages using Google Translate.
- **GPU Acceleration**: Supports GPU acceleration using PyTorch for faster transcriptions.
- **Dynamic Requirements Installation**: Users can install missing dependencies directly from the application.
- **Real-Time System Monitoring**: Displays CPU, RAM, and (if available) GPU usage in real-time.
- **Multiple Languages**: Supports both English and Turkish as the UI language.
- **Character Count**: Displays the character count for both the transcription and translation.
- **Log System**: Shows detailed logs during transcription and translation processes.

## Prerequisites

To run this project locally, make sure you have the following installed:

- Python 3.10 or higher
- `pip` package manager

## Dependencies

The application depends on the following Python libraries:

- `openai-whisper`: For audio transcription
- `torch`: PyTorch for GPU acceleration
- `psutil`: For system resource monitoring (CPU, RAM)
- `googletrans==4.0.0-rc1`: For text translation via Google Translate
- `GPUtil`: For GPU monitoring (optional)

![Screenshot 2024-10-10 145125](https://github.com/user-attachments/assets/307f2bfa-4a26-4e88-a2ea-55402e1efab8)
