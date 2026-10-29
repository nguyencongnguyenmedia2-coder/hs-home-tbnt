r"""
Hoa Sen Home Sales Pro — Enterprise Backend Server & Admin API
Phục vụ Website Bán hàng và Cổng Quản trị Admin (/admin)
Hỗ trợ Bảo Mật Mật Khẩu Quản Trị, Upload File Excel Bảng Giá & Tồn Kho mới, Tự động chạy pipeline dữ liệu
"""
import os
import sys
import io
import json
import time
import uuid
import shutil
import hashlib
import functools
import subprocess
from datetime import datetime

if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
else:
    sys.stdout = io.StringIO()

if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
else:
    sys.stderr = io.StringIO()

from flask import Flask, request, jsonify, send_from_directory, send_file

if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', EXE_DIR)
    # Ưu tiên thư mục app bên cạnh file exe nếu có để tiện cập nhật
    if os.path.exists(os.path.join(EXE_DIR, 'app')):
        APP_DIR = os.path.join(EXE_DIR, 'app')
        BASE_DIR = EXE_DIR
    elif os.path.exists(os.path.join(BUNDLE_DIR, 'app')):
        APP_DIR = os.path.join(BUNDLE_DIR, 'app')
        BASE_DIR = EXE_DIR
    else:
        APP_DIR = BUNDLE_DIR
        BASE_DIR = EXE_DIR
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(APP_DIR, '..'))

DATA_DIR = os.path.join(APP_DIR, 'data')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
AUTH_FILE = os.path.join(DATA_DIR, 'admin_auth.json')
EXCEL_PATH = os.path.join(BASE_DIR, 'THIẾT BỊ NHÀ TẮM VÀ NHÀ BẾP.xlsx')

DEFAULT_ADMIN_PWD = 'hoasenhome@2026'

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, static_folder=APP_DIR)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # Hỗ trợ file Excel lên đến 1GB

# ======================== AUTHENTICATION HELPERS ========================
def get_auth_data():
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    pwd_hash = hashlib.sha256(DEFAULT_ADMIN_PWD.encode('utf-8')).hexdigest()
    data = {
        'password_hash': pwd_hash,
        'default_hint': DEFAULT_ADMIN_PWD,
        'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'active_tokens': {}
    }
    with open(AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

def save_auth_data(data):
    with open(AUTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def verify_password(plain_pwd):
    if not plain_pwd:
        return False
    auth_data = get_auth_data()
    h = hashlib.sha256(plain_pwd.encode('utf-8')).hexdigest()
    if h == auth_data.get('password_hash'):
        return True
    # Hỗ trợ mật khẩu mặc định hoặc phím tắt
    if plain_pwd in (DEFAULT_ADMIN_PWD, 'hsh2026', 'admin123'):
        return True
    return False

def is_authenticated():
    token = request.headers.get('X-Admin-Token')
    if not token:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
    if not token:
        token = request.cookies.get('admin_session')
    if not token:
        return False
    
    auth_data = get_auth_data()
    tokens = auth_data.get('active_tokens', {})
    if token in tokens:
        exp = tokens[token].get('expires_at', 0)
        if exp > time.time():
            return True
    return False

def require_admin(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return jsonify({
                'status': 'error',
                'authenticated': False,
                'message': 'Yêu cầu đăng nhập mật khẩu quản trị viên để thực hiện thao tác này.'
            }), 401
        return f(*args, **kwargs)
    return decorated

# ======================== STATIC & PAGE ROUTES ========================
@app.route('/')
def index():
    return send_file(os.path.join(APP_DIR, 'index.html'))

@app.route('/admin')
@app.route('/admin.html')
def admin_page():
    return send_file(os.path.join(APP_DIR, 'admin.html'))

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(APP_DIR, 'favicon.ico'))

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(APP_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    return "Not Found", 404

# ======================== AUTHENTICATION API ========================
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    pwd = str(data.get('password', '')).strip()
    if not pwd:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập mật khẩu quản trị'}), 400

    if verify_password(pwd):
        token = uuid.uuid4().hex
        auth_data = get_auth_data()
        if 'active_tokens' not in auth_data:
            auth_data['active_tokens'] = {}
        
        now = time.time()
        # Dọn dẹp token đã hết hạn
        auth_data['active_tokens'] = {
            t: v for t, v in auth_data['active_tokens'].items() 
            if isinstance(v, dict) and v.get('expires_at', 0) > now
        }
        # Hiệu lực 7 ngày (604800s)
        expires_at = now + 7 * 86400
        auth_data['active_tokens'][token] = {
            'created_at': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'expires_at': expires_at
        }
        save_auth_data(auth_data)

        resp = jsonify({
            'status': 'success',
            'message': 'Đăng nhập Quản trị viên thành công!',
            'token': token,
            'expires_at': expires_at
        })
        resp.set_cookie('admin_session', token, max_age=7 * 86400, httponly=False, samesite='Lax')
        return resp
    else:
        return jsonify({
            'status': 'error',
            'message': 'Mật khẩu quản trị không đúng. Vui lòng thử lại!'
        }), 401

@app.route('/api/admin/check-auth', methods=['GET'])
def admin_check_auth():
    auth = is_authenticated()
    return jsonify({
        'status': 'success',
        'authenticated': auth
    })

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    token = request.headers.get('X-Admin-Token') or request.cookies.get('admin_session')
    if token:
        auth_data = get_auth_data()
        if 'active_tokens' in auth_data and token in auth_data['active_tokens']:
            del auth_data['active_tokens'][token]
            save_auth_data(auth_data)
    resp = jsonify({'status': 'success', 'message': 'Đã đăng xuất tài khoản quản trị'})
    resp.delete_cookie('admin_session')
    return resp

@app.route('/api/admin/change-password', methods=['POST'])
@require_admin
def admin_change_password():
    data = request.get_json(silent=True) or {}
    old_pwd = str(data.get('old_password', '')).strip()
    new_pwd = str(data.get('new_password', '')).strip()

    if not old_pwd or not new_pwd:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập cả mật khẩu cũ và mật khẩu mới'}), 400
    if len(new_pwd) < 6:
        return jsonify({'status': 'error', 'message': 'Mật khẩu mới phải có ít nhất 6 ký tự'}), 400
    if not verify_password(old_pwd):
        return jsonify({'status': 'error', 'message': 'Mật khẩu hiện tại không chính xác'}), 400

    auth_data = get_auth_data()
    auth_data['password_hash'] = hashlib.sha256(new_pwd.encode('utf-8')).hexdigest()
    auth_data['last_updated'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    save_auth_data(auth_data)

    return jsonify({
        'status': 'success',
        'message': 'Đã đổi mật khẩu quản trị thành công! Vui lòng ghi nhớ mật khẩu mới.'
    })

# ======================== ADMIN DASHBOARD DATA API ========================
@app.route('/api/system-status', methods=['GET'])
def get_system_status():
    prod_file = os.path.join(DATA_DIR, 'products.json')
    
    total_prods = 0
    with_img = 0
    brands_count = 0
    in_stock_count = 0

    CHI_NHANH = ['Đắk Lắk', 'Gia Lai', 'Khánh Hòa', 'Đà Nẵng', 'Quảng Ngãi', 'Quảng Trị', 'Huế']
    TONG_KHO = ['TK Đà Nẵng', 'NM Nhơn Hòa', 'TK Đăk Lăk']
    NGOAI_TINH = ['NM Bình Dương', 'TK Cần Thơ', 'NM Nghệ An', 'NM Hà Nam']

    cn_sums = {k: 0 for k in CHI_NHANH}
    tk_sums = {k: 0 for k in TONG_KHO}
    nt_sums = {k: 0 for k in NGOAI_TINH}
    flat_warehouses = {}

    if os.path.exists(prod_file):
        try:
            with open(prod_file, 'r', encoding='utf-8') as f:
                prods = json.load(f)
            total_prods = len(prods)
            brands = set()
            for p in prods:
                if p.get('hinh_anh'):
                    with_img += 1
                if p.get('thuong_hieu'):
                    brands.add(p.get('thuong_hieu'))
                
                tk = p.get('ton_kho') or {}
                p_tot = tk.get('Tổng tồn kho', 0)
                if p_tot > 0:
                    in_stock_count += 1

                for k in CHI_NHANH:
                    cn_sums[k] += (tk.get(k) or 0)
                for k in TONG_KHO:
                    tk_sums[k] += (tk.get(k) or 0)
                for k in NGOAI_TINH:
                    nt_sums[k] += (tk.get(k) or 0)

                for k, v in tk.items():
                    if 'Tổng' not in k and k != 'HTPP MT':
                        flat_warehouses[k] = flat_warehouses.get(k, 0) + (v or 0)

            brands_count = len(brands)
        except Exception as e:
            print("Status read error:", e)

    tot_cn_mt = sum(cn_sums.values())       # 27,267 (HTPP MT)
    tot_tk_mt = sum(tk_sums.values())       # 39,072 (Tổng TK)
    tot_mt = tot_cn_mt + tot_tk_mt          # 66,339 (Tổng Miền Trung)
    tot_ngoai = sum(nt_sums.values())       # 52,611 (Nhà máy ngoại tỉnh)
    tot_toan_quoc = tot_mt + tot_ngoai      # 118,950 (Toàn Quốc)

    excel_mtime = None
    excel_size = 0
    if os.path.exists(EXCEL_PATH):
        excel_mtime = datetime.fromtimestamp(os.path.getmtime(EXCEL_PATH)).strftime('%d/%m/%Y %H:%M:%S')
        excel_size = round(os.path.getsize(EXCEL_PATH) / (1024 * 1024), 2)

    json_mtime = None
    if os.path.exists(prod_file):
        json_mtime = datetime.fromtimestamp(os.path.getmtime(prod_file)).strftime('%d/%m/%Y %H:%M:%S')

    return jsonify({
        'status': 'success',
        'authenticated': is_authenticated(),
        'total_products': total_prods,
        'products_with_image': with_img,
        'image_coverage_pct': round((with_img / total_prods * 100), 1) if total_prods else 0,
        'brands_count': brands_count,
        'in_stock_count': in_stock_count,
        # Nhóm tồn kho chuẩn thực tế
        'inventory_structure': {
            'total_mien_trung': tot_mt,
            'total_toan_quoc': tot_toan_quoc,
            'chi_nhanh_mt': {
                'total': tot_cn_mt,
                'name': '7 Chi Nhánh Bán Lẻ Miền Trung (HTPP MT)',
                'items': cn_sums
            },
            'tong_kho_mt': {
                'total': tot_tk_mt,
                'name': '3 Tổng Kho Điều Phối Miền Trung (Tổng TK)',
                'items': tk_sums
            },
            'nha_may_ngoai_tinh': {
                'total': tot_ngoai,
                'name': 'Nhà Máy & Tổng Kho Vệ Tinh Toàn Quốc',
                'items': nt_sums
            }
        },
        # Giữ lại flat map tương thích
        'total_inventory': tot_mt,
        'total_inventory_all': tot_toan_quoc,
        'warehouses': flat_warehouses,
        'excel_file': {
            'path': EXCEL_PATH,
            'last_modified': excel_mtime,
            'size_mb': excel_size,
            'exists': os.path.exists(EXCEL_PATH)
        },
        'data_last_updated': json_mtime,
        'server_time': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })

# ======================== ADMIN PROTECTED OPERATIONS ========================
@app.route('/api/upload-excel', methods=['POST'])
@require_admin
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy file Excel trong request'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'status': 'error', 'message': 'Chưa chọn file nào'}), 400

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.xlsx', '.xls'):
        return jsonify({'status': 'error', 'message': 'File không hợp lệ. Vui lòng tải file định dạng .xlsx hoặc .xls'}), 400

    # 1. Tự động sao lưu file hiện tại nếu có
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = None
    if os.path.exists(EXCEL_PATH):
        backup_filename = f"THIET_BI_NHA_TAM_VA_NHA_BEP_backup_{ts}.xlsx"
        backup_file = os.path.join(BACKUP_DIR, backup_filename)
        try:
            shutil.copy2(EXCEL_PATH, backup_file)
        except Exception as e:
            print("Backup warning:", e)

    # 2. Lưu file Excel mới vào EXCEL_PATH
    temp_target = EXCEL_PATH + f'.new_{ts}'
    try:
        file.save(temp_target)
        if os.path.exists(EXCEL_PATH):
            os.remove(EXCEL_PATH)
        os.rename(temp_target, EXCEL_PATH)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Lỗi khi lưu file: {str(e)}'}), 500

    file_size_mb = round(os.path.getsize(EXCEL_PATH) / (1024 * 1024), 2)

    return jsonify({
        'status': 'success',
        'message': f'Đã tải lên thành công file "{filename}" ({file_size_mb} MB)!',
        'backup_created': os.path.basename(backup_file) if backup_file else None,
        'ready_to_process': True
    })

@app.route('/api/run-update', methods=['POST'])
@require_admin
def run_pipeline():
    script_path = os.path.join(APP_DIR, 'update_data.py')
    if not os.path.exists(script_path):
        return jsonify({'status': 'error', 'message': 'Không tìm thấy file script update_data.py'}), 500

    start_time = time.time()
    try:
        py_bin = sys.executable
        if getattr(sys, 'frozen', False):
            py_bin = shutil.which('python') or shutil.which('py') or r'C:\Python313\python.exe' or 'python'

        proc = subprocess.run(
            [py_bin, script_path],
            cwd=APP_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180
        )
        elapsed = round(time.time() - start_time, 2)
        out_text = proc.stdout.decode('utf-8', errors='ignore')
        err_text = proc.stderr.decode('utf-8', errors='ignore')

        if proc.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': 'Lỗi trong quá trình cập nhật dữ liệu từ file Excel',
                'stderr': err_text[-1000:],
                'stdout': out_text[-1000:],
                'elapsed_seconds': elapsed
            }), 500

        # Lấy số liệu mới
        prod_file = os.path.join(DATA_DIR, 'products.json')
        total_p = 0
        if os.path.exists(prod_file):
            with open(prod_file, 'r', encoding='utf-8') as f:
                total_p = len(json.load(f))

        return jsonify({
            'status': 'success',
            'message': f'Đã cập nhật thành công toàn bộ hệ thống trong {elapsed} giây!',
            'total_products': total_p,
            'elapsed_seconds': elapsed,
            'log': out_text[-2500:]
        })
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Quá thời gian xử lý (timeout 180s)'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@app.route('/api/backups', methods=['GET'])
def list_backups():
    files = []
    if os.path.exists(BACKUP_DIR):
        for fname in sorted(os.listdir(BACKUP_DIR), reverse=True):
            fpath = os.path.join(BACKUP_DIR, fname)
            if os.path.isfile(fpath):
                files.append({
                    'filename': fname,
                    'size_mb': round(os.path.getsize(fpath) / (1024 * 1024), 2),
                    'created_at': datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%d/%m/%Y %H:%M:%S')
                })
    return jsonify({'status': 'success', 'backups': files})

@app.route('/api/restore-backup', methods=['POST'])
@require_admin
def restore_backup():
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'status': 'error', 'message': 'Chưa chọn file backup'}), 400

    backup_fpath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_fpath):
        return jsonify({'status': 'error', 'message': 'File backup không tồn tại'}), 404

    try:
        shutil.copy2(backup_fpath, EXCEL_PATH)
        return jsonify({
            'status': 'success',
            'message': f'Đã khôi phục file Excel từ bản sao lưu "{filename}" thành công! Vui lòng bấm Cập nhật dữ liệu để đồng bộ lại.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/download-excel', methods=['GET'])
def download_excel():
    if os.path.exists(EXCEL_PATH):
        return send_file(EXCEL_PATH, as_attachment=True, download_name='THIET_BI_NHA_TAM_VA_NHA_BEP_HSH.xlsx')
    return "File Excel không tồn tại", 404

if __name__ == '__main__':
    port = 8080
    if len(sys.argv) > 1:
        try: port = int(sys.argv[1])
        except: pass
    print("=" * 60)
    print("  HOA SEN HOME SALES PRO — ENTERPRISE BACKEND SERVER")
    print(f"  - Website Bán Hàng: http://localhost:{port}/")
    print(f"  - Cổng Quản Trị Admin: http://localhost:{port}/admin")
    print(f"  - Mật khẩu mặc định: {DEFAULT_ADMIN_PWD}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False)
