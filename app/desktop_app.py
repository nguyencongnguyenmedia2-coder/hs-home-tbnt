r"""
Hoa Sen Home Sales Pro — Desktop Application Launcher
Khởi động Server Flask nội bộ và mở giao diện ứng dụng dưới dạng Desktop App độc lập.
"""
import os
import sys
import io
import time
import socket
import threading
import subprocess
import webbrowser
from datetime import datetime

# Đảm bảo mã hóa UTF-8 cho Windows console (hỗ trợ cả chế độ Windowed không có console)
if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
else:
    sys.stdout = io.StringIO()

if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
else:
    sys.stderr = io.StringIO()

# Xác định thư mục gốc của ứng dụng (hỗ trợ cả khi chạy file .py và khi đóng gói .exe qua PyInstaller)
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, '_MEIPASS', EXE_DIR)
else:
    EXE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = EXE_DIR

# Kiểm tra vị trí thư mục app
if os.path.basename(EXE_DIR).lower() == 'app':
    BASE_DIR = os.path.abspath(os.path.join(EXE_DIR, '..'))
    APP_DIR = EXE_DIR
else:
    BASE_DIR = EXE_DIR
    APP_DIR = os.path.join(EXE_DIR, 'app')
    if not os.path.exists(APP_DIR):
        APP_DIR = BUNDLE_DIR

# Thêm APP_DIR vào sys.path để import server
sys.path.insert(0, APP_DIR)
sys.path.insert(0, os.path.join(APP_DIR, 'app'))

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_available_port(start_port=8080):
    for port in range(start_port, start_port + 20):
        if not is_port_in_use(port):
            return port
    return start_port

PORT = find_available_port(8080)

def start_flask_server(port):
    try:
        from server import app
        # Vô hiệu hóa thông báo debug của werkzeug để app chạy êm ái
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        from werkzeug.serving import make_server
        srv = make_server('127.0.0.1', port, app, threaded=True)
        srv.serve_forever()
    except Exception as e:
        print("Lỗi khởi động Flask server:", e)

def wait_for_server(port, timeout=8):
    import urllib.request
    url = f'http://127.0.0.1:{port}/api/system-status'
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False

def open_standalone_browser(url):
    edge_paths = [
        os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%LocalAppData%\Microsoft\Edge\Application\msedge.exe')
    ]
    chrome_paths = [
        os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe')
    ]
    
    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            try:
                return subprocess.Popen([p, f'--app={url}', '--window-size=1440,920'])
            except Exception:
                pass
    webbrowser.open(url)
    return None

def main():
    # 1. Khởi động server nền
    server_thread = threading.Thread(target=start_flask_server, args=(PORT,), daemon=True)
    server_thread.start()

    # 2. Đợi server sẵn sàng
    wait_for_server(PORT)

    app_url = f'http://127.0.0.1:{PORT}/'

    # 3. Thử mở cửa sổ Native Desktop qua pywebview
    webview_success = False
    try:
        import webview
        
        # Cấu hình cửa sổ ứng dụng
        window = webview.create_window(
            title='Hoa Sen Home — Tra Cứu Thiết Bị Nhà Tắm & Nhà Bếp Miền Trung 2026',
            url=app_url,
            width=1440,
            height=920,
            min_size=(1024, 680),
            confirm_close=False,
            easy_drag=False
        )
        
        # Khởi chạy giao diện WebView2 (Chromium engine)
        webview.start(debug=False)
        webview_success = True
    except Exception as e:
        webview_success = False

    # 4. Nếu pywebview không mở được, mở cửa sổ App Mode qua Edge/Chrome
    if not webview_success:
        browser_proc = open_standalone_browser(app_url)
        if browser_proc:
            try:
                browser_proc.wait()
            except Exception:
                while True:
                    time.sleep(2)
        else:
            while True:
                time.sleep(2)

    sys.exit(0)

if __name__ == '__main__':
    main()

