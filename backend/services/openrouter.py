import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("openrouter_service")

# Danh sách các model chất lượng cao ưu tiên fallback
FALLBACK_MODELS = [
    "google/gemini-2.5-flash",
    "qwen/qwen-2.5-72b-instruct",
    "openai/gpt-4o-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat"
]

class OpenRouterService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.default_model = os.getenv("DEFAULT_MODEL", "google/gemini-2.5-flash")
        self.image_model = os.getenv("IMAGE_MODEL", "qwen/qwen-2.5-vl-72b-instruct:free")
        self.base_url = "https://openrouter.ai/api/v1"

    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "",
        model: Optional[str] = None,
        json_output: bool = True,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Gọi OpenRouter API để sinh văn bản (Director, Scene Planner, Evaluator).
        Tự động chuyển đổi sang model dự phòng (fallback) nếu model chính gặp lỗi.
        """
        if not self.is_configured():
            logger.warning("OPENROUTER_API_KEY chưa được cấu hình. Sử dụng phân tích kịch bản cục bộ.")
            raise ValueError("OPENROUTER_API_KEY chưa được cấu hình trong file .env!")

        # Chuẩn bị danh sách model để thử
        models_to_try: List[str] = []
        primary_model = model or self.default_model
        models_to_try.append(primary_model)
        for fb in FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost:8000",
            "X-Title": "AI Storytelling Contest App",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None

        async with httpx.AsyncClient(timeout=45.0) as client:
            for current_model in models_to_try:
                payload = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": temperature
                }
                if json_output:
                    payload["response_format"] = {"type": "json_object"}

                try:
                    logger.info(f"Đang gửi yêu cầu tới OpenRouter model: {current_model}")
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )

                    if response.status_code != 200:
                        error_text = response.text
                        logger.warning(f"Model {current_model} trả về lỗi HTTP {response.status_code}: {error_text[:200]}")
                        last_error = Exception(f"HTTP {response.status_code}: {error_text}")
                        continue

                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        logger.warning(f"Model {current_model} không trả về choices.")
                        continue

                    content = choices[0]["message"]["content"]

                    if json_output:
                        clean_content = content.strip()
                        # Tháo gỡ markdown wrapper ```json ... ```
                        if clean_content.startswith("```"):
                            lines = clean_content.splitlines()
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines and lines[-1].strip() == "```":
                                lines = lines[:-1]
                            clean_content = "\n".join(lines).strip()

                        try:
                            parsed_json = json.loads(clean_content)
                            return parsed_json
                        except json.JSONDecodeError as err:
                            # Cố gắng tìm JSON substring giữa dấu ngoặc nhọn { ... }
                            start_brace = clean_content.find("{")
                            end_brace = clean_content.rfind("}")
                            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                                try:
                                    return json.loads(clean_content[start_brace:end_brace+1])
                                except Exception:
                                    pass
                            logger.error(f"Lỗi parse JSON từ LLM output: {content[:300]}")
                            last_error = err
                            continue
                    return {"text": content}

                except Exception as e:
                    logger.warning(f"Lỗi khi gọi model {current_model}: {str(e)}")
                    last_error = e
                    continue

        # Nếu tất cả các model đều thất bại
        raise last_error or Exception("Tất cả các model AI đều không phản hồi thành công.")

    async def generate_image(
        self,
        image_prompt: str,
        style: str = "Hoạt hình",
        ref_image_url: Optional[str] = None
    ) -> str:
        """
        Sinh ảnh cho cảnh câu chuyện.
        """
        if not self.is_configured():
            raise ValueError("OPENROUTER_API_KEY chưa được cấu hình!")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost:8000",
            "X-Title": "AI Storytelling Contest App",
            "Content-Type": "application/json"
        }

        full_prompt = (
            f"Vẽ tranh minh họa phong cách {style} dành cho sách truyện thiếu nhi tiểu học. "
            f"Độ phân giải cao, màu sắc rực rỡ, nét vẽ đáng yêu. Chi tiết cảnh: {image_prompt}"
        )
        if ref_image_url:
            full_prompt += f" Giữ nhất quán nhân vật theo ảnh tham chiếu: {ref_image_url}"

        payload = {
            "model": self.image_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Generate a vivid children story illustration: {full_prompt}"}
                    ]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    if "http" in content:
                        import re
                        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
                        if urls:
                            return urls[0]
                    return content
                else:
                    return ""
            except Exception as e:
                logger.error(f"Lỗi khi sinh ảnh OpenRouter: {str(e)}")
                return ""

openrouter_service = OpenRouterService()
