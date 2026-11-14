@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
    echo [check.bat] 未找到虚拟环境 .venv，请先按 README 完成环境搭建
    pause
    exit /b 1
)

echo ===== 项目体检 doctor.py（环境/依赖/配置/端口/连通性）=====
.venv\Scripts\python.exe scripts\doctor.py
echo.
echo ===== 项目检查 check_project.py（含接口自检，需服务已启动）=====
.venv\Scripts\python.exe scripts\check_project.py
echo.
echo [check.bat] 体检完成。若有「需处理」项，按输出中的下一步命令修复。
pause
