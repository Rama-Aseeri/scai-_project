# 🎬 Sports Highlight Extractor

This is a Flask web app that automatically detects and extracts key moments from sports videos. It uses [OpenAI's Whisper] to transcribe the audio commentary, then searches for sport-specific keywords to identify the most exciting clips.

---

## ⚙️ Features

- 🧠 Audio transcription powered by Whisper
- 🏟️ Detects highlight-worthy moments using keyword matching
- ✂️ Automatically extracts short highlight clips (default: 7s each)
- 🔁 Combines multiple highlights into one final video
- 📦 Simple web interface for uploading and downloading videos
- ✅ Supports:
  - ⚽ Football
  - 🏀 Basketball
  - 🤼 Martial Arts
  - 🏎️ Car Racing
  - 🤾 Handball

---

## 🛠️ Tech Stack

- Python
- Flask
- MoviePy
- OpenAI Whisper
- HTML/CSS (via `index.html`)
- Tempfile for secure file handling
