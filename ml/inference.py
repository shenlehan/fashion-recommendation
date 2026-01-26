import os
import numpy as np
import torch
import argparse
from torch.utils.data import Dataset, DataLoader
from diffusers.image_processor import VaeImageProcessor
from tqdm import tqdm
from PIL import Image, ImageOps

from model.pipeline import CatVTONPipeline
from model.cloth_masker import AutoMasker

# ==========================================
# 辅助函数：保持比例缩放 + 填充
# ==========================================
def resize_and_padding(image, target_size):
    width, height = target_size
    w, h = image.size
    scale = min(width / w, height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    image = image.resize((new_w, new_h), Image.LANCZOS)
    new_image = Image.new("RGB", (width, height), (127, 127, 127))
    paste_x = (width - new_w) // 2
    paste_y = (height - new_h) // 2
    new_image.paste(image, (paste_x, paste_y))
    return new_image, (paste_x, paste_y, new_w, new_h) # 返回坐标以便后续回贴

class InferenceDataset(Dataset):
    def __init__(self, args, automasker):
        self.args = args
        self.automasker = automasker
        self.vae_processor = VaeImageProcessor(vae_scale_factor=8)
        # Mask 处理器
        self.mask_processor = VaeImageProcessor(
            vae_scale_factor=8, 
            do_normalize=False, 
            do_binarize=False, 
            do_convert_grayscale=True
        )
        self.data = self.load_data()
        
    def load_data(self):
        return []
        
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        data = self.data[idx]
        
        # 1. 读取
        person_raw = Image.open(data['person']).convert("RGB")
        cloth_raw = Image.open(data['cloth']).convert("RGB")
        
        # 2. 缩放
        target_size = (self.args.width, self.args.height)
        person, _ = resize_and_padding(person_raw, target_size)
        cloth, _ = resize_and_padding(cloth_raw, target_size)
        
        # 3. 生成 Mask (带日志提示)
        # 注意：这里我们无法直接 print，因为多进程 DataLoader 会吞掉 print
        # 但如果 batch_size 设置较小或 num_workers=0 可以看到
        mask_result = self.automasker(person, mask_type='upper')
        mask = mask_result['mask']
        
        # 4. 模糊处理 Mask (柔化边缘)
        mask_blurred = self.mask_processor.blur(mask, blur_factor=9)

        # 5. 返回数据
        return {
            'index': idx,
            'person_name': data['person_name'],
            'person': self.vae_processor.preprocess(person, self.args.height, self.args.width)[0],
            'cloth': self.vae_processor.preprocess(cloth, self.args.height, self.args.width)[0],
            'mask': self.mask_processor.preprocess(mask_blurred, self.args.height, self.args.width)[0],
            # [新增] 额外返回原始 PIL 图片，用于保存调试和回贴
            'person_pil': np.array(person),  # 转 numpy 才能通过 DataLoader 传输
            'mask_pil': np.array(mask)       # 转 numpy
        }

class VITONHDTestDataset(InferenceDataset):
    def load_data(self):
        pair_txt = os.path.join(self.args.data_root_path, 'test_pairs_unpaired.txt')
        assert os.path.exists(pair_txt), f"File {pair_txt} does not exist."
        with open(pair_txt, 'r') as f:
            lines = f.readlines()
        self.args.data_root_path = os.path.join(self.args.data_root_path, "test")
        data = []
        for line in lines:
            person_img, cloth_img = line.strip().split(" ")
            data.append({
                'person_name': person_img,
                'person': os.path.join(self.args.data_root_path, 'image', person_img),
                'cloth': os.path.join(self.args.data_root_path, 'cloth', cloth_img),
            })
        return data

class DressCodeTestDataset(InferenceDataset):
    def load_data(self):
        data = []
        for sub_folder in ['upper_body', 'lower_body', 'dresses']:
            folder_path = os.path.join(self.args.data_root_path, sub_folder)
            pair_txt = os.path.join(folder_path, 'test_pairs_paired.txt' if self.args.eval_pair else 'test_pairs_unpaired.txt')
            if not os.path.exists(pair_txt): continue
            with open(pair_txt, 'r') as f:
                lines = f.readlines()
            for line in lines:
                person_img, cloth_img = line.strip().split(" ")
                data.append({
                    'person_name': os.path.join(sub_folder, person_img),
                    'person': os.path.join(self.args.data_root_path, sub_folder, 'images', person_img),
                    'cloth': os.path.join(self.args.data_root_path, sub_folder, 'images', cloth_img),
                })
        return data

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model_path", type=str, default="booksforcharlie/stable-diffusion-inpainting")
    parser.add_argument("--resume_path", type=str, default="zhengchong/CatVTON")
    parser.add_argument("--dataset_name", type=str, required=True)
    parser.add_argument("--data_root_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="output")
    parser.add_argument("--seed", type=int, default=555)
    parser.add_argument("--batch_size", type=int, default=1) # 建议改为1以便观察日志
    parser.add_argument("--num_inference_steps", type=int, default=50)
    parser.add_argument("--guidance_scale", type=float, default=2.5)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--repaint", action="store_true") # 我们的代码默认就会执行回贴逻辑
    parser.add_argument("--eval_pair", action="store_true")
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    print(f"Inference with args: {args}")
    
    # 1. 加载模型
    pipeline = CatVTONPipeline(
        base_ckpt=args.base_model_path,
        attn_ckpt=args.resume_path,
        attn_load_type="all",
        weight_dtype=torch.float16,
        use_tf32=True,
        device='cuda'
    )
    
    # 2. 初始化 AutoMasker (会有加载日志)
    print("正在加载 AutoMasker (DensePose + SCHP)...")
    automasker = AutoMasker(
        densepose_ckpt=os.path.join(args.base_model_path, "DensePose"),
        schp_ckpt=os.path.join(args.base_model_path, "SCHP"),
        device='cuda'
    )
    print("AutoMasker 加载完成。")

    # 3. 数据集
    if args.dataset_name == 'vitonhd':
        dataset = VITONHDTestDataset(args, automasker)
    elif args.dataset_name == 'dresscode':
        dataset = DressCodeTestDataset(args, automasker)
    else:
        raise ValueError(f"Dataset {args.dataset_name} not supported.")
        
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=0) # num_workers=0 以便看到实时print
    
    # 准备保存路径
    debug_mask_dir = os.path.join(args.output_dir, "debug_masks")
    os.makedirs(debug_mask_dir, exist_ok=True)

    # 4. 推理循环
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="正在试衣中"):
            # 拿到数据
            person = batch['person'].to(pipeline.device)
            cloth = batch['cloth'].to(pipeline.device)
            mask = batch['mask'].to(pipeline.device)
            
            # 还原 PIL 以便后续处理
            person_pils = [Image.fromarray(img.numpy().astype('uint8')) for img in batch['person_pil']]
            mask_pils = [Image.fromarray(img.numpy().astype('uint8')) for img in batch['mask_pil']]
            
            # 生成
            generator = torch.Generator(device='cuda').manual_seed(args.seed)
            results = pipeline(
                person,
                cloth,
                mask,
                num_inference_steps=args.num_inference_steps,
                guidance_scale=args.guidance_scale,
                height=args.height,
                width=args.width,
                generator=generator
            )[0]
            
            # 5. 保存结果与调试信息
            for i, generated_image in enumerate(results):
                person_name = batch['person_name'][i]
                original_person_img = person_pils[i]
                mask_img = mask_pils[i] # 这是 AutoMasker 生成的原始 Mask
                
                # --- [验证步骤] 保存 Mask 供检查 ---
                mask_save_name = os.path.basename(person_name).replace('.jpg', '_debug_mask.png')
                mask_img.save(os.path.join(debug_mask_dir, mask_save_name))
                # -------------------------------

                # --- [优化步骤] 回贴 (Paste Back) ---
                # 逻辑：最终结果 = 生成图 * Mask区域 + 原图 * (1-Mask区域)
                # 这样可以保持原图的脸部和背景绝对清晰
                mask_img = mask_img.convert("L").resize(generated_image.size)
                # 对 Mask 做一点羽化，让接缝自然
                mask_alpha = mask_img.filter(ImageFilter.GaussianBlur(radius=1))
                
                # 组合：将生成的衣服贴回原图
                # 注意：generated_image 里是“换好衣服的人”，original_person_img 是“原图”
                # 我们希望在 Mask 白色区域使用 generated_image，黑色区域使用 original_person_img
                final_image = Image.composite(generated_image, original_person_img, mask_alpha)
                # -------------------------------

                # 保存路径处理
                if args.dataset_name == 'dresscode':
                    folder, filename = os.path.split(person_name)
                    save_dir = os.path.join(args.output_dir, f"dresscode-{args.height}", 
                                          'unpaired' if not args.eval_pair else 'paired', folder)
                else:
                    save_dir = os.path.join(args.output_dir, "vitonhd", 
                                          'unpaired' if not args.eval_pair else 'paired')
                
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, os.path.basename(person_name))
                
                final_image.save(save_path)

if __name__ == "__main__":
    main()