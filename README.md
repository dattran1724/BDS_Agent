# Agent Viết Content Bất Động Sản Tự Động

Đây là hệ thống AI Agent hoàn chỉnh (Frontend + Backend) được thiết kế chuyên biệt để tự động hóa quy trình viết Content bán hàng Facebook cho các Môi giới Bất Động Sản tại Việt Nam.

Hệ thống ứng dụng kiến trúc **Human-in-the-loop (HITL)** của LangGraph, cho phép con người can thiệp vào giữa quá trình AI suy nghĩ để chỉnh sửa thông tin, định hướng góc viết và tinh chỉnh văn phong.

---

## 🚀 Công Nghệ Sử Dụng

- **Backend**: FastAPI, Python 3.12
- **Agent Framework**: LangGraph, LangChain
- **Frontend (Giao diện người dùng)**: Streamlit
- **Mô hình AI (LLM)**: Hỗ trợ OpenAI, Groq (LLaMA-3), Anthropic...
- **Quản lý Package**: `uv`

---

## 🔑 Hướng Dẫn Cấu Hình API Key (Groq / OpenAI)

Để AI có thể hoạt động, bạn cần cung cấp một API Key. Hệ thống đang được cấu hình mặc định dùng **Groq** (miễn phí, tốc độ cực nhanh, dùng model LLaMA-3).

### Cách lấy Groq API Key miễn phí:
1. Truy cập trang web: [https://console.groq.com/](https://console.groq.com/)
2. Đăng nhập bằng tài khoản Google hoặc GitHub.
3. Ở menu bên trái, chọn mục **API Keys**.
4. Bấm nút **Create API Key**.
5. Đặt tên bất kỳ (VD: `bds-agent-key`) và bấm Create.
6. **Copy ngay đoạn mã (Bắt đầu bằng `gsk_...`)** vì nó chỉ hiện 1 lần duy nhất.

---

## 💻 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng Nội Bộ (Local)

### Bước 1: Cài đặt thư viện
Đảm bảo máy bạn đã cài Python và công cụ `uv`. Mở Terminal (Command Prompt / PowerShell) tại thư mục dự án và gõ:
```bash
uv sync
```

### Bước 2: Khởi động Backend (FastAPI)
Mở một Terminal **thứ nhất**, gõ lệnh sau để chạy Server xử lý AI:
```bash
uv run uvicorn app.main:app --reload
```
*(Đợi đến khi màn hình hiện chữ `Application startup complete`)*.

### Bước 3: Khởi động Frontend (Streamlit UI)
Mở thêm một Terminal **thứ hai** (Giữ nguyên Terminal 1 đang chạy Backend), gõ lệnh sau để mở giao diện chat:
```bash
uv run streamlit run frontend/app.py
```
Trình duyệt sẽ tự động bật lên ở địa chỉ: `http://localhost:8501`.

---

## 📖 Hướng Dẫn Sử Dụng Agent Trên Giao Diện

Dán key vào ô API Key bên trái màn hình

Khi giao diện chat mở lên, quy trình làm việc với Agent sẽ trải qua **5 bước**:

1. **Nhập liệu thô (Input):** Bạn chỉ cần ném bất cứ thông tin gì bạn có về BĐS vào ô chat (VD: *"Bán căn Shophouse Vinhome 85m2, đang cho Highland thuê 35tr, giá cắt lỗ 9.5 tỷ, sổ đỏ trao tay"*).
2. **AI Trích xuất & Hỏi thêm (Extractor):** AI sẽ tự động bóc tách thông tin thành các trường dữ liệu (Giá, Diện tích, Tiện ích...). Nếu thiếu thông tin quan trọng, nó sẽ dừng lại và hỏi bạn. Bạn có thể điền bảng hoặc chat trả lời.
3. **Xác nhận thông tin & Sửa lỗi (Live Edit):** Hệ thống sẽ hiện một bảng tóm tắt thông tin. Nếu có thông tin sai hoặc viết sai chính tả, bạn hãy bấm nút **"✏️ Chỉnh sửa"** để sửa trực tiếp rồi bấm Xác nhận.
4. **Chọn Hướng Tiếp Cận (Strategist):** Dựa vào thông tin, AI sẽ đẻ ra 3 góc viết (Angles) khác nhau. Bạn bấm chọn 1 hướng ưng ý nhất.
5. **Sinh bài viết (Writer):** AI sẽ viết ra một bài đăng Facebook hoàn chỉnh chuẩn văn phong Môi giới thực chiến. Bạn có thể tải bài viết về máy dạng file Text.
