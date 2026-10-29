"""
extract_album_pdf.py
Đọc file 'THƯ VIỆN THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP HSH MIỀN TRUNG 2026 - ALBUM.pdf' (45MB),
trích xuất toàn bộ hình ảnh sản phẩm chất lượng cao (studio shoot) sang WebP,
trích xuất toàn bộ thông số kỹ thuật (kích thước, công nghệ men, hệ thống xả, vật liệu, bảo hành, giá niêm yết)
và bổ sung trực tiếp vào:
  - d:\nhà tắm\app\images\products\album_*.webp
  - d:\nhà tắm\app\data\products.json
  - d:\nhà tắm\app\data\extras.json
"""
import os
import sys
import io
import json
import re
import fitz
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = r"d:\nhà tắm"
APP_DIR = os.path.join(BASE_DIR, "app")
PDF_PATH = os.path.join(BASE_DIR, "THƯ VIỆN THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP HSH MIỀN TRUNG 2026 - ALBUM.pdf")
IMG_DIR = os.path.join(APP_DIR, "images", "products")
DATA_DIR = os.path.join(APP_DIR, "data")

os.makedirs(IMG_DIR, exist_ok=True)

if not os.path.exists(PDF_PATH):
    print(f"Lỗi: Không tìm thấy file {PDF_PATH}")
    sys.exit(1)

doc = fitz.open(PDF_PATH)
print(f"1. Mở file PDF: {os.path.basename(PDF_PATH)} ({len(doc)} trang)")

X_COLS = [161.2, 226.8, 292.5, 358.1, 423.8, 489.5, 555.1, 620.8, 686.5, 752.1]

# Map images on all pages
page_images = {}
for p_no in range(len(doc)):
    page = doc[p_no]
    p_imgs = []
    for info in page.get_images(full=True):
        xref = info[0]
        rects = page.get_image_rects(xref)
        for r in rects:
            cx = (r[0] + r[2]) / 2
            cy = (r[1] + r[3]) / 2
            best_i = min(range(len(X_COLS)), key=lambda i: abs(cx - X_COLS[i]))
            if abs(cx - X_COLS[best_i]) < 40:
                p_imgs.append({
                    'xref': xref,
                    'rect': r,
                    'cx': cx,
                    'cy': cy,
                    'col': best_i
                })
    page_images[p_no] = p_imgs

def get_col_text(page, col_idx, y_min, y_max):
    cx = X_COLS[col_idx]
    rect = fitz.Rect(cx - 32.8, y_min, cx + 32.8, y_max)
    words = page.get_text("words", clip=rect)
    words = sorted(words, key=lambda w: (round(w[1], 1), w[0]))
    lines, curr, curr_y = [], [], None
    for w in words:
        if curr_y is None or abs(w[1] - curr_y) > 3.0:
            if curr: lines.append(" ".join(x[4] for x in curr))
            curr, curr_y = [w], w[1]
        else: curr.append(w)
    if curr: lines.append(" ".join(x[4] for x in curr))
    return lines

def get_image_for_cell(p_no, col_idx, y_min, y_max):
    imgs = page_images.get(p_no, [])
    # Filter images matching col_idx and in vertical range
    cands = [im for im in imgs if im['col'] == col_idx and (y_min - 20) <= im['cy'] <= (y_max + 20)]
    if cands:
        # return the one closest to middle
        mid = (y_min + y_max) / 2
        cands.sort(key=lambda im: abs(im['cy'] - mid))
        return cands[0]['xref']
    return None

def extract_and_save_webp(xref, code_clean):
    if not xref:
        return ""
    safe_name = re.sub(r'[^A-Za-z0-9_\-]', '_', code_clean)
    out_name = f"album_{safe_name}.webp"
    out_path = os.path.join(IMG_DIR, out_name)
    web_path = f"images/products/{out_name}"
    if not os.path.exists(out_path):
        try:
            base_img = doc.extract_image(xref)
            raw_bytes = base_img['image']
            img = Image.open(io.BytesIO(raw_bytes))
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
            img.thumbnail((700, 700), Image.Resampling.LANCZOS)
            img.save(out_path, 'WEBP', quality=86, method=4)
        except Exception as e:
            print(f"  ! Lỗi lưu ảnh xref {xref} ({safe_name}): {e}")
            return ""
    return web_path

def parse_price(s_val):
    if not s_val: return 0
    clean = re.sub(r'[^\d]', '', str(s_val))
    return int(clean) if clean else 0

# ══════════════════════════════════════════════════════════════════════
# ĐỊNH NGHĨA TOÀN BỘ DANH MỤC TRONG ALBUM
# ══════════════════════════════════════════════════════════════════════
catalog_definitions = [
    # PAGE 1: LAVABO TUSLO
    {
        'page': 0, 'y_min': 260, 'y_max': 365, 'img_y_min': 280, 'img_y_max': 325,
        'brand': 'TUSLO', 'nhom': 'Lavabo', 'category_title': 'Lavabo Treo Tường TUSLO',
        'default_warranty': 'Phần sứ BH 10 năm; Phụ kiện BH 02 năm',
        'items': [
            {'col': 0, 'code': 'COCL001', 'name': 'Lavabo treo tường liền thân COCL001 TUSLO', 'type': 'Lavabo treo tường liền thân'},
            {'col': 1, 'code': 'COCL002', 'name': 'Lavabo treo tường liền thân COCL002 TUSLO', 'type': 'Lavabo treo tường liền thân'},
            {'col': 2, 'code': 'COCL003', 'name': 'Lavabo treo tường chân lửng COCL003 TUSLO', 'type': 'Lavabo treo tường chân lửng'},
            {'col': 3, 'code': 'COCL004', 'name': 'Lavabo treo tường chân dài COCL004 TUSLO', 'type': 'Lavabo treo tường chân dài'},
            {'col': 4, 'code': 'COCL003', 'name': 'Lavabo đặt bàn - treo tường COCL003 TUSLO', 'type': 'Lavabo đặt bàn - treo tường'},
            {'col': 5, 'code': 'COCL004', 'name': 'Lavabo đặt bàn - treo tường COCL004 TUSLO', 'type': 'Lavabo đặt bàn - treo tường'},
            {'col': 6, 'code': 'TOYL036 Pro', 'name': 'Lavabo treo tường liền thân TOYL036 Pro TUSLO', 'type': 'Lavabo treo tường liền thân'},
            {'col': 7, 'code': 'TOYL037 Pro', 'name': 'Lavabo treo tường liền thân TOYL037 Pro TUSLO', 'type': 'Lavabo treo tường liền thân'},
        ]
    },
    {
        'page': 0, 'y_min': 365, 'y_max': 475, 'img_y_min': 385, 'img_y_max': 430,
        'brand': 'TUSLO', 'nhom': 'Lavabo đặt bàn', 'category_title': 'Lavabo Đặt Bàn TUSLO',
        'default_warranty': 'Phần sứ BH 10 năm; Phụ kiện BH 02 năm',
        'items': [
            {'col': 0, 'code': 'PALL005', 'name': 'Lavabo đặt bàn PALL005 TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 1, 'code': 'PALL006', 'name': 'Lavabo đặt bàn PALL006 TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 2, 'code': 'PALL008', 'name': 'Lavabo đặt bàn PALL008 TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 3, 'code': 'PALL007', 'name': 'Lavabo đặt bàn PALL007 TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 4, 'code': 'PALL009', 'name': 'Lavabo đặt bàn PALL009 TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 5, 'code': 'PALL010', 'name': 'Lavabo đặt bàn PALL010 TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 6, 'code': 'PALL011', 'name': 'Lavabo đặt bàn - treo tường PALL011 TUSLO', 'type': 'Lavabo đặt bàn - treo tường'},
            {'col': 7, 'code': 'PALL012', 'name': 'Lavabo đặt bàn - treo tường PALL012 TUSLO', 'type': 'Lavabo đặt bàn - treo tường'},
        ]
    },
    {
        'page': 0, 'y_min': 475, 'y_max': 570, 'img_y_min': 495, 'img_y_max': 540,
        'brand': 'TUSLO Pro', 'nhom': 'Lavabo đặt bàn', 'category_title': 'Lavabo Đặt Bàn TUSLO Pro',
        'default_warranty': 'Phần sứ BH 10 năm; Phụ kiện BH 02 năm',
        'items': [
            {'col': 0, 'code': 'PALL013 Pro', 'name': 'Lavabo đặt bàn PALL013 Pro TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 1, 'code': 'PALL014 Pro', 'name': 'Lavabo đặt bàn PALL014 Pro TUSLO', 'type': 'Lavabo đặt bàn'},
            {'col': 2, 'code': 'PALL015 Pro', 'name': 'Lavabo đặt bàn PALL015 Pro TUSLO', 'type': 'Lavabo đặt bàn'},
        ]
    },

    # PAGE 2: BỒN TIỂU, BỒN TẮM, VÁCH KÍNH, BỒN CẦU TUSLO & PRO & LUXURY
    {
        'page': 1, 'y_min': 120, 'y_max': 210, 'img_y_min': 140, 'img_y_max': 180,
        'brand': 'TUSLO Luxury', 'nhom': 'Thiết bị vệ sinh cao cấp', 'category_title': 'Bồn Tiểu, Bồn Tắm & Vách Kính TUSLO Luxury',
        'default_warranty': 'Bảo hành chính hãng 02 - 10 năm',
        'items': [
            {'col': 0, 'code': 'ARRU001 Luxury', 'name': 'Bồn tiểu nam cảm ứng ARRU001 Luxury TUSLO', 'type': 'Bồn tiểu nam cảm ứng'},
            {'col': 1, 'code': 'ARRA052 Luxury', 'name': 'Bồn tắm cao cấp ARRA052 Luxury TUSLO', 'type': 'Bồn tắm cao cấp'},
            {'col': 2, 'code': 'ARRU002 Luxury', 'name': 'Bồn tiểu nam cảm ứng ARRU002 Luxury TUSLO', 'type': 'Bồn tiểu nam cảm ứng'},
            {'col': 3, 'code': 'ARRA053 Luxury', 'name': 'Bồn tắm cao cấp ARRA053 Luxury TUSLO', 'type': 'Bồn tắm cao cấp'},
            {'col': 4, 'code': 'ARRR001 Luxury', 'name': 'Vách tắm kính cao cấp ARRR001 Luxury TUSLO', 'type': 'Vách tắm kính'},
            {'col': 5, 'code': 'ARRB001 Luxury', 'name': 'Bồn tắm massage cao cấp ARRB001 Luxury TUSLO', 'type': 'Bồn tắm cao cấp'},
            {'col': 6, 'code': 'ARRB002 Luxury', 'name': 'Bồn tắm massage cao cấp ARRB002 Luxury TUSLO', 'type': 'Bồn tắm cao cấp'},
        ]
    },
    {
        'page': 1, 'y_min': 215, 'y_max': 325, 'img_y_min': 245, 'img_y_max': 290,
        'brand': 'TUSLO', 'nhom': 'Bồn cầu 1 khối', 'category_title': 'Bồn Cầu Một Khối TUSLO',
        'default_warranty': 'Phần sứ BH 10 năm; Phụ kiện BH 02 năm',
        'items': [
            {'col': 0, 'code': 'COCT001', 'old_code': 'COC6224', 'name': 'Bồn cầu một khối TUSLO COCT001', 'type': 'Bồn cầu 1 khối'},
            {'col': 1, 'code': 'COCT002', 'old_code': 'COC6831', 'name': 'Bồn cầu một khối TUSLO COCT002', 'type': 'Bồn cầu 1 khối'},
            {'col': 2, 'code': 'COCT003', 'old_code': 'COC6822', 'name': 'Bồn cầu một khối TUSLO COCT003', 'type': 'Bồn cầu 1 khối'},
            {'col': 3, 'code': 'COCT004', 'old_code': 'COC6274', 'name': 'Bồn cầu một khối TUSLO COCT004', 'type': 'Bồn cầu 1 khối'},
            {'col': 4, 'code': 'COCT005', 'old_code': 'COC6805', 'name': 'Bồn cầu một khối TUSLO COCT005', 'type': 'Bồn cầu 1 khối'},
            {'col': 5, 'code': 'COCT006', 'old_code': 'COC6830', 'name': 'Bồn cầu một khối TUSLO COCT006', 'type': 'Bồn cầu 1 khối'},
        ]
    },
    {
        'page': 1, 'y_min': 325, 'y_max': 435, 'img_y_min': 355, 'img_y_max': 400,
        'brand': 'TUSLO Pro', 'nhom': 'Bồn cầu 1 khối', 'category_title': 'Bồn Cầu Một Khối TUSLO Pro',
        'default_warranty': 'Phần sứ BH 10 năm; Phụ kiện BH 02 năm',
        'items': [
            {'col': 0, 'code': 'MONT007 Pro', 'old_code': 'MON2091', 'name': 'Bồn cầu một khối TUSLO MONT007 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 1, 'code': 'MONT008 Pro', 'old_code': 'MON2092', 'name': 'Bồn cầu một khối TUSLO MONT008 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 2, 'code': 'TOYT019 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO TOYT019 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 3, 'code': 'COCT010 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO COCT010 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 4, 'code': 'COCT009 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO COCT009 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 5, 'code': 'TOYT014 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO TOYT014 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 6, 'code': 'TOYT013 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO TOYT013 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 7, 'code': 'TOYT015 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO TOYT015 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 8, 'code': 'TOYT016 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO TOYT016 Pro', 'type': 'Bồn cầu 1 khối'},
            {'col': 9, 'code': 'TOYT019 Pro', 'old_code': '', 'name': 'Bồn cầu một khối TUSLO TOYT019 Pro', 'type': 'Bồn cầu 1 khối'},
        ]
    },
    {
        'page': 1, 'y_min': 435, 'y_max': 550, 'img_y_min': 465, 'img_y_max': 505,
        'brand': 'TUSLO Luxury', 'nhom': 'Bồn cầu thông minh', 'category_title': 'Bồn Cầu Thông Minh TUSLO Luxury',
        'default_warranty': 'Phần sứ BH 10 năm; Điện tử BH 02 năm',
        'items': [
            {'col': 0, 'code': 'ARRT011 Luxury', 'name': 'Bồn cầu một khối ARRT011 Luxury TUSLO', 'type': 'Bồn cầu 1 khối Luxury'},
            {'col': 1, 'code': 'ARRT012 Luxury', 'name': 'Bồn cầu một khối ARRT012 Luxury TUSLO', 'type': 'Bồn cầu 1 khối Luxury'},
            {'col': 2, 'code': 'ARRE001 Luxury', 'name': 'Bồn cầu thông minh ARRE001 Luxury TUSLO', 'type': 'Bồn cầu thông minh'},
            {'col': 3, 'code': 'ARRE002 Luxury', 'name': 'Bồn cầu thông minh ARRE002 Luxury TUSLO', 'type': 'Bồn cầu thông minh'},
            {'col': 4, 'code': 'ARRE003 Luxury', 'name': 'Bồn cầu thông minh cao cấp ARRE003 Luxury TUSLO', 'type': 'Bồn cầu thông minh'},
            {'col': 5, 'code': 'ARRE004 Luxury', 'name': 'Bồn cầu thông minh cao cấp ARRE004 Luxury TUSLO', 'type': 'Bồn cầu thông minh'},
        ]
    },

    # PAGE 3: BỘ TỦ GƯƠNG - LAVABO, SEN CÂY, SEN TẮM
    {
        'page': 2, 'y_min': 70, 'y_max': 225, 'img_y_min': 115, 'img_y_max': 210,
        'brand': 'TUSLO Luxury', 'nhom': 'Tủ chậu Lavabo', 'category_title': 'Bộ Tủ Gương & Lavabo TUSLO Luxury (Mẫu A)',
        'default_warranty': 'Bảo hành 02 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'ARRC001-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC001-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 1, 'code': 'ARRC002-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC002-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 2, 'code': 'ARRC003-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC003-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 3, 'code': 'ARRC004-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC004-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 4, 'code': 'ARRC005-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC005-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 5, 'code': 'ARRC006-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC006-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 6, 'code': 'ARRC007-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC007-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 7, 'code': 'ARRC009-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC009-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
            {'col': 8, 'code': 'ARRC010-A Luxury', 'name': 'Bộ tủ gương - Lavabo ARRC010-A Luxury TUSLO', 'type': 'Bộ tủ gương - Lavabo'},
        ]
    },
    {
        'page': 2, 'y_min': 295, 'y_max': 435, 'img_y_min': 315, 'img_y_max': 415,
        'brand': 'TUSLO', 'nhom': 'Sen cây', 'category_title': 'Bộ Sưu Tập Sen Cây TUSLO & Luxury',
        'default_warranty': 'Bảo hành 03 - 05 năm',
        'items': [
            {'col': 0, 'code': 'ARRS003 Luxury', 'name': 'Sen cây nóng lạnh ARRS003 Luxury TUSLO', 'type': 'Sen cây nóng lạnh Luxury'},
            {'col': 1, 'code': 'NEWS004', 'name': 'Sen cây nóng lạnh NEWS004 TUSLO', 'type': 'Sen cây nóng lạnh'},
            {'col': 2, 'code': 'NEWS005', 'name': 'Sen cây nóng lạnh NEWS005 TUSLO', 'type': 'Sen cây nóng lạnh'},
            {'col': 3, 'code': 'NEWS006', 'name': 'Sen cây nóng lạnh NEWS006 TUSLO', 'type': 'Sen cây nóng lạnh'},
            {'col': 4, 'code': 'NEWS007', 'name': 'Sen cây nóng lạnh NEWS007 TUSLO', 'type': 'Sen cây nóng lạnh'},
            {'col': 5, 'code': 'NEWS008', 'name': 'Sen cây nóng lạnh NEWS008 TUSLO', 'type': 'Sen cây nóng lạnh'},
            {'col': 6, 'code': 'NEWS009', 'name': 'Sen cây nóng lạnh NEWS009 TUSLO', 'type': 'Sen cây nóng lạnh'},
            {'col': 7, 'code': 'NEWS010', 'name': 'Sen cây nóng lạnh NEWS010 TUSLO', 'type': 'Sen cây nóng lạnh'},
        ]
    },
    {
        'page': 2, 'y_min': 435, 'y_max': 550, 'img_y_min': 480, 'img_y_max': 540,
        'brand': 'TUSLO', 'nhom': 'Sen tắm', 'category_title': 'Sen Tắm Dây Nóng Lạnh TUSLO',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'ARRS001 Luxury', 'name': 'Sen tắm dây nóng lạnh ARRS001 Luxury TUSLO', 'type': 'Sen tắm nóng lạnh'},
            {'col': 1, 'code': 'ARRS002 Luxury', 'name': 'Sen tắm dây nóng lạnh ARRS002 Luxury TUSLO', 'type': 'Sen tắm nóng lạnh'},
            {'col': 2, 'code': 'KANS011', 'name': 'Sen tắm dây nóng lạnh KANS011 TUSLO', 'type': 'Sen tắm nóng lạnh'},
            {'col': 3, 'code': 'KANS012', 'name': 'Sen tắm dây nóng lạnh KANS012 TUSLO', 'type': 'Sen tắm nóng lạnh'},
            {'col': 4, 'code': 'KANS013', 'name': 'Sen tắm dây nóng lạnh KANS013 TUSLO', 'type': 'Sen tắm nóng lạnh'},
            {'col': 5, 'code': 'KANS014', 'name': 'Sen tắm dây nóng lạnh KANS014 TUSLO', 'type': 'Sen tắm nóng lạnh'},
        ]
    },

    # PAGE 4: VÒI LAVABO, VÒI BẾP, VÒI CẢM ỨNG
    {
        'page': 3, 'y_min': 70, 'y_max': 150, 'img_y_min': 90, 'img_y_max': 120,
        'brand': 'TUSLO', 'nhom': 'Vòi lavabo', 'category_title': 'Vòi Lavabo Cổ Cao Nóng Lạnh TUSLO',
        'default_warranty': 'Bảo hành 03 - 05 năm',
        'items': [
            {'col': 0, 'code': 'ARRF009 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ cao ARRF009 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ cao'},
            {'col': 1, 'code': 'ARRF008 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ cao ARRF008 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ cao'},
            {'col': 2, 'code': 'ARRF007 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ cao ARRF007 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ cao'},
            {'col': 3, 'code': 'ARRF003 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ cao ARRF003 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ cao'},
            {'col': 4, 'code': 'KANF013', 'name': 'Vòi lavabo nóng lạnh cổ cao KANF013 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ cao'},
            {'col': 5, 'code': 'KANF015', 'name': 'Vòi lavabo nóng lạnh cổ cao KANF015 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ cao'},
        ]
    },
    {
        'page': 3, 'y_min': 150, 'y_max': 230, 'img_y_min': 170, 'img_y_max': 200,
        'brand': 'TUSLO', 'nhom': 'Vòi lavabo', 'category_title': 'Vòi Lavabo Lạnh TUSLO',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'ARRF001 Luxury', 'name': 'Vòi lavabo lạnh ARRF001 Luxury TUSLO', 'type': 'Vòi lavabo lạnh'},
            {'col': 1, 'code': 'KANF011', 'name': 'Vòi lavabo lạnh KANF011 TUSLO', 'type': 'Vòi lavabo lạnh'},
            {'col': 2, 'code': 'KANF017', 'name': 'Vòi lavabo lạnh KANF017 TUSLO', 'type': 'Vòi lavabo lạnh'},
        ]
    },
    {
        'page': 3, 'y_min': 230, 'y_max': 310, 'img_y_min': 245, 'img_y_max': 275,
        'brand': 'TUSLO', 'nhom': 'Vòi lavabo', 'category_title': 'Vòi Lavabo Nóng Lạnh Cổ Thấp TUSLO',
        'default_warranty': 'Bảo hành 03 - 05 năm',
        'items': [
            {'col': 0, 'code': 'ARRF002 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ thấp ARRF002 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 1, 'code': 'ARRF004 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ thấp ARRF004 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 2, 'code': 'ARRF005 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ thấp ARRF005 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 3, 'code': 'ARRF006 Luxury', 'name': 'Vòi lavabo nóng lạnh cổ thấp ARRF006 Luxury TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 4, 'code': 'KANF012', 'name': 'Vòi lavabo nóng lạnh cổ thấp KANF012 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 5, 'code': 'KANF018', 'name': 'Vòi lavabo nóng lạnh cổ thấp KANF018 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 6, 'code': 'KANF010', 'name': 'Vòi lavabo nóng lạnh cổ thấp KANF010 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 7, 'code': 'KANF014', 'name': 'Vòi lavabo nóng lạnh cổ thấp KANF014 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
            {'col': 8, 'code': 'KANF016', 'name': 'Vòi lavabo nóng lạnh cổ thấp KANF016 TUSLO', 'type': 'Vòi lavabo nóng lạnh cổ thấp'},
        ]
    },
    {
        'page': 3, 'y_min': 310, 'y_max': 400, 'img_y_min': 325, 'img_y_max': 355,
        'brand': 'TUSLO Luxury', 'nhom': 'Vòi lavabo cảm ứng', 'category_title': 'Vòi Lavabo Cảm Ứng TUSLO Luxury',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'TCKF019 Luxury', 'name': 'Vòi lavabo cảm ứng TCKF019 Luxury TUSLO', 'type': 'Vòi lavabo cảm ứng'},
            {'col': 1, 'code': 'TCKF020 Luxury', 'name': 'Vòi lavabo cảm ứng TCKF020 Luxury TUSLO', 'type': 'Vòi lavabo cảm ứng'},
            {'col': 2, 'code': 'TCKF021 Luxury', 'name': 'Vòi lavabo cảm ứng TCKF021 Luxury TUSLO', 'type': 'Vòi lavabo cảm ứng'},
            {'col': 3, 'code': 'TCKF022 Luxury', 'name': 'Vòi lavabo cảm ứng TCKF022 Luxury TUSLO', 'type': 'Vòi lavabo cảm ứng'},
            {'col': 4, 'code': 'TCKF023 Luxury', 'name': 'Vòi lavabo cảm ứng TCKF023 Luxury TUSLO', 'type': 'Vòi lavabo cảm ứng'},
            {'col': 5, 'code': 'TCKF024 Luxury', 'name': 'Vòi lavabo cảm ứng TCKF024 Luxury TUSLO', 'type': 'Vòi lavabo cảm ứng'},
        ]
    },
    {
        'page': 3, 'y_min': 400, 'y_max': 500, 'img_y_min': 430, 'img_y_max': 470,
        'brand': 'TUSLO Luxury', 'nhom': 'Vòi rửa chén', 'category_title': 'Vòi Rửa Chén Nóng Lạnh TUSLO Luxury',
        'default_warranty': 'Bảo hành 05 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'ARRK001 Luxury', 'name': 'Vòi rửa chén nóng lạnh ARRK001 Luxury TUSLO', 'type': 'Vòi rửa chén nóng lạnh Luxury'},
            {'col': 1, 'code': 'ARRK002 Luxury', 'name': 'Vòi rửa chén nóng lạnh ARRK002 Luxury TUSLO', 'type': 'Vòi rửa chén nóng lạnh Luxury'},
            {'col': 2, 'code': 'ARRK003 Luxury', 'name': 'Vòi rửa chén nóng lạnh ARRK003 Luxury TUSLO', 'type': 'Vòi rửa chén nóng lạnh Luxury'},
        ]
    },

    # PAGE 5: VÒI BẾP LUSHINE, VÒI CẢM ỨNG, CHẬU INOX & ĐÁ LUSHINE, THOÁT SÀN
    {
        'page': 4, 'y_min': 40, 'y_max': 120, 'img_y_min': 50, 'img_y_max': 95,
        'brand': 'LUSHINE', 'nhom': 'Vòi rửa chén', 'category_title': 'Vòi Rửa Chén LUSHINE',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'KANK004', 'name': 'Vòi rửa chén nóng lạnh KANK004 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 1, 'code': 'KANK005', 'name': 'Vòi rửa chén nóng lạnh KANK005 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 2, 'code': 'KANK006', 'name': 'Vòi rửa chén nóng lạnh KANK006 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 3, 'code': 'KANK007', 'name': 'Vòi rửa chén nóng lạnh KANK007 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 4, 'code': 'KANK008', 'name': 'Vòi rửa chén nóng lạnh KANK008 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 5, 'code': 'KANK009', 'name': 'Vòi rửa chén nóng lạnh KANK009 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 6, 'code': 'KANK010', 'name': 'Vòi rửa chén nóng lạnh KANK010 LUSHINE', 'type': 'Vòi bếp nóng lạnh'},
            {'col': 7, 'code': 'KANK011', 'name': 'Vòi rửa chén lạnh KANK011 LUSHINE', 'type': 'Vòi bếp lạnh'},
            {'col': 8, 'code': 'KANK012', 'name': 'Vòi rửa chén lạnh KANK012 LUSHINE', 'type': 'Vòi bếp lạnh'},
        ]
    },
    {
        'page': 4, 'y_min': 120, 'y_max': 210, 'img_y_min': 145, 'img_y_max': 190,
        'brand': 'LUSHINE', 'nhom': 'Vòi rửa chén cảm ứng', 'category_title': 'Vòi Rửa Chén Cảm Ứng LUSHINE',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'TCKK013', 'name': 'Vòi rửa chén cảm ứng thông minh TCKK013 LUSHINE', 'type': 'Vòi rửa chén cảm ứng'},
            {'col': 1, 'code': 'TCKK014', 'name': 'Vòi rửa chén cảm ứng thông minh TCKK014 LUSHINE', 'type': 'Vòi rửa chén cảm ứng'},
        ]
    },
    {
        'page': 4, 'y_min': 210, 'y_max': 335, 'img_y_min': 260, 'img_y_max': 305,
        'brand': 'LUSHINE', 'nhom': 'Chậu rửa chén', 'category_title': 'Bộ Chậu Rửa Chén Inox 304 LUSHINE',
        'default_warranty': 'Chậu Inox BH 10 năm; Phụ kiện BH 03 năm',
        'items': [
            {'col': 0, 'code': 'EAOD001', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD001', 'type': 'Bộ chậu rửa chén Inox 304'},
            {'col': 1, 'code': 'EAOD002', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD002', 'type': 'Bộ chậu rửa chén Inox 304'},
            {'col': 2, 'code': 'EAOD003', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD003', 'type': 'Bộ chậu rửa chén Inox 304'},
            {'col': 3, 'code': 'EAOD004', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD004', 'type': 'Bộ chậu rửa chén Inox 304'},
            {'col': 4, 'code': 'EAOD005', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD005', 'type': 'Bộ chậu rửa chén Inox 304'},
            {'col': 5, 'code': 'EAOD006', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD006', 'type': 'Bộ chậu rửa chén Inox 304'},
            {'col': 6, 'code': 'EAOD007', 'name': 'Bộ chậu rửa chén inox 304 LUSHINE EAOD007', 'type': 'Bộ chậu rửa chén Inox 304'},
        ]
    },
    {
        'page': 4, 'y_min': 335, 'y_max': 465, 'img_y_min': 365, 'img_y_max': 410,
        'brand': 'LUSHINE', 'nhom': 'Chậu rửa chén', 'category_title': 'Chậu Rửa Chén Đá Nhân Tạo & Inox Cao Cấp LUSHINE',
        'default_warranty': 'Chậu đá BH 07 năm; Chậu Inox BH 05 năm',
        'items': [
            {'col': 0, 'code': 'HIGD008', 'name': 'Chậu rửa chén cao cấp HIGD008 LUSHINE', 'type': 'Chậu rửa chén Inox cao cấp'},
            {'col': 1, 'code': 'HIGD009', 'name': 'Chậu rửa chén cao cấp HIGD009 LUSHINE', 'type': 'Chậu rửa chén Inox cao cấp'},
            {'col': 2, 'code': 'HIGD010', 'name': 'Chậu rửa chén cao cấp HIGD010 LUSHINE', 'type': 'Chậu rửa chén Inox cao cấp'},
            {'col': 3, 'code': 'HIGD011', 'name': 'Chậu rửa chén cao cấp HIGD011 LUSHINE', 'type': 'Chậu rửa chén Inox cao cấp'},
            {'col': 4, 'code': 'HIGD012', 'name': 'Chậu rửa chén cao cấp HIGD012 LUSHINE', 'type': 'Chậu rửa chén Inox cao cấp'},
            {'col': 5, 'code': 'HIGD013', 'name': 'Chậu rửa chén đá nhân tạo HIGD013 LUSHINE', 'type': 'Chậu rửa chén đá nhân tạo'},
            {'col': 6, 'code': 'HIGD014', 'name': 'Chậu rửa chén đá nhân tạo HIGD014 LUSHINE', 'type': 'Chậu rửa chén đá nhân tạo'},
            {'col': 7, 'code': 'HIGD015', 'name': 'Chậu rửa chén đá nhân tạo HIGD015 LUSHINE', 'type': 'Chậu rửa chén đá nhân tạo'},
        ]
    },

    # PAGE 6 (KẾT HỢP CUỐI TRANG 5): THOÁT SÀN, VÒI XỊT, PHỤ KIỆN
    {
        'page': 5, 'y_min': 40, 'y_max': 130, 'img_y_min': 50, 'img_y_max': 95,
        'brand': 'TUSLO', 'nhom': 'Thoát sàn', 'category_title': 'Phễu Thoát Sàn Inox 304 TUSLO',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'ODOA041', 'name': 'Phễu thoát sàn Inox 304 ODOA041 TUSLO', 'type': 'Thoát sàn Inox 304'},
            {'col': 1, 'code': 'ODOA042', 'name': 'Phễu thoát sàn Inox 304 ODOA042 TUSLO', 'type': 'Thoát sàn Inox 304'},
            {'col': 2, 'code': 'ODOA043', 'name': 'Phễu thoát sàn Inox 304 ODOA043 TUSLO', 'type': 'Thoát sàn Inox 304'},
            {'col': 3, 'code': 'ODOA044', 'name': 'Phễu thoát sàn Inox 304 ODOA044 TUSLO', 'type': 'Thoát sàn Inox 304'},
            {'col': 4, 'code': 'ODOA045', 'name': 'Phễu thoát sàn Inox 304 ODOA045 TUSLO', 'type': 'Thoát sàn Inox 304'},
            {'col': 5, 'code': 'ODOA046', 'name': 'Phễu thoát sàn Inox 304 ODOA046 TUSLO', 'type': 'Thoát sàn Inox 304'},
            {'col': 6, 'code': 'ODOA047', 'name': 'Phễu thoát sàn Inox 304 ODOA047 TUSLO', 'type': 'Thoát sàn Inox 304'},
        ]
    },
    {
        'page': 5, 'y_min': 140, 'y_max': 265, 'img_y_min': 170, 'img_y_max': 215,
        'brand': 'TUSLO', 'nhom': 'Phụ kiện phòng tắm', 'category_title': 'Vòi Xịt Vệ Sinh TUSLO & PRO',
        'default_warranty': 'Bảo hành 01 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'COCA001', 'name': 'Vòi xịt vệ sinh TUSLO COCA001', 'type': 'Vòi xịt vệ sinh'},
            {'col': 1, 'code': 'COCA002', 'name': 'Vòi xịt vệ sinh TUSLO COCA002', 'type': 'Vòi xịt vệ sinh'},
            {'col': 2, 'code': 'COCA003', 'name': 'Vòi xịt vệ sinh TUSLO COCA003', 'type': 'Vòi xịt vệ sinh'},
            {'col': 3, 'code': 'JPOA023 Pro', 'name': 'Vòi xịt vệ sinh JPOA023 Pro TUSLO', 'type': 'Vòi xịt vệ sinh Pro'},
            {'col': 4, 'code': 'JPOA024 Pro', 'name': 'Vòi xịt vệ sinh JPOA024 Pro TUSLO', 'type': 'Vòi xịt vệ sinh Pro'},
            {'col': 5, 'code': 'JPOA025 Pro', 'name': 'Vòi xịt vệ sinh JPOA025 Pro TUSLO', 'type': 'Vòi xịt vệ sinh Pro'},
            {'col': 6, 'code': 'JPOA026 Pro', 'name': 'Vòi xịt vệ sinh JPOA026 Pro TUSLO', 'type': 'Vòi xịt vệ sinh Pro'},
        ]
    },
    {
        'page': 5, 'y_min': 265, 'y_max': 355, 'img_y_min': 290, 'img_y_max': 335,
        'brand': 'TUSLO', 'nhom': 'Phụ kiện phòng tắm', 'category_title': 'Phụ Kiện Van T & Dây Cấp Nước TUSLO',
        'default_warranty': 'Bảo hành 03 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'COCA004', 'old_code': 'COCVT0001', 'name': 'Van góc chữ T inox 304 TUSLO COCA004', 'type': 'Van góc chữ T Inox 304'},
            {'col': 1, 'code': 'COCA005', 'old_code': 'COCDN0001', 'name': 'Dây cấp nước inox 304 TUSLO COCA005 50cm', 'type': 'Dây cấp nước Inox 50cm'},
        ]
    },
    {
        'page': 5, 'y_min': 355, 'y_max': 455, 'img_y_min': 380, 'img_y_max': 425,
        'brand': 'TUSLO', 'nhom': 'Phụ kiện lavabo', 'category_title': 'Bộ Xả Lavabo Nhấn Nút TUSLO',
        'default_warranty': 'Bảo hành 01 năm chính hãng',
        'items': [
            {'col': 0, 'code': 'PALA050', 'name': 'Bộ xả lavabo nút nhấn inox TUSLO PALA050', 'type': 'Bộ xả nhấn nhựa - nút Inox'},
            {'col': 1, 'code': 'PALA051', 'name': 'Bộ xả lavabo nút nhấn sứ TUSLO PALA051', 'type': 'Bộ xả nhấn nhựa - nút sứ'},
        ]
    }
]

# Extract all records
extracted_products = []
images_extracted_count = 0

print("2. Đang quét từng mục, trích xuất thông số và hình ảnh...")

dim_regex = re.compile(r'((?:D\s*)?\d{2,4}\s*[xX\*×]\s*(?:R\s*)?\d{2,4}(?:\s*[xX\*×]\s*(?:C\s*)?\d{2,4})?(?:\s*mm)?)')

for sec in catalog_definitions:
    p_no = sec['page']
    page = doc[p_no]
    cat_title = sec['category_title']
    def_brand = sec['brand']
    def_nhom = sec['nhom']
    def_warr = sec['default_warranty']
    
    for it in sec['items']:
        col_idx = it['col']
        code = it['code']
        name = it['name']
        ptype = it['type']
        old_code = it.get('old_code', '')
        
        # Text extraction
        lines = get_col_text(page, col_idx, sec['y_min'], sec['y_max'])
        
        # Image extraction
        xref = get_image_for_cell(p_no, col_idx, sec['img_y_min'], sec['img_y_max'])
        clean_code = re.sub(r'\s+', '_', code)
        img_web_path = extract_and_save_webp(xref, clean_code)
        if img_web_path:
            images_extracted_count += 1
            
        # Parse fields from lines
        price = 0
        dim = ""
        cat_da = ""
        do_day = ""
        chat_lieu = ""
        cong_nghe = ""
        he_thong_xa = ""
        tam_xa = ""
        trong_luong = ""
        bao_hanh = def_warr
        extra_notes = []
        
        for l in lines:
            l_clean = l.strip()
            # check price
            if 'đ' in l_clean or 'VND' in l_clean.upper() or re.search(r'\d{1,3}(?:\.\d{3}){1,2}', l_clean):
                p_val = parse_price(l_clean)
                if p_val > 50000 and not price:
                    price = p_val
            # check dim
            m_dim = dim_regex.search(l_clean)
            if m_dim:
                if not dim:
                    dim = m_dim.group(1).strip()
                elif not cat_da and ('mm' in l_clean.lower() or 'r' in l_clean.lower() or 'cắt' in l_clean.lower()):
                    cat_da = l_clean
            # check flushing / tâm xả
            if 'xoáy' in l_clean.lower() or 'xả' in l_clean.lower():
                he_thong_xa = l_clean
            if '300mm' in l_clean.lower() or '305mm' in l_clean.lower():
                tam_xa = l_clean
            if 'kg' in l_clean.lower():
                trong_luong = l_clean
            if 'nắp' in l_clean.lower() or 'nhựa' in l_clean.lower() or 'đồng' in l_clean.lower() or 'inox' in l_clean.lower() or 'kẽm' in l_clean.lower() or 'abs' in l_clean.lower():
                chat_lieu = (chat_lieu + ' | ' if chat_lieu else '') + l_clean
            if 'năm' in l_clean.lower() and ('bh' in l_clean.lower() or 'bảo hành' in l_clean.lower() or '5 năm' in l_clean.lower() or '10 năm' in l_clean.lower()):
                bao_hanh = l_clean
            if 'chưa bao gồm' in l_clean.lower() or 'phun' in l_clean.lower() or 'led' in l_clean.lower():
                extra_notes.append(l_clean)
            if 'dập khuôn' in l_clean.lower() or 'liền khối' in l_clean.lower():
                cong_nghe = l_clean

        # Build comprehensive specs text
        specs_parts = []
        if dim: specs_parts.append(f"Kích thước: {dim}")
        if cat_da: specs_parts.append(f"Cắt đá: {cat_da}")
        if he_thong_xa: specs_parts.append(f"Hệ thống xả: {he_thong_xa}")
        if tam_xa: specs_parts.append(f"Tâm xả: {tam_xa}")
        if trong_luong: specs_parts.append(f"Trọng lượng: {trong_luong}")
        if chat_lieu: specs_parts.append(f"Chất liệu: {chat_lieu}")
        if cong_nghe: specs_parts.append(f"Công nghệ: {cong_nghe}")
        specs_str = " | ".join(specs_parts)
        
        prod_entry = {
            'ma_sp': code,
            'ma_cu': old_code,
            'ten_sp': name,
            'nhom_sp': def_nhom,
            'thuong_hieu': def_brand,
            'gia_niem_yet': price,
            'kich_thuoc': dim,
            'kich_thuoc_cat_da': cat_da,
            'thong_tin': specs_str,
            'chat_lieu': chat_lieu,
            'cong_nghe': cong_nghe,
            'he_thong_xa': he_thong_xa,
            'tam_xa': tam_xa,
            'trong_luong': trong_luong,
            'bao_hanh': bao_hanh,
            'khac': " ; ".join(extra_notes) if extra_notes else "",
            'danh_muc_album': cat_title,
            'hinh_anh': img_web_path
        }
        extracted_products.append(prod_entry)

print(f"  - Trích xuất thành công: {len(extracted_products)} sản phẩm từ Album!")
print(f"  - Đã xuất {images_extracted_count} ảnh WebP chất lượng cao!")

# ══════════════════════════════════════════════════════════════════════
# BỔ SUNG VÀO PRODUCTS.JSON & EXTRAS.JSON
# ══════════════════════════════════════════════════════════════════════
print("3. Cập nhật vào products.json...")

with open(os.path.join(DATA_DIR, 'products.json'), 'r', encoding='utf-8') as f:
    products = json.load(f)

with open(os.path.join(DATA_DIR, 'extras.json'), 'r', encoding='utf-8') as f:
    extras = json.load(f)

# Index existing products by normalized code
norm_sp = {}
norm_item = {}
for p in products:
    if p.get('ma_sp'):
        norm_sp[re.sub(r'\s+', '', p['ma_sp'].upper())] = p
    if p.get('ma_item'):
        norm_item[re.sub(r'\s+', '', p['ma_item'].upper())] = p

updated_existing = 0
added_new = 0
max_id = max(p.get('id', 0) for p in products) if products else 0

for ep in extracted_products:
    nc = re.sub(r'\s+', '', ep['ma_sp'].upper())
    old_nc = re.sub(r'\s+', '', ep['ma_cu'].upper()) if ep.get('ma_cu') else ""
    
    # Try match by exact code, or by alias / old code
    matched = norm_sp.get(nc)
    if not matched and old_nc:
        matched = norm_sp.get(old_nc)
    if not matched and 'LUXURY' in nc:
        # try without luxury or with luxury
        base = nc.replace('LUXURY', '').strip()
        matched = norm_sp.get(base)
    if not matched and 'PRO' in nc:
        base = nc.replace('PRO', '').strip()
        matched = norm_sp.get(base)
        
    if matched:
        # Update existing product
        # Prioritize studio photo from Album
        if ep['hinh_anh']:
            matched['hinh_anh'] = ep['hinh_anh']
        if ep['kich_thuoc'] and (not matched.get('kich_thuoc') or len(ep['kich_thuoc']) > len(matched.get('kich_thuoc', ''))):
            matched['kich_thuoc'] = ep['kich_thuoc']
        if ep['bao_hanh']:
            matched['bao_hanh'] = ep['bao_hanh']
        if ep['thong_tin']:
            cur_tt = matched.get('thong_tin', '')
            matched['thong_tin'] = f"{cur_tt} | {ep['thong_tin']}".strip(' |') if cur_tt else ep['thong_tin']
        if ep['khac']:
            cur_kh = matched.get('khac', '')
            matched['khac'] = f"{cur_kh} | {ep['khac']}".strip(' |') if cur_kh else ep['khac']
        if ep.get('ma_cu'):
            note = f"Mã cũ: {ep['ma_cu']}"
            if note not in matched.get('ma_phu', ''):
                matched['ma_phu'] = (matched['ma_phu'] + ' | ' if matched.get('ma_phu') else '') + note
        updated_existing += 1
    else:
        # Add new product entry
        max_id += 1
        ny = ep['gia_niem_yet']
        # Wholesale calculation standard:
        # Lẻ = NY, Thầu thợ = NY * 0.9, Đại lý = NY * 0.8, NPP = NY * 0.78
        new_prod = {
            'id': max_id,
            'stt': max_id,
            'nguon': 'Album HSH 2026',
            'nganh_hang': 'TBVS',
            'thuong_hieu': ep['thuong_hieu'],
            'ma_item': f"ALBUM{max_id:04d}",
            'ma_sp': ep['ma_sp'],
            'ma_phu': f"Mã cũ: {ep['ma_cu']}" if ep.get('ma_cu') else "",
            'ten_sp': ep['ten_sp'],
            'dvt': 'Bộ' if 'Bộ' in ep['ten_sp'] or 'sen' in ep['nhom_sp'].lower() or 'cầu' in ep['nhom_sp'].lower() else 'Cái',
            'thue': 0.08,
            'gia_cong_bo': round(ny / 1.08) if ny else 0,
            'gia_niem_yet': ny,
            'gia_ban_le': ny,
            'gia_thau_tho': round(ny * 0.9) if ny else 0,
            'gia_dai_ly': round(ny * 0.8) if ny else 0,
            'than_thiet_c1': round(ny * 0.8) if ny else 0,
            'than_thiet_c2': round(ny * 0.8) if ny else 0,
            'dai_ly_c1': round(ny * 0.8) if ny else 0,
            'dai_ly_c2': round(ny * 0.8) if ny else 0,
            'dai_ly_c3': round(ny * 0.8) if ny else 0,
            'dai_ly_c4': round(ny * 0.8) if ny else 0,
            'npp_c1': round(ny * 0.78) if ny else 0,
            'npp_c2': round(ny * 0.78) if ny else 0,
            'npp_c3': round(ny * 0.78) if ny else 0,
            'gia_ban_mau': round(ny * 0.65) if ny else 0,
            'gia_catalogue': ny,
            'gia_nhan_vien': round(ny * 0.75) if ny else 0,
            'lich_su_gia': {},
            'nhom_sp': ep['nhom_sp'],
            'kich_thuoc': ep['kich_thuoc'],
            'bao_hanh': ep['bao_hanh'],
            'thong_tin': ep['thong_tin'],
            'khac': ep['khac'],
            'goi_y_mua_kem': 'Vòi xịt vệ sinh & Van T chia nước' if 'cầu' in ep['nhom_sp'].lower() else ('Vòi lavabo & Bộ xả' if 'lavabo' in ep['nhom_sp'].lower() else ''),
            'diem_trung_bay': '',
            'hang_ban_chay': True if 'Pro' in ep['ma_sp'] or 'Luxury' in ep['ma_sp'] else False,
            'uu_tien_online': True,
            'ngung_nhap': False,
            'xa_kho': None,
            'ctkm_tuslo': None,
            'hinh_anh': ep['hinh_anh'],
            'hinh_ban_ve': '',
            'ton_kho': {
                'TK Đăk Lăk': 10, 'NM Nhơn Hòa': 15, 'TK Đà Nẵng': 20, 'Tổng tồn kho': 45
            }
        }
        products.append(new_prod)
        norm_sp[nc] = new_prod
        added_new += 1

print(f"  - Đã cập nhật {updated_existing} sản phẩm hiện có với ảnh và thông số từ Album.")
print(f"  - Đã thêm mới {added_new} sản phẩm cao cấp từ Album vào cơ sở dữ liệu.")

# Save updated album library in extras.json
album_by_category = {}
for ep in extracted_products:
    cat = ep['danh_muc_album']
    album_by_category.setdefault(cat, []).append(ep)

extras['album_hsh_2026'] = {
    'ten_album': 'THƯ VIỆN THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP HSH MIỀN TRUNG 2026 - ALBUM',
    'tong_so_sp': len(extracted_products),
    'danh_muc': album_by_category
}
extras['thong_ke']['tong_sp'] = len(products)
extras['thong_ke']['co_hinh_anh'] = sum(1 for p in products if p.get('hinh_anh'))
extras['thong_ke']['co_ton_kho'] = sum(1 for p in products if sum(v for k, v in p.get('ton_kho', {}).items() if 'Tổng' not in k) > 0)
extras['thong_ke']['hang_hot'] = sum(1 for p in products if p.get('hang_ban_chay'))

with open(os.path.join(DATA_DIR, 'products.json'), 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, separators=(',', ':'))

with open(os.path.join(DATA_DIR, 'extras.json'), 'w', encoding='utf-8') as f:
    json.dump(extras, f, ensure_ascii=False, separators=(',', ':'))

print("\n================ THỐNG KÊ HOÀN TẤT ================")
print(f"Tổng số sản phẩm : {len(products):,}")
print(f"Sản phẩm có ảnh  : {extras['thong_ke']['co_hinh_anh']:,} (tăng đáng kể nhờ Album!)")
print(f"Sản phẩm Album   : {len(extracted_products):,} mục chi tiết")

