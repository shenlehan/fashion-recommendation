import os
import shutil
from huggingface_hub import hf_hub_download

# 1. 强制使用国内镜像
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

print("🚀 开始尝试通过 huggingface_hub 下载...")

try:
    # 2. 定义目标路径
    target_dir = os.path.join("CatVTON", "model", "DensePose")
    target_file = os.path.join(target_dir, "model_final_162be9.pkl")
    
    # 确保目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 3. 删除之前可能下载错误的损坏文件 (如果小于 1MB 肯定是错的)
    if os.path.exists(target_file):
        if os.path.getsize(target_file) < 1024 * 1024: 
            print("🗑️ 检测到之前下载的损坏文件，正在删除...")
            os.remove(target_file)
        else:
            print("⚠️ 文件貌似已存在且大小正常。")
            # 如果您确定文件没问题，可以注释掉下面这行，否则会强制重新下载
            # return 

    # 4. 从 yisol/IDM-VTON 仓库下载 (这个仓库也有这个文件，且通常是公开的)
    # subfolder 参数指定文件在仓库内的子目录
    downloaded_path = hf_hub_download(
        repo_id="yisol/IDM-VTON",
        filename="densepose/model_final_162be9.pkl",
        local_dir="./temp_download",  # 先下载到临时目录
        local_dir_use_symlinks=False  # 下载真实文件，不要软链接
    )
    
    # 5. 移动文件到正确位置
    # IDM-VTON 仓库里，文件在 densepose/ 目录下
    source_file = os.path.join("./temp_download", "densepose", "model_final_162be9.pkl")
    
    print(f"📦 正在将文件移动到: {target_file}")
    shutil.move(source_file, target_file)
    
    # 清理临时目录
    shutil.rmtree("./temp_download")

    print("✅ 下载并安装成功！")
    print(f"📂 文件大小: {os.path.getsize(target_file) / 1024 / 1024:.2f} MB")

except Exception as e:
    print(f"\n❌ 下载失败: {e}")
    print("如果是权限问题，请检查您的网络是否允许访问 hf-mirror.com")