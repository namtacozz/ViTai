# ViTai - Trợ Lý Học Thuật Siêu Tốc (Ghost Mode)

ViTai là một ứng dụng System Tray trên Windows giúp bạn giải đáp các câu hỏi học thuật, trắc nghiệm ngay lập tức. Chỉ cần bôi đen văn bản ở bất kỳ đâu (Trình duyệt, Word, PDF) và nhấn `Alt+Q`, đáp án sẽ xuất hiện lơ lửng ngay cạnh con trỏ chuột mà không làm gián đoạn công việc của bạn.

## 🚀 Tính năng nổi bật

- **Tàng hình (Zero-UI):** Đáp án hiển thị dưới dạng văn bản lơ lửng, không có khung viền, không cướp focus của ứng dụng hiện tại (rất thân thiện khi copy/paste).
- **Hỗ trợ Đa nền tảng AI (Zero-Dependency):** Không sử dụng các SDK nặng nề. Gọi trực tiếp qua REST API siêu nhẹ, hỗ trợ đầy đủ:
  - Gemini (Google)
  - OpenAI (ChatGPT)
  - DeepSeek
  - Anthropic / Proxy nội bộ (như 9Router)
- **Hệ thống RAG siêu tốc:** Ném bất kỳ cuốn giáo trình/tài liệu PDF nào vào thư mục `docs/`. Lần chạy tiếp theo, ViTai sẽ tự động đọc, lập chỉ mục và tham khảo kiến thức từ sách đó để trả lời câu hỏi của bạn với độ chính xác tuyệt đối. (App được đóng gói kèm sẵn tài liệu *Modern Operating Systems 4th Edition*).
- **Auto-close:** Popup sẽ tự động biến mất khi bạn click chuột ra chỗ khác.
- **Tối ưu Trắc nghiệm:** Tự động nhận diện câu hỏi trắc nghiệm (MCQ) và chỉ đưa ra các ký tự đáp án (VD: A, B, C) một cách dứt khoát nhất.

## 📥 Tải về & Cài đặt nhanh (Dành cho người dùng)

1. Truy cập trang [Releases](https://github.com/namtacozz/ViTai/releases) và tải về file `ViTai_Release.zip` mới nhất.
2. Giải nén file ZIP.
3. Mở file `.env` (bằng Notepad). Xóa dấu `#` ở phần AI mà bạn muốn dùng và dán **API Key** của bạn vào.
4. Chạy file `ViTai.exe`. App sẽ xuất hiện dưới góc phải màn hình (System Tray).

## 🛠 Hướng dẫn Build từ Mã nguồn (Dành cho Dev)

Nếu bạn muốn tự chỉnh sửa mã nguồn và đóng gói:

1. Tạo và kích hoạt môi trường ảo (Virtual Environment):
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Thêm file sách (nếu có) vào thư mục `docs/`.

4. Đóng gói thành file `.exe`:
```bash
python scripts/build_windows.py
```
*Lưu ý: Nếu có lỗi Permission denied, hãy đảm bảo bạn đã thoát hoàn toàn ViTai.exe trước khi build.*

Thư mục `dist/ViTai/` sẽ chứa ứng dụng hoàn chỉnh để sử dụng.

## 🖱 Hướng dẫn sử dụng

1. Đảm bảo ViTai đang chạy ở System Tray.
2. Bôi đen một đoạn văn bản/câu hỏi ở bất kỳ ứng dụng nào.
3. Nhấn tổ hợp phím `Alt + Q`.
4. Xem đáp án hiện lên lơ lửng ngay cạnh con trỏ chuột.
5. Click chuột vào vị trí bất kỳ để tắt đáp án.
