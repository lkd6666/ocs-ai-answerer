@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║          OCS智能答题API - 快速启动脚本 (Windows)        ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

REM 激活虚拟环境
echo 🔄 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📦 检查并安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

REM 检查.env文件
if not exist ".env" (
    echo.
    echo ⚠️  未找到.env配置文件
    echo 📝 正在创建.env文件，请编辑后重新运行
    copy .env.example .env >nul 2>&1
    echo.
    echo 请编辑.env文件，填入您的DeepSeek API密钥
    echo 文件位置: %cd%\.env
    echo.
    notepad .env
    pause
    exit /b 0
)

echo.
echo 🚀 启动API服务...
echo.
python ocs_ai_answerer_advanced.py

pause

