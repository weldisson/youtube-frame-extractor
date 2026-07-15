import os
import sys
import time
import socket
import subprocess
import base64
import pytest
import httpx

# Minimal 1-second MP4 video base64 string fallback
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

MOCK_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "mock_assets"))

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def generate_mock_assets():
    os.makedirs(MOCK_ASSETS_DIR, exist_ok=True)
    
    # 1. Write mock subtitles (SRT)
    srt_path = os.path.join(MOCK_ASSETS_DIR, "mock_subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(
            "1\n"
            "00:00:00,000 --> 00:00:02,000\n"
            "First subtitle: Hello World\n\n"
            "2\n"
            "00:00:02,000 --> 00:00:05,000\n"
            "Second subtitle: YouTube Frame Extractor\n"
        )
        
    # 2. Write mock subtitles (JSON)
    json_path = os.path.join(MOCK_ASSETS_DIR, "mock_subtitles.json")
    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([
            {"text": "First subtitle: Hello World", "start": 0.0, "duration": 2.0},
            {"text": "Second subtitle: YouTube Frame Extractor", "start": 2.0, "duration": 3.0}
        ], f)

    # 3. Write mock video (MP4)
    video_path = os.path.join(MOCK_ASSETS_DIR, "mock_video.mp4")
    try:
        import cv2
        import numpy as np
        fps = 1
        width, height = 320, 240
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        if not out.isOpened():
            raise RuntimeError("VideoWriter failed to open")
        for i in range(5):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.putText(frame, f"Frame {i+1}", (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            out.write(frame)
        out.release()
    except Exception:
        # Fallback to writing minimal MP4 bytes
        with open(video_path, "wb") as f:
            f.write(base64.b64decode(MINIMAL_MP4_BASE64))

@pytest.fixture(scope="session", autouse=True)
def app_server():
    generate_mock_assets()
    
    mock_mode = os.environ.get("YOUTUBE_FRAME_EXTRACTOR_MOCK")
    port = get_free_port()
    
    env = os.environ.copy()
    if mock_mode == "1":
        env["YOUTUBE_FRAME_EXTRACTOR_MOCK"] = "1"
    env["PORT"] = str(port)
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = os.path.pathsep.join([project_root, env.get("PYTHONPATH", "")])

    cmd = [sys.executable, "-m", "app.main"]
    
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    server_url = f"http://127.0.0.1:{port}"
    timeout = 10.0
    start_time = time.time()
    started = False
    
    while time.time() - start_time < timeout:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            raise RuntimeError(
                f"Server subprocess terminated prematurely with code {proc.returncode}.\n"
                f"stdout: {stdout.decode()}\n"
                f"stderr: {stderr.decode()}"
            )
        try:
            with httpx.Client() as client_check:
                response = client_check.get(f"{server_url}/health", timeout=1.0)
                if response.status_code == 200:
                    started = True
                    break
        except Exception:
            pass
        time.sleep(0.5)
        
    if not started:
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        raise RuntimeError(
            f"Server failed to start on port {port} within {timeout} seconds.\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )
        
    yield server_url
    
    proc.terminate()
    try:
        proc.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        proc.kill()

@pytest.fixture(scope="session")
def client(app_server):
    with httpx.Client(base_url=app_server) as c:
        yield c
