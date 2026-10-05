import logging
import re
from typing import Dict, Any, List
from backend.services.openrouter import openrouter_service
from module.prompts import DIRECTOR_PROMPT

logger = logging.getLogger("director_module")

async def generate_storyboard(
    user_input: str,
    age_group: str = "Lớp 1 - 2",
    art_style: str = "Hoạt hình"
) -> Dict[str, Any]:
    """
    Model Đạo diễn (Director Agent): Tiếp nhận ý tưởng của người dùng, phân tích cốt truyện
    và tạo ra Storyboard 3 phân cảnh liên kết logic, đồng nhất ý nghĩa, bám sát 100% yêu cầu.
    """
    user_prompt = (
        f"--- YÊU CẦU TỪ NGƯỜI DÙNG ---\n"
        f"Ý tưởng / Cốt truyện / Phân cảnh: {user_input}\n"
        f"Lứa tuổi học sinh: {age_group}\n"
        f"Phong cách đồ họa: {art_style}\n\n"
        f"--- LƯU Ý BẮT BUỘC KHI ĐẠO DIỄN KỊCH BẢN ---\n"
        f"1. Nếu người dùng đã chia sẵn các phân cảnh (ví dụ Cảnh 1, Cảnh 2, Cảnh 3...), hãy giữ nguyên 100% nội dung từng cảnh đó vào mảng 'storyboard'.\n"
        f"2. Nếu người dùng nhập ý tưởng chung, hãy tạo 3 phân cảnh có mạch truyện liền mạch chặt chẽ (Mở đầu -> Diễn biến thử thách -> Kết thúc thành công).\n"
        f"3. Cả 3 cảnh phải đồng nhất một câu chuyện, cùng một bối cảnh phát triển tự nhiên, giữ nguyên các nhân vật và tính cách, tuyệt đối không lạc đề.\n"
        f"4. Trả về đúng định dạng JSON yêu cầu."
    )

    try:
        if openrouter_service.is_configured():
            result = await openrouter_service.chat_completion(
                prompt=user_prompt,
                system_prompt=DIRECTOR_PROMPT,
                json_output=True
            )
            # Kiểm tra và chuẩn hóa kết quả từ LLM
            if isinstance(result, dict) and "storyboard" in result:
                storyboard_list = result.get("storyboard", [])
                if isinstance(storyboard_list, list) and len(storyboard_list) >= 3:
                    # Đảm bảo có đủ các trường cần thiết
                    if not result.get("characters"):
                        result["characters"] = extract_characters_from_input(user_input)
                    if not result.get("setting"):
                        result["setting"] = extract_setting_from_input(user_input)
                    return result
            logger.warning("Kết quả từ LLM chưa đầy đủ cấu trúc 3 cảnh, kết hợp với bộ phân tích thông minh.")
            fallback_sb = get_smart_storyboard(user_input, age_group, art_style)
            # Trộn kết quả nếu có trường hợp lệ từ LLM
            if isinstance(result, dict):
                for k in ["title", "theme", "characters", "setting", "story_summary", "moral"]:
                    if result.get(k):
                        fallback_sb[k] = result[k]
            return fallback_sb
        else:
            logger.info("OpenRouter chưa cấu hình key. Phân tích kịch bản thông minh bằng thuật toán cục bộ.")
            return get_smart_storyboard(user_input, age_group, art_style)
    except Exception as e:
        logger.error(f"Lỗi ở Director module: {str(e)}. Sử dụng bộ phân tích kịch bản thông minh dự phòng.")
        return get_smart_storyboard(user_input, age_group, art_style)

def parse_user_scenes(text: str) -> List[str]:
    """
    Tách các phân cảnh nếu người dùng đã chủ động phân chia trong nội dung nhập vào.
    Hỗ trợ các định dạng: 'Cảnh 1:...', 'Phân cảnh 1:...', '1. ...', 'Hồi 1:...', 'Bước 1:...'
    """
    cleaned = text.strip()
    
    # 1. Tìm các mẫu chia cảnh rõ ràng
    patterns = [
        r'(?:cảnh|phân cảnh|hồi|bước|phần)\s*\d+[\s:.-]+',
        r'(?:scene)\s*\d+[\s:.-]+',
        r'^\s*\d+[\s.)-]+\s+'
    ]
    
    # Kiểm tra xem có chứa từ khóa phân cảnh không
    scene_regex = re.compile(r'(?:(?:cảnh|phân cảnh|hồi|bước|phần|scene)\s*\d+[\s:.-]+|^\s*\d+[\s.)-]+\s+)', re.IGNORECASE | re.MULTILINE)
    splits = scene_regex.split(cleaned)
    matches = scene_regex.findall(cleaned)
    
    if len(splits) > 1:
        extracted = []
        for part in splits:
            p = part.strip()
            if p and len(p) > 5:
                extracted.append(p)
        if len(extracted) >= 2:
            return extracted

    # 2. Thử tách theo dòng mới nếu người dùng xuống dòng từng cảnh
    lines = [line.strip().lstrip("-*•123456789. ") for line in cleaned.split("\n") if len(line.strip()) > 8]
    if len(lines) >= 3:
        return lines[:3]
    
    # 3. Thử tách theo các câu văn dài
    sentences = [s.strip() for s in re.split(r'[.!?]+', cleaned) if len(s.strip()) > 10]
    if len(sentences) >= 3:
        return sentences[:3]
    elif len(sentences) == 2:
        return [sentences[0], sentences[1], f"Cả hai cùng nhau chia sẻ niềm vui và nhận được bài học ý nghĩa."]

    return []

def extract_setting_from_input(text: str) -> str:
    """
    Trích xuất bối cảnh không gian tự nhiên từ câu chuyện của người dùng.
    """
    t_lower = text.lower()
    if "rừng" in t_lower:
        return "Khu rừng xanh ngát với cỏ cây hoa lá và ánh nắng ấm áp"
    elif "trường" in t_lower or "lớp" in t_lower:
        return "Trường tiểu học khang trang với sân chơi rộn ràng tiếng cười"
    elif "biển" in t_lower or "đảo" in t_lower:
        return "Bờ biển xanh trong với bãi cát vàng óng ả"
    elif "nhà" in t_lower or "phòng" in t_lower:
        return "Ngôi nhà ấm cúng ngập tràn tình yêu thương"
    elif "suối" in t_lower or "sông" in t_lower:
        return "Dòng suối trong veo chảy róc rách giữa khung cảnh thiên nhiên thanh bình"
    elif "công viên" in t_lower or "vườn" in t_lower:
        return "Khu vườn hoa rực rỡ sắc màu với bướm lượn dập dờn"
    elif "vũ trụ" in t_lower or "sao" in t_lower:
        return "Không gian vũ trụ kỳ thú với muôn ngàn vì sao lấp lánh"
    elif "kỳ ảo" in t_lower or "phép thuật" in t_lower or "thần tiên" in t_lower or "xứ sở" in t_lower or "lâu đài" in t_lower or "mây" in t_lower:
        return "Xứ sở kỳ ảo diệu kỳ với những đám mây ngũ sắc và ánh sáng thần tiên lung linh"
    else:
        return "Khung cảnh thiên nhiên tươi sáng và thanh bình"

def extract_characters_from_input(user_input: str) -> List[Dict[str, str]]:
    """
    Trích xuất thông minh tất cả nhân vật từ ý tưởng người dùng (hỗ trợ tên ghép Tiếng Việt).
    """
    text = user_input.strip()
    text_lower = text.lower()
    
    characters: List[Dict[str, str]] = []
    found_names = set()

    # Nhận diện các danh từ nhân vật phổ biến trong truyện thiếu nhi Việt Nam
    known_entities = [
        ("Kỳ Lân", "Chú kỳ lân nhỏ có cánh lấp lánh, chiếc sừng ánh sáng diệu kỳ và bộ lông màu cầu vồng"),
        ("Rồng Con", "Chú rồng nhỏ màu ngọc bích đáng yêu, có đôi cánh nhỏ và đôi mắt tinh nghịch"),
        ("Tiên Nhỏ", "Cô tiên nhỏ bé có đôi cánh trong suốt như cánh chuồn chuồn và chiếc đũa thần lấp lánh"),
        ("Bé Bo", "Cậu bé nhỏ nhắn, đôi mắt sáng thông minh và chiếc áo khoác màu tím kỳ diệu"),
        ("Mèo Miu", "Chú mèo con lông vàng mềm mại, đôi mắt to tròn lấp lánh và chiếc nơ đỏ"),
        ("Mèo Bông", "Chú mèo nhỏ lông trắng muốt như bông, lanh lợi và hiền lành"),
        ("Thỏ Trắng", "Chú thỏ trắng xinh xắn với đôi tai dài và chiếc áo khoác màu xanh"),
        ("Thỏ Ngọc", "Cô thỏ nhỏ dễ thương, nhanh nhẹn với đôi mắt hồng đáng yêu"),
        ("Chú Rùa", "Bác rùa già hiền hậu mang chiếc mai vững chắc, tính cách kiên trì"),
        ("Rùa Con", "Chú rùa nhỏ chăm chỉ, luôn cần mẫn từng bước một"),
        ("Cún Bông", "Chú chó nhỏ lông xù đáng yêu, trung thành và luôn vui vẻ vẫy đuôi"),
        ("Cún Con", "Chú cún nhỏ tinh nghịch với đôi tai cụp và nụ cười rạng rỡ"),
        ("Bé Bi", "Cậu bé nhỏ nhắn, mặc áo thun xanh, nụ cười rạng rỡ và thích khám phá"),
        ("Bé Na", "Cô bé tóc buộc hai bên dễ thương, mặc váy hồng và rất tốt bụng"),
        ("Bé An", "Cậu bé thông minh, tốt bụng với ánh mắt sáng ngời"),
        ("Bác Voi", "Bác voi to lớn, tốt bụng luôn sẵn lòng giúp đỡ muôn loài"),
        ("Gấu Con", "Chú gấu nâu mập mạp, hiền lành và rất thích mật ong"),
        ("Sóc Nhỏ", "Chú sóc nhanh thoăn thoắt với chiếc đuôi xù ấm áp"),
        ("Chim Non", "Chú chim nhỏ lông xanh biếc với giọng hót líu lo trong trẻo"),
        ("Robot", "Chú Robot thân thiện với ánh mắt đèn LED sáng ngời"),
        ("Shin", "Cậu bé Shin ngộ nghĩnh, hài hước và rất yêu thương bạn bè"),
        ("Tom", "Chú mèo Tom lém lỉnh và nhanh nhẹn"),
        ("Jerry", "Chú chuột nhỏ Jerry thông minh và lanh lợi")
    ]

    for name, appearance in known_entities:
        if name.lower() in text_lower:
            if name not in found_names:
                found_names.add(name)
                characters.append({"name": name, "appearance": appearance})

    # Tìm kiếm tên riêng sau các từ xưng hô: bé, cậu bé, bạn, cô bé, chú, bác
    name_patterns = re.findall(r'(?:bé|cậu bé|cô bé|bạn|chú|bác)\s+([A-ZĐÊÔỨÁÀẢẠÃẮẰẲẶẴẤẦẨẬẪẾỀỂỆỄỐỒỔỘỖỨỪỬỰỮÍÌỈỊĨÓÒỎỌÕÚÙỦỤŨÝỲỶẠỸ][a-zA-Zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹđ]+(?:\s+[A-ZĐÊÔỨÁÀẢẠÃẮẰẲẶẴẤẦẨẬẪẾỀỂỆỄỐỒỔỘỖỨỪỬỰỮÍÌỈỊĨÓÒỎỌÕÚÙỦỤŨÝỲỶẠỸ][a-zA-Zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹđ]+)?)', text)
    for np in name_patterns:
        clean_np = np.strip()
        if clean_np and clean_np not in found_names and len(clean_np) > 1:
            found_names.add(clean_np)
            characters.append({
                "name": clean_np,
                "appearance": f"Nhân vật {clean_np} đáng yêu với trang phục rực rỡ, biểu cảm tươi vui"
            })

    # Nếu chưa tìm thấy nhân vật nào, phân tích từ các loài vật hoặc nhân vật chung
    if not characters:
        if "mèo" in text_lower:
            characters.append({"name": "Chú Mèo", "appearance": "Chú mèo nhỏ lông vàng cam mềm mại, mắt to tròn đáng yêu"})
        elif "thỏ" in text_lower:
            characters.append({"name": "Chú Thỏ", "appearance": "Chú thỏ trắng nhỏ nhắn, đôi tai dài xinh xắn"})
        elif "chó" in text_lower or "cún" in text_lower:
            characters.append({"name": "Chú Cún", "appearance": "Chú cún nhỏ lông nâu mềm, đôi mắt sáng và chiếc đuôi vẫy vui vẻ"})
        elif "cậu bé" in text_lower or "bé trai" in text_lower:
            characters.append({"name": "Cậu bé", "appearance": "Cậu bé nhỏ nhắn, mặc áo thun xanh, nụ cười nhân hậu"})
        elif "cô bé" in text_lower or "bé gái" in text_lower:
            characters.append({"name": "Cô bé", "appearance": "Cô bé dễ thương với tóc buộc nơ xinh và váy hoa rực rỡ"})
        else:
            characters.append({"name": "Bạn nhỏ", "appearance": "Nhân vật chính dễ thương, tốt bụng và tràn đầy niềm vui"})

    return characters[:3]

def get_smart_storyboard(user_input: str, age_group: str, art_style: str) -> Dict[str, Any]:
    """
    Tạo Storyboard thông minh bám sát 100% nội dung và phân cảnh của người dùng.
    """
    clean_prompt = user_input.strip()
    characters = extract_characters_from_input(clean_prompt)
    main_char_name = characters[0]["name"] if characters else "Bạn nhỏ"
    setting = extract_setting_from_input(clean_prompt)
    
    # Kiểm tra xem người dùng đã chia sẵn cảnh chưa
    user_scenes = parse_user_scenes(clean_prompt)
    
    if len(user_scenes) >= 3:
        # Sử dụng đúng 3 phân cảnh người dùng đưa ra
        scene1 = user_scenes[0]
        scene2 = user_scenes[1]
        scene3 = user_scenes[2]
    elif len(user_scenes) == 2:
        scene1 = user_scenes[0]
        scene2 = user_scenes[1]
        scene3 = f"Nhờ sự kiên trì và giúp đỡ lẫn nhau, {main_char_name} đã đạt được kết quả tuyệt vời và mang lại niềm vui cho tất cả mọi người."
    else:
        # Nếu là đoạn văn ngắn hoặc ý tưởng chung: chia 3 hồi logic liền mạch
        scene1 = f"Tại {setting.lower()}, {main_char_name} bắt đầu hành trình: {clean_prompt}."
        scene2 = f"{main_char_name} cùng các bạn tận tâm thực hiện, đối mặt với thử thách bằng lòng tốt và sự dũng cảm."
        scene3 = f"{main_char_name} hoàn thành trọn vẹn mục tiêu, nhận được sự yêu quý của bạn bè và đúc kết bài học quý giá."

    title_clean = clean_prompt.replace("\n", " ")
    title = f"Chuyến Phiêu Lưu Ý Nghĩa Của {main_char_name}"
    if len(title_clean) <= 40:
        title = f"{main_char_name}: {title_clean}"

    return {
        "title": title,
        "theme": "Lòng tốt, sự kiên trì và tình yêu thương",
        "characters": characters,
        "setting": setting,
        "story_summary": f"Câu chuyện kể về {main_char_name} trong bối cảnh {setting.lower()}. Qua những thử thách và hành động cụ thể, {main_char_name} đã cùng bạn bè tạo nên một kỷ niệm đẹp và học được bài học giáo dục sâu sắc.",
        "moral": "Hãy luôn nhân ái, kiên trì và sẵn sàng giúp đỡ mọi người xung quanh để cuộc sống luôn tràn ngập niềm vui.",
        "storyboard": [
            scene1,
            scene2,
            scene3
        ]
    }
