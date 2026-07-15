# Project: youtube_frame_extractor

## Architecture
- A Python local web application using a simple framework (FastAPI or Flask).
- Backend Module:
  - Video and subtitle download manager using `yt-dlp` and `youtube-transcript-api`.
  - Frame extraction engine using OpenCV/ffmpeg.
  - Image processor using Pillow to overlay subtitles with high readability (centered bottom, dark shadow/background) and compress to JPEG (quality 80) or WebP.
  - Metadata and packager to produce `metadata.json`/`subtitles.srt` and packaging into a ZIP file.
- Frontend Module:
  - Clean HTML/JS frontend or streamlit interface.
  - Interactive inputs (YouTube URL, extraction interval, language).
  - Live progress display during downloading, extraction, and processing.
  - Preview gallery of generated frames with subtitle overlays.
  - Download ZIP button.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Test_Infra | Design and build E2E test infrastructure and Tiers 1-4 test cases | None | IN_PROGRESS (Conv: 71be678f-dd65-4d70-99b7-365f3a1c396d) |
| 2 | Backend_Retrieval | Download YouTube videos and subtitles using yt-dlp & transcript-api | None | IN_PROGRESS (Conv: 6b694673-33b7-498f-8cf7-51ee568819a7) |
| 3 | Backend_Extraction | Extract frames, overlay subtitles, compress images, and save with seconds_subtitle.jpg name | Backend_Retrieval | IN_PROGRESS (Conv: 6b694673-33b7-498f-8cf7-51ee568819a7) |
| 4 | Backend_Packaging | Generate metadata.json/subtitles.srt and package to ZIP | Backend_Extraction | IN_PROGRESS (Conv: 6b694673-33b7-498f-8cf7-51ee568819a7) |
| 5 | Web_Interface | FastAPI/Flask web UI with gallery, progress feedback, download ZIP | Backend_Packaging | IN_PROGRESS (Conv: 6b694673-33b7-498f-8cf7-51ee568819a7) |
| 6 | Integration_E2E | Integrate frontend/backend, pass 100% of E2E tests, and perform Tier 5 hardening | Web_Interface, Test_Infra | PLANNED |

## Code Layout
- `app/`
  - `__init__.py`
  - `main.py` (FastAPI app entrypoint)
  - `downloader.py` (Retrieves video/subtitles)
  - `extractor.py` (Extracts frames and overlays subtitles)
  - `packager.py` (Creates metadata mapping and ZIP)
- `static/` (For web frontend files if using HTML/JS)
  - `index.html`
  - `app.js`
  - `style.css`
- `tests/`
  - `conftest.py`
  - `test_e2e.py` (Tiers 1-4 test cases)
  - `test_runner.py` (Utility to execute tests)
- `requirements.txt`

## Interface Contracts
### Downloader ↔ Extractor
- `download_video(url: str, output_dir: str) -> str`: downloads video, returns path.
- `download_subtitles(url: str, lang: str, output_dir: str) -> str`: downloads subtitles in SRT/JSON format, returns path.
### Extractor ↔ Packager
- `extract_frames(video_path: str, subtitle_path: str, interval: float, quality: int, output_dir: str) -> List[Dict]`: returns list of dicts with `timestamp`, `frame_path`, `subtitle_text`.
- `create_zip(frames_metadata: List[Dict], output_zip_path: str) -> str`: returns ZIP file path.
