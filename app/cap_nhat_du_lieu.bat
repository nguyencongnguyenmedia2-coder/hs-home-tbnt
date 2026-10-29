@echo off
chcp 65001 >nul
echo.
echo =========================================
echo   Cap nhat du lieu san pham tu Excel
echo =========================================
echo.
python update_data.py
if errorlevel 1 (
    echo.
    echo [!] Co loi xay ra. Kiem tra lai file Excel.
) else (
    echo.
    echo [OK] Da cap nhat xong! Lam moi trang web de thay du lieu moi.
)
echo.
pause

