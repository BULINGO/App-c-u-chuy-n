# HARNESS AI AGENTIC - Dự Án KHKT AI Kể Chuyện Tiểu Học

Hệ thống Agentic AI Kể chuyện dành cho học sinh tiểu học. Hệ thống tự động chuyển đổi ý tưởng người dùng thành kịch bản phân cảnh trực quan và hình ảnh minh họa bằng Qwen Image 3 Pro thông qua LangGraph điều phối.

---

## 🛠️ Kiến Trúc Khung Agentic

```text
Ý tưởng người dùng (Frontend Task 3)
         ↓
  Backend FastAPI
         ↓
LangGraph Workflow
   ├── 🧠 Model Đạo diễn (Director Agent) -> Sinh Storyboard JSON
   ├── 🎬 Model Chia cảnh (Scene Planner) -> Phân 3-5 phân cảnh chi tiết
   ├── 🎨 Model Tạo ảnh (Qwen Image 3 Pro via OpenRouter) -> Sinh ảnh hoạt hình nhất quán
   └── 🛡️ Model Đánh giá (Evaluator Agent) -> Kiểm duyệt nội dung cho tiểu học
         ↓
Kết quả hiển thị lên Frontend
```

---

## 📁 Cấu Trúc Thư Mục

```text
d:\APP AI/
├── SP dự thi.html                # Giao diện gốc Task 3 (Giữ nguyên)
├── frontend/
│   ├── index.html                # Giao diện Task 3 mở rộng hiển thị kết quả Agentic
│   ├── style.css                 # Styling giao diện hoạt hình & card phân cảnh
│   └── app.js                    # Đấu nối API FastAPI POST /api/story/create
├── backend/
│   ├── main.py                   # Khởi tạo FastAPI Server & CORS
│   ├── routes/
│   │   └── story.py              # API Router /api/story/create
│   └── services/
│       └── openrouter.py         # OpenRouter API Service (JSON Completion & Qwen Image Gen)
├── module/
│   ├── prompts.py                # System Prompts định dạng JSON chuẩn cho từng Agent
│   ├── director.py               # Model Đạo diễn kịch bản
│   ├── scene_planner.py          # Model Phân chia cảnh
│   ├── image_generator.py        # Model Sinh hình ảnh Qwen 3 Pro
│   └── evaluator.py              # Model Kiểm duyệt an toàn tiểu học
├── graph/
│   ├── state.py                  # StoryState TypedDict cho LangGraph
│   └── story_graph.py            # Khởi tạo sơ đồ LangGraph với conditional edge retry loop
├── .env                          # Lưu trữ OPENROUTER_API_KEY
├── requirements.txt              # Danh sách thư viện Python
└── README.md                     # Hướng dẫn chạy dự án
```

---

## 🚀 Hướng Dẫn Chạy Dự Án

### 1. Cấu hình API Key
Mở file `.env` và điền OpenRouter API Key của bạn:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```
*(Nếu chưa điền API Key, hệ thống sẽ tự động chạy chế độ thử nghiệm Mock Data để bạn thử nghiệm giao diện).*

### 2. Cài đặt môi trường
Mở Terminal tại thư mục `d:\APP AI`:
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy Máy chủ Backend
Chạy lệnh uvicorn:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Trải nghiệm trên Trình duyệt
- Trực tiếp mở file `frontend/index.html` hoặc `SP dự thi.html` bằng trình duyệt web.
- Hoặc truy cập đường dẫn địa chỉ local: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
