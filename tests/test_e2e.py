import time
import os

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["mock_mode"] is True

def test_process_flow(client):
    # Submit job
    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "interval": 2.0,
        "lang": "pt"
    }
    response = client.post("/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]
    
    # Poll status until completed
    max_retries = 20
    completed = False
    status_data = None
    
    for _ in range(max_retries):
        status_response = client.get(f"/status/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        if status_data["status"] in ["completed", "failed"]:
            completed = True
            break
        time.sleep(0.5)
        
    assert completed is True, f"Job did not complete in time. Last status: {status_data}"
    assert status_data["status"] == "completed", f"Job failed with message: {status_data['message']}"
    assert status_data["progress"] == 100.0
    assert status_data["zip_url"] == f"/outputs/{job_id}/bundle.zip"
    
    frames = status_data["frames"]
    assert len(frames) > 0
    
    # Check that metadata matches expected frame structures
    for frame in frames:
        assert "timestamp" in frame
        assert "filename" in frame
        assert "subtitle" in frame
        assert "url" in frame
        assert frame["url"].startswith(f"/outputs/{job_id}/frames/")
        
        # Verify the actual files exist in the project directory
        # The base dir path relative to the test runner is ../outputs/job_id/frames/filename
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_file_path = os.path.join(base_dir, "outputs", job_id, "frames", frame["filename"])
        assert os.path.exists(output_file_path), f"File {output_file_path} was not found on disk"
        
    # Verify that bundle.zip is created
    zip_file_path = os.path.join(base_dir, "outputs", job_id, "bundle.zip")
    assert os.path.exists(zip_file_path), f"ZIP file {zip_file_path} was not found on disk"

