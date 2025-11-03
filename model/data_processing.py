import pandas as pd
import json
import os
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from torchvision import transforms
from sklearn.model_selection import train_test_split  # 需要安装这个库


# ... (保留之前的 get_label_info 函数) ...
def get_label_info(data_dir):
    """
    加载标签描述，并创建ID到名称的映射。
    """
    with open(os.path.join(data_dir, 'label_descriptions.json'), 'r') as f:
        labels_data = json.load(f)

    id_to_name = {}
    for category in labels_data['categories']:
        id_to_name[category['id']] = category['name']
    for attribute in labels_data['attributes']:
        id_to_name[attribute['id']] = attribute['name']

    all_ids = sorted(list(id_to_name.keys()))
    total_labels = len(all_ids)
    id_to_index = {id_val: i for i, id_val in enumerate(all_ids)}

    return id_to_index, total_labels




def get_data_loaders(data_dir, batch_size=128):
    """
    加载数据，处理标签，并创建训练和验证数据加载器。
    """
    id_to_index, total_labels = get_label_info(data_dir)

    train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))

    # --- 关键改动：将数据拆分为训练集和验证集 ---
    train_df, val_df = train_test_split(train_df, test_size=0.2, random_state=42)

    def process_labels(attributes_str):
        if isinstance(attributes_str, str):
            ids = [int(x) for x in attributes_str.split(',')]
        else:
            ids = []
        label_vector = np.zeros(total_labels, dtype=np.float32)
        for id_val in ids:
            if id_val in id_to_index:
                label_vector[id_to_index[id_val]] = 1
        return label_vector

    train_df['multi_hot_labels'] = train_df['AttributesIds'].apply(process_labels)
    val_df['multi_hot_labels'] = val_df['AttributesIds'].apply(process_labels)

    data_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_image_dir = os.path.join(data_dir, 'train')

    # --- 创建训练集和验证集 Dataset ---
    train_dataset = FashionDataset(dataframe=train_df, image_dir=train_image_dir, transform=data_transforms)
    val_dataset = FashionDataset(dataframe=val_df, image_dir=train_image_dir, transform=data_transforms)

    # --- 创建训练集和验证集 DataLoader ---
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=10)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=10)

    # --- 返回两个数据加载器和标签总数 ---
    return train_loader, val_loader, total_labels


class FashionDataset(Dataset):
    """
    一个自定义的数据集类，用于加载图像和多标签。
    """

    def __init__(self, dataframe, image_dir, transform=None):
        self.dataframe = dataframe
        self.image_dir = image_dir
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        img_name = self.dataframe.iloc[idx, 0]
        img_path = os.path.join(self.image_dir, f'{img_name}.jpg')
        labels = self.dataframe.iloc[idx]['multi_hot_labels']

        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)

        return image, torch.from_numpy(labels)