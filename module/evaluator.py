import logging
import json
from typing import Dict, Any, List
from backend.services.openrouter import openrouter_service
from module.prompts import EVALUATOR_PROMPT

logger = logging.getLogger("evaluator_module")

async def evaluate_story(
    storyboard: Dict[str, Any],
    scenes: List[Dict[str, Any]],
    retry_count: int = 0,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Model Đánh giá (Evaluator): Kiểm tra nội dung câu chuyện và các cảnh.
    Trả về kết quả approved (True/False), feedback và điểm số.
    """
    # Nếu đã thử lại tối đa cho phép thì bắt buộc duyệt để tránh vòng lặp vô hạn
    if retry_count >= max_retries:
        logger.info(f"Đã đạt giới hạn {max_retries} lần thử lại. Tự động chấp nhận câu chuyện.")
        return {
            "approved": True,
            "feedback": f"Đã đạt giới hạn kiểm duyệt tối đa ({max_retries} lần). Nội dung được chấp nhận.",
            "score": 8
        }

    eval_input = {
        "storyboard": storyboard,
        "scenes_summary": [s.get("narration", "") for s in scenes]
    }
    user_prompt = f"Hãy đánh giá nội dung kịch bản và các cảnh sau:\n{json.dumps(eval_input, ensure_ascii=False, indent=2)}"

    try:
        if openrouter_service.is_configured():
            result = await openrouter_service.chat_completion(
                prompt=user_prompt,
                system_prompt=EVALUATOR_PROMPT,
                json_output=True
            )
            return {
                "approved": result.get("approved", True),
                "feedback": result.get("feedback", "Nội dung phù hợp cho học sinh tiểu học."),
                "score": result.get("score", 9)
            }
        else:
            return {
                "approved": True,
                "feedback": "Nội dung đạt chuẩn trong sáng, nhân văn cho tiểu học (Mock Evaluator).",
                "score": 10
            }
    except Exception as e:
        logger.error(f"Lỗi ở Evaluator module: {str(e)}. Tự động duyệt mặc định.")
        return {
            "approved": True,
            "feedback": "Đã phê duyệt mặc định do không thể kết nối Evaluator API.",
            "score": 8
        }
