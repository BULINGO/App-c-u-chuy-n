import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from graph.story_graph import story_graph_app
from graph.state import StoryState
from backend.services.storage import storage_service
from module.audio_generator import attach_audio_to_story, generate_tts_file

logger = logging.getLogger("story_route")

router = APIRouter(prefix="/api/story", tags=["Story AI Agentic"])

class CreateStoryRequest(BaseModel):
    prompt: str = Field(..., description="Ý tưởng câu chuyện của người dùng", example="Chú mèo con dũng cảm giúp bác rùa sang đường")
    age: Optional[str] = Field("Lớp 1 - 2", description="Nhóm lứa tuổi học sinh")
    style: Optional[str] = Field("Hoạt hình", description="Phong cách đồ họa câu chuyện")
    voice: Optional[str] = Field("female", description="Giọng đọc (female: Nữ, male: Nam)")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Văn bản cần đọc")
    voice: Optional[str] = Field("female", description="Giọng đọc: female hoặc male")

@router.post("/create")
async def create_story(request: CreateStoryRequest) -> Dict[str, Any]:
    """
    API Endpoint chính: Tiếp nhận yêu cầu, kích hoạt LangGraph điều phối các AI Agent,
    tự động sinh giọng đọc AI cho các cảnh, trả về kết quả và lưu vào Lịch sử.
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ý tưởng câu chuyện không được để trống!"
        )

    initial_state: StoryState = {
        "user_input": request.prompt.strip(),
        "age_group": request.age or "Lớp 1 - 2",
        "art_style": request.style or "Hoạt hình",
        "storyboard": {},
        "scenes": [],
        "evaluation": {},
        "retry_count": 0,
        "status": "started",
        "error": None
    }

    try:
        logger.info(f"Bắt đầu kích hoạt LangGraph cho ý tưởng: '{request.prompt}'")
        
        final_state = await story_graph_app.ainvoke(initial_state)

        storyboard = final_state.get("storyboard", {})
        scenes = final_state.get("scenes", [])
        evaluation = final_state.get("evaluation", {})

        story_payload = {
            "title": storyboard.get("title", "Câu chuyện AI"),
            "theme": storyboard.get("theme", ""),
            "characters": storyboard.get("characters", []),
            "setting": storyboard.get("setting", ""),
            "story_summary": storyboard.get("story_summary", ""),
            "moral": storyboard.get("moral", ""),
            "storyboard": storyboard.get("storyboard", []),
            "scenes": scenes,
            "evaluation": evaluation
        }

        # Sinh giọng đọc AI cho tất cả các cảnh
        voice_type = request.voice or "female"
        story_payload = await attach_audio_to_story(story_payload, voice_type=voice_type)

        # Tự động lưu vào lịch sử Thư viện truyện
        saved_record = storage_service.save_story(
            story_data=story_payload,
            user_input=request.prompt.strip(),
            age=request.age or "Lớp 1 - 2",
            style=request.style or "Hoạt hình"
        )

        return {
            "success": True,
            "data": saved_record
        }

    except Exception as e:
        logger.error(f"Lỗi khi xử lý LangGraph: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Hệ thống gặp sự cố khi xử lý AI: {str(e)}"
        }

@router.post("/tts")
async def generate_tts(request: TTSRequest) -> Dict[str, Any]:
    """
    API Endpoint sinh giọng đọc AI cho một văn bản tùy chỉnh.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Văn bản đọc không được rỗng!")
    
    audio_url = await generate_tts_file(request.text, voice_type=request.voice or "female")
    if audio_url:
        return {"success": True, "audio_url": audio_url}
    else:
        return {"success": False, "error": "Không thể tạo file âm thanh."}

@router.get("/history")

async def get_story_history() -> Dict[str, Any]:
    """
    API lấy danh sách lịch sử các câu chuyện đã tạo.
    """
    stories = storage_service.get_all_stories()
    return {
        "success": True,
        "count": len(stories),
        "data": stories
    }

@router.get("/detail/{story_id}")
async def get_story_detail(story_id: str) -> Dict[str, Any]:
    """
    API lấy thông tin chi tiết một câu chuyện theo ID.
    """
    story = storage_service.get_story_by_id(story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy câu chuyện!"
        )
    return {
        "success": True,
        "data": story
    }

@router.delete("/delete/{story_id}")
async def delete_story(story_id: str) -> Dict[str, Any]:
    """
    API xóa một câu chuyện khỏi Thư viện.
    """
    success = storage_service.delete_story(story_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không thể xóa hoặc không tìm thấy câu chuyện!"
        )
    return {
        "success": True,
        "message": "Đã xóa câu chuyện khỏi Thư viện thành công."
    }
