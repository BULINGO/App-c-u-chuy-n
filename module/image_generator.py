import logging
import asyncio
from typing import List, Dict, Any
from backend.services.openrouter import openrouter_service

logger = logging.getLogger("image_generator_module")

async def generate_scene_images(
    scenes: List[Dict[str, Any]],
    style: str = "Hoạt hình"
) -> List[Dict[str, Any]]:
    """
    Model Tạo hình ảnh: Sinh hình ảnh minh họa cho từng cảnh trong danh sách cảnh.
    Duy trì sự nhất quán của nhân vật bằng cách sử dụng ảnh cảnh trước làm tham chiếu.
    """
    updated_scenes = []
    prev_image_url = None

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", idx + 1)
        image_prompt = scene.get("image_prompt", f"Illustration for scene {scene_id}")

        logger.info(f"Đang sinh hình ảnh cho Cảnh {scene_id}...")

        try:
            if openrouter_service.is_configured():
                img_url = await openrouter_service.generate_image(
                    image_prompt=image_prompt,
                    style=style,
                    ref_image_url=prev_image_url
                )
            else:
                img_url = get_svg_placeholder(scene_id, scene.get("description", "Cảnh hoạt hình"))
        except Exception as e:
            logger.error(f"Lỗi khi tạo ảnh cho Cảnh {scene_id}: {str(e)}")
            img_url = get_svg_placeholder(scene_id, scene.get("description", "Cảnh minh họa"))

        prev_image_url = img_url
        scene_copy = dict(scene)
        scene_copy["image_url"] = img_url
        updated_scenes.append(scene_copy)

    return updated_scenes

def get_svg_placeholder(scene_id: int, title: str) -> str:
    """
    Sinh Data URI ảnh SVG hoạt hình minh họa mẫu đẹp mắt khi không có API key.
    """
    import urllib.parse
    colors = ["#2878d4", "#48bb78", "#ed8936", "#9f7aea", "#ed64a6"]
    bg_color = colors[(scene_id - 1) % len(colors)]
    
    clean_title = (title[:30] + '...') if len(title) > 30 else title
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
      <rect width="600" height="400" fill="{bg_color}" rx="16"/>
      <circle cx="300" cy="160" r="70" fill="white" opacity="0.2"/>
      <path d="M 230 280 Q 300 210 370 280" stroke="white" stroke-width="8" fill="none" stroke-linecap="round"/>
      <circle cx="260" cy="150" r="12" fill="white"/>
      <circle cx="340" cy="150" r="12" fill="white"/>
      <text x="300" y="340" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="white" text-anchor="middle">CẢNH {scene_id}: {clean_title}</text>
    </svg>"""
    
    encoded_svg = urllib.parse.quote(svg)
    return f"data:image/svg+xml;utf8,{encoded_svg}"
