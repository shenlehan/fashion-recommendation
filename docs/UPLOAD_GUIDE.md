# AutoDL 上传代码指南

## 方法一: AutoDL 文件管理界面上传 (推荐)

### 步骤:

1. **打包代码 (在你的 Windows 电脑上)**
   ```powershell
   # 进入项目目录
   cd C:\Users\22232\Desktop\fashion-recommendation
   
   # 使用 7-Zip 或 WinRAR 压缩整个文件夹为 zip
   # 压缩后得到: fashion-recommendation.zip
   ```

2. **登录 AutoDL 控制台**
   - 访问: https://www.autodl.com/console
   - 进入你租用的实例

3. **打开 JupyterLab**
   - 点击「打开 JupyterLab」按钮
   - 或访问实例提供的 JupyterLab 链接

4. **上传文件**
   - 在 JupyterLab 左侧文件浏览器中,点击「上传」图标
   - 选择 `fashion-recommendation.zip`
   - 等待上传完成 (根据网速,可能需要几分钟)

5. **解压文件**
   在 JupyterLab 的 Terminal 中执行:
   ```bash
   cd /root/autodl-tmp
   unzip fashion-recommendation.zip
   cd fashion-recommendation
   
   # 给脚本添加执行权限
   chmod +x *.sh
   
   # 开始安装
   bash autodl_install.sh
   ```

---

## 方法二: SSH + SCP 上传

### 步骤:

1. **获取 SSH 连接信息**
   在 AutoDL 控制台,点击「SSH 连接」,复制连接命令,类似:
   ```
   ssh -p 12345 root@region-x.autodl.com
   ```

2. **使用 SCP 上传 (在 PowerShell 中)**
   ```powershell
   # 打包项目
   Compress-Archive -Path "C:\Users\22232\Desktop\fashion-recommendation" -DestinationPath "fashion-recommendation.zip"
   
   # 上传 (替换端口和地址)
   scp -P 12345 fashion-recommendation.zip root@region-x.autodl.com:/root/autodl-tmp/
   ```

3. **SSH 登录并解压**
   ```bash
   ssh -p 12345 root@region-x.autodl.com
   cd /root/autodl-tmp
   unzip fashion-recommendation.zip
   cd fashion-recommendation
   chmod +x *.sh
   bash autodl_install.sh
   ```

---

## 方法三: Git 克隆 (如果代码在 GitHub)

### 步骤:

1. **推送代码到 GitHub/GitLab**
   ```powershell
   cd C:\Users\22232\Desktop\fashion-recommendation
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <你的仓库地址>
   git push -u origin main
   ```

2. **在 AutoDL 实例上克隆**
   ```bash
   cd /root/autodl-tmp
   git clone <你的仓库地址> fashion-recommendation
   cd fashion-recommendation
   chmod +x *.sh
   bash autodl_install.sh
   ```

---

## 方法四: 使用 AutoDL 学术资源加速 (网盘)

如果文件太大,上传慢,可以先上传到百度云/阿里云盘,然后在 AutoDL 实例上下载:

```bash
# 安装阿里云盘命令行工具 (示例)
wget https://github.com/tickstep/aliyunpan/releases/download/v0.2.8/aliyunpan-v0.2.8-linux-amd64.zip
unzip aliyunpan-v0.2.8-linux-amd64.zip
./aliyunpan login

# 下载文件
./aliyunpan download /fashion-recommendation.zip /root/autodl-tmp/
cd /root/autodl-tmp
unzip fashion-recommendation.zip
```

---

## 注意事项

### 1. 文件大小优化

**在上传前,可以删除不必要的文件以减少大小:**

```powershell
# 在 Windows 上,删除以下目录 (如果存在)
Remove-Item -Recurse -Force frontend\node_modules  # 会在服务器上重新安装
Remove-Item -Recurse -Force backend\__pycache__
Remove-Item -Recurse -Force ml\__pycache__
Remove-Item -Recurse -Force "*.pyc"
```

### 2. 添加执行权限

**上传后一定要给 shell 脚本添加执行权限:**

```bash
cd /root/autodl-tmp/fashion-recommendation
chmod +x autodl_install.sh start.sh stop.sh check_env.sh
```

### 3. 持久化存储

**AutoDL 的持久化目录:**
- `/root/autodl-tmp` - 持久化 (关机后数据保留)
- `/root` - 非持久化 (关机后可能清空)

**务必将项目放在 `/root/autodl-tmp` 下!**

---

## 快速验证

上传并解压后,运行:

```bash
cd /root/autodl-tmp/fashion-recommendation
ls -la

# 应该看到:
# autodl_install.sh
# start.sh
# stop.sh
# check_env.sh
# backend/
# frontend/
# ml/
# ...
```

然后执行环境检查:

```bash
bash check_env.sh
```

如果缺少依赖,运行安装脚本:

```bash
bash autodl_install.sh
```

---

## Windows PowerShell 快捷命令

将以下内容保存为 `upload_to_autodl.ps1`,双击运行:

```powershell
# 配置你的 AutoDL 信息
$AUTODL_HOST = "region-x.autodl.com"  # 替换为你的实例地址
$AUTODL_PORT = "12345"                 # 替换为你的 SSH 端口
$AUTODL_USER = "root"

# 项目路径
$PROJECT_DIR = "C:\Users\22232\Desktop\fashion-recommendation"

# 1. 打包项目
Write-Host "正在打包项目..." -ForegroundColor Green
$ZIP_FILE = "$env:TEMP\fashion-recommendation.zip"
Compress-Archive -Path $PROJECT_DIR -DestinationPath $ZIP_FILE -Force

# 2. 上传到 AutoDL
Write-Host "正在上传到 AutoDL..." -ForegroundColor Green
scp -P $AUTODL_PORT $ZIP_FILE ${AUTODL_USER}@${AUTODL_HOST}:/root/autodl-tmp/

# 3. SSH 登录并解压
Write-Host "正在解压..." -ForegroundColor Green
ssh -p $AUTODL_PORT ${AUTODL_USER}@${AUTODL_HOST} @"
cd /root/autodl-tmp
unzip -o fashion-recommendation.zip
cd fashion-recommendation
chmod +x *.sh
echo '上传完成! 运行以下命令开始安装:'
echo 'bash autodl_install.sh'
"@

Write-Host "完成!" -ForegroundColor Green
```

使用方法:
1. 修改脚本中的 `$AUTODL_HOST` 和 `$AUTODL_PORT`
2. 在 PowerShell 中运行: `.\upload_to_autodl.ps1`

---

## 故障排查

### 上传失败
- 检查网络连接
- 尝试使用 AutoDL 的 VPN 加速
- 分批上传 (先上传代码,模型在服务器上下载)

### 解压失败
```bash
# 如果提示 unzip 未安装
apt-get update && apt-get install -y unzip

# 如果解压出错
rm fashion-recommendation.zip
# 重新上传
```

### 权限问题
```bash
# 给所有脚本添加执行权限
find /root/autodl-tmp/fashion-recommendation -name "*.sh" -exec chmod +x {} \;
```

---

现在你可以使用任意一种方法上传代码,然后运行 `bash autodl_install.sh` 安装环境! 🚀
