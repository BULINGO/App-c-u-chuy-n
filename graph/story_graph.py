import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from graph.state import StoryState
from module.director import generate_storyboard
from module.scene_planner import plan_scenes
from module.image_generator import generate_scene_images
from module.evaluator import evaluate_story

logger = logging.getLogger("story_graph")

# --- ĐỊNH NGHĨA CÁC NODES ---

async def director_node(state: StoryState) -> Dict[str, Any]:
    logger.info("--> [LangGraph] Node: Đạo diễn đang tạo kịch bản Storyboard...")
    user_input = state.get("user_input", "")
    age_group = state.get("age_group", "Lớp 1 - 2")
    art_style = state.get("art_style", "Hoạt hình")

    storyboard = await generate_storyboard(user_input, age_group, art_style)
    return {
        "storyboard": storyboard,
        "status": "director_completed"
    }

async def scene_planner_node(state: StoryState) -> Dict[str, Any]:
    logger.info("--> [LangGraph] Node: Scene Planner đang phân chia thành các cảnh chi tiết...")
    storyboard = state.get("storyboard", {})

    scenes = await plan_scenes(storyboard)
    return {
        "scenes": scenes,
        "status": "scene_planner_completed"
    }

async def image_generator_node(state: StoryState) -> Dict[str, Any]:
    logger.info("--> [LangGraph] Node: Image Generator đang sinh hình ảnh cho các cảnh...")
    scenes = state.get("scenes", [])
    art_style = state.get("art_style", "Hoạt hình")

    scenes_with_images = await generate_scene_images(scenes, art_style)
    return {
        "scenes": scenes_with_images,
        "status": "image_generator_completed"
    }

async def evaluator_node(state: StoryState) -> Dict[str, Any]:
    logger.info("--> [LangGraph] Node: Evaluator đang kiểm duyệt chất lượng câu chuyện...")
    storyboard = state.get("storyboard", {})
    scenes = state.get("scenes", [])
    retry_count = state.get("retry_count", 0)

    evaluation = await evaluate_story(storyboard, scenes, retry_count=retry_count)
    return {
        "evaluation": evaluation,
        "status": "evaluator_completed"
    }

# --- ĐIỀU KIỆN RẼ NHÁNH (CONDITIONAL ROUTING) ---

def check_evaluation_result(state: StoryState) -> Literal["approved", "retry"]:
    evaluation = state.get("evaluation", {})
    retry_count = state.get("retry_count", 0)
    approved = evaluation.get("approved", True)

    if approved or retry_count >= 2:
        logger.info(f"Kết quả kiểm duyệt: CHẤP NHẬN (Approved={approved}, Retries={retry_count})")
        return "approved"
    else:
        logger.warning(f"Kết quả kiểm duyệt: KHÔNG CHẤP NHẬN. Tiến hành làm lại (Retry {retry_count + 1})")
        return "retry"

async def retry_increment_node(state: StoryState) -> Dict[str, Any]:
    current_retries = state.get("retry_count", 0)
    return {
        "retry_count": current_retries + 1,
        "status": "retrying"
    }

# --- THIẾT LẬP LANGGRAPH WORKFLOW ---

def create_story_graph():
    builder = StateGraph(StoryState)

    # Thêm các nút vào sơ đồ
    builder.add_node("director", director_node)
    builder.add_node("scene_planner", scene_planner_node)
    builder.add_node("image_generator", image_generator_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("retry_increment", retry_increment_node)

    # Xây dựng luồng di chuyển (Director -> Scene Planner -> Image Generator -> Kết thúc)
    builder.add_edge(START, "director")
    builder.add_edge("director", "scene_planner")
    builder.add_edge("scene_planner", "image_generator")
    builder.add_edge("image_generator", END)

    return builder.compile()

# Khởi tạo sẵn ứng dụng đồ thị LangGraph
story_graph_app = create_story_graph()
