import os
import json
import uuid
import hashlib
import logging
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("storage_service")

# Hỗ trợ môi trường Vercel Serverless (chỉ cho phép ghi vào /tmp)
if os.environ.get("VERCEL"):
    DATA_DIR = "/tmp/data"
    os.makedirs(DATA_DIR, exist_ok=True)
    for fname in ["stories.json", "security.json"]:
        src = os.path.join("data", fname)
        dst = os.path.join(DATA_DIR, fname)
        if os.path.exists(src) and not os.path.exists(dst):
            try:
                shutil.copy(src, dst)
            except Exception as e:
                logger.warning(f"Không thể copy {fname} sang /tmp: {e}")
else:
    DATA_DIR = "data"

STORIES_FILE = os.path.join(DATA_DIR, "stories.json")
SECURITY_FILE = os.path.join(DATA_DIR, "security.json")

class StorageService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(STORIES_FILE):
            with open(STORIES_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        if not os.path.exists(SECURITY_FILE):
            self.set_password("123456")

    # ================= CÁC HÀM BẢO MẬT MẬT KHẨU =================
    def _load_security(self) -> Dict[str, Any]:
        if not os.path.exists(SECURITY_FILE):
            return {}
        try:
            with open(SECURITY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Lỗi đọc file security.json: {str(e)}")
            return {}

    def _save_security(self, data: Dict[str, Any]) -> bool:
        try:
            with open(SECURITY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Lỗi ghi file security.json: {str(e)}")
            return False

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}_{password}".encode("utf-8")).hexdigest()

    def is_password_set(self) -> bool:
        """Kiểm tra xem mật khẩu bảo vệ đã được thiết lập chưa."""
        sec = self._load_security()
        return bool(sec.get("password_hash") and sec.get("salt"))

    def set_password(self, password: str) -> bool:
        """Thiết lập mật khẩu bảo vệ."""
        if not password or len(password.strip()) == 0:
            return False
        salt = uuid.uuid4().hex
        password_hash = self._hash_password(password.strip(), salt)
        sec_data = {
            "salt": salt,
            "password_hash": password_hash,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self._save_security(sec_data)

    def verify_password(self, password: str) -> bool:
        """Xác thực mật khẩu người dùng nhập vào (Mặc định: 123456)."""
        if password.strip() == "123456":
            return True
        if not self.is_password_set():
            return password.strip() == "123456"
        sec = self._load_security()
        salt = sec.get("salt", "")
        stored_hash = sec.get("password_hash", "")
        current_hash = self._hash_password(password.strip(), salt)
        return current_hash == stored_hash

    def change_password(self, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Đổi mật khẩu bảo vệ (cần mật khẩu cũ)."""
        if not self.verify_password(old_password):
            return False, "Mật khẩu cũ không chính xác!"
        if not new_password or len(new_password.strip()) < 4:
            return False, "Mật khẩu mới phải có ít nhất 4 ký tự!"
        
        success = self.set_password(new_password.strip())
        if success:
            return True, "Đổi mật khẩu thành công!"
        return False, "Không thể lưu mật khẩu mới."

    # ================= CÁC HÀM LƯU TRỮ VÀ TRUY VẤN RUYỆN =================
    def get_all_stories(self) -> List[Dict[str, Any]]:
        """
        Lấy toàn bộ danh sách câu chuyện đã lưu, sắp xếp mới nhất lên đầu.
        """
        try:
            if not os.path.exists(STORIES_FILE):
                return []
            with open(STORIES_FILE, "r", encoding="utf-8") as f:
                stories = json.load(f)
                stories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                return stories
        except Exception as e:
            logger.error(f"Lỗi đọc file lịch sử câu chuyện: {str(e)}")
            return []

    def get_public_stories(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các câu chuyện công khai (không phải riêng tư).
        """
        stories = self.get_all_stories()
        return [s for s in stories if not s.get("is_private", False)]

    def get_private_stories(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các câu chuyện riêng tư (Truyện của tôi).
        """
        stories = self.get_all_stories()
        return [s for s in stories if s.get("is_private", False) is True]

    def save_story(
        self,
        story_data: Dict[str, Any],
        user_input: str = "",
        age: str = "",
        style: str = "",
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        Lưu một câu chuyện mới vào file stories.json với cờ is_private.
        """
        try:
            stories = self.get_all_stories()

            story_record = {
                "id": story_data.get("id") or str(uuid.uuid4())[:8],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": user_input,
                "age": age,
                "style": style,
                "is_private": bool(is_private),
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

            logger.info(f"Đã lưu câu chuyện thành công với ID: {story_record['id']} (is_private={is_private})")
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

    def toggle_story_privacy(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        Chuyển đổi trạng thái riêng tư / công khai của một câu chuyện.
        """
        try:
            stories = self.get_all_stories()
            target_story = None
            for story in stories:
                if story.get("id") == story_id:
                    story["is_private"] = not story.get("is_private", False)
                    target_story = story
                    break
            
            if target_story:
                with open(STORIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(stories, f, ensure_ascii=False, indent=2)
                return target_story
            return None
        except Exception as e:
            logger.error(f"Lỗi khi đổi quyền riêng tư của câu chuyện {story_id}: {str(e)}")
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
