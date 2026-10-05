import os
import hashlib
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger("audio_generator")

if os.environ.get("VERCEL"):
    AUDIO_DIR = "/tmp/data/audio"
else:
    AUDIO_DIR = os.path.join("data", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Edge-TTS voice mapping (Giọng Tiếng Việt chuẩn Neural chất lượng cao)
VOICES = {
    "nữ": "vi-VN-HoaiMyNeural",
    "female": "vi-VN-HoaiMyNeural",
    "nu": "vi-VN-HoaiMyNeural",
    "nam": "vi-VN-NamMinhNeural",
    "male": "vi-VN-NamMinhNeural"
}

def get_voice_code(voice_type: str) -> str:
    vt = (voice_type or "female").lower().strip()
    return VOICES.get(vt, "vi-VN-HoaiMyNeural")

async def generate_tts_file(text: str, voice_type: str = "female", custom_id: Optional[str] = None) -> Optional[str]:
    """
    Tạo file MP3 từ chính xác văn bản lời kể bằng edge-tts (hoặc gTTS nếu edge-tts lỗi).
    Tên file BẮT BUỘC gắn liền với hash MD5 của nội dung text và giọng đọc,
    đảm bảo 100% file âm thanh tương ứng đúng nội dung câu chuyện, không bao giờ đọc nhầm văn bản khác.
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()
    norm_voice = "male" if voice_type.lower() in ["male", "nam"] else "female"
    voice_name = get_voice_code(norm_voice)

    # Hash nội dung văn bản + giọng đọc để đảm bảo độc nhất vô nhị
    text_hash = hashlib.md5(f"{clean_text}_{norm_voice}".encode('utf-8')).hexdigest()[:16]
    
    if custom_id:
        clean_cid = "".join(c for c in custom_id if c.isalnum() or c in "_-")
        filename = f"{clean_cid}_{norm_voice}_{text_hash}.mp3"
    else:
        filename = f"tts_{norm_voice}_{text_hash}.mp3"

    file_path = os.path.join(AUDIO_DIR, filename)
    web_url = f"/static/audio/{filename}"

    # Nếu file đã tồn tại và kích thước hợp lệ, tái sử dụng (vì cùng text_hash = đúng chính xác nội dung đó)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 500:
        logger.info(f"Âm thanh chuẩn nội dung đã có sẵn: {web_url}")
        return web_url

    # Thử nghiệm 1: edge-tts (Microsoft Edge Neural TTS - giọng đọc tự nhiên, chuẩn cảm xúc nhất)
    try:
        import edge_tts
        logger.info(f"Đang tạo giọng đọc AI cho câu chuyện: '{clean_text[:40]}...' ({voice_name})")
        communicate = edge_tts.Communicate(clean_text, voice_name)
        await communicate.save(file_path)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 500:
            logger.info(f"Tạo âm thanh edge-tts thành công: {web_url}")
            return web_url
    except Exception as e:
        logger.warning(f"edge-tts không khả dụng ({str(e)}), chuyển sang gTTS...")

    # Thử nghiệm 2: gTTS (Google Text-to-Speech dự phòng)
    try:
        from gtts import gTTS
        logger.info("Đang tạo giọng đọc dự phòng với gTTS...")
        
        def run_gtts():
            tts = gTTS(text=clean_text, lang='vi', slow=False)
            tts.save(file_path)

        await asyncio.to_thread(run_gtts)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 500:
            logger.info(f"Tạo âm thanh gTTS thành công: {web_url}")
            return web_url
    except Exception as e:
        logger.error(f"Lỗi cả edge-tts và gTTS khi sinh âm thanh: {str(e)}")

    return None

async def attach_audio_to_story(story_data: Dict[str, Any], voice_type: str = "female") -> Dict[str, Any]:
    """
    Sinh file giọng đọc audio cho từng phân cảnh trong câu chuyện.
    ĐẢM BẢO đọc chính xác 100% nội dung lời kể (narration) của từng cảnh đã tạo ra.
    """
    story_id = story_data.get("id") or "story"
    scenes = story_data.get("scenes", [])

    if not scenes:
        return story_data

    logger.info(f"Bắt đầu sinh giọng đọc AI cho {len(scenes)} phân cảnh của câu chuyện ID: {story_id}...")

    for idx, scene in enumerate(scenes):
        narration = (scene.get("narration") or scene.get("description") or "").strip()
        if narration:
            custom_id = f"story_{story_id}_scene_{idx+1}"
            audio_url = await generate_tts_file(
                text=narration,
                voice_type=voice_type,
                custom_id=custom_id
            )
            if audio_url:
                scene["audio_url"] = audio_url
                logger.info(f"Đã gắn giọng đọc chính xác cho Cảnh {idx+1}: {audio_url}")
        else:
            logger.warning(f"Cảnh {idx+1} không có văn bản lời kể, bỏ qua tạo audio.")

    return story_data
