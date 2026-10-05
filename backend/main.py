import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes.story import router as story_router

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main_backend")

app = FastAPI(
    title="HARNESS AI AGENTIC - Backend API",
    description="Hệ thống AI Kể chuyện Tiểu học với LangGraph, OpenRouter và Qwen Image 3 Pro",
    version="1.0.0"
)

# Cấu hình CORS để Frontend có thể gửi request từ bất kỳ origin nào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Router câu chuyện (phải đứng TRƯỚC StaticFiles)
app.include_router(story_router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend FastAPI đang chạy bình thường."}

@app.get("/sp-du-thi")
async def get_sp_du_thi():
    if os.path.exists("SP dự thi.html"):
        return FileResponse("SP dự thi.html")
    return {"error": "File SP dự thi.html không tồn tại"}

# Phục vụ thư mục âm thanh static (cho giọng đọc TTS)
if os.environ.get("VERCEL"):
    audio_dir = "/tmp/data/audio"
else:
    audio_dir = os.path.join("data", "audio")
os.makedirs(audio_dir, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=audio_dir), name="audio_static")

# Phục vụ toàn bộ thư mục frontend (index.html, style.css, app.js) tại gốc '/'
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend_static")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
