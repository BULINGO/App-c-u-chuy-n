import os
import json
import logging
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("openrouter_service")

class OpenRouterService:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.default_model = os.getenv("DEFAULT_MODEL", "qwen/qwen-2.5-72b-instruct")
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
        Trả về dictionary (nếu json_output=True) hoặc chuỗi văn bản.
        """
        selected_model = model or self.default_model

        if not self.is_configured():
            logger.warning("OPENROUTER_API_KEY chưa được cấu hình. Đang sử dụng chế độ Mock Data.")
            raise ValueError("OPENROUTER_API_KEY chưa được cấu hình trong file .env!")

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

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature
        }

        if json_output:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"OpenRouter Error {response.status_code}: {error_text}")
                    raise Exception(f"Lỗi OpenRouter API ({response.status_code}): {error_text}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                if json_output:
                    try:
                        # Tháo gỡ dấu markdown json nếu có
                        clean_content = content.strip()
                        if clean_content.startswith("```json"):
                            clean_content = clean_content[7:]
                        if clean_content.endswith("```"):
                            clean_content = clean_content[:-3]
                        return json.loads(clean_content.strip())
                    except json.JSONDecodeError as err:
                        logger.error(f"Lỗi parse JSON từ LLM output: {content}")
                        raise Exception(f"Kết quả trả về không đúng định dạng JSON: {str(err)}")
                return {"text": content}

            except httpx.RequestError as e:
                logger.error(f"Lỗi kết nối OpenRouter API: {str(e)}")
                raise Exception(f"Không thể kết nối tới máy chủ OpenRouter: {str(e)}")

    async def generate_image(
        self,
        image_prompt: str,
        style: str = "Hoạt hình",
        ref_image_url: Optional[str] = None
    ) -> str:
        """
        Sinh ảnh cho cảnh câu chuyện thông qua OpenRouter / Qwen Image Model.
        Nếu API thành công trả về URL ảnh hoặc SVG placeholder nếu chạy chế độ thử nghiệm.
        """
        if not self.is_configured():
            logger.warning("OPENROUTER_API_KEY chưa cấu hình. Trả về ảnh hoạt hình mẫu.")
            raise ValueError("OPENROUTER_API_KEY chưa được cấu hình!")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://localhost:8000",
            "X-Title": "AI Storytelling Contest App",
            "Content-Type": "application/json"
        }

        # Prompt nâng cao hình ảnh hoạt hình cho học sinh tiểu học
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

        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    # Kiểm tra xem trả về URL hay markdown image
                    if "http" in content:
                        # Extract URL từ response
                        import re
                        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content)
                        if urls:
                            return urls[0]
                    # Nếu model trả về mô tả hình ảnh hoặc SVG
                    return content
                else:
                    logger.warning(f"Image API returned status {response.status_code}. Fallback to dynamic illustration.")
                    return f"https://placehold.co/600x400/e2e8f0/1e293b?text={httpx.QueryParams({'text': image_prompt[:30]}).get('text')}"
            except Exception as e:
                logger.error(f"Lỗi khi sinh ảnh: {str(e)}")
                # Trả về URL ảnh minh họa tạm thời không crash server
                return f"https://placehold.co/600x400/e2e8f0/1e293b?text=Anh+Minh+Hoa"

openrouter_service = OpenRouterService()
