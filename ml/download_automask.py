import os
import requests
from tqdm import tqdm

# 基础路径
BASE_DIR = os.path.join(os.getcwd(), "CatVTON", "model")
SCHP_DIR = os.path.join(BASE_DIR, "SCHP", "checkpoints")
DP_DIR = os.path.join(BASE_DIR, "DensePose", "checkpoints")

os.makedirs(SCHP_DIR, exist_ok=True)
os.makedirs(DP_DIR, exist_ok=True)

# ⚠️ 注意：这里已经把域名改成 hf-mirror.com 了
files = [
    # SCHP 模型
    {
        "url": "https://hf-mirror.com/zhengchong/CatVTON/resolve/main/SCHP/exp-schp-201908261155-lip.pth",
        "path": os.path.join(SCHP_DIR, "exp-schp-201908261155-lip.pth"),
        "name": "SCHP Model"
    },
    # DensePose 模型
    {
        "url": "https://hf-mirror.com/zhengchong/CatVTON/resolve/main/DensePose/model_final_162be9.pkl",
        "path": os.path.join(DP_DIR, "model_final_162be9.pkl"),
        "name": "DensePose Weights"
    },
    # DensePose 配置文件 1
    {
        "url": "https://hf-mirror.com/zhengchong/CatVTON/resolve/main/DensePose/densepose_rcnn_R_50_FPN_s1x.yaml",
        "path": os.path.join(DP_DIR, "densepose_rcnn_R_50_FPN_s1x.yaml"),
        "name": "DensePose Config 1"
    },
    # DensePose 配置文件 2
    {
        "url": "https://hf-mirror.com/zhengchong/CatVTON/resolve/main/DensePose/Base-DensePose-RCNN-FPN.yaml",
        "path": os.path.join(DP_DIR, "Base-DensePose-RCNN-FPN.yaml"),
        "name": "DensePose Config 2"
    }
]

def download_file(url, filename, desc):
    if os.path.exists(filename):
        print(f"✅ {desc} 已存在，跳过。")
        return
    
    print(f"⬇️ 正在下载 {desc}...")
    try:
        # 增加 timeout 设置，防止卡死
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code != 200:
            print(f"❌ 下载失败 (状态码 {response.status_code}): {url}")
            return
            
        total_size = int(response.headers.get('content-length', 0))
        with open(filename, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as bar:
            for data in response.iter_content(chunk_size=1024):
                f.write(data)
                bar.update(len(data))
        print(f"✅ {desc} 下载完成！")
    except Exception as e:
        print(f"💥 网络错误: {e}")

if __name__ == "__main__":
    print(f"🚀 开始通过国内镜像下载辅助模型...")
    for file in files:
        download_file(file["url"], file["path"], file["name"])
    print("🎉 下载脚本运行结束！")