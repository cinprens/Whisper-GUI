Whisper Transcriber & Translator
This project is a Python GUI application that utilizes OpenAI's Whisper model for audio transcription and Google Translate for text translation. It supports multiple languages, GPU acceleration, real-time system monitoring, and provides options for saving transcriptions and translations.

## Features

- **Audio Transcription**: Transcribe audio files (e.g., `.mp3`, `.mp4`, `.wav`) into text using the Whisper model.
- **Text Translation**: Translate the transcribed text into multiple languages using Google Translate.
- **GPU Acceleration**: Supports GPU acceleration using PyTorch for faster transcriptions.
- **Dynamic Requirements Installation**: Users can install missing dependencies directly from the application.
- **Real-Time System Monitoring**: Displays CPU, RAM, and (if available) GPU usage in real-time.
- **Character Count**: Displays the character count for both the transcription
- **Log System**: Shows detailed logs during transcription and translation processes.

## Prerequisites

To run this project locally, make sure you have the following installed:

- Python 3.10 or higher
- `pip` package manager

## Dependencies
GUI SPOILER

![Screenshot 2025-01-27 195702](https://github.com/user-attachments/assets/88da864f-8532-4d0f-9aa9-be550f00336e)
                

The application depends on the following Python libraries:

- `openai-whisper`: For audio transcription
- `torch`: PyTorch for GPU acceleration
- `psutil`: For system resource monitoring (CPU, RAM)
- `GPUtil`: For GPU monitoring (optional)



if not work follow this page
https://github.com/openai/whisper
