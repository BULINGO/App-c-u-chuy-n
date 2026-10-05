import logging
import asyncio
import random
import urllib.parse
from typing import List, Dict, Any

logger = logging.getLogger("image_generator_module")

def generate_pollinations_image_url(scene: Dict[str, Any], style: str = "Hoạt hình") -> str:
    """
    Sinh URL ảnh AI nghệ thuật thực tế sinh động 100% từ Pollinations AI Engine (Flux/SD).
    Tự động kết hợp prompt chi tiết từ Scene Planner để đảm bảo tính nhất quán hình ảnh nhân vật và bối cảnh.
    """
    image_prompt = scene.get("image_prompt", "").strip()
    
    style_keyword = "3D Disney Pixar animated cute 3d illustration, vivid pastel colors"
    if "dễ thương" in style.lower():
        style_keyword = "Super cute anime watercolor storybook illustration, adorable characters, soft pastel colors"
    elif "cổ tích" in style.lower():
        style_keyword = "Magical fairy tale storybook illustration, enchanted scenery, glowing sparkles"
    elif "kỳ ảo" in style.lower() or "fantasy" in style.lower():
        style_keyword = "Epic magical fantasy art style, mythical creatures, mystical glowing magic effects, ethereal starry lighting, enchanted vibrant colors"

    if image_prompt and len(image_prompt) > 20 and not image_prompt.startswith("Cute animation"):
        prompt = f"{image_prompt}, {style_keyword}, masterpiece, 8k resolution, children storybook art"
    else:
        action = scene.get("action") or scene.get("description") or "doing fun activity"
        background = scene.get("background") or "sunny outdoor background"
        chars = scene.get("characters") or ["cute character"]
        char_str = ", ".join(chars) if isinstance(chars, list) else str(chars)
        prompt = f"{style_keyword}, cute characters {char_str}, {action}, {background}, masterpiece, 8k resolution, children storybook illustration"

    clean_prompt = prompt.replace("\n", " ").strip()
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed = random.randint(1000, 99999)

    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=500&nologo=true&seed={seed}"

async def generate_scene_images(
    scenes: List[Dict[str, Any]],
    style: str = "Hoạt hình"
) -> List[Dict[str, Any]]:
    """
    Model Tạo hình ảnh: Sinh hình ảnh AI minh họa sắc nét và nhất quán cho từng cảnh.
    """
    updated_scenes = []

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", idx + 1)
        logger.info(f"Đang sinh hình ảnh AI nghệ thuật cho Cảnh {scene_id}...")

        img_url = generate_pollinations_image_url(scene, style)
        if not img_url:
            img_url = get_svg_placeholder(scene, style)

        scene_copy = dict(scene)
        scene_copy["image_url"] = img_url
        updated_scenes.append(scene_copy)

    return updated_scenes

def get_svg_placeholder(scene: Dict[str, Any], style: str = "Hoạt hình") -> str:
    """
    Sinh Data URI ảnh SVG minh họa hoạt hình trực quan, đẹp mắt, khớp từng bối cảnh và hành động câu chuyện.
    """
    scene_id = scene.get("scene_id", 1)
    action = scene.get("action") or scene.get("description") or "Diễn biến câu chuyện"
    bg_text = scene.get("background") or "Bối cảnh tự nhiên"
    chars = scene.get("characters") or ["Nhân vật"]
    char_str = ", ".join(chars) if isinstance(chars, list) else str(chars)

    clean_action = (action[:45] + '...') if len(action) > 45 else action
    clean_bg = (bg_text[:35] + '...') if len(bg_text) > 35 else bg_text

    themes = [
        {"top": "#38bdf8", "bottom": "#4ade80", "accent": "#facc15", "icon": "🐱 🐰 🌲", "title": "Bắt đầu hành trình"},
        {"top": "#fb923c", "bottom": "#f43f5e", "accent": "#fef08a", "icon": "🌉 🌊 🐾", "title": "Cùng vượt thử thách"},
        {"top": "#c084fc", "bottom": "#6366f1", "accent": "#f472b6", "icon": "🌅 💖 ✨", "title": "Kỷ niệm đẹp đẽ"},
        {"top": "#34d399", "bottom": "#059669", "accent": "#fef08a", "icon": "🏰 🌸 🎈", "title": "Khám phá thú vị"},
        {"top": "#f472b6", "bottom": "#db2777", "accent": "#fde047", "icon": "🎓 📚 🌟", "title": "Bài học ý nghĩa"}
    ]
    
    theme = themes[(scene_id - 1) % len(themes)]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
      <defs>
        <linearGradient id="bgGrad{scene_id}" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="{theme['top']}"/>
          <stop offset="100%" stop-color="{theme['bottom']}"/>
        </linearGradient>
        <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.25"/>
        </filter>
      </defs>

      <rect width="600" height="400" fill="url(#bgGrad{scene_id})" rx="16"/>
      <circle cx="500" cy="70" r="45" fill="{theme['accent']}" opacity="0.8"/>
      <circle cx="100" cy="320" r="90" fill="white" opacity="0.15"/>
      <circle cx="520" cy="340" r="110" fill="white" opacity="0.15"/>

      <rect x="40" y="50" width="520" height="300" rx="16" fill="white" opacity="0.92" filter="url(#shadow)"/>

      <rect x="60" y="70" width="120" height="32" rx="16" fill="{theme['top']}"/>
      <text x="120" y="91" font-family="'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="bold" fill="white" text-anchor="middle">CẢNH {scene_id}</text>

      <text x="300" y="150" font-family="sans-serif" font-size="52" text-anchor="middle">{theme['icon']}</text>

      <text x="300" y="200" font-family="'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="bold" fill="#1e293b" text-anchor="middle">📍 {clean_bg}</text>
      <text x="300" y="235" font-family="'Segoe UI', Roboto, sans-serif" font-size="15" fill="#334155" text-anchor="middle">🎭 {clean_action}</text>
      <text x="300" y="270" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" fill="#64748b" text-anchor="middle">👥 Nhân vật: {char_str}</text>

      <rect x="40" y="310" width="520" height="40" rx="0" fill="#f8fafc" style="border-bottom-left-radius: 16px; border-bottom-right-radius: 16px;"/>
      <text x="300" y="335" font-family="'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="600" fill="#0284c7" text-anchor="middle">✨ Tranh minh họa trực quan phong cách {style} ✨</text>
    </svg>"""

    encoded_svg = urllib.parse.quote(svg)
    return f"data:image/svg+xml;utf8,{encoded_svg}"
