import logging
import uuid
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
    is_private: Optional[bool] = Field(False, description="Cờ riêng tư (Truyện của tôi)")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Văn bản cần đọc")
    voice: Optional[str] = Field("female", description="Giọng đọc: female hoặc male")

class SetupPasswordRequest(BaseModel):
    password: str = Field(..., min_length=4, description="Mật khẩu bảo vệ mới")

class VerifyPasswordRequest(BaseModel):
    password: str = Field(..., description="Mật khẩu cần xác minh")

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Mật khẩu cũ")
    new_password: str = Field(..., min_length=4, description="Mật khẩu mới")

# ================= AUTH & BẢO MẬT =================
@router.get("/auth/status")
async def get_auth_status() -> Dict[str, Any]:
    """
    Kiểm tra trạng thái mật khẩu bảo vệ đã được thiết lập hay chưa.
    """
    is_set = storage_service.is_password_set()
    return {
        "success": True,
        "has_password": is_set
    }

@router.post("/auth/setup")
async def setup_password(request: SetupPasswordRequest) -> Dict[str, Any]:
    """
    Thiết lập mật khẩu bảo vệ lần đầu cho Truyện của tôi.
    """
    if storage_service.is_password_set():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu bảo vệ đã được thiết lập trước đó. Vui lòng sử dụng tính năng đổi mật khẩu."
        )
    success = storage_service.set_password(request.password)
    if not success:
        raise HTTPException(status_code=500, detail="Không thể lưu mật khẩu.")
    return {
        "success": True,
        "message": "Thiết lập mật khẩu bảo vệ thành công!"
    }

@router.post("/auth/verify")
async def verify_password(request: VerifyPasswordRequest) -> Dict[str, Any]:
    """
    Xác minh mật khẩu để mở khóa không gian riêng tư.
    """
    if not storage_service.is_password_set():
        return {
            "success": False,
            "has_password": False,
            "message": "Chưa thiết lập mật khẩu bảo vệ!"
        }
    
    is_valid = storage_service.verify_password(request.password)
    if not is_valid:
        return {
            "success": False,
            "has_password": True,
            "message": "Mật khẩu không chính xác. Vui lòng thử lại!"
        }
    
    return {
        "success": True,
        "has_password": True,
        "message": "Mở khóa thành công!"
    }

@router.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest) -> Dict[str, Any]:
    """
    Đổi mật khẩu bảo vệ khi đã biết mật khẩu cũ.
    """
    success, msg = storage_service.change_password(request.old_password, request.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {
        "success": True,
        "message": msg
    }

# ================= QUẢN LÝ TRUYỆN =================
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
        logger.info(f"Bắt đầu kích hoạt LangGraph cho ý tưởng: '{request.prompt}' (Riêng tư: {request.is_private})")
        
        final_state = await story_graph_app.ainvoke(initial_state)

        storyboard = final_state.get("storyboard", {})
        scenes = final_state.get("scenes", [])
        evaluation = final_state.get("evaluation", {})

        story_id = str(uuid.uuid4())[:8]
        story_payload = {
            "id": story_id,
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

        # Sinh giọng đọc AI cho tất cả các cảnh đúng theo lời kể của từng cảnh
        voice_type = request.voice or "female"
        story_payload = await attach_audio_to_story(story_payload, voice_type=voice_type)

        # Tự động lưu vào lịch sử Thư viện truyện hoặc Truyện của tôi
        saved_record = storage_service.save_story(
            story_data=story_payload,
            user_input=request.prompt.strip(),
            age=request.age or "Lớp 1 - 2",
            style=request.style or "Hoạt hình",
            is_private=bool(request.is_private)
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
    API lấy danh sách các câu chuyện công khai trong Thư viện chung.
    """
    stories = storage_service.get_public_stories()
    return {
        "success": True,
        "count": len(stories),
        "data": stories
    }

@router.get("/my-stories")
async def get_my_stories() -> Dict[str, Any]:
    """
    API lấy danh sách các câu chuyện riêng tư (Truyện của tôi).
    """
    stories = storage_service.get_private_stories()
    return {
        "success": True,
        "count": len(stories),
        "data": stories
    }

@router.post("/toggle-privacy/{story_id}")
async def toggle_story_privacy(story_id: str) -> Dict[str, Any]:
    """
    API chuyển đổi trạng thái riêng tư <-> công khai của một câu chuyện.
    """
    updated_story = storage_service.toggle_story_privacy(story_id)
    if not updated_story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy câu chuyện để cập nhật quyền riêng tư!"
        )
    return {
        "success": True,
        "is_private": updated_story.get("is_private", False),
        "message": "Đã chuyển sang Riêng tư 🔒" if updated_story.get("is_private") else "Đã chuyển sang Công khai 🌐",
        "data": updated_story
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
    API xóa một câu chuyện.
    """
    success = storage_service.delete_story(story_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không thể xóa hoặc không tìm thấy câu chuyện!"
        )
    return {
        "success": True,
        "message": "Đã xóa câu chuyện thành công."
    }
