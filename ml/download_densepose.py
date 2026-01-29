import os
import requests
from tqdm import tqdm

# =================配置区域=================
# 使用 HuggingFace 国内镜像 (hf-mirror.com)
# 来源仓库: yisol/IDM-VTON (这是一个非常可靠的 VTON 项目备份)
MIRROR_URL = "https://hf-mirror.com/yisol/IDM-VTON/resolve/main/densepose/model_final_162be9.pkl"

# 目标路径 (与您的报错路径一致)
TARGET_DIR = os.path.join("CatVTON", "model", "DensePose")
TARGET_FILE = os.path.join(TARGET_DIR, "model_final_162be9.pkl")
# =========================================

def download_file(url, dest_path):
    print(f"🔗 正在连接镜像源: {url}")
    print(f"📂 目标保存位置: {dest_path}")
    
    try:
        # stream=True 允许分块下载大文件
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status() # 检查是否连接成功 (200 OK)
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024 # 1MB
        
        with open(dest_path, 'wb') as file, tqdm(
            desc="下载进度",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(block_size):
                size = file.write(data)
                bar.update(size)
        print("\n✅ 下载成功！权重文件已就位。")
        return True
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print("建议：如果镜像也被拦截，请尝试在本地下载后通过 FTP/SCP 上传到服务器。")
        return False

if __name__ == "__main__":
    # 1. 确保目录存在
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 2. 检查文件是否已存在
    if os.path.exists(TARGET_FILE):
        file_size = os.path.getsize(TARGET_FILE)
        print(f"⚠️ 文件已存在 ({file_size / 1024 / 1024:.2f} MB)")
        # 如果文件太小（比如小于 1MB），说明之前下载失败了，删掉重下
        if file_size < 1024 * 1024:
            print("   -> 文件过小，判定为损坏，正在重新下载...")
            os.remove(TARGET_FILE)
            download_file(MIRROR_URL, TARGET_FILE)
        else:
            print("   -> 跳过下载。如果不确定文件是否完好，请手动删除后重试。")
    else:
        # 3. 执行下载
        if download_file(MIRROR_URL, TARGET_FILE):
            print("\n🎉 修复完成！请重新运行: python vton_server.py")