@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo [start.bat] 未找到虚拟环境 .venv
    echo 请先按 README「快速开始」完成环境搭建，或运行: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist .env (
    echo [start.bat] 未找到 .env 配置文件
    echo 请先复制: copy .env.example .env ，并按需填写密钥（retrieval 模式无需密钥）
    pause
    exit /b 1
)

set HF_ENDPOINT=https://hf-mirror.com
echo [start.bat] 启动服务: http://127.0.0.1:8000  （操作页面: http://127.0.0.1:8000/ ）
echo [start.bat] 按 Ctrl+C 停止服务
echo.
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
