import os
import hashlib
import logging
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger("audio_generator")

AUDIO_DIR = os.path.join("data", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Edge-TTS voice mapping
VOICES = {
    "nữ": "vi-VN-HoaiMyNeural",
    "nam": "vi-VN-NamMinhNeural"
}

async def generate_tts_file(text: str, voice_type: str = "nữ", custom_id: Optional[str] = None) -> Optional[str]:
    """
    Tạo file MP3 từ văn bản bằng edge-tts (hoặc gTTS nếu edge-tts thất bại).
    Trả về relative path cho Web Client: /static/audio/<filename>.mp3
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()
    
    # Tạo tên file duy nhất dựa trên md5 của text + voice_type hoặc custom_id
    if custom_id:
        filename = f"{custom_id}.mp3"
    else:
        text_hash = hashlib.md5(f"{clean_text}_{voice_type}".encode('utf-8')).hexdigest()[:12]
        filename = f"narration_{text_hash}.mp3"

    file_path = os.path.join(AUDIO_DIR, filename)
    web_url = f"/static/audio/{filename}"

    # Nếu file đã tồn tại và không rỗng, trả về luôn để tiết kiệm tài nguyên
    if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
        logger.info(f"Âm thanh đã có sẵn: {web_url}")
        return web_url

    voice_name = VOICES.get(voice_type.lower(), "vi-VN-HoaiMyNeural")

    # Thử nghiệm 1: edge-tts (Microsoft Edge Neural TTS - chất lượng cao nhất)
    try:
        import edge_tts
        logger.info(f"Đang tạo giọng đọc với edge-tts ({voice_name})...")
        communicate = edge_tts.Communicate(clean_text, voice_name)
        await communicate.save(file_path)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
            logger.info(f"Tạo âm thanh edge-tts thành công: {web_url}")
            return web_url
    except Exception as e:
        logger.warning(f"edge-tts không khả dụng hoặc lỗi: {str(e)}. Tiến hành thử gTTS...")

    # Thử nghiệm 2: gTTS (Google Text-to-Speech)
    try:
        from gtts import gTTS
        logger.info("Đang tạo giọng đọc với gTTS (Google TTS)...")
        
        def run_gtts():
            tts = gTTS(text=clean_text, lang='vi', slow=False)
            tts.save(file_path)

        await asyncio.to_thread(run_gtts)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
            logger.info(f"Tạo âm thanh gTTS thành công: {web_url}")
            return web_url
    except Exception as e:
        logger.error(f"Lỗi cả edge-tts và gTTS khi sinh âm thanh: {str(e)}")

    return None

async def attach_audio_to_story(story_data: Dict[str, Any], voice_type: str = "nữ") -> Dict[str, Any]:
    """
    Sinh file giọng đọc audio cho từng phân cảnh trong câu chuyện và đính kèm vào story_data.
    """
    story_id = story_data.get("id", "temp")
    scenes = story_data.get("scenes", [])

    if not scenes:
        return story_data

    logger.info(f"Bắt đầu sinh giọng đọc AI cho {len(scenes)} phân cảnh...")

    for idx, scene in enumerate(scenes):
        narration = scene.get("narration") or scene.get("description") or ""
        if narration:
            custom_id = f"story_{story_id}_scene_{idx+1}_{voice_type}"
            audio_url = await generate_tts_file(text=narration, voice_type=voice_type, custom_id=custom_id)
            if audio_url:
                scene["audio_url"] = audio_url

    return story_data
