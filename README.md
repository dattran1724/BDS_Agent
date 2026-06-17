# Siêu Cò AI - Agent Viết Content Bất Động Sản Tự Động

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

### Thiết lập vào dự án:
1. Tại thư mục gốc của dự án, bạn sẽ thấy file `.env.example`.
2. Copy file đó và đổi tên thành `.env` (Nếu dùng Windows, bạn có thể mở file này bằng Notepad và Save As thành `.env`).
3. Mở file `.env` lên và dán Key của bạn vào dòng `OPENAI_API_KEY`:
   ```env
   OPENAI_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   OPENAI_API_BASE=https://api.groq.com/openai/v1
   ```

*(Lưu ý: Mặc dù tên biến là OPENAI nhưng do cấu trúc code dùng chuẩn API tương thích của OpenAI để gọi Groq, bạn BẮT BUỘC phải dùng tên biến này và giữ nguyên dòng OPENAI_API_BASE)*.

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

## ☁️ Hướng Dẫn Deploy Lên Mạng (Cho người khác Test)

### CÁCH 1: GIẢI PHÁP TỐC ĐỘ BÀN THỜ (Dùng Ngrok - Khuyên Dùng Cho Demo Nhanh)
Cách này giúp bạn biến luôn máy tính của bạn thành Server. Mất đúng 1 phút là có link gửi cho khách, không cần set up Cloud phức tạp. Khách truy cập bình thường miễn là máy tính của bạn vẫn đang mở và đang chạy 2 lệnh Terminal ở trên.

1. Vào [ngrok.com](https://ngrok.com/) tạo 1 tài khoản miễn phí và tải file `.exe` về máy tính.
2. Trên trang chủ ngrok, copy lệnh Authtoken và dán vào Terminal của bạn:
   ```bash
   ngrok config add-authtoken <mã_token_của_bạn>
   ```
3. Mở Terminal lên gõ lệnh:
   ```bash
   ngrok http 8501
   ```
4. Ngrok sẽ cấp cho bạn một link dạng `https://xxxx.ngrok-free.app`. Bạn chỉ cần copy link này gửi cho bất kỳ ai!


### CÁCH 2: DEPLOY ĐÁM MÂY LÂU DÀI (Render + Streamlit Cloud)
Nếu bạn muốn hệ thống chạy 24/7 mà không cần mở máy tính cá nhân.

**Bước 1: Đẩy code lên GitHub**
Tạo 1 Repository trên GitHub và đẩy toàn bộ thư mục code lên (Lưu ý: Git bỏ qua file `.env`).

**Bước 2: Deploy Backend (FastAPI)**
- Tạo tài khoản [Render.com](https://render.com) hoặc [Railway.app](https://railway.app).
- Tạo Web Service mới -> Kết nối với Github của bạn.
- Lệnh chạy (Start Command): `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Vào mục Environment Variables điền 2 biến môi trường y hệt trong file `.env`:
  `OPENAI_API_KEY`: <Điền key Groq của bạn>
  `OPENAI_API_BASE`: `https://api.groq.com/openai/v1`
- Sau khi Deploy thành công, Render sẽ cấp link Backend (VD: `https://bds-backend.onrender.com`).

**Bước 3: Deploy Frontend (Streamlit Cloud)**
- Mở file `frontend/app.py` ra. Ở dòng số 5, sửa lại cái link Backend nội bộ thành link Render vừa cấp:
  `BACKEND_URL = "https://bds-backend.onrender.com"`
- Đẩy phần code vừa sửa lên Github.
- Vào [share.streamlit.io](https://share.streamlit.io/), đăng nhập bằng Github, chọn kho chứa và file `frontend/app.py` rồi bấm Deploy.
- Streamlit sẽ cấp cho bạn 1 đường link cực đẹp để gửi cho khách hàng.

---

## 📖 Hướng Dẫn Sử Dụng Agent Trên Giao Diện

Khi giao diện chat mở lên, quy trình làm việc với Agent sẽ trải qua **5 bước**:

1. **Nhập liệu thô (Input):** Bạn chỉ cần ném bất cứ thông tin gì bạn có về BĐS vào ô chat (VD: *"Bán căn Shophouse Vinhome 85m2, đang cho Highland thuê 35tr, giá cắt lỗ 9.5 tỷ, sổ đỏ trao tay"*).
2. **AI Trích xuất & Hỏi thêm (Extractor):** AI sẽ tự động bóc tách thông tin thành các trường dữ liệu (Giá, Diện tích, Tiện ích...). Nếu thiếu thông tin quan trọng, nó sẽ dừng lại và hỏi bạn. Bạn có thể điền bảng hoặc chat trả lời.
3. **Xác nhận thông tin & Sửa lỗi (Live Edit):** Hệ thống sẽ hiện một bảng tóm tắt thông tin. Nếu có thông tin sai hoặc viết sai chính tả, bạn hãy bấm nút **"✏️ Chỉnh sửa"** để sửa trực tiếp rồi bấm Xác nhận.
4. **Chọn Hướng Tiếp Cận (Strategist):** Dựa vào thông tin, AI sẽ đẻ ra 3 góc viết (Angles) khác nhau. Bạn bấm chọn 1 hướng ưng ý nhất.
5. **Sinh bài viết (Writer):** AI sẽ viết ra một bài đăng Facebook hoàn chỉnh chuẩn văn phong Môi giới thực chiến. Bạn có thể tải bài viết về máy dạng file Text.
