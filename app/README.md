# 🛁 HSH Tra Cứu Sản Phẩm

> **Website tra cứu thiết bị nhà tắm & nhà bếp** dành cho nhân viên kinh doanh Hoa Sen Home

---

## 🚀 Khởi Động Nhanh

### Cách 1: Chạy file BAT (dễ nhất)
```
Double-click vào file:  start_server.bat
```
→ Trình duyệt tự mở tại `http://localhost:8080`

### Cách 2: Dùng lệnh Python
```bash
cd d:\nhà tắm\app
python -m http.server 8080
# Mở trình duyệt: http://localhost:8080
```

---

## 📦 Cấu Trúc Thư Mục

```
app/
├── index.html              ← Trang chính
├── css/style.css           ← Giao diện
├── js/app.js               ← Logic ứng dụng
├── data/products.json      ← Dữ liệu sản phẩm (1.663 SP)
├── sw.js                   ← Service Worker (offline)
├── manifest.json           ← PWA manifest
├── update_data.py          ← Script cập nhật dữ liệu
├── start_server.bat        ← Khởi động server
└── cap_nhat_du_lieu.bat    ← Cập nhật dữ liệu từ Excel
```

---

## 🔄 Cập Nhật Dữ Liệu Khi Excel Thay Đổi

```
Double-click:  cap_nhat_du_lieu.bat
```

Hoặc chạy thủ công:
```bash
python update_data.py
```

---

## ✨ Tính Năng

| Tính năng | Mô tả |
|-----------|-------|
| 🔍 **Tìm kiếm thông minh** | Tìm theo tên, mã SP, thương hiệu — hỗ trợ tìm mờ |
| 💰 **Bảng giá đa cấp** | Lẻ, thầu thợ, đại lý C1-C4, NPP C1-C3 |
| 📦 **Tồn kho theo khu vực** | HTPP MT, Khánh Hòa, Đắk Lắk, Gia Lai, Đà Nẵng... |
| 🔥 **Hàng HOT** | Đánh dấu sản phẩm bán chạy |
| ❤️ **Yêu thích** | Lưu SP hay dùng để truy cập nhanh |
| ⚖️ **So sánh** | So sánh tối đa 4 sản phẩm cùng lúc |
| 📋 **Báo giá** | Tạo báo giá, xuất CSV/PDF, copy text gửi Zalo |
| 📤 **Chia sẻ** | Gửi link sản phẩm cho khách hàng |
| 📴 **Offline** | Hoạt động khi không có internet (PWA) |
| 📱 **Di động** | Tối ưu cho điện thoại và máy tính bảng |

---

## ⌨️ Phím Tắt

| Phím | Chức năng |
|------|-----------|
| `/`  | Focus vào ô tìm kiếm |
| `Esc` | Xóa ô tìm kiếm / đóng modal |

---

## 📊 Dữ Liệu

- **1.663 sản phẩm** từ 16 thương hiệu
- **16 thương hiệu**: INAX, TOTO, American Standard, CAESAR, ROCA, ARROW, TUSLO, LUSHINE, HAFELE, TEKA, KITTO, Sơn Hà, VIGLACERA, Toàn Mỹ, Hùng Anh, Tân An Vinh
- **Tồn kho 13 khu vực**: HTPP MT, Khánh Hòa, Đắk Lắk, Gia Lai, Quảng Ngãi, Đà Nẵng, Huế, Quảng Trị...

---

## 🌐 Triển Khai Online (Tùy chọn)

Để truy cập từ điện thoại mà không cần server cục bộ:

1. **Vercel** (miễn phí): Upload thư mục `app/` lên GitHub → kết nối Vercel
2. **GitHub Pages**: Đưa lên GitHub repository → bật Pages
3. **Netlify**: Kéo thả thư mục `app/` vào [netlify.com/drop](https://app.netlify.com/drop)

---

*Được xây dựng cho đội kinh doanh Hoa Sen Home — Thiết Bị Nhà Tắm & Nhà Bếp*

