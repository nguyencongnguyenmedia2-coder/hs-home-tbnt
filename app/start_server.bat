@echo off
chcp 65001 >nul
echo.
echo =========================================
echo   HSH Tra Cuu San Pham - Local Server
echo =========================================
echo.
echo [1] Dang kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Khong tim thay Python. Thu Node.js...
    node --version >nul 2>&1
    if errorlevel 1 (
        echo [!] Khong tim thay Node.js. Vui long cai dat Python hoac Node.js.
        pause
        exit /b 1
    )
    echo [OK] Da tim thay Node.js
    echo [2] Khoi dong server tai http://localhost:8080
    echo.
    echo   Nhan Ctrl+C de dung server
    echo.
    start "" "http://localhost:8080"
    npx serve . -p 8080 -s
) else (
    echo [OK] Da tim thay Python
    echo [2] Khoi dong Enterprise Server tai:
    echo     - Trang Ban Hang: http://localhost:8080
    echo     - Trang Quan Tri: http://localhost:8080/admin
    echo     - Mat khau Quan Tri Admin: hoasenhome@2026
    echo.
    echo   Nhan Ctrl+C de dung server
    echo.
    timeout /t 1 >nul
    start "" "http://localhost:8080"
    python server.py 8080 2>nul || python -m http.server 8080
)
pause

