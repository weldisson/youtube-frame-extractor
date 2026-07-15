import os
import re
import shutil
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
)
from app.exceptions import VideoNotFoundError, SubtitlesNotFoundError

# Resolve the mock assets directory path dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_ASSETS_DIR = os.path.join(BASE_DIR, "tests", "mock_assets")


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS,mmm SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    if milliseconds == 1000:
        secs += 1
        milliseconds = 0
        if secs == 60:
            minutes += 1
            secs = 0
            if minutes == 60:
                hours += 1
                minutes = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def write_srt(transcript: list, srt_path: str):
    """Write transcript data list to an SRT file."""
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, entry in enumerate(transcript, start=1):
            if isinstance(entry, dict):
                start = entry["start"]
                duration = entry.get("duration", 0.0)
                if duration is None:
                    duration = 0.0
                text = entry["text"]
            else:
                start = getattr(entry, "start", 0.0)
                duration = getattr(entry, "duration", 0.0)
                if duration is None:
                    duration = 0.0
                text = getattr(entry, "text", "")
                
            end = start + duration
            
            start_str = format_timestamp(start)
            end_str = format_timestamp(end)
            
            f.write(f"{idx}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")


def extract_video_id(url: str) -> str:
    """Extract YouTube 11-character video ID from various URL patterns."""
    patterns = [
        r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})(?:\?|&|$)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    if len(url) == 11:
        return url
    return ""


def is_mock_mode() -> bool:
    """Check if the application is running in mock/offline mode."""
    return (
        os.environ.get("YOUTUBE_FRAME_EXTRACTOR_MOCK") == "1"
        or os.environ.get("MOCK_YOUTUBE") == "1"
    )


def download_video(url: str, output_dir: str) -> str:
    """
    Download video from YouTube, returning the path of the downloaded file.
    Supports YOUTUBE_FRAME_EXTRACTOR_MOCK=1 offline mode.
    """
    if is_mock_mode():
        if "invalid" in url.lower():
            raise VideoNotFoundError("Mock mode: Video not found for invalid URL.")
        
        os.makedirs(output_dir, exist_ok=True)
        src_path = os.path.join(MOCK_ASSETS_DIR, "mock_video.mp4")
        dest_path = os.path.join(output_dir, "mock_video.mp4")
        
        # Ensure mock source asset exists
        if not os.path.exists(src_path):
            os.makedirs(os.path.dirname(src_path), exist_ok=True)
            import base64
            MINIMAL_MP4_BASE64 = (
                "AAAAIGZ0eXBpc29tAAAAAGlzb21tcDQydjEAAAADbWRhdAAAAAAgbW9vdgAAAGxtdmhk"
                "AAAAAAAAAAAAAAAAAAAAAQAAlgAAAPAAAAABAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAAAC"
                "HHRyYWsAAABcdGtoZAAAAAMAAAAAAAAAAAAAAAABAAAAAAAAlgAAAAAAAAABAAAAAAAA"
                "AAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAkZWR0cwAAABxlbHN0AAAAAAAAAAEAAACWAAAAAQAAAAEAAAAAbWRpYQAAACBt"
                "ZGhkAAAAAAAAAAAAAAAAAAAAAQAAlgAAAPAAAAABAAAAAWhkbHIAAAAAAAAAAHZpZGVh"
                "AAAAAAAAAAAAAAAAVmlkZW9IYW5kbGVyAAAAAYxtaW5mAAAAEHZtYWhkAAAAAQAAAAAA"
                "AAAkZGluZgAAABxkcmVmAAAAAAAAAAEAAAAMdXJsIAAAAAEAAAFibXNkaAAAADhzdGJs"
                "AAAALHN0c2QAAAAAAAAAAQAAABx2Y2MxAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAABgA"
                "AAAAY29sbAABAAgAAgAAAAAsc3R0cwAAAAAAAAABAAAAAQAAAJYAAAAUc3RzeQAAAAAA"
                "AAABAAAAAQAAAAAcc3RzYwAAAAAAAAABAAAAAQAAAAEAAAABAAAAHHN0c3oAAAAAAAAA"
                "AQAAAAAAAACWAAAAFHN0Y28AAAAAAAAAAQAAADAAAAAIdWR0YQAAABBtZXRhAAAAAAAA"
                "ACVoZGxyAAAAAAAAAABtZGlyAAAAAAAAAAAAAAAAAAAAAAAAY2hsaXN0AAAAEGlsc3QA"
                "AAAIAAAAAGRhdGE="
            )
            with open(src_path, "wb") as f:
                f.write(base64.b64decode(MINIMAL_MP4_BASE64))
        
        shutil.copy(src_path, dest_path)
        return dest_path

    # Real mode
    try:
        os.makedirs(output_dir, exist_ok=True)
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s-%(id)s.%(ext)s'),
            'format': 'mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android']
                }
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            if not os.path.exists(filepath):
                base, _ = os.path.splitext(filepath)
                dir_name = os.path.dirname(filepath)
                base_name = os.path.basename(base)
                for f in os.listdir(dir_name):
                    if f.startswith(base_name):
                        filepath = os.path.join(dir_name, f)
                        break
            return filepath
    except Exception as e:
        raise VideoNotFoundError(f"Failed to download video: {e}") from e


def download_subtitles(url: str, lang: str, output_dir: str) -> str:
    """
    Download subtitles in SRT format, returning the path of the SRT file.
    Supports YOUTUBE_FRAME_EXTRACTOR_MOCK=1 offline mode.
    """
    if is_mock_mode():
        if "invalid" in url.lower():
            raise VideoNotFoundError("Mock mode: Video not found for invalid URL.")
        if "no_subtitles" in url.lower():
            raise SubtitlesNotFoundError("Mock mode: Subtitles not found.")
        
        os.makedirs(output_dir, exist_ok=True)
        src_path = os.path.join(MOCK_ASSETS_DIR, "mock_subtitles.srt")
        dest_path = os.path.join(output_dir, "mock_subtitles.srt")
        
        # Ensure mock source asset exists
        if not os.path.exists(src_path):
            os.makedirs(os.path.dirname(src_path), exist_ok=True)
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(
                    "1\n"
                    "00:00:00,000 --> 00:00:02,000\n"
                    "First subtitle: Hello World\n\n"
                    "2\n"
                    "00:00:02,000 --> 00:00:05,000\n"
                    "Second subtitle: YouTube Frame Extractor\n"
                )
        
        shutil.copy(src_path, dest_path)
        return dest_path

    # Real mode
    video_id = extract_video_id(url)
    if not video_id:
        raise VideoNotFoundError(f"Could not extract video ID from URL: {url}")
        
    try:
        transcript_list = YouTubeTranscriptApi().list(video_id)
        
        try:
            transcript_obj = transcript_list.find_transcript([lang])
        except NoTranscriptFound:
            # Fallback to auto-translate if possible
            try:
                # Find any translatable transcript
                for t in transcript_list:
                    if t.is_translatable:
                        transcript_obj = t.translate(lang)
                        break
                else:
                    raise SubtitlesNotFoundError(f"No transcript found or translatable to language: {lang}")
            except Exception as e:
                raise SubtitlesNotFoundError(f"No transcript found or translatable to language {lang}: {e}")
        
        transcript_data = transcript_obj.fetch()
        
        srt_filename = f"{video_id}_{lang}.srt"
        dest_path = os.path.join(output_dir, srt_filename)
        
        os.makedirs(output_dir, exist_ok=True)
        write_srt(transcript_data, dest_path)
        return dest_path
        
    except VideoUnavailable as e:
        raise VideoNotFoundError(f"Video unavailable: {video_id}") from e
    except (TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript) as e:
        raise SubtitlesNotFoundError(f"Subtitles not found: {e}") from e
    except Exception as e:
        msg = str(e).lower()
        if "unavailable" in msg or "not found" in msg or "does not exist" in msg:
            raise VideoNotFoundError(f"Video not found or unavailable: {e}") from e
        else:
            raise SubtitlesNotFoundError(f"Could not download subtitles: {e}") from e
