import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from data_processing import get_data_loaders
import os

# 1. 定义数据目录
data_dir = '../imaterialist-fashion-2020-fgvc7'

# 2. 调用 get_data_loaders 函数来获取数据加载器
# 确保你的 data_processing 模块中的函数已经修改为可以返回 val_loader
try:
    train_loader, val_loader, num_labels = get_data_loaders(data_dir)
except ValueError:
    print("错误: get_data_loaders 函数没有返回 val_loader。")
    print("请检查 data_processing.py 文件，确保它能正确地将数据分为训练集和验证集。")
    exit()

# 3. 定义模型
model = models.resnet50(pretrained=False)  # 暂时不加载预训练权重
num_ftrs = model.fc.in_features
model.fc = nn.Sequential(
    nn.Linear(num_ftrs, num_labels),
)

# 将数据加载器和模型移动到GPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model.to(device)

# --- 检查并加载模型权重 ---
model_path = "model_weights.pth"
if os.path.exists(model_path):
    print(f"检测到已保存的模型文件：{model_path}，正在加载...")
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print("模型权重加载成功！")
    except RuntimeError as e:
        print(f"加载模型权重失败: {e}")
        print("这通常是由于模型架构与保存时的不匹配。请确保模型定义正确。")
        exit()
else:
    print("未找到模型权重文件，无法进行准确度测试。")
    print("请先运行训练脚本并保存模型。")
    exit()

# 4. 在验证集上评估模型准确度
print("\n--- 正在评估模型在验证集上的准确度 ---")
model.eval()  # 切换到评估模式
criterion = nn.BCEWithLogitsLoss()
val_loss = 0.0
correct_labels = 0
total_labels = 0

with torch.no_grad():
    for images, labels in val_loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)
        val_loss += loss.item()

        predicted = (torch.sigmoid(outputs) > 0.5).float()

        correct_labels += (predicted == labels).sum().item()
        total_labels += labels.numel()

avg_val_loss = val_loss / len(val_loader)
accuracy = correct_labels / total_labels

print(f"验证集平均损失: {avg_val_loss:.4f}")
print(f"模型在验证集上的标签准确度: {accuracy:.4f}")