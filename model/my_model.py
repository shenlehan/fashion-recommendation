import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from data_processing import get_data_loaders
import os

# 1. 定义数据目录
data_dir = '../imaterialist-fashion-2020-fgvc7'

# 2. 调用 get_data_loaders 函数来获取数据加载器和标签总数
train_loader, num_labels = get_data_loaders(data_dir)

# 3. 定义模型
model = models.resnet18(pretrained=True)
num_ftrs = model.fc.in_features
model.fc = nn.Sequential(
    nn.Linear(num_ftrs, num_labels),
)

# 4. 定义损失函数和优化器
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 将数据加载器和模型移动到GPU
print(torch.cuda.is_available())
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model.to(device)

# --- 新增部分：检查并加载模型权重 ---
model_path = "model_weights.pth"
if os.path.exists(model_path):
    print(f"检测到已保存的模型文件：{model_path}，正在加载...")
    # 加载模型的 state_dict
    model.load_state_dict(torch.load(model_path, map_location=device))
    print("模型权重加载成功，将从中断处继续训练。")
else:
    print("未找到模型权重文件，将从头开始训练。")
# --- 新增部分结束 ---

# 编写训练循环
num_epochs = 5

print_every = 100  # 设置每隔100个批次打印一次

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0

    # enumerate() 函数会返回批次的索引 i
    for i, (images, labels) in enumerate(train_loader):
        # 将数据和标签移动到GPU
        images = images.to(device)
        labels = labels.to(device)

        # 清零梯度
        optimizer.zero_grad()

        # 前向传播
        outputs = model(images)
        loss = criterion(outputs, labels)

        # 反向传播和优化
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        # 每隔 print_every 个批次就打印一次损失
        if (i + 1) % print_every == 0:
            print(
                f"Epoch [{epoch + 1}/{num_epochs}], Batch [{i + 1}/{len(train_loader)}], Loss: {running_loss / print_every:.4f}")
            running_loss = 0.0

print("训练完成！")

# 始终在训练结束后保存模型参数
torch.save(model.state_dict(), model_path)

print(f"最终模型参数已保存到 {model_path}")