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

def get_mock_storyboard(user_input: str, age_group: str, art_style: str) -> Dict[str, Any]:
    """
    Kịch bản mẫu dự phòng khi API chưa được cấu hình hoặc gặp sự cố.
    """
    return {
        "title": f"Hành Trình Thú Vị: {user_input[:25]}...",
        "theme": "Tình bạn và tinh thần giúp đỡ lẫn nhau",
        "characters": [
            {
                "name": "Mèo Bông",
                "appearance": "Chú mèo nhỏ lông trắng muốt, đôi mắt xanh ngọc bích lấp lánh, đeo chiếc nơ đỏ ở cổ"
            },
            {
                "name": "Thỏ Ngọc",
                "appearance": "Chú thỏ đôi tai dài đáng yêu, mang chiếc balo màu vàng nhỏ nhắn"
            }
        ],
        "setting": "Khu rừng xanh thẫm xinh đẹp rộn rã tiếng chim hót",
        "story_summary": f"Một ngày nọ, Mèo Bông và Thỏ Ngọc cùng nhau bước vào hành trình phiêu lưu. Qua ý tưởng '{user_input}', hai bạn nhỏ đã cùng nhau học được bài học sẻ chia quý giá.",
        "moral": "Hãy luôn sẵn lòng mở lòng giúp đỡ bạn bè xung quanh.",
        "storyboard": [
            "Mèo Bông và Thỏ Ngọc gặp nhau ở bìa rừng và quyết định khởi hành.",
            "Hai bạn gặp một thử thách nhỏ trên đường đi và cùng nhau vượt qua.",
            "Cuối cùng cả hai tìm thấy niềm vui và trao nhau nụ cười ấm áp."
        ]
    }
