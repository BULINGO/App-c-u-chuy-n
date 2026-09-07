import logging
from typing import Dict, Any
from backend.services.openrouter import openrouter_service
from module.prompts import DIRECTOR_PROMPT

logger = logging.getLogger("director_module")

async def generate_storyboard(
    user_input: str,
    age_group: str = "Lớp 1 - 2",
    art_style: str = "Hoạt hình"
) -> Dict[str, Any]:
    """
    Model Đạo diễn: Tiếp nhận ý tưởng người dùng và phân tích tạo Storyboard kịch bản.
    """
    user_prompt = (
        f"Ý tưởng câu chuyện: {user_input}\n"
        f"Đối tượng độc giả: {age_group}\n"
        f"Phong cách đồ họa: {art_style}\n"
        f"Hãy tạo kịch bản kịch bản Storyboard theo đúng định dạng JSON yêu cầu."
    )

    try:
        if openrouter_service.is_configured():
            result = await openrouter_service.chat_completion(
                prompt=user_prompt,
                system_prompt=DIRECTOR_PROMPT,
                json_output=True
            )
            return result
        else:
            logger.info("Chạy chế độ thử nghiệm kịch bản mẫu cho Director.")
            return get_mock_storyboard(user_input, age_group, art_style)
    except Exception as e:
        logger.error(f"Lỗi ở Director module: {str(e)}. Sử dụng kịch bản dự phòng.")
        return get_mock_storyboard(user_input, age_group, art_style)

import re

def extract_characters_from_input(user_input: str) -> list:
    """
    Trích xuất tên nhân vật chính xác từ ý tưởng của người dùng.
    """
    text = user_input.strip()
    text_lower = text.lower()
    
    ignored = {"Là", "Một", "Có", "Đang", "Và", "Với", "Cho", "Trong", "Không", "Tên", "Tạo", "Chuyện", "Về", "Bé", "Cậu", "Chú", "Cô", "Bạn", "Những", "Hãy", "Khi", "Được"}

    names = []
    
    # 1. Tìm từ sau các cụm như "tên là X", "tên X", "cậu bé X", "bạn X"
    match_name = re.search(r'(?:tên là|tên|cậu bé|bạn|chú|cô|bé)\s+([a-zA-Zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹđ]+)', text, re.IGNORECASE)
    if match_name:
        extracted = match_name.group(1).capitalize()
        if extracted not in ignored and len(extracted) > 1:
            names.append(extracted)

    # Special check cho Shin hoặc các tên nhân vật quen thuộc
    if "shin" in text_lower and "Shin" not in names:
        names.append("Shin")

    # 2. Tìm các từ viết hoa khác trong prompt
    capitalized = re.findall(r'\b[A-ZĐÊÔỨÁÀẢẠÃẮẰẲẶẴẤẦẨẬẪẾỀỂỆỄỐỒỔỘỖỨỪỬỰỮÍÌỈỊĨỨỪỬỰỮÓÒỎỌÕÚÙỦỤŨÝỲỶẠỸ]\w+\b', text)
    for cap in capitalized:
        if cap not in ignored and cap not in names and len(cap) > 1:
            names.append(cap)

    characters = []
    if names:
        for name in names[:2]:
            characters.append({
                "name": name,
                "appearance": f"Nhân vật {name} ngộ nghĩnh, thông minh với trang phục rực rỡ"
            })
    else:
        # Nếu trích xuất theo loài hoặc chức danh
        if "cậu bé" in text_lower or "bé" in text_lower:
            characters.append({"name": "Cậu bé", "appearance": "Chú bé nhỏ nhắn, rạng rỡ và thích khám phá"})
        elif "robot" in text_lower:
            characters.append({"name": "Robot", "appearance": "Chú Robot thân thiện với ánh mắt đèn LED sáng"})
        elif "mèo" in text_lower:
            characters.append({"name": "Chú Mèo", "appearance": "Chú mèo nhỏ lông mượt xinh xắn"})
        elif "chó" in text_lower:
            characters.append({"name": "Chú Chó", "appearance": "Chú chó nhỏ lanh lợi, vẫy đuôi vui vẻ"})
        else:
            characters.append({"name": "Bạn nhỏ", "appearance": "Nhân vật chính nhân hậu của câu chuyện"})

    return characters

def get_mock_storyboard(user_input: str, age_group: str, art_style: str) -> Dict[str, Any]:
    """
    Kịch bản mẫu động sinh theo đúng nhân vật và ý tưởng của người dùng.
    """
    chars = extract_characters_from_input(user_input)
    main_char_name = chars[0]["name"] if chars else "Bạn nhỏ"
    
    # Rút gọn ý tưởng người dùng làm tiêu đề
    clean_prompt = user_input.strip()
    title_text = (clean_prompt[:30] + "...") if len(clean_prompt) > 30 else clean_prompt

    return {
        "title": f"Câu Chuyện Của {main_char_name}: {title_text}",
        "theme": "Lòng nhân ái, sự chăm chỉ và tinh thần yêu thiên nhiên",
        "characters": chars,
        "setting": f"Bối cảnh sinh động phù hợp với câu chuyện '{clean_prompt}'",
        "story_summary": f"Câu chuyện xoay quanh {main_char_name} cùng những trải nghiệm ý nghĩa dựa trên ý tưởng '{clean_prompt}'. Qua đó, {main_char_name} đã mang lại niềm vui và học được bài học cuộc sống bổ ích.",
        "moral": "Hãy luôn chăm chỉ, yêu thương bạn bè và môi trường xung quanh.",
        "storyboard": [
            f"Giới thiệu {main_char_name} và bắt đầu hoạt động '{clean_prompt}'.",
            f"{main_char_name} kiên trì thực hiện công việc và nhận được sự hỗ trợ đáng yêu.",
            f"{main_char_name} hoàn thành công việc và gặt hái bài học giáo dục sâu sắc."
        ]
    }

