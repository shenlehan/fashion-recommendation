# Fashion Recommendation ML 模块

本模块使用 **Qwen3-VL-8B-Instruct** - Qwen 系列中最强大的多模态大语言模型，用于：
1. **衣物图像分析**：从衣物图片中提取分类、颜色、季节和材质
2. **穿搭推荐**：基于衣橱、天气和偏好生成个性化穿搭建议

## 模型信息

- **模型**: [Qwen/Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct)
- **参数量**: 80 亿
- **能力**: 增强的视觉 + 语言理解，改进的空间感知
- **硬件要求**：
  - **GPU**: 推荐（16GB+ 显存以获得最佳性能）
  - **CPU**: 支持但较慢（推荐 32GB+ 内存）

## 安装

### 1. 安装依赖

```bash
cd ml
pip install -r requirements.txt
```

### 2. 下载模型（自动）

模型将在首次使用时从 HuggingFace 自动下载。根据你的网络速度，这可能需要一些时间（约 15GB 下载）。

### 3. 手动下载模型（可选）

如果你偏好手动下载：

```bash
# 使用 huggingface-cli
huggingface-cli download Qwen/Qwen3-VL-8B-Instruct
```

## 使用方法

### 衣物图像分析

```python
from ml.inference import predict

# 分析衣物图片
result = predict("路径/到/衣物/图片.jpg")

# 结果格式:
# {
#     "category": "top",
#     "color": "blue",
#     "season": "spring,summer",
#     "material": "cotton"
# }
```

### 穿搭推荐

```python
from ml.inference import get_recommendations

# 生成推荐
result = get_recommendations(
    user={
        "body_type": "athletic",
        "city": "New York"
    },
    wardrobe=[
        {"id": 1, "name": "蓝色T恤", "category": "top", "color": "blue", "season": "spring,summer", "material": "cotton"},
        {"id": 2, "name": "牛仔裤", "category": "bottom", "color": "blue", "season": "all", "material": "denim"}
    ],
    weather={
        "temperature": 22,
        "condition": "Sunny"
    },
    preferences={
        "occasion": "casual",
        "style": "minimalist",
        "color_preference": "blue,white"
    }
)

# 结果格式:
# {
#     "outfits": [
#         {
#             "items": [wardrobe_item1, wardrobe_item2],
#             "description": "适合晋天的完美休闲穿搭..."
#         }
#     ],
#     "missing_items": [
#         {
#             "category": "shoes",
#             "reason": "可以完善休闲穿搭"
#         }
#     ]
# }
```

## 模型性能

### GPU 性能
- **首次加载**: 约30秒（模型加载）
- **图像分析**: 每张图片约 2-5 秒
- **推荐生成**: 约 5-10 秒

### CPU 性能
- **首次加载**: 约60秒（模型加载）
- **图像分析**: 每张图片约 15-30 秒
- **推荐生成**: 约 30-60 秒

## 与后端集成

ML 模块自动与后端服务集成：

1. **图像服务** (`app/services/image_service.py`)：
   - 调用 `ml.inference.predict()` 进行衣物分析
   - 上传衣物时自动使用

2. **推荐服务** (`app/services/recommendation_service.py`)：
   - 调用 `recommendation.logic.get_recommendations()`
   - 内部使用 `ml.inference.get_recommendations()`

## 模型行为

### 图像分析
模型会识别：
- **分类**: 上装、下装、连衣裙、外套、鞋子、配饰
- **颜色**: 主要颜色名称
- **季节**: 适用季节（春、夏、秋、冬）
- **材质**: 面料类型（棉、牛仔布、羊毛等）

### 推荐生成
模型会考虑：
- 可用的衣橱物品
- 当前天气条件
- 用户的体型和地理位置
- 用户偏好（场合、风格、颜色）
- 时尚配搭和造型规则

## 问题排查

### 内存不足 (OOM) 错误

如果遇到 CUDA OOM 错误：

```python
# 方案 1: 使用 CPU
export CUDA_VISIBLE_DEVICES=""

# 方案 2: 减少 batch size / 使用模型卸载
# 模型已配置为自动设备映射
```

### 性能较慢

- 确保使用 GPU（如果可用）
- 首次推理总是较慢，因为需要加载模型
- 后续推理使用缓存的模型实例

### 未找到模型

如果下载失败：
```bash
# 检查 HuggingFace 连接
huggingface-cli whoami

# 手动下载
huggingface-cli download Qwen/Qwen3-VL-8B-Instruct
```

## 替代模型

如果 Qwen3-VL-8B 太大，您可以修改 `inference.py` 使用：
- **Qwen3-VL-2B-Instruct**: 更小、更快、准确度较低
- **Qwen3-VL-4B-Instruct**: 平衡选项
- **Qwen2.5-VL-7B-Instruct**: 上一代模型

在 `FashionQwenModel.__init__()` 中修改模型名称：
```python
def __init__(self, model_name: str = "Qwen/Qwen3-VL-4B-Instruct"):
```

## API 访问（替代本地模型）

不运行本地模型，您可以使用 Qwen API 进行更快的推理：

### 获取 API 密钥：
1. **阿里云百炼大模型** (官方): https://www.alibabacloud.com/help/zh/model-studio/get-api-key
2. **Qwen.ai 平台**: https://qwen.ai/apiplatform
3. **OpenRouter** (免费套餐): https://openrouter.ai

设置环境变量：
```bash
export QWEN_API_KEY="your-api-key-here"
```

## 许可证

本模块使用的 Qwen3-VL 模型采用 Apache 2.0 许可证。
