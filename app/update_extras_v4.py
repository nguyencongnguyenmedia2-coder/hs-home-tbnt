r"""
update_extras_v4.py
Bổ sung dữ liệu nâng cao vào d:\nhà tắm\app\data\extras.json (và ảnh vào products.json):
  - Combo bán hàng soạn sẵn (COMBO DUY, Combo, Thư chào giá)
  - Thư chào giá bồn cầu thông minh TOTO / INAX (TCG) kèm hình ảnh
  - Top 10 SKU đề xuất (ĐỀ XUẤT) kèm hình ảnh
  - Bảng giá thương hiệu bếp: TEKA, HAFELE, TOÀN MỸ, Chậu rửa INOX theo khu vực
  - Ma trận chiết khấu theo nhóm khách, danh sách CTKM đang chạy,
    chiết khấu trả sau / tháng / quý (sheet "Thư viện có gì")
Chạy sau update_data.py (được gọi tự động ở cuối update_data.py).
"""
import os, sys, io, json, re, zipfile
import xml.etree.ElementTree as ET
from PIL import Image
import openpyxl

if hasattr(sys.stdout, 'buffer') and (sys.stdout.encoding or '').lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

XLSX_PATH = r'd:\nhà tắm\THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP.xlsx'
APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(APP_DIR, 'images', 'products')
DATA_DIR = os.path.join(APP_DIR, 'data')
os.makedirs(IMG_DIR, exist_ok=True)

NS = {'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'}
R_EMBED = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'


def s(v):
    if v is None: return ''
    t = str(v).strip()
    return '' if t in ('None', '#N/A', '#REF!', '#VALUE!', '#DIV/0!', 'nan') else t


def n(v):
    try:
        t = s(v).replace(',', '')
        return float(t) if t else 0.0
    except ValueError:
        return 0.0


def norm(code):
    return re.sub(r'\s+', '', s(code).upper())


def cell(row, col):
    """col: 1-based"""
    return row[col - 1] if len(row) >= col else None


# ─── Load ───
with open(os.path.join(DATA_DIR, 'products.json'), encoding='utf-8') as f:
    products = json.load(f)
with open(os.path.join(DATA_DIR, 'extras.json'), encoding='utf-8') as f:
    extras = json.load(f)

by_sp, by_item = {}, {}
for p in products:
    if p.get('ma_sp'): by_sp.setdefault(norm(p['ma_sp']), p)
    if p.get('ma_item'): by_item.setdefault(norm(p['ma_item']), p)


def find_product(ma_sp='', ma_item=''):
    k = norm(ma_sp)
    if k and k in by_sp: return by_sp[k]
    k2 = norm(ma_item)
    if k2 and k2 in by_item: return by_item[k2]
    if k and '/' in k:
        pre = k.split('/')[0]
        if len(pre) >= 5:
            for kk, p in by_sp.items():
                if kk == pre or kk.startswith(pre + '/'):
                    return p
    return None


zf = zipfile.ZipFile(XLSX_PATH)
_media_cache = {}


def drawing_anchors(num):
    """{row: [(col, media_path)]}"""
    dpath = f'xl/drawings/drawing{num}.xml'
    rpath = f'xl/drawings/_rels/drawing{num}.xml.rels'
    if dpath not in zf.namelist() or rpath not in zf.namelist():
        return {}
    rid = {r.attrib['Id']: r.attrib['Target'].replace('../', 'xl/')
           for r in ET.fromstring(zf.read(rpath)).findall('rel:Relationship', NS)}
    out = {}
    root = ET.fromstring(zf.read(dpath))
    for tag in ('twoCellAnchor', 'oneCellAnchor'):
        for a in root.findall(f'xdr:{tag}', NS):
            fr = a.find('xdr:from', NS)
            b = a.find('.//a:blip', NS)
            if fr is None or b is None: continue
            m = rid.get(b.attrib.get(R_EMBED))
            if not m: continue
            r = int(fr.find('xdr:row', NS).text) + 1
            c = int(fr.find('xdr:col', NS).text) + 1
            out.setdefault(r, []).append((c, m))
    return out


def export_media(media_path):
    """Giải nén + tối ưu 1 ảnh -> đường dẫn web"""
    if not media_path: return ''
    if media_path in _media_cache: return _media_cache[media_path]
    if media_path not in zf.namelist(): return ''
    base = os.path.splitext(os.path.basename(media_path))[0]
    out = os.path.join(IMG_DIR, base + '.webp')
    web = f'images/products/{base}.webp'
    if not os.path.exists(out):
        try:
            img = Image.open(io.BytesIO(zf.read(media_path)))
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
            img.thumbnail((600, 600), Image.Resampling.LANCZOS)
            img.save(out, 'WEBP', quality=84, method=4)
        except Exception as e:
            print(f'  ! Lỗi ảnh {media_path}: {e}')
            web = ''
    _media_cache[media_path] = web
    return web


def image_in_row(anchors, row, col_min=1, col_max=20):
    for c, m in sorted(anchors.get(row, [])):
        if col_min <= c <= col_max:
            return export_media(m)
    return ''


img_added = 0


def give_image(p, web):
    """Gán ảnh cho sản phẩm nếu sản phẩm chưa có ảnh"""
    global img_added
    if p is not None and web and not p.get('hinh_anh'):
        p['hinh_anh'] = web
        img_added += 1


print('📦 Đọc workbook...')
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)


def rows_of(name, max_row=None):
    return list(wb[name].iter_rows(max_row=max_row, values_only=True))


# ═══════════════════════════════════════════════════════════════
# 1. COMBO BÁN HÀNG SOẠN SẴN
# ═══════════════════════════════════════════════════════════════
print('1. Trích xuất Combo soạn sẵn...')
# Cấu hình cột (1-based) cho từng mẫu sheet
COMBO_LAYOUTS = {
    'COMBO DUY':    dict(stt=3, brand=4, loai=5, ma=6, ten=7, dvt=9, ny=10, sl=11, gia=12, muc=18, note=17),
    'Combo':        dict(stt=3, brand=4, loai=5, ma=6, ten=7, dvt=9, ny=10, sl=11, tt=12, muc=13),
    'Thư chào giá': dict(stt=2, brand=3, loai=4, ma=5, ten=6, dvt=8, ny=9, sl=10, gia=11, muc=12),
}
COMBO_MO_TA = {
    'COMBO TBNT - NB ARROW TRUNG CAO': 'Trọn bộ nhà tắm ARROW phân khúc trung cao cấp (bồn cầu 1 khối, tủ lavabo, tủ gương, sen cây). Khách sỉ được chiết khấu combo 20%–25%.',
    'COMBO TBNT - NB': 'Trọn bộ nhà tắm + nhà bếp thương hiệu Hoa Sen Home (TUSLO + LUSHINE) — tặng kèm van T & dây cấp khi mua bồn cầu.',
    'THAM KHẢO COMBO 2': 'Combo kết hợp ARROW + TUSLO: bồn cầu ARROW ưu đãi 10% + tặng van T & dây cấp TUSLO.',
    '"MUA 1 TẶNG 1 - COMBO THIẾT BỊ NHÀ BẾP"': 'Mua bộ chậu rửa chén inox 304 LUSHINE EAOD002 — TẶNG vòi bếp nóng lạnh TUSLO ARRK003 Luxury.',
}

combos = []
for sheet, L in COMBO_LAYOUTS.items():
    rows = rows_of(sheet, 80)
    cur = None

    def flush():
        if cur and cur['items']:
            combos.append(cur)

    for r_idx, row in enumerate(rows, 1):
        stt_raw = s(cell(row, L['stt']))
        ma = s(cell(row, L['ma']))
        ten = s(cell(row, L['ten']))
        stt_is_num = bool(re.fullmatch(r'\d+(\.0)?', stt_raw))
        if stt_is_num and ma and ten:
            if cur is None:
                continue
            marker = s(cell(row, 1)).lower()
            ny = n(cell(row, L['ny']))
            sl = max(1, int(n(cell(row, L['sl'])) or 1))
            muc = n(cell(row, L['muc'])) if L.get('muc') else 0
            note = s(cell(row, L['note'])) if L.get('note') else ''
            p = find_product(ma)
            if not ny and p:
                ny = p.get('gia_niem_yet', 0)
            if 'gia' in L:
                gia = n(cell(row, L['gia']))
            else:
                gia = n(cell(row, L['tt'])) / sl if n(cell(row, L['tt'])) else 0
            tang = marker == 't' or note.lower() == 'tặng' or (muc == 1 and ny > 0)
            if tang:
                gia = 0
            elif not gia:
                gia = ny * (1 - muc) if muc < 1 else ny
            cur['items'].append({
                'ma_sp': ma, 'ten_sp': ten, 'thuong_hieu': s(cell(row, L['brand'])),
                'loai': s(cell(row, L['loai'])), 'dvt': s(cell(row, L['dvt'])),
                'so_luong': sl, 'gia_niem_yet': round(ny), 'gia_combo': round(gia),
                'tang': tang, 'id': p['id'] if p else None,
                'hinh_anh': (p or {}).get('hinh_anh', ''),
            })
            continue
        # Dòng tiêu đề combo: chữ trong cột STT, không phải header/ghi chú
        title = stt_raw.replace('\n', ' ').strip()
        low = title.lower()
        if title and not stt_is_num and 'combo' in low and not low.startswith('*'):
            flush()
            cur = {'ten_combo': title, 'nguon': sheet, 'items': []}
    flush()

# Bổ sung ảnh, tổng tiền, loại trùng (theo tập mã sản phẩm)
uniq, seen = [], set()
for c in combos:
    key = tuple(sorted(i['ma_sp'] for i in c['items']))
    if key in seen: continue
    seen.add(key)
    c['tong_niem_yet'] = sum(i['gia_niem_yet'] * i['so_luong'] for i in c['items'])
    c['tong_combo'] = sum(i['gia_combo'] * i['so_luong'] for i in c['items'])
    c['tiet_kiem'] = max(0, c['tong_niem_yet'] - c['tong_combo'])
    c['mo_ta'] = next((v for k, v in COMBO_MO_TA.items() if c['ten_combo'].upper().startswith(k.upper())), '')
    uniq.append(c)
# Đặt tên rõ ràng hơn cho các combo
for c in uniq:
    if c['ten_combo'].strip() == 'COMBO TBNT - NB':
        c['ten_combo'] = 'COMBO TBNT - NB TUSLO & LUSHINE TRỌN BỘ'
    if c['ten_combo'].strip().upper().startswith('COMBO 5 - THIẾT BỊ NHÀ BẾP'):
        c['ten_combo'] = 'MUA 1 TẶNG 1 - COMBO THIẾT BỊ NHÀ BẾP'
        c['mo_ta'] = COMBO_MO_TA['"MUA 1 TẶNG 1 - COMBO THIẾT BỊ NHÀ BẾP"']
    if 'ĐẠI LÝ 307' in c['ten_combo'].upper() and not c['mo_ta']:
        c['mo_ta'] = 'Combo trọn bộ nhà tắm & nhà bếp TUSLO + LUSHINE giá đại lý (ưu đãi 20%–30%, tặng van T, dây cấp, gương).'
    c['ten_combo'] = c['ten_combo'].strip('" ')
combos = uniq
print(f'   → {len(combos)} combo: ' + ' | '.join(f"{c['ten_combo']} ({len(c['items'])} SP)" for c in combos))

# ═══════════════════════════════════════════════════════════════
# 2. TCG – BỒN CẦU THÔNG MINH TOTO / INAX (có hình ảnh)
# ═══════════════════════════════════════════════════════════════
print('2. Trích xuất Thư chào giá bồn cầu thông minh (TCG)...')
anc = drawing_anchors(50)
tcg = []
for r_idx, row in enumerate(rows_of('TCG', 60), 1):
    ma = s(cell(row, 6)); ten = s(cell(row, 7))
    if not re.fullmatch(r'\d+(\.0)?', s(cell(row, 3))) or not ma or not ten:
        continue
    web = image_in_row(anc, r_idx, 7, 9)
    p = find_product(ma)
    give_image(p, web)
    tcg.append({
        'thuong_hieu': s(cell(row, 4)), 'loai': s(cell(row, 5)), 'ma_sp': ma, 'ten_sp': ten,
        'dvt': s(cell(row, 9)), 'gia_niem_yet': round(n(cell(row, 10))),
        'gia_ban': round(n(cell(row, 11))), 'chiet_khau': n(cell(row, 13)),
        'hinh_anh': web or (p or {}).get('hinh_anh', ''), 'id': p['id'] if p else None,
    })
tcg_ghi_chu = []
for row in rows_of('TCG', 45)[33:]:
    t = s(cell(row, 4))
    if t: tcg_ghi_chu.append(t)
print(f'   → {len(tcg)} mẫu, {sum(1 for x in tcg if x["hinh_anh"])} có ảnh')

# ═══════════════════════════════════════════════════════════════
# 3. TOP 10 SKU ĐỀ XUẤT
# ═══════════════════════════════════════════════════════════════
print('3. Trích xuất Top 10 SKU đề xuất...')
anc = drawing_anchors(52)
de_xuat = []
for r_idx, row in enumerate(rows_of('ĐỀ XUẤT', 20), 1):
    ma = s(cell(row, 4))
    if not re.fullmatch(r'\d+', s(cell(row, 2))) or not ma: continue
    web = image_in_row(anc, r_idx, 4, 6)
    p = find_product(ma)
    give_image(p, web)
    de_xuat.append({
        'phan_loai': s(cell(row, 3)), 'ma_sp': ma, 'gia_niem_yet': round(n(cell(row, 6))),
        'ton_kho': {'TK Đăk Lăk': int(n(cell(row, 7))), 'NM Nhơn Hòa': int(n(cell(row, 8))), 'TK Đà Nẵng': int(n(cell(row, 9)))},
        'ten_sp': (p or {}).get('ten_sp', ma), 'hinh_anh': web or (p or {}).get('hinh_anh', ''),
        'id': p['id'] if p else None,
    })
print(f'   → {len(de_xuat)} SKU')

# ═══════════════════════════════════════════════════════════════
# 4. BẢNG GIÁ THƯƠNG HIỆU BẾP: TEKA / HAFELE / TOÀN MỸ / INOX
# ═══════════════════════════════════════════════════════════════
print('4. Trích xuất bảng giá TEKA / HAFELE / TOÀN MỸ / Chậu INOX...')
anc = drawing_anchors(19)
teka = []
for r_idx, row in enumerate(rows_of('TEKA', 40), 1):
    item = s(cell(row, 3)); ten = s(cell(row, 4))
    if not re.match(r'^[A-Z]\d{6,}', item) or not ten: continue
    web = image_in_row(anc, r_idx, 4, 6)
    p = find_product('', item)
    give_image(p, web)
    teka.append({'ma_item': item, 'ten_sp': ten, 'gia_niem_yet': round(n(cell(row, 6))),
                 'gia_uu_dai': round(n(cell(row, 7))), 'muc_uu_dai': n(cell(row, 8)),
                 'gia_dm_cho_lon': round(n(cell(row, 9))),
                 'ton_kho': {'Đắk Lắk': int(n(cell(row, 11))), 'Gia Lai': int(n(cell(row, 12))),
                             'Quảng Ngãi': int(n(cell(row, 13))), 'Đà Nẵng': int(n(cell(row, 14)))},
                 'hinh_anh': web or (p or {}).get('hinh_anh', ''), 'id': p['id'] if p else None})

hafele = []
for row in rows_of('HAFELE', 30):
    item = s(cell(row, 6)); ten = s(cell(row, 7))
    if not re.match(r'^[A-Z]\d{6,}', item): continue
    ny = n(cell(row, 10))
    p = find_product(s(cell(row, 5)), item)
    hafele.append({'phan_loai': s(cell(row, 3)), 'ma_sp': s(cell(row, 5)), 'ma_item': item, 'ten_sp': ten,
                   'dvt': s(cell(row, 9)), 'gia_niem_yet': round(ny),
                   'gia_ck10': round(ny * 0.9), 'gia_ck15': round(ny * 0.85), 'gia_ck20': round(ny * 0.8),
                   'hinh_anh': (p or {}).get('hinh_anh', ''), 'id': p['id'] if p else None})

anc = drawing_anchors(24)
toan_my = []
for r_idx, row in enumerate(rows_of('TOÀN MỸ', 30), 1):
    item = s(cell(row, 6)); ten = s(cell(row, 7))
    if not re.match(r'^[A-Z]\d{6,}', item): continue
    ny = n(cell(row, 10))
    web = image_in_row(anc, r_idx, 7, 9)
    p = find_product('', item)
    give_image(p, web)
    toan_my.append({'quy_cach': s(cell(row, 5)), 'ma_item': item, 'ten_sp': ten, 'dvt': s(cell(row, 9)),
                    'gia_niem_yet': round(ny), 'gia_ck10': round(ny * 0.9), 'gia_ck15': round(ny * 0.85),
                    'gia_ck20': round(ny * 0.8), 'hinh_anh': web or (p or {}).get('hinh_anh', ''),
                    'id': p['id'] if p else None})

inox_kv = []
cur = None
for row in rows_of('BG CHẬU RỬA INOX', 200):
    hdr = s(cell(row, 4))
    if hdr.upper().startswith('INOX') and 'ÁP DỤNG' in hdr.upper():
        cur = {'khu_vuc': hdr, 'ck_le': n(cell(row, 9)), 'ck_si': n(cell(row, 10)), 'items': []}
        inox_kv.append(cur)
        continue
    if cur is not None and re.fullmatch(r'\d+(\.0)?', s(cell(row, 2))) and hdr:
        item = s(cell(row, 3))
        p = find_product('', item) if item else None
        cur['items'].append({'ma_item': item, 'ten_sp': hdr, 'dvt': s(cell(row, 5)),
                             'ny_chua_vat': round(n(cell(row, 7))), 'ny_co_vat': round(n(cell(row, 8))),
                             'gia_le': round(n(cell(row, 9))), 'gia_si': round(n(cell(row, 10))),
                             'hinh_anh': (p or {}).get('hinh_anh', ''), 'id': p['id'] if p else None})
bg_inox_info = ''
for row in rows_of('BG CHẬU RỬA INOX', 6):
    t = s(cell(row, 2)) + ' ' + s(cell(row, 4))
    if 'Khu vực' in t or 'Số:' in t: bg_inox_info = t.strip()
print(f'   → TEKA {len(teka)} | HAFELE {len(hafele)} | TOÀN MỸ {len(toan_my)} | INOX {len(inox_kv)} khu vực')

# ═══════════════════════════════════════════════════════════════
# 5. CHÍNH SÁCH & CTKM (sheet "Thư viện có gì")
# ═══════════════════════════════════════════════════════════════
print('5. Trích xuất Chính sách kinh doanh & CTKM đang chạy...')
tv = rows_of('Thư viện có gì', 140)


def pct(v):
    t = s(v)
    if not t: return ''
    if t.upper() == 'X': return 'Không áp dụng'
    if t.endswith('%'): return t
    try:
        f = float(t)
        return f'{f * 100:g}%' if f <= 1 else t
    except ValueError:
        return t.replace('\n', ' ').strip()


ma_tran_ck = [
    {'loai_hang': 'Sản phẩm Hoa Sen Home (TUSLO, LUSHINE)', 'vang_lai': 'Giá niêm yết',
     'thau_tho': pct(cell(tv[16], 6)), 'si_thuong_mai': pct(cell(tv[16], 7)), 'ban_mau': pct(cell(tv[16], 8))},
    {'loai_hang': 'Sản phẩm thương mại (INAX, TOTO, AS, ARROW, CAESAR, Tân An Vinh, Hùng Anh...)',
     'vang_lai': pct(cell(tv[19], 5)), 'thau_tho': pct(cell(tv[19], 6)),
     'si_thuong_mai': pct(cell(tv[19], 7)), 'ban_mau': pct(cell(tv[19], 8))},
]

ctkm = []
r = 31
while r < 48:
    row = tv[r]
    title = s(cell(row, 5)) or s(cell(row, 3))
    if title and (title.startswith('"') or title.startswith('“') or title.isupper()):
        han = cell(row, 8)
        han_s = han.strftime('%d/%m/%Y') if hasattr(han, 'strftime') else s(han).replace('\n', ' ')
        loai = s(cell(row, 3)) if s(cell(row, 5)) else ''
        nd = s(cell(tv[r + 1], 5)) or s(cell(tv[r + 1], 3))
        ctkm.append({'ten': title.strip('"“” '), 'loai_hang': loai.replace('\n', ' '),
                     'noi_dung': nd, 'thoi_han': han_s})
        r += 2
    else:
        r += 1


def tiers(r0, r1, cols):
    out = []
    for row in tv[r0 - 1:r1]:
        if not re.fullmatch(r'\d+(\.0)?', s(cell(row, 2))): continue
        d = {'khung': s(cell(row, 3)).replace('\n', ' ')}
        for k, c in cols.items():
            d[k] = pct(cell(row, c))
        out.append(d)
    return out


ck_tra_sau = tiers(52, 59, {'ck_thang': 4, 'ck_quy': 5, 'ck_chuyen_nganh': 6, 'ck_dinh_muc': 7, 'tong': 8})
ck_thang = tiers(63, 69, {'muc_ck': 5})
ck_quy = tiers(75, 81, {'muc_ck': 5})
lich_can_tru_quy = [{'quy': s(cell(row, 2)).replace('.0', ''), 'thoi_gian': s(cell(row, 3)), 'can_tru': s(cell(row, 5))}
                    for row in tv[82:86] if s(cell(row, 3))]
print(f'   → {len(ctkm)} CTKM | trả sau {len(ck_tra_sau)} | tháng {len(ck_thang)} | quý {len(ck_quy)}')

# ═══════════════════════════════════════════════════════════════
# 6. Cập nhật lại ảnh combo sau khi gán ảnh mới & lưu
# ═══════════════════════════════════════════════════════════════
for c in combos:
    for i in c['items']:
        if not i['hinh_anh'] and i['id']:
            p = next((x for x in products if x['id'] == i['id']), None)
            i['hinh_anh'] = (p or {}).get('hinh_anh', '')

extras['combo_ban_hang'] = combos
extras['tcg_thong_minh'] = {'items': tcg, 'ghi_chu': tcg_ghi_chu}
extras['top_de_xuat'] = de_xuat
extras['bang_gia_bep'] = {'teka': teka, 'hafele': hafele, 'toan_my': toan_my,
                          'inox_khu_vuc': inox_kv, 'inox_info': bg_inox_info}
extras['chinh_sach_kinh_doanh'] = {
    'ma_tran_ck': ma_tran_ck, 'ctkm_dang_chay': ctkm, 'ck_tra_sau': ck_tra_sau,
    'ck_thang': ck_thang, 'ck_quy': ck_quy, 'lich_can_tru_quy': lich_can_tru_quy,
}
extras.setdefault('thong_ke', {})['co_hinh_anh'] = sum(1 for p in products if p.get('hinh_anh'))

with open(os.path.join(DATA_DIR, 'products.json'), 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'extras.json'), 'w', encoding='utf-8') as f:
    json.dump(extras, f, ensure_ascii=False, separators=(',', ':'))

print(f'\n✅ Hoàn tất v4: +{img_added} ảnh mới cho sản phẩm | Tổng SP có ảnh: {extras["thong_ke"]["co_hinh_anh"]:,}/{len(products):,}')
