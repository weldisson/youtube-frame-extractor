# YouTube Frame & Subtitle Extractor 🎥🖼️

A modern local web application (Python/FastAPI backend + Glassmorphism HTML/JS frontend) that allows you to extract frames from any YouTube video at custom intervals (e.g., every 1 second, 1.5s, 5s, etc.), draw the active subtitle/caption text directly onto the image, and download them bundled in a compressed ZIP file.

This application has been developed and optimized to bypass recent YouTube download restrictions (such as HTTP Error 403: Forbidden and "The page needs to be reloaded") using player-client spoofing (Android client emulation) and robust transcript fetching logic.

---

## ✨ Features

- **Custom Extraction Interval:** Extract frames at precise intervals (e.g., every 1.0s, 1.5s, 5s, etc.).
- **Embedded Captions:** The app retrieves the active subtitle at each frame's timestamp and renders it at the bottom of the image with a translucent black background for maximum legibility.
- **Smart File Naming:** Frames are saved as `{timestamp_seconds}s_{sanitized_subtitle}.jpg` for easy reference.
- **Optimized Storage:** The original video file is automatically deleted from the server once frame extraction completes to save disk space.
- **Premium Interface:** A modern, responsive Dark Mode UI featuring Glassmorphism, real-time progress updates (downloading, extracting, packaging), a gallery grid, lightbox previews, and a ZIP download button.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, FastAPI, Uvicorn, OpenCV (for frame extraction and caption rendering), Pillow/numpy.
- **Download Engine:** `yt-dlp` (configured with Android player client spoofing) and `youtube-transcript-api`.
- **Frontend:** HTML5, CSS3 (with Glassmorphic elements and fluid transitions), JavaScript (ES6).

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.9+ installed on your system.

### Step 1: Navigate to the project directory
Open your terminal and run:
```bash
cd /Users/weldissonaraujo/.gemini/antigravity/scratch/youtube_frame_extractor
```

### Step 2: Start the application
The project includes a startup script that activates the virtual environment (`venv`) and boots up the FastAPI server:
```bash
./start.sh
```

### Step 3: Access the Web UI
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 📁 Project Structure

```text
youtube_frame_extractor/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI endpoints & Frontend HTML page
│   ├── downloader.py    # Downloads YouTube video and transcript streams
│   ├── processor.py     # Frame extraction, subtitle drawing & ZIP creation
│   └── exceptions.py    # Custom application exceptions
├── tests/               # E2E integration test suite & mock assets
├── requirements.txt     # Python dependencies
├── start.sh             # Automatic server startup script
├── .gitignore           # Prevents uploading local cache/videos to Git
└── README.md            # Project documentation
```

---

## 🧪 Running E2E Tests (Offline)
To run the integrated offline test suite:
```bash
./venv/bin/python tests/test_runner.py
```
