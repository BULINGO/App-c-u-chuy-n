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
    Danh sách cảnh mẫu động theo đúng nhân vật và kịch bản từ Đạo diễn.
    """
    title = storyboard.get("title", "Câu chuyện đáng yêu")
    summary = storyboard.get("story_summary", "Một hành trình ý nghĩa")
    chars = storyboard.get("characters", [])
    
    char_names = []
    if isinstance(chars, list):
        for c in chars:
            if isinstance(c, dict):
                char_names.append(c.get("name", "Nhân vật"))
            else:
                char_names.append(str(c))
    
    if not char_names:
        char_names = ["Bạn nhỏ"]

    main_char = char_names[0]

    return [
        {
            "scene_id": 1,
            "description": f"Giới thiệu nhân vật {main_char} và khởi đầu câu chuyện.",
            "characters": char_names,
            "background": "Bối cảnh tươi sáng rạng rỡ nắng mai.",
            "action": f"{main_char} mỉm cười chuẩn bị bắt đầu công việc.",
            "narration": f"Chào mừng các bạn nhỏ đến với câu chuyện '{title}'. Hôm nay là một ngày rất tươi đẹp!",
            "image_prompt": IMAGE_PROMPT_TEMPLATE.format(
                characters_desc=f"Cute cartoon character named {main_char}",
                action_desc="Smiling happily and preparing for a new day",
                background_desc="Bright sunny morning background with colorful scenery"
            )
        },
        {
            "scene_id": 2,
            "description": f"{main_char} hăng hái thực hiện hoạt động.",
            "characters": char_names,
            "background": "Bối cảnh rộn rã đầy sức sống.",
            "action": f"{main_char} cẩn thận tập trung làm công việc của mình.",
            "narration": f"Với sự chăm chỉ và hào hứng, {main_char} từng bước vượt qua những điều mới mẻ.",
            "image_prompt": IMAGE_PROMPT_TEMPLATE.format(
                characters_desc=f"Cute cartoon character named {main_char}",
                action_desc="Focusing carefully on doing activities with enthusiasm",
                background_desc="Vivid and active scene background"
            )
        },
        {
            "scene_id": 3,
            "description": f"{main_char} hoàn thành niềm vui và bài học ý nghĩa.",
            "characters": char_names,
            "background": "Khung cảnh hoàng hôn ấm áp và niềm vui ngập tràn.",
            "action": f"{main_char} mỉm cười hạnh phúc ngắm nhìn thành quả.",
            "narration": f"Hành trình khép lại thật êm đềm và nhiều niềm vui. {summary}",
            "image_prompt": IMAGE_PROMPT_TEMPLATE.format(
                characters_desc=f"Cute cartoon character named {main_char}",
                action_desc="Smiling proudly and happily looking at achievements",
                background_desc="Warm golden sunset background with cozy atmosphere"
            )
        }
    ]

