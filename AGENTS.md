# QUY TẮC PHÁT TRIỂN & BẢO MẬT HỆ THỐNG ViTai CHO AI AGENTS

> **QUAN TRỌNG & BẮT BUỘC TUÂN THỦ ĐỐI VỚI TẤT CẢ CÁC AGENT / DEVELOPER**:

---

## 1. Bảo Vệ Tuyệt Đối Dữ Liệu Tài Khoản & Cơ Sở Dữ Liệu (User Database Integrity)
- **Tài khoản Quản Trị Viên (Admin) gốc**: Duy nhất `vinguoitai` (Mật khẩu: `vit24052005`).
- **Chính sách phần cứng Admin**: Tài khoản `admin` (`vinguoitai`) **KHÔNG BAO GIỜ bị khóa cố định địa chỉ MAC** hay bị chặn MAC khi đăng nhập từ các máy tính khác nhau.
- **Chính sách tài khoản User thường**: Tự động gán và khóa cố định địa chỉ MAC trong lần đăng nhập đầu tiên.
- **NGHIÊM CẤM**:
  1. **Không tự ý thêm, sửa, xóa, hoặc seed các tài khoản thử nghiệm / tài khoản mẫu** (như `admin/admin`, `test/test`, `alice`, `bob`, `charlie`...) vào cơ sở dữ liệu Supabase Cloud hoặc file `users.json` thực tế.
  2. **Mọi test case (pytest)** phải sử dụng fixture cô lập `tmp_path` với `CloudConfig(is_enabled=False)` để không bao giờ can thiệp vào cơ sở dữ liệu Supabase sản xuất.
  3. **Không thay đổi các trường dữ liệu người dùng hiện có** trên Supabase Database nếu không có yêu cầu cụ thể từ người dùng.

---

## 2. Giao Diện & Trải Nghiệm Người Dùng (UI / UX Standards)
- **Giao diện thuần text sạch sẽ (Linux / Windows)**:
  - Hạn chế tối đa việc nhúng các biểu tượng emoji/icon không tương thích lên font chữ hệ thống Linux/Windows.
  - Sử dụng văn bản rõ ràng, súc tích, giao diện tối giản tinh tế (Dark mode carbon & Warm amber).
- **Phím tắt kích hoạt & Phím chuột**:
  - Gộp chung phím bàn phím và nút chuột vào 1 nút duy nhất.
  - Hỗ trợ gán trực tiếp phím bàn phím (Ctrl+Q, Alt+Q...) hoặc nút chuột (mouse_right, mouse_middle, mouse_x1, mouse_x2...).
- **Chọn Màu Sắc (Color Wheel)**:
  - Ô swatch màu bên cạnh ô chọn màu là nút bấm trực tiếp để mở Bảng Chọn Màu Tròn 360° (Photoshop / Aseprite Style).
- **Lưu Cấu Hình (Persistence)**:
  - Giữ nguyên Model AI (`config.model`), Provider, Hotkey, Theme và màu sắc đã lưu của người dùng cho mọi lần khởi động app tiếp theo.

---

## 3. Kiến Trúc Hybrid Cloud Auth Client
- Ứng dụng hoạt động với kiến trúc Hybrid Offline/Online Fallback:
  - Cache cục bộ: `~/.vitai/users.json`
  - Cloud Backend: Supabase PostgREST Client nhúng sẵn (`https://yndwxcnedlilmsbbydvb.supabase.co`) sử dụng chuẩn `urllib.request` (0 external dependencies).
