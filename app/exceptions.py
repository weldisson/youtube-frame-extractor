class VideoNotFoundError(Exception):
    """Exception raised when a video cannot be found or downloaded from YouTube."""
    pass


class SubtitlesNotFoundError(Exception):
    """Exception raised when subtitles in the specified language cannot be found or downloaded."""
    pass
