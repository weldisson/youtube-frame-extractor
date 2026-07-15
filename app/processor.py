import os
import re
import cv2

def parse_srt(srt_path: str):
    """
    Parses an SRT file and returns a list of dictionaries with start, end, and text.
    """
    if not os.path.exists(srt_path):
        return []
        
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading SRT file: {e}")
        return []
    
    entries = []
    # Standardize line endings and split by double newlines
    content = content.replace("\r\n", "\n")
    blocks = content.strip().split("\n\n")
    
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            # Check if second line is the timestamp
            # Format: 00:00:00,000 --> 00:00:02,000
            time_match = re.match(
                r"(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})",
                lines[1].strip()
            )
            if time_match:
                sh, sm, ss, sms, eh, em, es, ems = map(int, time_match.groups())
                start = sh * 3600 + sm * 60 + ss + sms / 1000.0
                end = eh * 3600 + em * 60 + es + ems / 1000.0
                text = " ".join(lines[2:]).strip()
                entries.append({"start": start, "end": end, "text": text})
    return entries


def get_subtitle_for_time(srt_entries, t: float) -> str:
    """Find the subtitle text active at time t (seconds)."""
    for entry in srt_entries:
        if entry["start"] <= t <= entry["end"]:
            return entry["text"]
    return ""


def overlay_subtitle(img, text: str):
    """
    Overlays text on the bottom center of the image.
    Wraps text to fit the image width and draws a semi-transparent black rectangle background.
    """
    h, w, c = img.shape
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.5, w / 1000.0)  # dynamically adjust font size to width
    thickness = max(1, int(w / 800.0))
    color = (255, 255, 255)  # white
    
    # Split text into multiple lines if too long
    words = text.split(" ")
    lines = []
    current_line = ""
    max_text_width = int(w * 0.85)  # text should occupy at most 85% of width
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        (text_w, text_h), baseline = cv2.getTextSize(test_line, font, font_scale, thickness)
        if text_w > max_text_width:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
        
    # Calculate vertical height of the text block
    line_height = 0
    line_widths = []
    for line in lines:
        (text_w, text_h), baseline = cv2.getTextSize(line, font, font_scale, thickness)
        line_height = max(line_height, text_h + baseline)
        line_widths.append(text_w)
        
    padding = 10
    total_text_h = len(lines) * (line_height + 5) - 5
    box_y1 = h - total_text_h - 2 * padding - 20  # 20px margin from bottom
    box_y2 = h - 20
    box_x1 = int(w * 0.05)
    box_x2 = int(w * 0.95)
    
    # Ensure coordinates are within image
    box_y1 = max(0, box_y1)
    box_y2 = min(h, box_y2)
    
    # Draw translucent black rectangle
    overlay = img.copy()
    cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), (0, 0, 0), -1)
    alpha = 0.6
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    
    # Draw text
    y_offset = box_y1 + padding + line_height
    for idx, line in enumerate(lines):
        text_w = line_widths[idx]
        x_pos = int((w - text_w) / 2)  # center horizontally
        cv2.putText(img, line, (x_pos, y_offset), font, font_scale, color, thickness, cv2.LINE_AA)
        y_offset += line_height + 5
        
    return img


def extract_frames(video_path: str, interval: float, output_dir: str, srt_entries: list):
    """
    Extracts frames from video_path at every `interval` seconds.
    Overlays the matching subtitle text if available.
    Saves compressed JPEG images to output_dir.
    Names files as {seconds}s_{sanitized_subtitle}.jpg.
    Returns list of generated image metadata.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Could not open video file: {video_path}")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    # Handle case where duration could be 0 or small
    if duration <= 0:
        # Try getting video length via other properties
        duration = 10.0  # fallback for dummy video if needed
        
    # Determine the timestamps we want to capture
    timestamps = []
    t = 0.0
    while t <= duration:
        timestamps.append(t)
        t += interval
        
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    for target_t in timestamps:
        # Seek to the frame
        frame_idx = int(target_t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            # Fallback to direct time-based seek if index seek failed
            cap.set(cv2.CAP_PROP_POS_MSEC, target_t * 1000.0)
            ret, frame = cap.read()
            if not ret:
                continue
                
        # Find matching subtitle
        subtitle_text = get_subtitle_for_time(srt_entries, target_t)
        
        # Draw subtitle text on frame if it exists
        if subtitle_text:
            frame = overlay_subtitle(frame, subtitle_text)
            
        # Sanitize subtitle for filename
        sanitized_sub = re.sub(r"[^\w\s-]", "", subtitle_text).strip()
        sanitized_sub = re.sub(r"\s+", "_", sanitized_sub)
        sanitized_sub = sanitized_sub[:50]  # Limit length for filesystem safety
        
        # Save filename
        if sanitized_sub:
            filename = f"{target_t:.2f}s_{sanitized_sub}.jpg"
        else:
            filename = f"{target_t:.2f}s_no_subtitle.jpg"
            
        output_path = os.path.join(output_dir, filename)
        
        # Save as JPEG with compression (quality 80)
        cv2.imwrite(output_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        
        generated_files.append({
            "timestamp": target_t,
            "filename": filename,
            "subtitle": subtitle_text,
            "path": output_path
        })
        
    cap.release()
    return generated_files
