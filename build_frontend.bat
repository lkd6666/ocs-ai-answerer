@echo off
chcp 65001 >nul
echo ===================================
echo    构建 OCS AI Answerer 前端
echo ===================================
echo.

cd frontend

echo [1/3] 检查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Node.js，请先安装: https://nodejs.org/
    pause
    exit /b 1
)

node -v
npm -v
echo.

echo [2/3] 安装依赖...
if not exist node_modules (
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ 依赖已安装，跳过
)
echo.

echo [3/3] 构建生产版本...
npm run build
if %errorlevel% neq 0 (
    echo ❌ 构建失败
    pause
    exit /b 1
)
echo.

cd ..

echo ===================================
echo ✅ 构建成功！
echo.
echo 静态文件已输出到: dist/
echo 现在可以启动服务: start.bat
echo ===================================
pause
