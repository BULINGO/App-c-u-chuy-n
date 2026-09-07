import logging
import json
from typing import Dict, Any, List
from backend.services.openrouter import openrouter_service
from module.prompts import SCENE_PLANNER_PROMPT, IMAGE_PROMPT_TEMPLATE

logger = logging.getLogger("scene_planner_module")

async def plan_scenes(storyboard: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Model 2 Chia Cảnh: Nhận Storyboard kịch bản và phân bổ thành danh sách các cảnh nhỏ.
    """
    user_prompt = (
        f"Hãy chia câu chuyện sau thành 3 đến 5 cảnh chi tiết:\n"
        f"Kịch bản Storyboard: {json.dumps(storyboard, ensure_ascii=False, indent=2)}\n"
    )

    try:
        if openrouter_service.is_configured():
            result = await openrouter_service.chat_completion(
                prompt=user_prompt,
                system_prompt=SCENE_PLANNER_PROMPT,
                json_output=True
            )
            scenes = result.get("scenes", [])
            if scenes:
                return scenes
            else:
                logger.warning("Không tìm thấy danh sách 'scenes' trong output LLM. Dùng mock scenes.")
                return get_mock_scenes(storyboard)
        else:
            return get_mock_scenes(storyboard)
    except Exception as e:
        logger.error(f"Lỗi ở Scene Planner module: {str(e)}. Sử dụng chia cảnh dự phòng.")
        return get_mock_scenes(storyboard)

def get_mock_scenes(storyboard: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Danh sách cảnh mẫu dự phòng khi chưa cấu hình OpenRouter API.
    """
    title = storyboard.get("title", "Câu chuyện đáng yêu")
    summary = storyboard.get("story_summary", "Một buổi sáng tươi đẹp")

    return [
        {
            "scene_id": 1,
            "description": "Giới thiệu nhân vật và khởi đầu buổi sáng tươi đẹp tại bìa rừng.",
            "characters": ["Mèo Bông", "Thỏ Ngọc"],
            "background": "Khu rừng rực rỡ nắng mai với hoa thảm cỏ xanh mướt.",
            "action": "Mèo Bông mỉm cười vẫy tay chào Thỏ Ngọc đang đeo chiếc balo vàng.",
            "narration": f"Chào mừng các bạn nhỏ đến với câu chuyện '{title}'. Hôm nay là một ngày nắng đẹp trời!",
            "image_prompt": IMAGE_PROMPT_TEMPLATE.format(
                characters_desc="Cute white cat with blue eyes and red ribbon next to a cute bunny with yellow backpack",
                action_desc="Waving hands cheerfully at each other under bright morning sunlight",
                background_desc="Beautiful enchanted forest with green grass and colorful blooming flowers"
            )
        },
        {
            "scene_id": 2,
            "description": "Hai bạn cùng nhau đối mặt với thử thách và hỗ trợ lẫn nhau.",
            "characters": ["Mèo Bông", "Thỏ Ngọc"],
            "background": "Cây cầu gỗ nhỏ bắc qua dòng stream trong veo.",
            "action": "Thỏ Ngọc cẩn thận chìa tay dắt Mèo Bông qua dòng suối nhỏ.",
            "narration": "Trên đường đi, cả hai cùng dắt tay nhau vượt qua dòng suối mát lành.",
            "image_prompt": IMAGE_PROMPT_TEMPLATE.format(
                characters_desc="Cute white cat holding hands with a cute bunny",
                action_desc="Crossing a small wooden bridge over a sparkling clear stream together carefully",
                background_desc="Sunny forest stream with shiny pebbles and jumping butterflies"
            )
        },
        {
            "scene_id": 3,
            "description": "Kết thúc hành trình vui vẻ và bài học ý nghĩa.",
            "characters": ["Mèo Bông", "Thỏ Ngọc"],
            "background": "Đồi cỏ hoa rực rỡ nắng chiều hoàng hôn êm đềm.",
            "action": "Hai bạn ngồi cạnh nhau ngắm hoàng hôn và mỉm cười hạnh phúc.",
            "narration": f"Hành trình khép lại thật êm đềm. {summary}",
            "image_prompt": IMAGE_PROMPT_TEMPLATE.format(
                characters_desc="Cute white cat and cute bunny sitting side by side",
                action_desc="Watching beautiful warm sunset sky and smiling happily together",
                background_desc="Grassy hill with soft golden sunset light and warm cozy atmosphere"
            )
        }
    ]
