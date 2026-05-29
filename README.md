<div align="center">
  <img src="assets/icon.ico" width="100" alt="ViTai Logo" />
  
  # ViTai
  ### Trợ Lý Học Thuật Lơ Lửng (Ghost Mode)
  
  ![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
  ![Windows](https://img.shields.io/badge/Windows-Supported-0078D6?style=for-the-badge&logo=windows)
  ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
</div>

---

**ViTai** là một ứng dụng System Tray tối giản trên Windows, được thiết kế chuyên biệt để giúp bạn giải đáp các câu hỏi học thuật, trắc nghiệm ngay lập tức. Chỉ cần bôi đen văn bản ở bất kỳ đâu (Trình duyệt, Word, PDF), đáp án sẽ xuất hiện lơ lửng ngay đuôi con trỏ chuột dưới dạng tooltip tinh tế mà không hề làm gián đoạn công việc của bạn.

## 🚀 Tính năng nổi bật

- 👻 **Trải nghiệm Tàng hình (Zero-UI):** Đáp án hiển thị dưới dạng văn bản lơ lửng (không viền, không nền đặc), xuất hiện chính xác ngay tại vị trí thả chuột (như một tooltip) và không bao giờ cướp focus của ứng dụng hiện tại.
- ⚙️ **Giao diện Cài đặt (Settings UI):** Dễ dàng cấu hình ứng dụng bằng cách nhấp chuột phải vào icon ở thanh Taskbar. Hỗ trợ:
  - Tùy chỉnh Phím tắt (VD: `Alt+Q`, `Ctrl+Shift+E`,...)
  - Chọn Font chữ, Cỡ chữ, và Nhập mã màu Hex tùy ý (VD: `#212529`, `#ff0000`).
  - Cài đặt **Khởi động cùng Windows**.
  - Giao diện Cài đặt tự động đồng bộ theo nền Sáng/Tối (Light/Dark mode) của Windows.
- ⚡ **Tự Động Bắt Từ & Cache Thông Minh:** Hỗ trợ tính năng tự động gọi AI ngay khi bạn vừa nhả chuột (không cần nhấn phím). Kết hợp với **Bộ nhớ đệm (Cache)**, ViTai sẽ nhớ đáp án cũ và phản hồi tức thì (`0ms`) nếu bạn bôi đen lại câu hỏi đó.
- 🧠 **Hỗ trợ Đa nền tảng AI (Zero-Dependency):** Hoạt động siêu nhẹ nhờ gọi trực tiếp qua REST API (không dùng SDK cồng kềnh). Hỗ trợ:
  - Gemini (Google)
  - OpenAI (ChatGPT)
  - DeepSeek
  - Anthropic / Proxy nội bộ (như 9Router)
- 📚 **Hệ thống RAG Tự Động:** Ném bất kỳ cuốn giáo trình/tài liệu PDF nào vào thư mục `docs/`. ViTai sẽ tự động đọc, lập chỉ mục và tham khảo kiến thức từ tài liệu đó để trả lời chính xác. (Bao gồm sẵn sách *Modern Operating Systems 4th Edition*).
- ✨ **Tối ưu Trắc nghiệm:** Thuật toán thông minh tự động nhận diện câu hỏi trắc nghiệm (MCQ) và đưa ra các ký tự đáp án (VD: A, B, C) một cách dứt khoát nhất.

## 📥 Tải về & Cài đặt nhanh

1. Truy cập trang [Releases](https://github.com/namtacozz/ViTai/releases) và tải về file `ViTai_Release.zip` mới nhất.
2. Giải nén toàn bộ thư mục ZIP.
3. Mở file `.env` (bằng Notepad). Xóa dấu `#` ở phần AI mà bạn muốn dùng và dán **API Key** của bạn vào.
4. Chạy file `ViTai.exe`. Ứng dụng sẽ chạy ngầm dưới góc phải màn hình (System Tray).

## 🖱 Hướng dẫn sử dụng

1. Đảm bảo ViTai đang chạy ở System Tray.
2. Bôi đen một đoạn văn bản/câu hỏi ở bất kỳ ứng dụng nào.
3. **Cách 1 (Tự động):** Nếu bật "Tự động trả lời ngay khi bôi đen text" trong phần Cài đặt, đáp án sẽ tự động nhảy ra sau 150ms.
4. **Cách 2 (Thủ công):** Nhấn tổ hợp phím mặc định `Alt + Q` (hoặc phím bạn đã tự cài).
5. Xem đáp án xuất hiện lơ lửng ngay dưới đuôi con trỏ chuột của bạn.
6. Click chuột ra ngoài hoặc ấn `Esc` để tắt đáp án.

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
*Lưu ý: Nếu có lỗi Permission denied, hãy đảm bảo bạn đã thoát hoàn toàn (chuột phải > Thoát) `ViTai.exe` trước khi build.*

Thư mục `dist/ViTai/` sẽ chứa ứng dụng hoàn chỉnh để sử dụng.
