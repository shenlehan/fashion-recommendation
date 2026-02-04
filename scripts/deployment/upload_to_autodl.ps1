# Fashion Recommendation - AutoDL 上传脚本
# 使用方法: 
# 1. 修改下面的配置信息
# 2. 在 PowerShell 中运行: .\upload_to_autodl.ps1

# ============================================
# 配置区域 - 请修改为你的 AutoDL 实例信息
# ============================================

# AutoDL SSH 连接信息 (在 AutoDL 控制台查看)
$AUTODL_HOST = "region-x.autodl.com"  # 示例: region-1.autodl.com
$AUTODL_PORT = "12345"                 # 示例: 36283
$AUTODL_USER = "root"

# 本地项目路径
$PROJECT_DIR = "C:\Users\22232\Desktop\fashion-recommendation"

# ============================================
# 脚本开始 - 无需修改
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Fashion Recommendation - AutoDL 部署工具" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查项目目录是否存在
if (-not (Test-Path $PROJECT_DIR)) {
    Write-Host "错误: 项目目录不存在!" -ForegroundColor Red
    Write-Host "路径: $PROJECT_DIR" -ForegroundColor Red
    exit 1
}

Write-Host "项目目录: $PROJECT_DIR" -ForegroundColor Green
Write-Host "目标服务器: $AUTODL_USER@$AUTODL_HOST:$AUTODL_PORT" -ForegroundColor Green
Write-Host ""

# 1. 打包项目
Write-Host "[1/3] 打包项目..." -ForegroundColor Yellow
$ZIP_FILE = "$env:TEMP\fashion-recommendation-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"

try {
    # 排除不必要的文件
    $excludeItems = @(
        "node_modules",
        "__pycache__",
        "*.pyc",
        ".git",
        "*.log",
        "uploads",
        "fashion.db",
        "logs"
    )
    
    Write-Host "  正在压缩 (排除 node_modules, __pycache__ 等)..." -ForegroundColor Gray
    
    # 创建临时目录
    $tempDir = "$env:TEMP\fashion-recommendation-temp"
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir
    }
    Copy-Item -Recurse $PROJECT_DIR $tempDir
    
    # 删除排除项
    foreach ($item in $excludeItems) {
        Get-ChildItem -Path $tempDir -Recurse -Filter $item -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # 压缩
    Compress-Archive -Path "$tempDir\*" -DestinationPath $ZIP_FILE -Force
    
    # 清理临时目录
    Remove-Item -Recurse -Force $tempDir
    
    $zipSize = (Get-Item $ZIP_FILE).Length / 1MB
    Write-Host "  压缩完成: $ZIP_FILE ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
}
catch {
    Write-Host "  打包失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. 上传到 AutoDL
Write-Host "[2/3] 上传到 AutoDL..." -ForegroundColor Yellow

# 检查 scp 是否可用
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 未找到 scp 命令!" -ForegroundColor Red
    Write-Host "请安装 OpenSSH 客户端:" -ForegroundColor Yellow
    Write-Host "  设置 -> 应用 -> 可选功能 -> OpenSSH 客户端" -ForegroundColor Yellow
    exit 1
}

try {
    Write-Host "  正在上传 (这可能需要几分钟)..." -ForegroundColor Gray
    scp -P $AUTODL_PORT $ZIP_FILE "${AUTODL_USER}@${AUTODL_HOST}:/root/autodl-tmp/"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  上传成功!" -ForegroundColor Green
    }
    else {
        Write-Host "  上传失败! (退出码: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  上传失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 3. SSH 登录并解压
Write-Host "[3/3] 解压并配置..." -ForegroundColor Yellow

$zipFileName = Split-Path $ZIP_FILE -Leaf
$remoteCommands = @"
cd /root/autodl-tmp
echo '解压文件...'
unzip -o $zipFileName
rm $zipFileName
cd fashion-recommendation
echo '添加执行权限...'
chmod +x *.sh
echo ''
echo '============================================'
echo '上传完成! 项目路径:'
echo '/root/autodl-tmp/fashion-recommendation'
echo '============================================'
echo ''
echo '下一步: 运行安装脚本'
echo '  cd /root/autodl-tmp/fashion-recommendation'
echo '  bash autodl_install.sh'
echo ''
"@

try {
    Write-Host "  正在解压..." -ForegroundColor Gray
    ssh -p $AUTODL_PORT "${AUTODL_USER}@${AUTODL_HOST}" $remoteCommands
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Green
        Write-Host "  部署完成!" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "现在你可以 SSH 登录到 AutoDL 实例:" -ForegroundColor Cyan
        Write-Host "  ssh -p $AUTODL_PORT $AUTODL_USER@$AUTODL_HOST" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "然后运行安装脚本:" -ForegroundColor Cyan
        Write-Host "  cd /root/autodl-tmp/fashion-recommendation" -ForegroundColor Yellow
        Write-Host "  bash autodl_install.sh" -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host "  解压失败! (退出码: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  SSH 连接失败: $_" -ForegroundColor Red
    exit 1
}

# 清理本地临时文件
Remove-Item $ZIP_FILE -Force -ErrorAction SilentlyContinue

Write-Host "脚本执行完成!" -ForegroundColor Green
Write-Host ""
