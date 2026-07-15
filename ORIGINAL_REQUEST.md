# Original User Request

## Initial Request — 2026-07-13T22:37:53Z

A local web application (HTML/JS frontend + Python backend) that takes a YouTube video URL and a time interval, downloads the video and subtitles, extracts frames at the specified interval, overlays the matching subtitle text directly onto each frame image, compresses the images, and names them using the timestamp and subtitle content. It also generates a mapping file (JSON/SRT) and presents a web UI to view and download the results.

Working directory: /Users/weldissonaraujo/.gemini/antigravity/scratch/youtube_frame_extractor
Integrity mode: development

## Requirements

### R1. Web Interface
- Provide a clean, modern, and intuitive local web interface (e.g., using FastAPI/Flask/Streamlit or similar simple Python web framework).
- Allow the user to input:
  - YouTube video URL.
  - Frame extraction interval in seconds (decimal numbers supported, e.g., 1.5).
  - Target language for subtitles (defaulting to Portuguese or English).
- Display real-time progress of the downloading, extraction, and processing phases.
- Show a gallery/preview of the processed frames with their overlaid subtitles in the UI.
- Provide a button/link to download all processed frames and subtitle mappings as a ZIP file.

### R2. Video and Subtitle Retrieval
- Use a robust tool/library (such as `yt-dlp` and `youtube-transcript-api`) to download the YouTube video and its subtitles.
- If subtitles are not available in the requested language, fall back to auto-generated subtitles or notify the user.

### R3. Frame Extraction and Text Overlay
- Extract frames exactly at the specified interval (e.g. 0s, 1s, 2s, etc., or 0s, 1.5s, 3.0s, etc.).
- For each frame:
  - Find the subtitle/caption text active at that exact timestamp.
  - Draw (overlay) the subtitle text clearly on the frame image (e.g., centered near the bottom with a dark background/shadow for readability).
  - Compress the image using a format like JPEG (with configurable quality, e.g., 80) or WebP.
  - Save the frame image with a filename pattern: `{seconds}s_{sanitized_subtitle_text}.jpg` (maximum filename length handled gracefully).

### R4. Metadata and Packaging
- Generate a mapping file (e.g., `metadata.json` or `subtitles.srt`) linking each frame image filename to its timestamp and full subtitle text.
- Package the generated frame images and the mapping file into a single download package (ZIP format) for the user.

## Acceptance Criteria

### Functionality
- [ ] Users can enter a YouTube link and an interval, then initiate processing.
- [ ] The app displays progress feedback during download and extraction.
- [ ] Frames are extracted at the correct interval.
- [ ] Subtitles are drawn on the frames clearly.
- [ ] Frame images are named with `{seconds}s_{subtitle}.jpg`.
- [ ] Subtitles mapping file is saved alongside the images.
- [ ] A preview gallery shows the generated images in the web interface.
- [ ] A ZIP download button is available and works correctly.

### Verification Plan
- [ ] The team must provide automated/integration scripts to test the backend extraction logic with a mock/real video and subtitles.
- [ ] Verify that files are correctly saved in the output directory and compressed properly.
- [ ] Verify that filenames are clean and do not crash on special characters or excessively long subtitle strings.
