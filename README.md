<div align="center">

# 👻 ViTai v3.3.0 — Vì Người Tài
### *Trợ lý AI giải trắc nghiệm & phân tích câu hỏi siêu tốc — Ẩn mình tuyệt đối*

[![Version](https://img.shields.io/badge/Version-v3.3.0-E09F5E?style=for-the-badge&logo=rocket&logoColor=white)](https://github.com/namtacozz/ViTai/releases)
[![Linux](https://img.shields.io/badge/Linux-Fedora%2044%20%2F%20Ubuntu-51A2DA?style=for-the-badge&logo=linux&logoColor=white)](https://getfedora.org/)
[![Windows](https://img.shields.io/badge/Windows-10%20%2F%2011-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

[Tải về & Cài đặt](#-tải-về--cài-đặt-nhanh) • [Cách sử dụng](#-hướng-dẫn-sử-dụng) • [Tài khoản & Kích hoạt](#-tài-khoản--cơ-chế-hoạt-động) • [Tính năng nổi bật](#-tính-năng-cốt-lõi)

---

</div>

## 🌟 Giới thiệu

**ViTai** ("Vì Người Tài") là công cụ hỗ trợ học tập và giải đề thi trắc nghiệm thông minh. Ứng dụng hoạt động theo cơ chế **ẩn mình tuyệt đối (Ghost Assistant)**: chỉ cần bôi đen câu hỏi trên màn hình, đáp án chính xác sẽ xuất hiện ngay lập tức mà không làm gián đoạn bài làm của bạn.

* 🎯 **Hiển thị trực tiếp**: Chỉ xuất hiện duy nhất 1 ký tự đáp án (`A`, `B`, `C`, `D`...) nổi nhẹ ngay sát đuôi đoạn bôi đen.
* 👻 **Tàng hình hoàn toàn**: Không icon thanh tác vụ (Taskbar), không hiện trong `Alt + Tab`, click chuột bất kỳ là biến mất.
* ⚡ **Phản hồi tức thì**: Kết nối trực tiếp các mô hình AI hàng đầu (Gemini, ChatGPT, Kiro, DeepSeek...) để đưa ra câu trả lời trong tích tắc.

---

## 📥 Tải về & Cài đặt nhanh

Tải bản phát hành mới nhất tại mục [Releases](https://github.com/namtacozz/ViTai/releases):

### 🪟 Dành cho Windows (10 / 11)
1. Tải file **`ViTai-Windows-x64.zip`** (hoặc `ViTai-v3.3.0-windows-x64.zip`).
2. Giải nén vào một thư mục bất kỳ.
3. Chạy file **`ViTai.exe`** để bắt đầu sử dụng (không cần cài đặt phần mềm phụ trợ).

### 🐧 Dành cho Linux (Fedora, Ubuntu, Debian, Arch...)
1. Tải file **`ViTai-Linux-x86_64.tar.gz`** (hoặc `ViTai-v3.3.0-linux-x86_64.tar.gz`).
2. Giải nén và mở Terminal trong thư mục vừa giải nén:
   ```bash
   tar -xvf ViTai-*-linux-x86_64.tar.gz
   cd ViTai
   ./ViTai
   ```
> 💡 **Mẹo cho người dùng Linux (Wayland / Fedora)**:
> Để bắt tọa độ chuột và bôi đen mượt mà nhất, hãy cấp quyền thiết bị input một lần duy nhất:
> ```bash
> sudo usermod -aG input $USER
> ```
> *(Sau đó đăng xuất và đăng nhập lại máy tính)*.

---

## 🎮 Hướng dẫn sử dụng

### 1. Lấy đáp án câu hỏi
1. Dùng chuột **bôi đen toàn bộ câu hỏi và các phương án trả lời** trên trình duyệt hoặc tài liệu.
2. Nhấn phím tắt kích hoạt (mặc định: **`Alt + Q`** hoặc nút chuột bạn đã gán).
3. Ký tự đáp án (ví dụ: `A`) sẽ hiện nổi ngay sát đuôi phần bôi đen.
4. **Nhấp chuột bất kỳ** trên màn hình để ẩn đáp án.

> ⚡ **Chế độ Fast Mode (Tự động)**: Bật tính năng này trong cài đặt, ViTai sẽ tự phân tích và hiện đáp án ngay khi bạn vừa nhả chuột bôi đen xong (không cần bấm phím tắt).

### 2. Mở bảng Cài Đặt (Menu)
* Bấm tổ hợp phím **`Ctrl + Alt + V`** bất kỳ lúc nào để mở bảng điều khiển.
* **Thẻ Vỏ (Giao diện & Phím tắt)**: 
  * Bấm vào ô phím tắt để đổi sang phím bất kỳ hoặc gán trực tiếp vào nút chuột (Chuột phải, Chuột giữa, Nút phụ Back/Forward).
  * Chọn màu chữ hiển thị bằng Bảng màu tròn 360°, đổi cỡ chữ, xem thử trên nền Đen/Trắng.
  * Bật/tắt chế độ tự động phân tích (Fast Mode) và bộ nhớ đệm (Cache).
* **Thẻ Lõi (Trí tuệ AI)**: 
  * Chọn nguồn AI muốn sử dụng: Google Gemini, OpenAI/ChatGPT Codex, Kiro AI, 9Router, DeepSeek...
  * Nhập API Key hoặc đăng nhập tài khoản OAuth.
* **Thẻ Quản Trị**: Quản lý thông tin tài khoản, danh sách thành viên và đổi mật khẩu.

---

## 👤 Tài khoản & Cơ chế hoạt động

Ứng dụng sử dụng hệ thống tài khoản để lưu giữ cấu hình cá nhân và đồng bộ dữ liệu an toàn:

### 1. Kích hoạt tài khoản tự động qua VietQR (50.000đ)
* Người dùng mới mở app $\rightarrow$ Nhấn nút **`Đăng Ký Tài Khoản (Quét QR 50.000đ)`** tại màn hình khóa.
* Quét mã VietQR chuyển khoản chính xác 50.000đ tới **MBBank (`99924052005 - LE VO THANH NAM`)** với cú pháp nội dung tự động `VITAIxxxxxx`.
* Hệ thống tự động xác nhận giao dịch thành công và **mở khóa tài khoản ngay lập tức 24/7** mà không cần chờ duyệt thủ công.

### 2. Cơ chế khóa thiết bị (Bảo vệ tài khoản)
* **Tài khoản người dùng thường**: Sẽ tự động gán và khóa cố định với địa chỉ phần cứng (MAC) của máy tính đăng nhập lần đầu tiên. Điều này giúp bảo mật và tránh chia sẻ tài khoản trái phép.
* **Khi đổi máy tính mới**: Bạn chỉ cần liên hệ Quản trị viên (Admin) để thực hiện thao tác gỡ khóa (Reset MAC) là có thể đăng nhập trên máy tính mới bình thường.

### 3. Tài khoản Quản trị viên (Admin)
* **Tài khoản Admin gốc**: `vinguoitai` (Mật khẩu mặc định: `vit24052005`).
* **Đặc quyền Admin**:
  * Đăng nhập tự do trên mọi máy tính khác nhau (không bị khóa cứng thiết bị).
  * Toàn quyền truy cập tab **Quản Trị**: Cấp phát tài khoản mới, xóa người dùng, đổi mật khẩu và mở khóa thiết bị (Reset MAC) cho học viên.

---

## ✨ Tính năng cốt lõi

* 👻 **Ghost Direct Overlay**: Lớp hiển thị trong suốt 100%, không khung nền, không chiếm tiêu điểm chuột hay bàn phím.
* 🖱️ **Gán phím linh hoạt**: Hỗ trợ mọi tổ hợp bàn phím hoặc nút chuột chuyên dụng.
* 🎨 **Bảng màu tròn 360°**: Dễ dàng tùy biến màu chữ đáp án tương phản rõ nét trên mọi nền trang web.
* 💾 **Lưu bền vững**: Giữ nguyên toàn bộ cấu hình, model AI, phím tắt và theme qua các lần sử dụng.
* 🧠 **Bộ nhớ đệm thông minh**: Trả lời tức thì **0ms** đối với các câu hỏi đã từng giải trước đó.

---

## 📄 Bản quyền (License)

Phát hành theo giấy phép [MIT License](LICENSE).  
Phát triển bởi: **Vì Người Tài (ViTai Team)**.
