import os
import uuid
import json
import zipfile
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.downloader import download_video, download_subtitles
from app.processor import parse_srt, extract_frames

app = FastAPI(title="YouTube Frame Extractor")

# Resolve directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Mount static files for outputs
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# In-memory jobs database
JOBS = {}

class ProcessRequest(BaseModel):
    url: str
    interval: float = 1.0
    lang: str = "pt"

def create_zip(source_dir: str, zip_path: str):
    """Zips the contents of source_dir, excluding the zip file itself and the raw video."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                filepath = os.path.join(root, file)
                # Skip the zip file and raw video if it still exists
                if file.endswith(".zip") or file.endswith(".mp4"):
                    continue
                # Calculate relative path
                relpath = os.path.relpath(filepath, source_dir)
                zipf.write(filepath, relpath)

def process_video_job(job_id: str, url: str, interval: float, lang: str):
    job = JOBS[job_id]
    job_dir = os.path.join(OUTPUTS_DIR, job_id)
    frames_dir = os.path.join(job_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    try:
        # Download video
        job["status"] = "downloading"
        job["message"] = "Baixando o vídeo do YouTube..."
        job["progress"] = 15.0
        video_path = download_video(url, job_dir)
        
        # Download subtitles
        job["message"] = "Buscando legendas..."
        job["progress"] = 35.0
        srt_path = None
        
        try:
            srt_path = download_subtitles(url, lang, job_dir)
        except Exception:
            # Fallback to English/Portuguese if requested language is unavailable
            fallback_lang = "en" if lang != "en" else "pt"
            try:
                srt_path = download_subtitles(url, fallback_lang, job_dir)
                lang = fallback_lang
            except Exception:
                # No subtitles found
                pass
                
        # Parse subtitles
        srt_entries = []
        if srt_path:
            job["message"] = "Processando as legendas..."
            job["progress"] = 50.0
            srt_entries = parse_srt(srt_path)
        else:
            job["message"] = "Nenhuma legenda encontrada. Continuando sem legendas..."
            job["progress"] = 50.0
            
        # Extract frames & draw subtitles
        job["message"] = "Extraindo frames e desenhando legendas..."
        job["progress"] = 60.0
        generated_frames = extract_frames(video_path, interval, frames_dir, srt_entries)
        
        # Clean up the downloaded video file to free up space
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass
                
        job["message"] = "Empacotando os frames..."
        job["progress"] = 85.0
        
        # Generate metadata.json
        metadata_path = os.path.join(job_dir, "metadata.json")
        metadata = {
            "url": url,
            "interval": interval,
            "language": lang,
            "frames": [
                {
                    "timestamp": f["timestamp"],
                    "filename": f["filename"],
                    "subtitle": f["subtitle"],
                    "url": f"/outputs/{job_id}/frames/{f['filename']}"
                }
                for f in generated_frames
            ]
        }
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        # Zip all outputs
        zip_path = os.path.join(job_dir, "bundle.zip")
        create_zip(job_dir, zip_path)
        
        # Update job database
        job["status"] = "completed"
        job["message"] = "Processamento concluído com sucesso!"
        job["progress"] = 100.0
        job["zip_url"] = f"/outputs/{job_id}/bundle.zip"
        job["frames"] = metadata["frames"]
        
    except Exception as e:
        job["status"] = "failed"
        job["message"] = f"Erro: {str(e)}"
        job["progress"] = 100.0


@app.get("/health")
def health_check():
    return {"status": "ok", "mock_mode": os.environ.get("YOUTUBE_FRAME_EXTRACTOR_MOCK") == "1"}


@app.post("/process")
def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "status": "queued",
        "message": "Enfileirando trabalho...",
        "progress": 0.0,
        "zip_url": None,
        "frames": []
    }
    background_tasks.add_task(
        process_video_job,
        job_id,
        request.url,
        request.interval,
        request.lang
    )
    return {"job_id": job_id}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS[job_id]


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Frame & Subtitle Extractor</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #131b2e;
            --accent-purple: #7c3aed;
            --accent-blue: #2563eb;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --glass-bg: rgba(19, 27, 46, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(124, 58, 237, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(37, 99, 23b, 0.15) 0%, transparent 40%);
            background-attachment: fixed;
        }

        header {
            width: 100%;
            max-width: 1200px;
            padding: 2.5rem 1.5rem;
            text-align: center;
        }

        header h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #a78bfa 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
        }

        header p {
            color: var(--text-muted);
            font-size: 1.1rem;
            font-weight: 400;
        }

        main {
            width: 100%;
            max-width: 800px;
            padding: 0 1.5rem 3rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        .card {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 2.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            box-shadow: 0 15px 35px rgba(124, 58, 237, 0.1);
        }

        .form-group {
            margin-bottom: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #c084fc;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        input, select {
            width: 100%;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 0.85rem 1rem;
            color: var(--text-main);
            font-size: 1rem;
            outline: none;
            transition: all 0.2s ease;
        }

        input:focus, select:focus {
            border-color: var(--accent-purple);
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.25);
            background: rgba(15, 23, 42, 0.9);
        }

        button.btn-primary {
            width: 100%;
            background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%);
            border: none;
            border-radius: 12px;
            padding: 1rem;
            color: white;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
        }

        button.btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
            filter: brightness(1.1);
        }

        button.btn-primary:active {
            transform: translateY(0);
        }

        button.btn-primary:disabled {
            background: #475569;
            box-shadow: none;
            cursor: not-allowed;
            transform: none;
            filter: none;
        }

        .progress-container {
            display: none;
            flex-direction: column;
            gap: 1rem;
        }

        .progress-text {
            display: flex;
            justify-content: space-between;
            font-size: 0.95rem;
        }

        .progress-msg {
            color: var(--text-main);
            font-weight: 600;
        }

        .progress-pct {
            color: var(--text-muted);
        }

        .progress-bar-bg {
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--accent-purple), var(--accent-blue));
            border-radius: 5px;
            transition: width 0.3s ease;
        }

        .gallery-container {
            display: none;
            flex-direction: column;
            gap: 1.5rem;
            margin-top: 1rem;
        }

        .gallery-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .gallery-header h2 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
        }

        .btn-download {
            background: #10b981;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            font-size: 0.95rem;
        }

        .btn-download:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(16, 185, 129, 0.5);
            background: #059669;
        }

        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 1.5rem;
        }

        .gallery-item {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .gallery-item:hover {
            transform: translateY(-5px);
            border-color: rgba(124, 58, 237, 0.4);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        .gallery-img-container {
            position: relative;
            width: 100%;
            padding-top: 56.25%; /* 16:9 Aspect Ratio */
            background: #000;
        }

        .gallery-img-container img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            cursor: pointer;
        }

        .gallery-info {
            padding: 1rem;
        }

        .gallery-time {
            font-size: 0.75rem;
            font-weight: 700;
            color: #a78bfa;
            margin-bottom: 0.25rem;
        }

        .gallery-sub {
            font-size: 0.85rem;
            color: var(--text-main);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* Lightbox modal for preview */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(11, 15, 25, 0.95);
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }

        .modal-content {
            max-width: 90%;
            max-height: 85%;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .modal-content img {
            width: 100%;
            height: auto;
            max-height: 80vh;
            display: block;
            object-fit: contain;
        }

        .modal-caption {
            padding: 1rem;
            background: var(--bg-secondary);
            text-align: center;
            color: var(--text-main);
            font-weight: 600;
        }

        .modal-close {
            position: absolute;
            top: 1.5rem;
            right: 2rem;
            color: white;
            font-size: 2.5rem;
            font-weight: 300;
            cursor: pointer;
            transition: color 0.2s ease;
        }
        .modal-close:hover {
            color: var(--accent-purple);
        }

        footer {
            margin-top: auto;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            text-align: center;
            width: 100%;
            max-width: 1200px;
            border-top: 1px solid var(--glass-border);
        }

        /* Spinner */
        .spinner {
            border: 3px solid rgba(255,255,255,0.1);
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border-left-color: white;
            animation: spin 1s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Responsive Grid adjustments */
        @media(max-width: 600px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            header h1 {
                font-size: 2.2rem;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>YouTube Frame Extractor</h1>
        <p>Extraia frames com legendas embutidas com precisão</p>
    </header>

    <main>
        <div class="card">
            <div class="form-group">
                <label for="video-url">URL do Vídeo do YouTube</label>
                <input type="text" id="video-url" placeholder="https://www.youtube.com/watch?v=..." value="https://www.youtube.com/watch?v=dQw4w9WgXcQ">
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="interval">Intervalo de extração (segundos)</label>
                    <input type="number" id="interval" min="0.1" step="0.1" value="1.0">
                </div>
                <div class="form-group">
                    <label for="lang">Idioma das Legendas</label>
                    <select id="lang">
                        <option value="pt">Português</option>
                        <option value="en">Inglês</option>
                    </select>
                </div>
            </div>

            <button id="btn-process" class="btn-primary" onclick="startProcess()">
                <span>Processar Vídeo</span>
            </button>
        </div>

        <div id="card-progress" class="card progress-container">
            <div class="progress-text">
                <span id="progress-message" class="progress-msg">Iniciando...</span>
                <span id="progress-percentage" class="progress-pct">0%</span>
            </div>
            <div class="progress-bar-bg">
                <div id="progress-bar-fill" class="progress-bar-fill"></div>
            </div>
        </div>

        <div id="gallery-wrapper" class="gallery-container">
            <div class="gallery-header">
                <h2>Frames Extraídos</h2>
                <a id="btn-zip-download" href="#" class="btn-download" download>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Baixar Pacote ZIP
                </a>
            </div>
            <div id="gallery-grid" class="gallery-grid"></div>
        </div>
    </main>

    <!-- Lightbox Modal -->
    <div id="lightbox" class="modal" onclick="closeLightbox()">
        <span class="modal-close" onclick="closeLightbox()">&times;</span>
        <div class="modal-content" onclick="event.stopPropagation()">
            <img id="lightbox-img" src="" alt="Frame Preview">
            <div id="lightbox-caption" class="modal-caption"></div>
        </div>
    </div>

    <footer>
        <p>&copy; 2026 YouTube Frame & Subtitle Extractor</p>
    </footer>

    <script>
        let pollInterval = null;

        function startProcess() {
            const url = document.getElementById("video-url").value.trim();
            const interval = parseFloat(document.getElementById("interval").value);
            const lang = document.getElementById("lang").value;

            if (!url) {
                alert("Por favor, insira uma URL de vídeo válida.");
                return;
            }

            const btn = document.getElementById("btn-process");
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> <span>Processando...</span>';

            // Show progress block
            const progressCard = document.getElementById("card-progress");
            progressCard.style.display = "flex";
            updateProgress("Iniciando processo...", 5);

            // Hide previous gallery
            document.getElementById("gallery-wrapper").style.display = "none";
            document.getElementById("gallery-grid").innerHTML = "";

            fetch("/process", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url, interval, lang })
            })
            .then(res => {
                if (!res.ok) throw new Error("Erro ao iniciar processamento.");
                return res.json();
            })
            .then(data => {
                const jobId = data.job_id;
                // Start polling
                pollInterval = setInterval(() => checkStatus(jobId), 1000);
            })
            .catch(err => {
                alert(err.message);
                resetButton();
                progressCard.style.display = "none";
            });
        }

        function checkStatus(jobId) {
            fetch(`/status/${jobId}`)
            .then(res => res.json())
            .then(data => {
                updateProgress(data.message, data.progress);

                if (data.status === "completed") {
                    clearInterval(pollInterval);
                    showGallery(data.frames, data.zip_url);
                    resetButton();
                } else if (data.status === "failed") {
                    clearInterval(pollInterval);
                    alert("O processamento falhou: " + data.message);
                    resetButton();
                }
            })
            .catch(err => {
                console.error("Erro no polling:", err);
            });
        }

        function updateProgress(message, percentage) {
            document.getElementById("progress-message").innerText = message;
            document.getElementById("progress-percentage").innerText = Math.round(percentage) + "%";
            document.getElementById("progress-bar-fill").style.width = percentage + "%";
        }

        function resetButton() {
            const btn = document.getElementById("btn-process");
            btn.disabled = false;
            btn.innerHTML = '<span>Processar Vídeo</span>';
        }

        function showGallery(frames, zipUrl) {
            const grid = document.getElementById("gallery-grid");
            grid.innerHTML = "";

            if (!frames || frames.length === 0) {
                grid.innerHTML = "<p style='grid-column: 1/-1; text-align: center; color: var(--text-muted);'>Nenhum frame extraído.</p>";
            } else {
                frames.forEach(frame => {
                    const item = document.createElement("div");
                    item.className = "gallery-item";
                    
                    const capText = frame.subtitle ? frame.subtitle : "Sem legenda";
                    
                    item.innerHTML = `
                        <div class="gallery-img-container">
                            <img src="${frame.url}" alt="${capText}" onclick="openLightbox('${frame.url}', '${capText.replace(/'/g, "\\'")}')">
                        </div>
                        <div class="gallery-info">
                            <div class="gallery-time">${frame.timestamp.toFixed(2)}s</div>
                            <div class="gallery-sub" title="${capText}">${capText}</div>
                        </div>
                    `;
                    grid.appendChild(item);
                });
            }

            document.getElementById("btn-zip-download").href = zipUrl;
            document.getElementById("gallery-wrapper").style.display = "flex";
            
            // Smooth scroll to gallery
            document.getElementById("gallery-wrapper").scrollIntoView({ behavior: 'smooth' });
        }

        function openLightbox(url, subtitle) {
            document.getElementById("lightbox-img").src = url;
            document.getElementById("lightbox-caption").innerText = subtitle;
            document.getElementById("lightbox").style.display = "flex";
        }

        function closeLightbox() {
            document.getElementById("lightbox").style.display = "none";
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="info")
