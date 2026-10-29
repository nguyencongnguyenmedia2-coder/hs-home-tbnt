r"""
build_full_data.py
Trích xuất toàn bộ hình ảnh sản phẩm (tối ưu kích thước) và toàn bộ dữ liệu từ các sheet
trong file 'THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP.xlsx' sang:
  - d:\nhà tắm\app\images\products\*.jpg / *.png
  - d:\nhà tắm\app\data\products.json
  - d:\nhà tắm\app\data\extras.json
"""
import os
import sys
import io
import json
import zipfile
import re
import xml.etree.ElementTree as ET
from PIL import Image
import openpyxl

if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
else:
    sys.stdout = io.StringIO()

XLSX_PATH = r'd:\nhà tắm\THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP.xlsx'
APP_DIR = r'd:\nhà tắm\app'
IMG_DIR = os.path.join(APP_DIR, 'images', 'products')
DATA_DIR = os.path.join(APP_DIR, 'data')

os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def safe_int(val):
    if val is None: return 0
    try:
        s = str(val).strip().replace(',', '')
        if s in ('', '-', 'None', 'nan', '#N/A', '#REF!', '#VALUE!'):
            return 0
        return int(round(float(s)))
    except:
        return 0

def safe_float(val):
    if val is None: return 0.0
    try:
        s = str(val).strip().replace(',', '')
        if s in ('', '-', 'None', 'nan', '#N/A', '#REF!', '#VALUE!'):
            return 0.0
        return float(s)
    except:
        return 0.0

def clean_str(val):
    if val is None: return ''
    s = str(val).strip()
    if s in ('None', '(blank)', '#N/A', '#REF!', 'nan'):
        return ''
    return s

def norm_code(code):
    if not code: return ''
    return re.sub(r'\s+', '', str(code).strip().upper())

def get_sheet_drawings(z, drawing_num):
    ns = {
        'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }
    draw_file = f'xl/drawings/drawing{drawing_num}.xml'
    rels_file = f'xl/drawings/_rels/drawing{drawing_num}.xml.rels'
    if draw_file not in z.namelist() or rels_file not in z.namelist():
        return {}
    draw_xml = ET.fromstring(z.read(draw_file))
    rels_xml = ET.fromstring(z.read(rels_file))
    rid_map = {}
    for r in rels_xml.findall('rel:Relationship', ns):
        t = r.attrib['Target'].replace('../', 'xl/')
        rid_map[r.attrib['Id']] = t
    
    row_col_to_img = {}
    for tag in ['twoCellAnchor', 'oneCellAnchor']:
        for anc in draw_xml.findall(f'xdr:{tag}', ns):
            frm = anc.find('xdr:from', ns)
            if frm is not None:
                c = int(frm.find('xdr:col', ns).text) + 1
                r = int(frm.find('xdr:row', ns).text) + 1
                blip = anc.find('.//a:blip', ns)
                if blip is not None:
                    embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if embed in rid_map:
                        row_col_to_img[(r, c)] = rid_map[embed]
    return row_col_to_img

print("1. Mở file Excel và đọc các bảng ánh xạ mã...")
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)

# ─── Đọc bảng chuyển đổi mã từ sheet LƯU Ý ───────────────────
ws_luuy = wb['LƯU Ý']
luuy_rows = list(ws_luuy.iter_rows(values_only=True))

code_aliases = {} # norm_code -> set of alias norm_codes
old_to_new_tuslo = []
nap_bon_cau_map = []
arrow_cn_en_map = []
online_priority_list = []
discontinued_list = []

for r_idx, row in enumerate(luuy_rows, 1):
    # Tuslo old -> new (rows 39..51)
    if 39 <= r_idx <= 52:
        c_old = clean_str(row[3] if len(row) > 3 else None)
        c_new = clean_str(row[5] if len(row) > 5 else None)
        if c_old and c_new and c_old != 'Mã cũ':
            old_to_new_tuslo.append({'ma_cu': c_old, 'ma_moi': c_new})
            nc1, nc2 = norm_code(c_old), norm_code(c_new)
            code_aliases.setdefault(nc1, set()).add(nc2)
            code_aliases.setdefault(nc2, set()).add(nc1)
        nap = clean_str(row[7] if len(row) > 7 else None)
        bc = clean_str(row[9] if len(row) > 9 else None)
        if nap and bc and nap != 'Mã nắp bồn cầu':
            nap_bon_cau_map.append({'ma_nap': nap, 'bon_cau': bc})
    # Online priority (rows 58..70)
    if 58 <= r_idx <= 70:
        ma = clean_str(row[4] if len(row) > 4 else None)
        ten = clean_str(row[6] if len(row) > 6 else None)
        nhom = clean_str(row[3] if len(row) > 3 else None)
        item = clean_str(row[5] if len(row) > 5 else None)
        if ma and ten:
            online_priority_list.append({'nhom': nhom, 'ma_sp': ma, 'ma_item': item, 'ten_sp': ten})
    # Discontinued (rows 75..102)
    if 75 <= r_idx <= 102:
        ma = clean_str(row[4] if len(row) > 4 else None)
        ten = clean_str(row[6] if len(row) > 6 else None)
        nhom = clean_str(row[3] if len(row) > 3 else None)
        item = clean_str(row[5] if len(row) > 5 else None)
        if ma and ten:
            discontinued_list.append({'nhom': nhom, 'ma_sp': ma, 'ma_item': item, 'ten_sp': ten})
    # Arrow CN <-> EN (rows 108..165)
    if r_idx >= 108:
        item_cn = clean_str(row[3] if len(row) > 3 else None)
        ma_cn = clean_str(row[4] if len(row) > 4 else None)
        ten_cn = clean_str(row[5] if len(row) > 5 else None)
        item_en = clean_str(row[8] if len(row) > 8 else None)
        ma_en = clean_str(row[9] if len(row) > 9 else None)
        ten_en = clean_str(row[10] if len(row) > 10 else None)
        if ma_cn and ma_en and ma_cn != 'Mã NCC':
            arrow_cn_en_map.append({
                'item_cn': item_cn, 'ma_cn': ma_cn, 'ten_cn': ten_cn,
                'item_en': item_en, 'ma_en': ma_en, 'ten_en': ten_en
            })
            nc1, nc2 = norm_code(ma_cn), norm_code(ma_en)
            code_aliases.setdefault(nc1, set()).add(nc2)
            code_aliases.setdefault(nc2, set()).add(nc1)

print(f"  - Tuslo Mã cũ->mới: {len(old_to_new_tuslo)}, Nắp bồn cầu: {len(nap_bon_cau_map)}, Arrow CN<->EN: {len(arrow_cn_en_map)}")

# ─── Quét toàn bộ Drawings để lấy media_path cho từng mã SP & tên SP ───
ma_to_media = {}      # norm_code -> xl/media/imageX.png
ma_to_ban_ve = {}     # norm_code -> xl/media/imageY.png (bản vẽ kỹ thuật)
name_to_media = {}    # norm_name -> xl/media/imageX.png

with zipfile.ZipFile(XLSX_PATH, 'r') as z:
    d6  = get_sheet_drawings(z, 6)   # DATA HÌNH ẢNH
    d4  = get_sheet_drawings(z, 4)   # HOT DMSP
    d37 = get_sheet_drawings(z, 37)  # Hình ảnh BCL
    d59 = get_sheet_drawings(z, 59)  # DMSP
    d60 = get_sheet_drawings(z, 60)  # DMSP - Arrow
    d31 = get_sheet_drawings(z, 31)  # QH ARROW
    d33 = get_sheet_drawings(z, 33)  # LIST TRƯNG ARROW
    d50 = get_sheet_drawings(z, 50)  # TCG
    d20 = get_sheet_drawings(z, 20)  # XẢ KHO
    d22 = get_sheet_drawings(z, 22)  # RA MẮT SP MỚI

    # Helper to register media for a code and its aliases
    def reg_media(ma_raw, name_raw, media_target, is_ban_ve=False):
        if not media_target: return
        target_dict = ma_to_ban_ve if is_ban_ve else ma_to_media
        if ma_raw:
            nc = norm_code(ma_raw)
            if nc and nc not in ('MÃSẢNPHẨM', 'MÃHÀNG', 'MÃSP'):
                target_dict.setdefault(nc, media_target)
                # Also strip trailing 'TM' for Toàn Mỹ if present
                if nc.endswith('TM') and len(nc) > 2:
                    target_dict.setdefault(nc[:-2], media_target)
                # Also register for aliases
                for al in code_aliases.get(nc, []):
                    target_dict.setdefault(al, media_target)
        if name_raw and not is_ban_ve:
            nn = norm_code(name_raw)
            if nn:
                name_to_media.setdefault(nn, media_target)

    # 1. DATA HÌNH ẢNH
    ws_ha = wb['DATA HÌNH ẢNH']
    ha_records = []
    for r_idx, row in enumerate(ws_ha.iter_rows(min_row=5, values_only=True), 5):
        if len(row) < 7: continue
        stt = row[1]
        nganh = clean_str(row[2])
        quy_cach = clean_str(row[3])
        brand = clean_str(row[4])
        ma = clean_str(row[5])
        ten = clean_str(row[6])
        if not ma and not ten: continue
        gia_ny = safe_int(row[8] if len(row) > 8 else 0) or safe_int(row[9] if len(row) > 9 else 0)
        gia_le = safe_int(row[10] if len(row) > 10 else 0)
        gia_si = safe_int(row[11] if len(row) > 11 else 0)
        bh = clean_str(row[12] if len(row) > 12 else None)
        thong_tin = clean_str(row[13] if len(row) > 13 else None)
        khac = clean_str(row[14] if len(row) > 14 else None)
        goi_y = clean_str(row[15] if len(row) > 15 else None)
        
        media = d6.get((r_idx, 8)) or d6.get((r_idx, 7)) or d6.get((r_idx, 9))
        reg_media(ma, ten, media)
        ha_records.append({
            'nganh_hang': nganh, 'quy_cach': quy_cach, 'thuong_hieu': brand,
            'ma_sp': ma, 'ten_sp': ten, 'gia_niem_yet': gia_ny,
            'gia_ban_le': gia_le, 'gia_ban_si': gia_si,
            'bao_hanh': bh, 'thong_tin': thong_tin, 'khac': khac, 'goi_y_mua_kem': goi_y,
            'media': media
        })

    # 2. HOT DMSP
    ws_hot = wb['HOT DMSP']
    hot_records = []
    for r_idx, row in enumerate(ws_hot.iter_rows(min_row=4, values_only=True), 4):
        if len(row) < 9: continue
        nganh = clean_str(row[2])
        nhom = clean_str(row[3])
        quy_cach = clean_str(row[4])
        nsx = clean_str(row[5])
        brand = clean_str(row[6])
        ma = clean_str(row[7])
        ten = clean_str(row[8])
        if not ma and not ten: continue
        thue = safe_float(row[10] if len(row) > 10 else 0)
        gia_ny = safe_int(row[11] if len(row) > 11 else 0)
        gia_le = safe_int(row[12] if len(row) > 12 else 0)
        gia_si = safe_int(row[13] if len(row) > 13 else 0)
        ma_ncc = clean_str(row[14] if len(row) > 14 else None)
        thong_so = clean_str(row[15] if len(row) > 15 else None)
        ghi_chu = clean_str(row[16] if len(row) > 16 else None)

        media = d4.get((r_idx, 10)) or d4.get((r_idx, 9)) or d4.get((r_idx, 11))
        reg_media(ma, ten, media)
        if ma_ncc: reg_media(ma_ncc, '', media)
        hot_records.append({
            'nganh_hang': nganh, 'nhom_sp': nhom, 'quy_cach': quy_cach, 'nsx': nsx,
            'thuong_hieu': brand, 'ma_sp': ma, 'ten_sp': ten, 'thue': thue,
            'gia_niem_yet': gia_ny, 'gia_ban_le': gia_le, 'gia_ban_si': gia_si,
            'ma_ncc': ma_ncc, 'thong_tin': thong_so, 'khac': ghi_chu, 'media': media
        })

    # 3. Hình ảnh BCL
    ws_bcl = wb['Hình ảnh BCL']
    bcl_records = []
    for r_idx, row in enumerate(ws_bcl.iter_rows(min_row=5, values_only=True), 5):
        if len(row) < 8: continue
        nganh = clean_str(row[2])
        quy_cach = clean_str(row[3])
        nsx = clean_str(row[4])
        brand = clean_str(row[5])
        ma = clean_str(row[6])
        ten = clean_str(row[7])
        if not ma and not ten: continue
        thue = safe_float(row[9] if len(row) > 9 else 0)
        gia_ny = safe_int(row[10] if len(row) > 10 else 0)
        gia_le = safe_int(row[11] if len(row) > 11 else 0)
        gia_nv = safe_int(row[12] if len(row) > 12 else 0)
        ma_ncc = clean_str(row[13] if len(row) > 13 else None)
        thong_so = clean_str(row[14] if len(row) > 14 else None)
        ghi_chu = clean_str(row[15] if len(row) > 15 else None)

        media = d37.get((r_idx, 9)) or d37.get((r_idx, 8)) or d37.get((r_idx, 10))
        reg_media(ma, ten, media)
        if ma_ncc: reg_media(ma_ncc, '', media)
        bcl_records.append({
            'nganh_hang': nganh, 'quy_cach': quy_cach, 'nsx': nsx,
            'thuong_hieu': brand, 'ma_sp': ma, 'ten_sp': ten, 'thue': thue,
            'gia_niem_yet': gia_ny, 'gia_ban_le': gia_le, 'gia_nhan_vien': gia_nv,
            'ma_ncc': ma_ncc, 'thong_tin': thong_so, 'ghi_chu_bcl': ghi_chu, 'media': media
        })

    # 4. DMSP
    ws_dmsp = wb['DMSP']
    dmsp_records = []
    for r_idx, row in enumerate(ws_dmsp.iter_rows(min_row=4, values_only=True), 4):
        if len(row) < 4 or not row[3]: continue
        brand = clean_str(row[1])
        nhom = clean_str(row[2])
        ma = clean_str(row[3])
        hot = bool(row[4] and 'X' in str(row[4]).upper())
        gia_cat = safe_int(row[6] if len(row) > 6 else 0)
        kt = clean_str(row[7] if len(row) > 7 else None)
        bh = clean_str(row[8] if len(row) > 8 else None)
        tt = clean_str(row[9] if len(row) > 9 else None)
        khac = clean_str(row[10] if len(row) > 10 else None)
        goi_y = clean_str(row[11] if len(row) > 11 else None)

        media = d59.get((r_idx, 6)) or d59.get((r_idx, 5))
        reg_media(ma, '', media)
        dmsp_records.append({
            'thuong_hieu': brand, 'nhom_sp': nhom, 'ma_sp': ma,
            'hang_ban_chay': hot, 'gia_catalogue': gia_cat,
            'kich_thuoc': kt, 'bao_hanh': bh, 'thong_tin': tt,
            'khac': khac, 'goi_y_mua_kem': goi_y, 'media': media
        })

    # 5. DMSP - Arrow
    ws_arr = wb['DMSP - Arrow']
    arr_records = []
    for r_idx, row in enumerate(ws_arr.iter_rows(min_row=5, values_only=True), 5):
        if len(row) < 5 or not row[3]: continue
        nhom = clean_str(row[2])
        ma = clean_str(row[3])
        ten = clean_str(row[4])
        ts = clean_str(row[5] if len(row) > 5 else None)
        gia_ny = safe_int(row[8] if len(row) > 8 else 0)
        diem_tb = clean_str(row[10] if len(row) > 10 else None)
        ma_cu = clean_str(row[11] if len(row) > 11 else None)

        media = d60.get((r_idx, 7))
        ban_ve = d60.get((r_idx, 8))
        reg_media(ma, ten, media)
        if ma_cu:
            nc1, nc2 = norm_code(ma), norm_code(ma_cu)
            code_aliases.setdefault(nc1, set()).add(nc2)
            code_aliases.setdefault(nc2, set()).add(nc1)
            reg_media(ma_cu, '', media)
        if ban_ve:
            reg_media(ma, '', ban_ve, is_ban_ve=True)
            if ma_cu: reg_media(ma_cu, '', ban_ve, is_ban_ve=True)
        arr_records.append({
            'nhom_sp': nhom, 'ma_sp': ma, 'ten_sp': ten, 'thong_tin': ts,
            'gia_niem_yet': gia_ny, 'diem_trung_bay': diem_tb, 'ma_cu': ma_cu,
            'media': media, 'ban_ve': ban_ve
        })

    # 6. QH ARROW & LIST TRƯNG ARROW
    ws_qh = wb['QH ARROW']
    for r_idx, row in enumerate(ws_qh.iter_rows(min_row=5, values_only=True), 5):
        if len(row) > 3 and row[3]:
            ma = clean_str(row[3])
            media = d31.get((r_idx, 8)) or d31.get((r_idx, 7))
            reg_media(ma, '', media)

    ws_lt = wb['LIST TRƯNG ARROW']
    for r_idx, row in enumerate(ws_lt.iter_rows(min_row=3, values_only=True), 3):
        if len(row) > 3 and row[3]:
            ma = clean_str(row[3])
            media = d33.get((r_idx, 8)) or d33.get((r_idx, 7))
            reg_media(ma, '', media)

print(f"2. Tổng số mã SP có ảnh: {len(ma_to_media)}, Bản vẽ kỹ thuật: {len(ma_to_ban_ve)}")

# ─── 3. Đọc TỒN KHO (17 kho + Phân loại + Quy cách) ──────────────
print("3. Đọc sheet TỒN KHO...")
ws_tk = wb['TỒN KHO']
kho_names = {}
for row in ws_tk.iter_rows(min_row=4, max_row=4, values_only=True):
    for j, v in enumerate(row):
        if v is not None and j >= 11:
            kho_names[j] = clean_str(v)

tk_by_ma = {}
for row in ws_tk.iter_rows(min_row=6, values_only=True):
    if len(row) < 8: continue
    ma_sp = clean_str(row[5])
    ma_item = clean_str(row[6]) if len(row) > 6 else ''
    nc = norm_code(ma_sp)
    ni = norm_code(ma_item)
    phan_loai = clean_str(row[2])
    quy_cach = clean_str(row[3])
    ton = {}
    for j, kho in kho_names.items():
        ton[kho] = safe_int(row[j]) if j < len(row) else 0
    data_entry = {
        'phan_loai': phan_loai,
        'quy_cach': quy_cach,
        'ton_kho': ton
    }
    if nc: tk_by_ma[nc] = data_entry
    if ni: tk_by_ma[ni] = data_entry
print(f"  - Đã đọc tồn kho của {len(tk_by_ma)} khóa tra cứu ({len(kho_names)} cột kho).")

# ─── 4. Đọc Giá Catalogue & ITEM ─────────────────────────────────
ws_cat = wb['Giá Catalogue']
cat_by_ma = {}
for row in ws_cat.iter_rows(min_row=3, values_only=True):
    if len(row) > 7 and row[2]:
        nc = norm_code(row[2])
        cat_by_ma[nc] = safe_int(row[6])
    if len(row) > 15 and row[9]:
        nc = norm_code(row[9])
        cat_by_ma[nc] = safe_int(row[14])

ws_item = wb['ITEM']
item_specs_by_code = {}
for row in ws_item.iter_rows(min_row=3, values_only=True):
    if len(row) < 4 or not row[2]: continue
    ma_item = clean_str(row[2])
    ma_sp = clean_str(row[19] if len(row) > 19 else None)
    spec_parts = []
    if len(row) > 9 and clean_str(row[9]): spec_parts.append(f"Tiêu chuẩn: {clean_str(row[9])}")
    if len(row) > 10 and clean_str(row[10]): spec_parts.append(f"Mác thép: {clean_str(row[10])}")
    if len(row) > 11 and clean_str(row[11]): spec_parts.append(f"Độ dày: {clean_str(row[11])}")
    if len(row) > 17 and clean_str(row[17]): spec_parts.append(f"Màu sắc: {clean_str(row[17])}")
    qc = clean_str(row[14] if len(row) > 14 else None)
    info = {
        'nhom_cap_1': clean_str(row[6] if len(row) > 6 else None),
        'nhom_cap_2': clean_str(row[7] if len(row) > 7 else None),
        'quy_cach': qc,
        'spec_extra': ' | '.join(spec_parts)
    }
    if ma_item: item_specs_by_code[norm_code(ma_item)] = info
    if ma_sp: item_specs_by_code[norm_code(ma_sp)] = info

# ─── 5. Đọc XẢ KHO 2026 & RA MẮT SP MỚI TUSLO ───────────────────
ws_xk = wb['“XẢ KHO ĐÓN MẪU MỚI 2026”']
xa_kho_items = []
xa_kho_by_item = {}
cur_category_xk = "Bồn cầu xả kho (CK thêm 12%)"
with zipfile.ZipFile(XLSX_PATH, 'r') as z_xk:
    for r_idx, row in enumerate(ws_xk.iter_rows(min_row=7, values_only=True), 7):
        if len(row) > 1 and row[1] and 'ƯU ĐÃI' in str(row[1]).upper():
            cur_category_xk = clean_str(row[1])
            continue
        if len(row) > 3 and row[2] and row[3] and str(row[2]).strip() not in ('Mã hàng', 'None'):
            ma_item = clean_str(row[2])
            ten_sp = clean_str(row[3])
            gia_ny = safe_int(row[5] if len(row) > 5 else 0)
            gia_new = safe_int(row[6] if len(row) > 6 else 0)
            gia_60_90 = safe_int(row[7] if len(row) > 7 else 0)
            gia_90_180 = safe_int(row[8] if len(row) > 8 else 0)
            gia_180_360 = safe_int(row[9] if len(row) > 9 else 0)
            gia_tren_360 = safe_int(row[10] if len(row) > 10 else 0)
            gia_thau = safe_int(row[11] if len(row) > 11 else 0)
            gia_dl = safe_int(row[12] if len(row) > 12 else 0)
            if gia_ny > 0:
                entry = {
                    'nhom_uu_dai': cur_category_xk,
                    'ma_item': ma_item,
                    'ten_sp': ten_sp,
                    'gia_niem_yet': gia_ny,
                    'gia_new_0_60': gia_new,
                    'gia_60_90': gia_60_90,
                    'gia_90_180': gia_90_180,
                    'gia_180_360': gia_180_360,
                    'gia_tren_360': gia_tren_360,
                    'gia_thau_tho': gia_thau,
                    'gia_dai_ly': gia_dl
                }
                xa_kho_items.append(entry)
                xa_kho_by_item[norm_code(ma_item)] = entry

ws_rm = wb['RA MẮT SẢN PHẨM MỚI - BST TUSLO']
ra_mat_items = []
ra_mat_by_item = {}
cur_promo_name = ''
cur_gift_val = 0
for r_idx, row in enumerate(ws_rm.iter_rows(min_row=6, values_only=True), 6):
    if len(row) < 15: continue
    if row[8]: cur_promo_name = clean_str(row[8])
    if row[10] and safe_int(row[10]) > 0: cur_gift_val = safe_int(row[10])
    ma_item = clean_str(row[2])
    ten_sp = clean_str(row[3])
    gift_item = clean_str(row[11])
    gift_ma = clean_str(row[12])
    gift_ten = clean_str(row[13])
    gift_gia = safe_int(row[15]) if len(row) > 15 else 0
    if ma_item and ten_sp:
        entry = {
            'ma_item': ma_item,
            'ten_sp': ten_sp,
            'gia_niem_yet': safe_int(row[5]),
            'gia_ban_le': safe_int(row[6]),
            'gia_dai_ly': safe_int(row[7]),
            'ctkm': cur_promo_name,
            'tong_qua_tang': cur_gift_val,
            'qua_tang': f"{gift_ten} ({gift_ma}) - Trị giá {gift_gia:,}đ" if gift_ten else ''
        }
        ra_mat_items.append(entry)
        ra_mat_by_item[norm_code(ma_item)] = entry

print(f"  - Xả kho 2026: {len(xa_kho_items)} SP, Ra mắt BST Tuslo: {len(ra_mat_items)} SP")

# ─── 6. Đọc DATA GIÁ (Toàn bộ 1.663 SP + sửa đúng cột giá + giá lịch sử) ───
print("4. Đọc DATA GIÁ và gộp dữ liệu chi tiết...")
ws_gia = wb['DATA GIÁ']
products = []
seen_norm_codes = set()
seen_norm_items = set()

online_set = {norm_code(x['ma_sp']) for x in online_priority_list} | {norm_code(x['ma_item']) for x in online_priority_list if x['ma_item']}
discont_set = {norm_code(x['ma_sp']) for x in discontinued_list} | {norm_code(x['ma_item']) for x in discontinued_list if x['ma_item']}
old_to_new_dict = {norm_code(x['ma_cu']): x['ma_moi'] for x in old_to_new_tuslo}
new_to_old_dict = {norm_code(x['ma_moi']): x['ma_cu'] for x in old_to_new_tuslo}
nap_dict = {norm_code(x['bon_cau']): x['ma_nap'] for x in nap_bon_cau_map}

for row in ws_gia.iter_rows(min_row=9, values_only=True):
    if row[1] is None or row[2] is None or not row[5]:
        continue
    brand = clean_str(row[2])
    ma_item = clean_str(row[3])
    ma_sp = clean_str(row[4])
    ten_sp = clean_str(row[5])
    dvt = clean_str(row[6])
    thue = safe_float(row[7])

    # Đúng chuẩn cột DATA GIÁ:
    # Col 8: Giá công bố (Chưa VAT)
    # Col 9: Giá niêm yết (Có VAT)
    # Col 10: Giá bán lẻ
    # Col 11: Giá thầu thợ (CK 10%)
    # Col 12: Thân thiết C1 (CK 20%)
    # Col 13: Thân thiết C2 (CK 20%)
    # Col 14: Đại lý C1 (CK 20%)
    # Col 15: Đại lý C2 (CK 20%)
    # Col 16: Đại lý C3 (CK 20%)
    # Col 17: Đại lý C4 (CK 20%)
    # Col 18: NPP C1 (CK 22%)
    # Col 19: NPP C2 (CK 22%)
    # Col 20: NPP C3 (CK 25%)
    # Col 21: Chính sách bán mẫu
    gia_cong_bo  = safe_int(row[8])
    gia_niem_yet = safe_int(row[9])
    gia_ban_le   = safe_int(row[10])
    gia_thau_tho = safe_int(row[11])
    than_thiet_c1 = safe_int(row[12])
    than_thiet_c2 = safe_int(row[13])
    dai_ly_c1    = safe_int(row[14])
    dai_ly_c2    = safe_int(row[15])
    dai_ly_c3    = safe_int(row[16])
    dai_ly_c4    = safe_int(row[17])
    npp_c1       = safe_int(row[18])
    npp_c2       = safe_int(row[19])
    npp_c3       = safe_int(row[20] if len(row) > 20 else 0)
    gia_ban_mau  = safe_int(row[21] if len(row) > 21 else 0)

    # Lịch sử giá cũ (Col 23..39)
    lich_su_gia = {}
    hist_cols = [
        (23, 'Trước 01/01/2025 (Niêm yết)'),
        (24, 'Trước 01/01/2025 (Giá lẻ)'),
        (25, 'Trước 01/01/2025 (Giá thầu)'),
        (26, 'Trước 01/01/2025 (Giá sỉ)'),
        (30, 'Ngày 24/05/2025 (Có VAT)'),
        (32, 'Trước 24/05/2025 (Có VAT)'),
        (34, 'Trước 01/07/2025 (Có VAT)'),
        (35, 'Trước 01/08/2025 (Có VAT)'),
        (36, 'INAX trước 21/04/2026 (Chưa VAT)'),
        (37, 'TUSLO trước 01/05/2026 (Chưa VAT)'),
        (38, 'INAX trước 28/05/2026 (Chưa VAT)'),
        (39, 'TUSLO-LUSHINE trước 17/06/2026 (Chưa VAT)')
    ]
    for c_idx, label in hist_cols:
        if len(row) > c_idx and safe_int(row[c_idx]) > 0:
            lich_su_gia[label] = safe_int(row[c_idx])

    nc = norm_code(ma_sp)
    ni = norm_code(ma_item)
    if nc: seen_norm_codes.add(nc)
    if ni: seen_norm_items.add(ni)

    products.append({
        'id': len(products) + 1,
        'stt': safe_int(row[1]) or (len(products) + 1),
        'nguon': 'Bảng giá chính',
        'nganh_hang': 'TBVS',
        'thuong_hieu': brand,
        'ma_item': ma_item,
        'ma_sp': ma_sp,
        'ma_phu': '',
        'ten_sp': ten_sp,
        'dvt': dvt,
        'thue': thue,
        'gia_cong_bo': gia_cong_bo,
        'gia_niem_yet': gia_niem_yet,
        'gia_ban_le': gia_ban_le,
        'gia_thau_tho': gia_thau_tho,
        'gia_dai_ly': dai_ly_c1 or than_thiet_c1,
        'than_thiet_c1': than_thiet_c1,
        'than_thiet_c2': than_thiet_c2,
        'dai_ly_c1': dai_ly_c1,
        'dai_ly_c2': dai_ly_c2,
        'dai_ly_c3': dai_ly_c3,
        'dai_ly_c4': dai_ly_c4,
        'npp_c1': npp_c1,
        'npp_c2': npp_c2,
        'npp_c3': npp_c3,
        'gia_ban_mau': gia_ban_mau,
        'gia_catalogue': cat_by_ma.get(nc, 0),
        'gia_nhan_vien': 0,
        'lich_su_gia': lich_su_gia,
        'nhom_sp': '',
        'kich_thuoc': '',
        'bao_hanh': '',
        'thong_tin': '',
        'khac': '',
        'goi_y_mua_kem': '',
        'diem_trung_bay': '',
        'hang_ban_chay': False,
        'uu_tien_online': (nc in online_set or ni in online_set),
        'ngung_nhap': (nc in discont_set or ni in discont_set),
        'xa_kho': xa_kho_by_item.get(ni) or xa_kho_by_item.get(nc),
        'ctkm_tuslo': ra_mat_by_item.get(ni) or ra_mat_by_item.get(nc),
        'hinh_anh': '',
        'hinh_ban_ve': '',
        'ton_kho': {}
    })

# Build index by norm_code and norm_name
prod_by_code = {}
prod_by_name = {}
for p in products:
    nc = norm_code(p['ma_sp'])
    ni = norm_code(p['ma_item'])
    nn = norm_code(p['ten_sp'])
    if nc:
        prod_by_code[nc] = p
        for al in code_aliases.get(nc, []):
            prod_by_code.setdefault(al, p)
    if ni:
        prod_by_code.setdefault(ni, p)
    if nn:
        prod_by_name[nn] = p

# Enrich from TỒN KHO
for p in products:
    nc = norm_code(p.get('ma_sp'))
    ni = norm_code(p.get('ma_item'))
    tk_info = tk_by_ma.get(nc) or tk_by_ma.get(ni)
    if tk_info:
        p['ton_kho'] = tk_info['ton_kho']
        if tk_info['phan_loai'] and not p.get('nhom_sp'):
            p['nhom_sp'] = tk_info['phan_loai']
        if tk_info['quy_cach'] and not p.get('kich_thuoc'):
            p['kich_thuoc'] = tk_info['quy_cach']

# Enrich from ITEM
for code_key, spec_info in item_specs_by_code.items():
    p = prod_by_code.get(code_key)
    if p:
        if spec_info['nhom_cap_2'] and not p['nhom_sp']:
            p['nhom_sp'] = spec_info['nhom_cap_2']
        if spec_info['quy_cach'] and not p['kich_thuoc']:
            p['kich_thuoc'] = spec_info['quy_cach']
        if spec_info['spec_extra'] and spec_info['spec_extra'] not in p['thong_tin']:
            p['thong_tin'] = (p['thong_tin'] + '\n' + spec_info['spec_extra']).strip()

# Enrich from DMSP
for rec in dmsp_records:
    nc = norm_code(rec['ma_sp'])
    p = prod_by_code.get(nc)
    if p:
        if rec['nhom_sp']: p['nhom_sp'] = rec['nhom_sp']
        if rec['hang_ban_chay']: p['hang_ban_chay'] = True
        if rec['gia_catalogue'] and not p['gia_catalogue']: p['gia_catalogue'] = rec['gia_catalogue']
        if rec['kich_thuoc']: p['kich_thuoc'] = rec['kich_thuoc']
        if rec['bao_hanh']: p['bao_hanh'] = rec['bao_hanh']
        if rec['thong_tin']: p['thong_tin'] = rec['thong_tin']
        if rec['khac']: p['khac'] = rec['khac']
        if rec['goi_y_mua_kem']: p['goi_y_mua_kem'] = rec['goi_y_mua_kem']

# Enrich from DMSP - Arrow
for rec in arr_records:
    nc = norm_code(rec['ma_sp'])
    p = prod_by_code.get(nc) or (prod_by_code.get(norm_code(rec['ma_cu'])) if rec['ma_cu'] else None)
    if p:
        if rec['nhom_sp'] and not p['nhom_sp']: p['nhom_sp'] = rec['nhom_sp']
        if rec['thong_tin'] and not p['thong_tin']: p['thong_tin'] = rec['thong_tin']
        if rec['diem_trung_bay']: p['diem_trung_bay'] = rec['diem_trung_bay']
        if rec['ma_cu']: p['ma_phu'] = f"Mã cũ: {rec['ma_cu']}"

# Enrich from DATA HÌNH ẢNH + Add any new products not in DATA GIÁ
added_from_ha = 0
for rec in ha_records:
    nc = norm_code(rec['ma_sp'])
    nn = norm_code(rec['ten_sp'])
    p = prod_by_code.get(nc) if nc else None
    if not p and nc.endswith('TM'):
        p = prod_by_code.get(nc[:-2])
    if not p and nn:
        p = prod_by_name.get(nn)
    if p:
        if rec['nganh_hang']: p['nganh_hang'] = rec['nganh_hang']
        if rec['quy_cach'] and not p['kich_thuoc']: p['kich_thuoc'] = rec['quy_cach']
        if rec['bao_hanh'] and not p['bao_hanh']: p['bao_hanh'] = rec['bao_hanh']
        if rec['thong_tin'] and not p['thong_tin']: p['thong_tin'] = rec['thong_tin']
        if rec['khac'] and not p['khac']: p['khac'] = rec['khac']
        if rec['goi_y_mua_kem'] and not p['goi_y_mua_kem']: p['goi_y_mua_kem'] = rec['goi_y_mua_kem']
        if not p['gia_niem_yet'] and rec['gia_niem_yet']: p['gia_niem_yet'] = rec['gia_niem_yet']
        if not p['gia_ban_le'] and rec['gia_ban_le']: p['gia_ban_le'] = rec['gia_ban_le']
        if not p['gia_dai_ly'] and rec['gia_ban_si']: p['gia_dai_ly'] = rec['gia_ban_si']
    elif rec['ma_sp'] and rec['ten_sp'] and rec['ma_sp'] != 'Mã sản phẩm':
        new_p = {
            'id': len(products) + 1,
            'stt': len(products) + 1,
            'nguon': 'Danh mục HSH Miền Trung',
            'nganh_hang': rec['nganh_hang'] or 'TBVS',
            'thuong_hieu': rec['thuong_hieu'] or 'Khác',
            'ma_item': '',
            'ma_sp': rec['ma_sp'],
            'ma_phu': '',
            'ten_sp': rec['ten_sp'],
            'dvt': 'Bộ/Cái',
            'thue': 0.08,
            'gia_cong_bo': 0,
            'gia_niem_yet': rec['gia_niem_yet'],
            'gia_ban_le': rec['gia_ban_le'] or rec['gia_niem_yet'],
            'gia_thau_tho': 0,
            'gia_dai_ly': rec['gia_ban_si'],
            'than_thiet_c1': rec['gia_ban_si'],
            'than_thiet_c2': rec['gia_ban_si'],
            'dai_ly_c1': rec['gia_ban_si'],
            'dai_ly_c2': rec['gia_ban_si'],
            'dai_ly_c3': rec['gia_ban_si'],
            'dai_ly_c4': rec['gia_ban_si'],
            'npp_c1': 0, 'npp_c2': 0, 'npp_c3': 0, 'gia_ban_mau': 0,
            'gia_catalogue': 0, 'gia_nhan_vien': 0,
            'lich_su_gia': {},
            'nhom_sp': rec['quy_cach'] if rec['quy_cach'] and not any(c.isdigit() for c in rec['quy_cach']) else 'Thiết bị vệ sinh',
            'kich_thuoc': rec['quy_cach'] if rec['quy_cach'] and any(c.isdigit() for c in rec['quy_cach']) else '',
            'bao_hanh': rec['bao_hanh'],
            'thong_tin': rec['thong_tin'],
            'khac': rec['khac'],
            'goi_y_mua_kem': rec['goi_y_mua_kem'],
            'diem_trung_bay': '',
            'hang_ban_chay': False,
            'uu_tien_online': False,
            'ngung_nhap': False,
            'xa_kho': None,
            'ctkm_tuslo': None,
            'hinh_anh': '',
            'hinh_ban_ve': '',
            'ton_kho': tk_by_ma.get(nc, {}).get('ton_kho', {})
        }
        products.append(new_p)
        prod_by_code[nc] = new_p
        added_from_ha += 1

# Enrich from HOT DMSP + Add any new products
added_from_hot = 0
for rec in hot_records:
    nc = norm_code(rec['ma_sp'])
    nn = norm_code(rec['ten_sp'])
    p = prod_by_code.get(nc) or (prod_by_code.get(norm_code(rec['ma_ncc'])) if rec['ma_ncc'] else None) or prod_by_name.get(nn)
    if p:
        p['hang_ban_chay'] = True
        if rec['nhom_sp'] and not p['nhom_sp']: p['nhom_sp'] = rec['nhom_sp']
        if rec['quy_cach'] and not p['nhom_sp']: p['nhom_sp'] = rec['quy_cach']
        if rec['thong_tin'] and not p['thong_tin']: p['thong_tin'] = rec['thong_tin']
        if rec['khac'] and not p['khac']: p['khac'] = rec['khac']
        if not p['gia_niem_yet'] and rec['gia_niem_yet']: p['gia_niem_yet'] = rec['gia_niem_yet']
        if not p['gia_ban_le'] and rec['gia_ban_le']: p['gia_ban_le'] = rec['gia_ban_le']
    elif rec['ma_sp'] and rec['ten_sp'] and rec['ma_sp'] != 'Mã sản phẩm':
        new_p = {
            'id': len(products) + 1,
            'stt': len(products) + 1,
            'nguon': 'HOT DMSP',
            'nganh_hang': rec['nganh_hang'] or 'TBVS',
            'thuong_hieu': rec['thuong_hieu'] or rec['nsx'] or 'Khác',
            'ma_item': '',
            'ma_sp': rec['ma_sp'],
            'ma_phu': rec['ma_ncc'],
            'ten_sp': rec['ten_sp'],
            'dvt': 'Bộ/Cái',
            'thue': rec['thue'] or 0.08,
            'gia_cong_bo': 0,
            'gia_niem_yet': rec['gia_niem_yet'],
            'gia_ban_le': rec['gia_ban_le'] or rec['gia_niem_yet'],
            'gia_thau_tho': 0,
            'gia_dai_ly': rec['gia_ban_si'],
            'than_thiet_c1': rec['gia_ban_si'], 'than_thiet_c2': rec['gia_ban_si'],
            'dai_ly_c1': rec['gia_ban_si'], 'dai_ly_c2': rec['gia_ban_si'],
            'dai_ly_c3': rec['gia_ban_si'], 'dai_ly_c4': rec['gia_ban_si'],
            'npp_c1': 0, 'npp_c2': 0, 'npp_c3': 0, 'gia_ban_mau': 0,
            'gia_catalogue': 0, 'gia_nhan_vien': 0,
            'lich_su_gia': {},
            'nhom_sp': rec['quy_cach'] or rec['nhom_sp'] or 'Thiết bị vệ sinh',
            'kich_thuoc': '',
            'bao_hanh': '',
            'thong_tin': rec['thong_tin'],
            'khac': rec['khac'],
            'goi_y_mua_kem': '',
            'diem_trung_bay': '',
            'hang_ban_chay': True,
            'uu_tien_online': False,
            'ngung_nhap': False,
            'xa_kho': None,
            'ctkm_tuslo': None,
            'hinh_anh': '',
            'hinh_ban_ve': '',
            'ton_kho': tk_by_ma.get(nc, {}).get('ton_kho', {})
        }
        products.append(new_p)
        prod_by_code[nc] = new_p
        added_from_hot += 1

# Enrich from Hình ảnh BCL + Add any new products
added_from_bcl = 0
for rec in bcl_records:
    nc = norm_code(rec['ma_sp'])
    nn = norm_code(rec['ten_sp'])
    p = prod_by_code.get(nc) or prod_by_name.get(nn)
    if p:
        if rec['gia_nhan_vien']: p['gia_nhan_vien'] = rec['gia_nhan_vien']
        if rec['thong_tin'] and not p['thong_tin']: p['thong_tin'] = rec['thong_tin']
        if rec['ghi_chu_bcl']:
            p['khac'] = (p['khac'] + '\n' + rec['ghi_chu_bcl']).strip() if p['khac'] else rec['ghi_chu_bcl']
    elif rec['ma_sp'] and rec['ten_sp'] and rec['ma_sp'] != 'Mã sản phẩm':
        new_p = {
            'id': len(products) + 1,
            'stt': len(products) + 1,
            'nguon': 'Hàng BCL / Dự án',
            'nganh_hang': rec['nganh_hang'] or 'TBVS',
            'thuong_hieu': rec['thuong_hieu'] or rec['nsx'] or 'Khác',
            'ma_item': '',
            'ma_sp': rec['ma_sp'],
            'ma_phu': rec['ma_ncc'],
            'ten_sp': rec['ten_sp'],
            'dvt': 'Bộ/Cái',
            'thue': rec['thue'] or 0.08,
            'gia_cong_bo': 0,
            'gia_niem_yet': rec['gia_niem_yet'],
            'gia_ban_le': rec['gia_ban_le'] or rec['gia_niem_yet'],
            'gia_thau_tho': 0,
            'gia_dai_ly': 0,
            'than_thiet_c1': 0, 'than_thiet_c2': 0,
            'dai_ly_c1': 0, 'dai_ly_c2': 0, 'dai_ly_c3': 0, 'dai_ly_c4': 0,
            'npp_c1': 0, 'npp_c2': 0, 'npp_c3': 0, 'gia_ban_mau': 0,
            'gia_catalogue': 0, 'gia_nhan_vien': rec['gia_nhan_vien'],
            'lich_su_gia': {},
            'nhom_sp': rec['quy_cach'] or 'Thiết bị vệ sinh',
            'kich_thuoc': '',
            'bao_hanh': '',
            'thong_tin': rec['thong_tin'],
            'khac': rec['ghi_chu_bcl'],
            'goi_y_mua_kem': '',
            'diem_trung_bay': '',
            'hang_ban_chay': False,
            'uu_tien_online': False,
            'ngung_nhap': False,
            'xa_kho': None,
            'ctkm_tuslo': None,
            'hinh_anh': '',
            'hinh_ban_ve': '',
            'ton_kho': tk_by_ma.get(nc, {}).get('ton_kho', {})
        }
        products.append(new_p)
        prod_by_code[nc] = new_p
        added_from_bcl += 1

print(f"  - Tổng sản phẩm sau khi gộp: {len(products)} (+{added_from_ha} từ DATA HÌNH ẢNH, +{added_from_hot} từ HOT DMSP, +{added_from_bcl} từ BCL)")

# ─── 7. Chuẩn hóa tên thương hiệu, suy luận nhóm SP nếu trống & gắn mã phụ / nắp bồn cầu ───
BRAND_MAP = {
    'AMERICAN STANDAR': 'American Standard',
    'AMERICAN STANDARD': 'American Standard',
    'ARROW': 'ARROW',
    'CAESAR': 'CAESAR',
    'HAFELE': 'HAFELE',
    'HÙNG ANH': 'Hùng Anh',
    'INAX': 'INAX',
    'KITTO': 'KITTO',
    'LUSHINE': 'LUSHINE',
    'ROCA': 'ROCA',
    'SƠN HÀ': 'Sơn Hà',
    'TEKA': 'TEKA',
    'TOTO': 'TOTO',
    'TUSLO': 'TUSLO',
    'TUSLO LUXURY': 'TUSLO',
    'TUSLO PRO': 'TUSLO',
    'TOÀN MỸ': 'Toàn Mỹ',
    'TÂN AN VINH': 'Tân An Vinh',
    'VIGLACERA': 'VIGLACERA',
}

def infer_group(name):
    n = name.lower()
    if 'combo' in n: return 'Combo TBVS'
    if 'bồn cầu thông minh' in n or 'nắp rửa điện tử' in n: return 'Bồn cầu thông minh'
    if 'bồn cầu một khối' in n or 'bồn cầu 1 khối' in n or 'bàn cầu 1 khối' in n: return 'Bồn cầu 1 khối'
    if 'bồn cầu hai khối' in n or 'bồn cầu 2 khối' in n or 'bàn cầu 2 khối' in n: return 'Bồn cầu 2 khối'
    if 'bồn cầu treo tường' in n or 'thân cầu treo tường' in n: return 'Bồn cầu treo tường'
    if 'bồn cầu' in n or 'bàn cầu' in n: return 'Bồn cầu'
    if 'bồn tiểu' in n or 'van xả tiểu' in n or 'bộ xả tiểu' in n: return 'Bồn tiểu & Van xả'
    if 'bồn tắm' in n: return 'Bồn tắm'
    if 'tủ lavabo' in n or 'bộ tủ lavabo' in n: return 'Tủ lavabo'
    if 'tủ gương' in n: return 'Tủ gương'
    if 'lavabo đặt bàn' in n or 'lavabo dương' in n: return 'Lavabo đặt bàn'
    if 'lavabo treo tường' in n: return 'Lavabo treo tường'
    if 'lavabo âm bàn' in n or 'lavabo bán âm' in n: return 'Lavabo âm bàn'
    if 'lavabo' in n or 'chậu rửa mặt' in n: return 'Lavabo'
    if 'sen cây' in n or 'sen tắm cây' in n: return 'Sen cây'
    if 'sen tắm' in n or 'sen dây' in n or 'củ sen' in n or 'bát sen' in n or 'tay sen' in n or 'đầu sen' in n: return 'Sen tắm'
    if 'vòi lavabo' in n: return 'Vòi lavabo'
    if 'vòi bếp' in n or 'vòi rửa chén' in n or 'vòi chén' in n: return 'Vòi rửa chén'
    if 'chậu rửa chén' in n or 'chậu rửa inox' in n: return 'Chậu rửa chén'
    if 'gương' in n: return 'Gương phòng tắm'
    if 'vòi xịt' in n: return 'Vòi xịt vệ sinh'
    if 'bếp từ' in n or 'bếp điện' in n or 'máy hút mùi' in n or 'lò nướng' in n: return 'Thiết bị bếp'
    if 'khóa' in n or 'bản lề' in n or 'tay nắm' in n: return 'Phụ kiện cửa & bếp'
    return 'Phụ kiện phòng tắm'

for p in products:
    b_up = p['thuong_hieu'].strip().upper()
    if b_up in BRAND_MAP:
        p['thuong_hieu'] = BRAND_MAP[b_up]
    if not p['nhom_sp'] or p['nhom_sp'] in ('(blank)', 'Thiết bị vệ sinh'):
        p['nhom_sp'] = infer_group(p['ten_sp'])
    nc = norm_code(p['ma_sp'])
    notes_extra = []
    if nc in old_to_new_dict:
        notes_extra.append(f"Mã mới tương ứng: {old_to_new_dict[nc]}")
    if nc in new_to_old_dict:
        notes_extra.append(f"Mã cũ tương ứng: {new_to_old_dict[nc]}")
    if nc in nap_dict:
        notes_extra.append(f"Mã nắp bồn cầu thay thế phù hợp: {nap_dict[nc]}")
    if notes_extra:
        p['ma_phu'] = (p['ma_phu'] + ' | ' if p['ma_phu'] else '') + ' | '.join(notes_extra)

# ─── 8. Giải nén & tối ưu toàn bộ ảnh sản phẩm được tham chiếu ───
print("5. Trích xuất và tối ưu hình ảnh từ file Excel...")
media_to_webpath = {}

def resolve_media_for_product(p):
    nc = norm_code(p['ma_sp'])
    ni = norm_code(p['ma_item'])
    nn = norm_code(p['ten_sp'])
    # 1. Exact norm_code
    if nc in ma_to_media: return ma_to_media[nc]
    if ni and ni in ma_to_media: return ma_to_media[ni]
    # 2. Alias codes
    for al in code_aliases.get(nc, []):
        if al in ma_to_media: return ma_to_media[al]
    for al in code_aliases.get(ni, []):
        if al in ma_to_media: return ma_to_media[al]
    # 3. Strip suffix/prefix before '/' if >= 5 chars
    if '/' in nc:
        prefix = nc.split('/')[0]
        if len(prefix) >= 5:
            for k, v in ma_to_media.items():
                if k == prefix or k.startswith(prefix + '/'):
                    return v
    # 4. Name match
    if nn in name_to_media:
        return name_to_media[nn]
    return ''

needed_media = set()
for p in products:
    m1 = resolve_media_for_product(p)
    m2 = ma_to_ban_ve.get(norm_code(p['ma_sp']), '')
    if m1:
        p['_media_1'] = m1
        needed_media.add(m1)
    if m2:
        p['_media_2'] = m2
        needed_media.add(m2)

print(f"  - Cần giải nén {len(needed_media)} file ảnh duy nhất cho {sum(1 for p in products if p.get('_media_1'))}/{len(products)} sản phẩm.")

with zipfile.ZipFile(XLSX_PATH, 'r') as z:
    extracted_cnt = 0
    for media_path in sorted(needed_media):
        if media_path not in z.namelist():
            continue
        base_name = os.path.splitext(os.path.basename(media_path))[0]
        out_filename = f"{base_name}.webp"
        out_fullpath = os.path.join(IMG_DIR, out_filename)
        web_relpath = f"images/products/{out_filename}"
        
        if not os.path.exists(out_fullpath):
            try:
                raw_bytes = z.read(media_path)
                img = Image.open(io.BytesIO(raw_bytes))
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
                img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                img.save(out_fullpath, 'WEBP', quality=84, method=4)
            except Exception as e:
                # Fallback copy raw file
                ext = os.path.splitext(media_path)[1].lower() or '.png'
                out_filename = f"{base_name}{ext}"
                out_fullpath = os.path.join(IMG_DIR, out_filename)
                web_relpath = f"images/products/{out_filename}"
                with open(out_fullpath, 'wb') as f_out:
                    f_out.write(z.read(media_path))
        media_to_webpath[media_path] = web_relpath
        extracted_cnt += 1

for p in products:
    m1 = p.pop('_media_1', '')
    m2 = p.pop('_media_2', '')
    if m1 and m1 in media_to_webpath:
        p['hinh_anh'] = media_to_webpath[m1]
    if m2 and m2 in media_to_webpath:
        p['hinh_ban_ve'] = media_to_webpath[m2]

print(f"  - Đã xuất {extracted_cnt} ảnh WebP thành công!")

# ─── 9. Đọc các sheet Cẩm Nang Kinh Doanh / Chính Sách / Phụ Kiện / DSCH ───
print("6. Trích xuất dữ liệu Cẩm nang, Chính sách, Lắp đặt, Phụ kiện, Cửa hàng...")

# 9.1 Chi phí lắp đặt
chi_phi_lap_dat = [
    {'stt': 1, 'mat_hang': 'Bồn cầu tiêu chuẩn, bồn tiểu', 'chua_vat': 450000, 'co_vat': 486000},
    {'stt': 2, 'mat_hang': 'Bồn cầu thông minh', 'chua_vat': 850000, 'co_vat': 918000},
    {'stt': 3, 'mat_hang': 'Bồn tắm, vách kính tắm', 'chua_vat': 1000000, 'co_vat': 1080000},
    {'stt': 4, 'mat_hang': 'Lavabo (không thi công cắt đá)', 'chua_vat': 350000, 'co_vat': 378000},
    {'stt': 5, 'mat_hang': 'Lavabo (có thi công cắt đá)', 'chua_vat': 500000, 'co_vat': 540000},
    {'stt': 6, 'mat_hang': 'Tủ gương lavabo', 'chua_vat': 500000, 'co_vat': 540000},
    {'stt': 7, 'mat_hang': 'Sen tắm', 'chua_vat': 300000, 'co_vat': 330000},
    {'stt': 8, 'mat_hang': 'Chậu rửa chén (có thi công cắt đá)', 'chua_vat': 500000, 'co_vat': 550000},
]

# 9.2 Kiến thức sản phẩm & Phụ kiện đi kèm (Sheet PHỤ KIỆN ĐI KÈM)
ws_pkdk = wb['PHỤ KIỆN ĐI KÈM']
kien_thuc_sp = []
cur_brand_pk = ''
cur_prod_pk = ''
for row in ws_pkdk.iter_rows(min_row=3, values_only=True):
    if len(row) < 10: continue
    if clean_str(row[1]): cur_brand_pk = clean_str(row[1])
    if clean_str(row[3]): cur_prod_pk = clean_str(row[3])
    chi_tiet = clean_str(row[4])
    chat_lieu = clean_str(row[5])
    cong_nghe = clean_str(row[6])
    cong_dung = clean_str(row[7])
    bao_hanh = clean_str(row[8])
    pk_di_kem = clean_str(row[9])
    tu_van_them = clean_str(row[10] if len(row) > 10 else None)
    ghi_chu = clean_str(row[11] if len(row) > 11 else None)
    if chi_tiet or cong_nghe or pk_di_kem:
        kien_thuc_sp.append({
            'thuong_hieu': cur_brand_pk,
            'san_pham': cur_prod_pk,
            'chi_tiet': chi_tiet,
            'chat_lieu': chat_lieu,
            'cong_nghe': cong_nghe,
            'cong_dung': cong_dung,
            'bao_hanh': bao_hanh,
            'phu_kien_di_kem': pk_di_kem,
            'tu_van_mua_them': tu_van_them,
            'ghi_chu': ghi_chu
        })

# 9.3 Danh sách cửa hàng (Sheet DSCH)
ws_dsch = wb['DSCH']
danh_sach_cua_hang = []
for row in ws_dsch.iter_rows(min_row=3, values_only=True):
    if len(row) < 7 or not row[4]: continue
    tinh_moi = clean_str(row[3])
    ma_ch = clean_str(row[4])
    ten_ch = clean_str(row[5])
    mo_hinh = clean_str(row[6])
    tinh_cu = clean_str(row[9] if len(row) > 9 else None)
    ma_cu = clean_str(row[10] if len(row) > 10 else None)
    ten_cu = clean_str(row[11] if len(row) > 11 else None)
    if ma_ch and ten_ch:
        danh_sach_cua_hang.append({
            'tinh_moi': tinh_moi, 'ma_ch': ma_ch, 'ten_ch': ten_ch, 'mo_hinh': mo_hinh,
            'tinh_cu': tinh_cu, 'ma_ch_cu': ma_cu, 'ten_ch_cu': ten_cu
        })

# 9.4 PT - CTKM
ws_pt = wb['PT - CTKM']
pt_ctkm_list = []
for row in ws_pt.iter_rows(min_row=9, values_only=True):
    if len(row) >= 13 and row[3] and row[4]:
        pt_ctkm_list.append({
            'stt': safe_int(row[2]),
            'ma_item': clean_str(row[3]),
            'ten_sp': clean_str(row[4]),
            'dvt': clean_str(row[5]),
            'so_luong': safe_int(row[6]),
            'gia_niem_yet': safe_int(row[7]),
            'gia_km': safe_int(row[8]),
            'thanh_tien_km': safe_int(row[9]),
            'gia_sau_km': safe_int(row[10]),
            'thanh_tien_sau_km': safe_int(row[11]),
            'chenh_lech': safe_int(row[12])
        })

# 9.5 Tổng hợp extras.json
extras = {
    'thong_ke': {
        'tong_sp': len(products),
        'co_hinh_anh': sum(1 for p in products if p['hinh_anh']),
        'co_ton_kho': sum(1 for p in products if sum(v for k, v in p.get('ton_kho', {}).items() if 'Tổng' not in k) > 0),
        'hang_hot': sum(1 for p in products if p['hang_ban_chay']),
        'danh_sach_kho': list(kho_names.values())
    },
    'thu_vien_links': [
        {'nhom': 'Tài liệu kiến thức', 'ten': '📚 Tài Liệu Kiến Thức Sản Phẩm Thiết Bị Vệ Sinh', 'url': 'https://drive.google.com/drive/folders/16mbfIQ8sT87oIPZ26GelFBwG9FKxfWyI?usp=sharing'},
        {'nhom': 'Catalogue', 'ten': '📖 Catalogue Thiết Bị Vệ Sinh Hoa Sen Group', 'url': 'https://drive.google.com/drive/folders/1C5tQQvyb7r4gFRlT_iR_7U5LcuEvdcyW?usp=sharing'},
        {'nhom': 'Video & Hình ảnh', 'ten': '🛀 Album Ảnh & Video TUSLO & LUSHINE HSH', 'url': 'https://photos.app.goo.gl/xxHkznYiK8AxwfEC7'},
        {'nhom': 'Tem & Tab giá', 'ten': '🏷️ File Tem - Tab Giá A5 & A7 TBNT - NB', 'url': 'https://drive.google.com/drive/folders/12z3Pc6KUsVXzWCBpD_agBY6TxENL4e0_'},
        {'nhom': 'Khiếu nại', 'ten': '🛠️ Hướng Dẫn Công Tác Khiếu Nại TBNT&NB (Google Sheet)', 'url': 'https://docs.google.com/spreadsheets/d/1Aao1CfUR5UO5SOHT-TlSK1Ld_ZeF9lT4n0xOERy9ZuU/edit?gid=17193684#gid=17193684'},
        {'nhom': 'Tồn kho Online', 'ten': '🏭 Tồn Kho TBNT&NB - Chi Tiết Tỉnh & Tổng Kho (Live Sheet)', 'url': 'https://docs.google.com/spreadsheets/d/1Aao1CfUR5UO5SOHT-TlSK1Ld_ZeF9lT4n0xOERy9ZuU/edit?gid=227307726#gid=227307726'},
        {'nhom': 'Tồn kho Cửa hàng', 'ten': '🏪 Tồn Kho TBNT&NB - Chi Tiết Cửa Hàng (Live Sheet)', 'url': 'https://docs.google.com/spreadsheets/d/1Aao1CfUR5UO5SOHT-TlSK1Ld_ZeF9lT4n0xOERy9ZuU/edit?gid=675559613#gid=675559613'},
    ],
    'chi_phi_lap_dat': {
        'so_van_ban': '56/CSNĐ/P.TH&CSKD/25',
        'ngay_ban_hanh': '24/01/2025 (Áp dụng từ 01/02/2025)',
        'pham_vi': 'Từ Quảng Trị trở vào Nam — Áp dụng cho khách hàng lẻ có phát sinh lắp đặt',
        'luu_y': [
            'Chi phí lắp đặt được cộng vào đơn giá bán phát sinh theo từng đơn hàng.',
            'Không bao gồm chi phí vật tư phát sinh như dây điện, công tắc, ổ cắm, ống nước phụ...',
            'Chính sách độc lập với các chương trình khuyến mãi/tờ trình khác đang áp dụng.'
        ],
        'bang_gia': chi_phi_lap_dat
    },
    'chinh_sach_chiet_khau': {
        'cong_trinh': [
            {'hang_muc': 'SPTM thương hiệu Hoa Sen Home (TUSLO, LUSHINE)', 'muc_ck': '10%'},
            {'hang_muc': 'SPTM thương hiệu còn lại (INAX, TOTO, AS, CAESAR...)', 'muc_ck': '20%'},
            {'hang_muc': 'Đơn hàng từ 50tr – dưới 100tr', 'muc_ck': '11.0%'},
            {'hang_muc': 'Đơn hàng từ 100tr – dưới 200tr', 'muc_ck': '11.5%'},
            {'hang_muc': 'Đơn hàng từ 200tr – dưới 500tr', 'muc_ck': '12.0%'},
            {'hang_muc': 'Đơn hàng từ 500tr – dưới 1 tỷ', 'muc_ck': '12.5%'},
            {'hang_muc': 'Đơn hàng từ 1 tỷ – dưới 1.5 tỷ', 'muc_ck': '13.0%'},
            {'hang_muc': 'Đơn hàng từ 1.5 tỷ – dưới 2 tỷ', 'muc_ck': '13.5%'},
            {'hang_muc': 'Đơn hàng từ 2 tỷ trở lên', 'muc_ck': '14.0%'},
        ],
        'khach_le_thau_tho': [
            {'doanh_so': 'Từ 50 triệu – dưới 100 triệu đồng (Chưa VAT)', 'muc_ck': '3%'},
            {'doanh_so': 'Từ 100 triệu – dưới 200 triệu đồng (Chưa VAT)', 'muc_ck': '5%'},
            {'doanh_so': 'Từ 200 triệu – dưới 500 triệu đồng (Chưa VAT)', 'muc_ck': '7%'},
            {'doanh_so': 'Từ 500 triệu đồng trở lên (Chưa VAT)', 'muc_ck': '10%'},
        ],
        'chuyen_nganh_hsh': [
            {'doanh_so_thang': 'Từ 50 triệu – dưới 100 triệu đồng', 'muc_ck': '1.0%'},
            {'doanh_so_thang': 'Từ 100 triệu – dưới 200 triệu đồng', 'muc_ck': '1.5%'},
            {'doanh_so_thang': 'Từ 200 triệu – dưới 500 triệu đồng', 'muc_ck': '2.0%'},
            {'doanh_so_thang': 'Từ 500 triệu – dưới 1,000 triệu đồng', 'muc_ck': '2.5%'},
            {'doanh_so_thang': 'Từ 1,000 triệu đồng trở lên', 'muc_ck': '3.0%'},
        ],
        'nhan_hang_tai_kho': [
            {'dia_diem': 'Nhận hàng tại Cửa hàng', 'muc_ck': '1.0%'},
            {'dia_diem': 'Nhận hàng tại Tổng kho', 'muc_ck': '2.0%'},
        ]
    },
    'bao_hanh_va_khieu_nai': {
        'email_ktcl': 'KTCL_HSHome@hoasengroup.vn',
        'bieu_mau': [
            'KT-TCCL.QT-03.BM01 — Phiếu Tiếp Nhận Khiếu Nại Khách hàng SPTM',
            'KT-TCCL.QT-03.BM02 — Biên bản kiểm tra làm việc'
        ],
        'hang_noi_dia': [
            {'thuong_hieu': 'TOTO', 'hotline': '1800.558.830', 'link': 'https://vn.toto.com/bao-hanh/'},
            {'thuong_hieu': 'INAX', 'hotline': '1800.6633', 'link': 'https://www.inax.com.vn/vi/support/warranty-provisions/'},
            {'thuong_hieu': 'VIGLACERA', 'hotline': '1800.585.805', 'link': 'https://viglacera-sanfi.com/pages/chinh-sach-bao-hanh-doi-tra'},
            {'thuong_hieu': 'KITTO', 'hotline': '02866.881.333', 'link': 'https://kitto.vn/chinh-sach-bao-hanh/'},
        ],
        'bao_hanh_tuslo': [
            {'danh_muc': 'Bồn cầu sứ (Tuslo / Tuslo Pro / Luxury)', 'thoi_gian': '10 năm phần sứ'},
            {'danh_muc': 'Bồn cầu thông minh (Tuslo Luxury)', 'thoi_gian': '2 năm'},
            {'danh_muc': 'Lavabo sứ', 'thoi_gian': '10 năm'},
            {'danh_muc': 'Vòi Lavabo & Sen tắm', 'thoi_gian': '3 năm'},
            {'danh_muc': 'Gương & Giá treo khăn điện', 'thoi_gian': '2 năm'},
            {'danh_muc': 'Phụ kiện thiết bị nhà tắm', 'thoi_gian': '3 năm'},
        ]
    },
    'bang_chuyen_doi_ma': {
        'tuslo_cu_moi': old_to_new_tuslo,
        'nap_bon_cau': nap_bon_cau_map,
        'arrow_trung_anh': arrow_cn_en_map,
        'uu_tien_online': online_priority_list,
        'ngung_nhap_hang': discontinued_list
    },
    'kien_thuc_sp': kien_thuc_sp,
    'xa_kho_2026': xa_kho_items,
    'ra_mat_tuslo': ra_mat_items,
    'pt_ctkm': pt_ctkm_list,
    'danh_sach_cua_hang': danh_sach_cua_hang
}

with open(os.path.join(DATA_DIR, 'products.json'), 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, separators=(',', ':'))

with open(os.path.join(DATA_DIR, 'extras.json'), 'w', encoding='utf-8') as f:
    json.dump(extras, f, ensure_ascii=False, separators=(',', ':'))

print("\n================ HOÀN TẤT ================")
print(f"Tổng số sản phẩm : {len(products):,}")
print(f"Sản phẩm có ảnh  : {extras['thong_ke']['co_hinh_anh']:,}")
print(f"Sản phẩm còn tồn : {extras['thong_ke']['co_ton_kho']:,}")
print(f"Sản phẩm HOT     : {extras['thong_ke']['hang_hot']:,}")
print(f"Cửa hàng HSH     : {len(danh_sach_cua_hang):,}")
import json
import re

with open(r'd:\nhà tắm\app\data\products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

with open(r'd:\nhà tắm\app\data\extras.json', 'r', encoding='utf-8') as f:
    extras = json.load(f)

# Build lookup from kien_thuc_sp in extras
kt_list = extras.get('kien_thuc_sp', [])

def get_default_warranty(brand, group, name):
    b = brand.upper()
    g = group.lower()
    n = name.lower()
    if 'TUSLO' in b or 'LUSHINE' in b:
        if 'thông minh' in g or 'thông minh' in n: return 'Bảo hành 02 năm chính hãng Hoa Sen Home'
        if 'bồn cầu' in g or 'lavabo' in g or 'bồn tiểu' in g: return 'Phần sứ BH 10 năm; Phụ kiện BH 02 năm'
        if 'gương' in g or 'treo khăn điện' in n: return 'Bảo hành 02 năm'
        return 'Bảo hành 03 năm chính hãng Hoa Sen Home'
    if 'INAX' in b or 'TOTO' in b or 'AMERICAN' in b or 'CAESAR' in b or 'ROCA' in b:
        if 'bồn cầu' in g or 'lavabo' in g or 'bồn tiểu' in g: return 'Phần sứ BH 10 năm; Phụ kiện/Nắp BH 01–02 năm'
        if 'sen' in g or 'vòi' in g: return 'Bảo hành 02 năm chính hãng'
        return 'Bảo hành 01–02 năm theo chính sách hãng'
    if 'VIGLACERA' in b:
        if 'bồn cầu' in g or 'lavabo' in g or 'bồn tiểu' in g: return 'Phần sứ BH 10 năm; Phụ kiện BH 30 tháng'
        return 'Bảo hành 02–03 năm chính hãng Viglacera'
    if 'KITTO' in b:
        if 'bồn cầu' in g or 'lavabo' in g: return 'Phần sứ BH 05 năm; Phụ kiện BH 01 năm'
        return 'Bảo hành 02 năm chính hãng Kitto'
    if 'ARROW' in b:
        if 'thông minh' in g or 'thông minh' in n: return 'Bảo hành điện tử 02–03 năm; Phần sứ BH 10 năm'
        if 'bồn cầu' in g or 'lavabo' in g or 'bồn tiểu' in g: return 'Phần sứ BH 10 năm; Phụ kiện BH 02–03 năm'
        return 'Bảo hành 02–03 năm chính hãng Arrow'
    if 'TOÀN MỸ' in b or 'SƠN HÀ' in b:
        return 'Bảo hành chính hãng theo tiêu chuẩn NSX (Inox 304/201)'
    if 'TEKA' in b or 'HAFELE' in b:
        return 'Bảo hành 02 năm chính hãng'
    return 'Bảo hành chính hãng theo quy định NSX'

def get_default_accessories_and_upsell(group, name):
    g = group.lower()
    n = name.lower()
    if 'bồn cầu 1 khối' in g or 'bồn cầu một khối' in n:
        return (
            '*Lưu ý: Linh kiện đi kèm trong thùng thường gồm dây cấp nước, đế thải (con thỏ), van khóa chữ T (tùy hãng).',
            'Vòi xịt vệ sinh (CFV-102A, VG826, COCA001, JPOA024 Pro...)'
        )
    if 'bồn cầu 2 khối' in g or 'bồn cầu hai khối' in n:
        return (
            '*Lưu ý: Linh kiện đi kèm gồm dây cấp nước, gioăng cao su; một số mẫu chưa bao gồm van khóa chữ T.',
            'Van khóa chữ T (COCA004, A-703VR...) & Vòi xịt vệ sinh'
        )
    if 'bồn cầu treo tường' in g:
        return (
            '*Lưu ý: Kiểm tra kỹ sản phẩm đã bao gồm két nước âm tường và mặt nút nhấn xả hay chưa.',
            'Két nước âm tường, mặt nút nhấn xả & Vòi xịt vệ sinh'
        )
    if 'lavabo đặt bàn' in g or 'lavabo âm bàn' in g:
        return (
            '*Lưu ý: Sản phẩm chậu sứ không bao gồm vòi lavabo và bộ xả (siphong/ống thải).',
            'Vòi lavabo cổ cao/cổ thấp & Bộ xả lavabo (xả nhấn/xả lật + ống thải chữ P)'
        )
    if 'lavabo treo tường' in g:
        return (
            '*Lưu ý: Đi kèm pát treo, ốc vít; không bao gồm vòi lavabo, bộ xả (siphong) và chân chậu (nếu mã lẻ).',
            'Chân lavabo, Vòi lavabo & Bộ xả lavabo (siphong)'
        )
    if 'vòi lavabo' in g:
        if 'nóng lạnh' in n:
            return ('*Lưu ý: Đã bao gồm 2 dây cấp nước nóng lạnh; kiểm tra kỹ có kèm trụ xả/họng xả hay chưa.', 'Ống thải chữ P / Bộ xả lavabo')
        return ('*Lưu ý: Vòi lavabo lạnh chưa bao gồm dây cấp nước và bộ xả.', 'Dây cấp nước (COCA005) & Bộ xả lavabo')
    if 'sen cây' in g or 'sen tắm' in g:
        return ('*Lưu ý: Linh kiện đi kèm gồm dây sen, bát sen/tay sen, cặp chân Z, chụp che, ron cao su.', 'Kệ góc / Thanh vắt khăn phòng tắm')
    if 'vòi rửa chén' in g:
        return ('*Lưu ý: Vòi nóng lạnh đã kèm dây cấp; vòi lạnh cần mua thêm dây cấp nước.', 'Dây cấp nước Inox 304 (COCA005) & Chậu rửa chén')
    if 'chậu rửa chén' in g:
        return ('*Lưu ý: Đã bao gồm bộ xi phông / bầu xả thoát nước đi kèm chậu.', 'Vòi rửa chén nóng lạnh / lạnh & Rổ inox gác bồn')
    return ('', '')

dim_regex = re.compile(r'((?:D\s*)?\d{2,4}\s*[xX\*×]\s*(?:R\s*)?\d{2,4}(?:\s*[xX\*×]\s*(?:C\s*)?\d{2,4})?(?:\s*mm)?)')

for p in products:
    # Extract kich_thuoc from ten_sp or thong_tin if empty
    if not p.get('kich_thuoc'):
        m = dim_regex.search(p.get('ten_sp', '')) or dim_regex.search(p.get('thong_tin', ''))
        if m:
            p['kich_thuoc'] = m.group(1).strip()
    # Fill default warranty if empty
    if not p.get('bao_hanh'):
        p['bao_hanh'] = get_default_warranty(p.get('thuong_hieu', ''), p.get('nhom_sp', ''), p.get('ten_sp', ''))
    # Fill default accessories & upsell if empty
    def_khac, def_goi_y = get_default_accessories_and_upsell(p.get('nhom_sp', ''), p.get('ten_sp', ''))
    if not p.get('khac') and def_khac:
        p['khac'] = def_khac
    if not p.get('goi_y_mua_kem') and def_goi_y:
        p['goi_y_mua_kem'] = def_goi_y

with open(r'd:\nhà tắm\app\data\products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, separators=(',', ':'))

print("After enrichment:")
print("  With kich_thuoc:", sum(1 for p in products if p.get('kich_thuoc')))
print("  With bao_hanh:", sum(1 for p in products if p.get('bao_hanh')))
print("  With khac:", sum(1 for p in products if p.get('khac')))
print("  With goi_y_mua_kem:", sum(1 for p in products if p.get('goi_y_mua_kem')))

# ─── Bổ sung dữ liệu nâng cao v4 (Combo, TCG, Top đề xuất, Bảng giá bếp, CTKM) ───
import runpy as _runpy
_runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_extras_v4.py'), run_name='__main__')

# ─── Đọc file PDF Album 2026 và bổ sung ảnh nét, thông số kỹ thuật chi tiết ───
_runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extract_album_pdf.py'), run_name='__main__')
