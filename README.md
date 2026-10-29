# 🪷 HOA SEN HOME — SALES PRO 2026
### Hệ Thống Bán Hàng & Tra Cứu Thiết Bị Nhà Tắm & Nhà Bếp Miền Trung

Hệ thống phần mềm và website chuyên nghiệp phục vụ tra cứu bảng giá đa cấp, danh mục sản phẩm, hình ảnh thực tế và số liệu tồn kho theo thời gian thực cho **Tập đoàn Hoa Sen — Hệ thống Siêu thị Nội thất Hoa Sen Home (Chi nhánh Miền Trung)**.

---

## 👨‍💻 Tác Giả & Bản Quyền
* **Thiết kế, phát triển và cập nhật giá**: **NGUYỄN CÔNG NGUYÊN**
* 📞 **Hotline**: `0344 979 307`
* 💬 **Zalo**: `0934 811 307`
* © **2026 NGUYỄN CÔNG NGUYÊN**. All Rights Reserved.

---

## ✨ Tính Năng Nổi Bật

1. **Tra Cứu Nhanh & Lọc Đa Chiều (1.804 Sản Phẩm)**:
   * Tìm kiếm tức thì theo Tên sản phẩm, Mã sản phẩm, Mã Item ERP, Kích thước, Nhóm hàng, Thương hiệu.
   * Hiển thị bảng giá đa cấp linh hoạt (Giá bán lẻ, Giá thầu thợ, Giá đại lý cấp 1-4, Giá NPP...).
   * Thư viện ảnh thực tế đạt tỷ lệ bao phủ **69.3% (1.250 sản phẩm có ảnh thật)**.
   * Tích hợp tính năng Zoom ảnh Lightbox sắc nét, so sánh thông số 4 sản phẩm cùng lúc.

2. **🔥 Album & Combo Tiết Kiệm (Hot 2026)**:
   * 23 danh mục sản phẩm kèm ảnh đại diện chụp Studio sắc nét.
   * Gợi ý các bộ Combo thiết bị vệ sinh trọn gói tiết kiệm chi phí cho khách hàng và công trình.

3. **📊 Bảng Giá & Tồn Kho Thực Tế 17 Kho Miền Trung**:
   * Phân định chuẩn xác theo mô hình phân phối của Tập đoàn:
     * **7 Chi nhánh Miền Trung (HTPP MT)**: Tổng **27.267** sản phẩm (Đắk Lắk, Gia Lai, Khánh Hòa, Đà Nẵng, Quảng Ngãi, Quảng Trị, Huế).
     * **3 Tổng kho Điều phối Miền Trung (Tổng TK)**: Tổng **39.072** sản phẩm (TK Đà Nẵng, NM Nhơn Hòa, TK Đắk Lắk).
     * **Tổng Tồn Miền Trung**: **66.339** sản phẩm (Chuẩn 100% cột Tổng tồn kho Excel).
     * **Nhà máy & Tổng kho vệ tinh**: NM Bình Dương, TK Cần Thơ, NM Nghệ An, NM Hà Nam (Tổng toàn quốc: **118.950** sản phẩm).

4. **⚙️ Cổng Quản Trị Hệ Thống (`/admin`)**:
   * **Bảo mật**: Màn hình đăng nhập quản trị viên (Mật khẩu mặc định: `hoasenhome@2026`).
   * **Upload Excel 1GB**: Kéo & thả file Excel mới để cập nhật bảng giá và tồn kho tự động.
   * **Auto-Backup & Restore**: Tự động sao lưu file cũ kèm mốc thời gian, khôi phục bản cũ 1-click.
   * **Live Terminal Log**: Giám sát tiến trình đọc và phân tích dữ liệu trực tiếp trên màn hình.

5. **💻 Đóng Gói Thành App Desktop Windows (`HoaSenHome.exe`)**:
   * Mở trực tiếp như một ứng dụng native máy tính, không cần cài đặt Python.
   * Có lối tắt ngoài màn hình chính (Desktop Shortcut).

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Chạy Trực Tiếp Bằng File .EXE:
* Bấm đúp vào file `HoaSenHome.exe` trong thư mục gốc hoặc biểu tượng `Hoa Sen Home` ngoài Desktop.
* **Cách mở Đăng Nhập Quản Trị Admin trên App EXE**:
  1. Bấm nút **⚙️ Quản Trị** màu vàng nổi bật ở góc trên bên phải thanh Header.
  2. Hoặc bấm nút nổi tròn **⚙️ Quản Trị Admin (F2)** ở góc dưới bên trái màn hình.
  3. Hoặc nhấn phím tắt **`F2`** hoặc tổ hợp phím **`Ctrl + Shift + A`** ở bất kỳ màn hình nào.
  4. Mật khẩu đăng nhập mặc định: `hoasenhome@2026`. Sau khi vào có thể đổi mật khẩu mới tùy ý.

### 2. Chạy Qua File Script (.bat):
* Bấm đúp vào file `app/start_server.bat`
* Truy cập Website Bán Hàng: `http://localhost:8080/`
* Truy cập Cổng Quản Trị: `http://localhost:8080/admin` (Mật khẩu: `hoasenhome@2026`)

### 3. Cập Nhật Dữ Liệu Từ File Excel Nguồn:
1. Đặt file Excel mới có tên `THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP.xlsx` vào thư mục gốc.
2. Hoặc truy cập `http://localhost:8080/admin` để kéo thả trực tiếp file Excel mới lên hệ thống.
3. Bấm **🚀 TIẾN HÀNH CẬP NHẬT HỆ THỐNG** để tự động đồng bộ.

