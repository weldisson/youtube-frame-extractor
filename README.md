# YouTube Frame & Subtitle Extractor 🎥🖼️

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-red?style=for-the-badge)](https://github.com/)

A modern, local web application designed to download YouTube videos, extract frames at regular, customizable intervals (e.g. every 1 second, 1.5s, 5s), match the active subtitle/caption text at each frame's timestamp, draw the subtitle directly on the image, and package them into a compressed ZIP file.

This application is built to robustly bypass recent YouTube scraping blocks (such as `HTTP Error 403: Forbidden` and `The page needs to be reloaded` errors) by implementing player-client spoofing (emulating the official YouTube Android client) and dynamic transcript list matching.

---

## ✨ Features

- **Custom extraction interval:** Extract frames at any user-defined interval in seconds (decimals supported, e.g. `1.5`s).
- **Embedded caption overlays:** Dynamically matches and overlays subtitles on the bottom center of the frame, wrapped in a semi-transparent black rectangle for maximum readability.
- **Smart filename mapping:** Saved files are named `{timestamp}s_{sanitized_subtitle}.jpg` for easy organization.
- **Auto-cleanup storage optimization:** The original high-resolution video file is automatically deleted from the server once extraction completes to optimize local disk usage.
- **High-quality, compressed outputs:** Saves frames in optimized, compressed JPEG format (quality 80) to keep packages small and manageable.
- **Premium Web UI:** Includes a dark-themed Glassmorphism single-page application with:
  - Real-time visual progress indicators (downloading, extracting, packaging).
  - A responsive gallery showing thumbnails of the extracted frames with subtitle text.
  - Interactive Lightbox popup modal for viewing high-resolution frame reviews.
  - Direct ZIP package downloader.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, FastAPI, Uvicorn, OpenCV (for frame seeking and caption overlay rendering).
- **Download Engine:** `yt-dlp` (configured with Android player client spoofing) and `youtube-transcript-api`.
- **Frontend:** HTML5, Vanilla CSS3 (featuring Glassmorphic gradients and modern typography), JavaScript (ES6).

---

## 🚀 Installation & Local Run

### Prerequisites
Make sure you have **Python 3.9+** installed on your system.

### 1. Clone the repository
```bash
git clone https://github.com/weldisson/youtube-frame-extractor.git
cd youtube-frame-extractor
```

### 2. Configure Virtual Environment & Dependencies
Create a virtual environment, activate it, and install the required libraries:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch the Application
Run the automated startup script to start the FastAPI server:
```bash
chmod +x start.sh
./start.sh
```

### 4. Open in browser
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 📁 Repository Structure

```text
youtube_frame_extractor/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI server routes & Web UI layout
│   ├── downloader.py    # Emulated downloader for YouTube streams and subtitles
│   ├── processor.py     # Frame extraction engine and subtitle drawing logic
│   └── exceptions.py    # Custom exception classes
├── tests/               # Offline E2E integration test suite & mock assets
├── requirements.txt     # Python package requirements
├── start.sh             # Startup wrapper script
├── .gitignore           # Ignores local virtual environments, video caches, and output downloads
└── README.md            # Repository documentation
```

---

## 🧪 Testing

To run the offline E2E integration tests to verify the routing, folder structures, and zip compilation logic:
```bash
./venv/bin/python tests/test_runner.py
```

---

## 📄 License

This project is licensed under the MIT License. Feel free to copy, modify, and distribute it as you wish.
