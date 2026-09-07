import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("storage_service")

DATA_DIR = "data"
STORIES_FILE = os.path.join(DATA_DIR, "stories.json")

class StorageService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(STORIES_FILE):
            with open(STORIES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Lấy toàn bộ danh sách câu chuyện đã lưu, sắp xếp mới nhất lên đầu.
        """
        try:
            if not os.path.exists(STORIES_FILE):
                return []
            with open(STORIES_FILE, "r", encoding="utf-8") as f:
                stories = json.load(f)
                # Sort newest first
                stories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return stories
        except Exception as e:
            logger.error(f"Lỗi đọc file lịch sử câu chuyện: {str(e)}")
            return []

    def save_story(self, story_data: Dict[str, Any], user_input: str = "", age: str = "", style: str = "") -> Dict[str, Any]:
        """
        Lưu một câu chuyện mới vào file stories.json
        """
        try:
            stories = self.get_all_stories()

            story_record = {
                "id": str(uuid.uuid4())[:8],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": user_input,
                "age": age,
                "style": style,
                "title": story_data.get("title", "Câu chuyện AI"),
                "theme": story_data.get("theme", ""),
                "characters": story_data.get("characters", []),
                "setting": story_data.get("setting", ""),
                "story_summary": story_data.get("story_summary", ""),
                "moral": story_data.get("moral", ""),
                "storyboard": story_data.get("storyboard", []),
                "scenes": story_data.get("scenes", []),
                "evaluation": story_data.get("evaluation", {})
            }

            stories.insert(0, story_record)

            with open(STORIES_FILE, "w", encoding="utf-8") as f:
                json.dump(stories, f, ensure_ascii=False, indent=2)

            logger.info(f"Đã lưu câu chuyện thành công với ID: {story_record['id']}")
            return story_record
        except Exception as e:
            logger.error(f"Lỗi khi lưu câu chuyện: {str(e)}")
            return story_data

    def get_story_by_id(self, story_id: str) -> Optional[Dict[str, Any]]:
        stories = self.get_all_stories()
        for story in stories:
            if story.get("id") == story_id:
                return story
        return None

    def delete_story(self, story_id: str) -> bool:
        try:
            stories = self.get_all_stories()
            filtered_stories = [s for s in stories if s.get("id") != story_id]
            if len(filtered_stories) < len(stories):
                with open(STORIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(filtered_stories, f, ensure_ascii=False, indent=2)
                return True
            return False
        except Exception as e:
            logger.error(f"Lỗi xóa câu chuyện {story_id}: {str(e)}")
            return False

storage_service = StorageService()
