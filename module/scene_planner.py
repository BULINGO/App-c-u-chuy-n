import logging
import json
from typing import Dict, Any, List, Optional
from backend.services.openrouter import openrouter_service
from module.prompts import SCENE_PLANNER_PROMPT, IMAGE_PROMPT_TEMPLATE

logger = logging.getLogger("scene_planner_module")

async def plan_scenes(
    storyboard: Dict[str, Any],
    user_input: Optional[str] = None,
    age_group: str = "Lớp 1 - 2",
    art_style: str = "Hoạt hình"
) -> List[Dict[str, Any]]:
    """
    Model Chia Cảnh (Scene Planner Agent): Nhận Storyboard từ Đạo diễn và yêu cầu của người dùng,
    phân chia thành đúng 3 phân cảnh chi tiết, liền mạch, đồng nhất ý nghĩa và không đứt gãy.
    """
    user_prompt = (
        f"--- THÔNG TIN KỊCH BẢN TỪ ĐẠO DIỄN ---\n"
        f"Kịch bản Storyboard: {json.dumps(storyboard, ensure_ascii=False, indent=2)}\n\n"
        f"Ý tưởng gốc của người dùng: {user_input or ''}\n"
        f"Lứa tuổi học sinh: {age_group}\n"
        f"Phong cách đồ họa: {art_style}\n\n"
        f"--- YÊU CẦU BẮT BUỘC KHI CHIA 3 CẢNH ---\n"
        f"1. Tạo đúng 3 phân cảnh tương ứng Cảnh 1, Cảnh 2, Cảnh 3 trong Storyboard.\n"
        f"2. Đảm bảo MẠCH TRUYỆN LIÊN HOÀN VÀ ĐỒNG NHẤT Ý NGHĨA: Cảnh 1 (Mở đầu) -> Cảnh 2 (Diễn biến thử thách từ cảnh 1) -> Cảnh 3 (Kết thúc viên mãn & bài học).\n"
        f"3. Lời kể (narration) tiếng Việt phải ấm áp, sinh động, đúng với diễn biến của cảnh.\n"
        f"4. Image prompt bằng tiếng Anh chi tiết, giữ nguyên mô tả ngoại hình nhân vật xuyên suốt 3 cảnh để đảm bảo tính nhất quán hình ảnh.\n"
        f"5. Bắt buộc trả về đúng định dạng JSON yêu cầu."
    )

    try:
        if openrouter_service.is_configured():
            result = await openrouter_service.chat_completion(
                prompt=user_prompt,
                system_prompt=SCENE_PLANNER_PROMPT,
                json_output=True
            )
            scenes = result.get("scenes", [])
            if isinstance(scenes, list) and len(scenes) >= 3:
                # Đảm bảo các trường cần thiết trong từng cảnh
                validated_scenes = []
                for idx, s in enumerate(scenes[:3]):
                    validated_scenes.append({
                        "scene_id": idx + 1,
                        "description": s.get("description", f"Diễn biến cảnh {idx + 1}"),
                        "characters": s.get("characters", [c.get("name", "Nhân vật") if isinstance(c, dict) else str(c) for c in storyboard.get("characters", [])]),
                        "background": s.get("background", storyboard.get("setting", "Khung cảnh thiên nhiên tươi đẹp")),
                        "action": s.get("action", f"Hành động trong cảnh {idx + 1}"),
                        "narration": s.get("narration", f"Lời kể cho cảnh {idx + 1}"),
                        "image_prompt": s.get("image_prompt", f"Cute animation illustration for scene {idx + 1}")
                    })
                return validated_scenes
            else:
                logger.warning("LLM trả về không đủ 3 cảnh. Chuyển sang tạo cảnh thông minh theo Storyboard.")
                return get_mock_scenes(storyboard, user_input, art_style)
        else:
            return get_mock_scenes(storyboard, user_input, art_style)
    except Exception as e:
        logger.error(f"Lỗi ở Scene Planner module: {str(e)}. Sử dụng chia cảnh thông minh dự phòng.")
        return get_mock_scenes(storyboard, user_input, art_style)

def get_mock_scenes(
    storyboard: Dict[str, Any],
    user_input: Optional[str] = None,
    art_style: str = "Hoạt hình"
) -> List[Dict[str, Any]]:
    """
    Sinh 3 phân cảnh chi tiết, sống động bám sát 100% nội dung Storyboard và ý tưởng người dùng.
    """
    title = storyboard.get("title", "Câu chuyện ý nghĩa")
    setting = storyboard.get("setting", "Khung cảnh thiên nhiên tươi sáng")
    moral = storyboard.get("moral", "Hãy luôn yêu thương và giúp đỡ mọi người xung quanh.")
    chars = storyboard.get("characters", [])
    sb_scenes = storyboard.get("storyboard", [])

    char_names = []
    char_desc_list = []
    if isinstance(chars, list):
        for c in chars:
            if isinstance(c, dict):
                c_name = c.get("name", "Bạn nhỏ")
                c_app = c.get("appearance", "đáng yêu")
                char_names.append(c_name)
                char_desc_list.append(f"{c_name} ({c_app})")
            else:
                char_names.append(str(c))
                char_desc_list.append(str(c))

    if not char_names:
        char_names = ["Bạn nhỏ"]
        char_desc_list = ["Bạn nhỏ dễ thương với nụ cười rạng rỡ"]

    main_char = char_names[0]
    all_chars_str = ", ".join(char_names)
    char_appearance_str = "; ".join(char_desc_list)

    # Lấy nội dung 3 cảnh từ Storyboard
    scene1_text = sb_scenes[0] if len(sb_scenes) > 0 else f"Giới thiệu {main_char} và khởi đầu câu chuyện tại {setting.lower()}."
    scene2_text = sb_scenes[1] if len(sb_scenes) > 1 else f"{main_char} cùng các bạn nỗ lực thực hiện hoạt động và vượt qua thử thách."
    scene3_text = sb_scenes[2] if len(sb_scenes) > 2 else f"{main_char} hoàn thành công việc xuất sắc, ngập tràn niềm vui và gặt hái bài học."

    # Style descriptor cho image prompt
    style_desc = "3D Disney Pixar animated movie style, masterpiece, vivid pastel colors"
    if "dễ thương" in art_style.lower():
        style_desc = "Super cute anime watercolor storybook style, soft dreamy lighting, adorable"
    elif "cổ tích" in art_style.lower():
        style_desc = "Magical fairy tale storybook illustration, glowing sparkles, lush enchanting scenery"
    elif "kỳ ảo" in art_style.lower() or "fantasy" in art_style.lower():
        style_desc = "Breathtaking magical fantasy storybook art, mystical glowing effects, mythical enchanting atmosphere, ethereal lighting, vibrant magical colors"

    return [
        {
            "scene_id": 1,
            "description": f"Mở đầu: {scene1_text}",
            "characters": char_names,
            "background": f"{setting} vào một buổi sáng sớm tươi sáng rạng rỡ nắng mai.",
            "action": f"{main_char} xuất hiện rạng rỡ, bắt đầu: {scene1_text}",
            "narration": f"Chào mừng các bạn nhỏ đến với câu chuyện '{title}'. Hôm nay tại {setting.lower()}, {scene1_text}. Một hành trình thật thú vị đã bắt đầu!",
            "image_prompt": f"{style_desc}, {char_appearance_str}, happily starting the journey, {scene1_text}, bright morning sunlight, warm friendly atmosphere, 8k resolution, children book illustration."
        },
        {
            "scene_id": 2,
            "description": f"Diễn biến: {scene2_text}",
            "characters": char_names,
            "background": f"{setting} với không gian sôi động và đầy hứng khởi.",
            "action": f"{all_chars_str} hăng hái cùng nhau hành động: {scene2_text}",
            "narration": f"Tiếp tục hành trình, {all_chars_str} không ngần ngại cố gắng. {scene2_text}. Sự chăm chỉ và tinh thần đoàn kết đã giúp mọi chuyện trở nên thật diệu kỳ!",
            "image_prompt": f"{style_desc}, {char_appearance_str}, actively cooperating and doing: {scene2_text}, dynamic action, detailed vibrant environment in {setting}, beautiful lighting, storybook illustration."
        },
        {
            "scene_id": 3,
            "description": f"Kết thúc: {scene3_text}",
            "characters": char_names,
            "background": f"{setting} ngập tràn ánh hoàng hôn ấm áp và tiếng cười hân hoan.",
            "action": f"{all_chars_str} mỉm cười hạnh phúc, cùng nhau tận hưởng thành quả: {scene3_text}",
            "narration": f"Cuối cùng, {scene3_text}. Mọi người cùng nở nụ cười rạng rỡ trong niềm vui trọn vẹn. Bài học quý giá rút ra là: {moral}",
            "image_prompt": f"{style_desc}, {char_appearance_str}, joyfully celebrating success, smiling proudly, golden sunset background in {setting}, cozy heartwarming atmosphere, masterpiece, 8k resolution."
        }
    ]
