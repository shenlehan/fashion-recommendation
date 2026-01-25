import os
import numpy as np
import torch
import argparse
from torch.utils.data import Dataset, DataLoader
from diffusers.image_processor import VaeImageProcessor
from tqdm import tqdm
from PIL import Image, ImageFilter

from model.pipeline import CatVTONPipeline

class InferenceDataset(Dataset):
    def __init__(self, args):
        self.args = args
    
        self.vae_processor = VaeImageProcessor(vae_scale_factor=8) 
        # [修改点 1/3] 去掉 do_binarize=True，防止边缘变硬
        self.mask_processor = VaeImageProcessor(vae_scale_factor=8, do_normalize=False, do_binarize=False, do_convert_grayscale=True) 
        self.data = self.load_data()
    
    def load_data(self):
        return []
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        data = self.data[idx]
        person, cloth, mask = [Image.open(data[key]) for key in ['person', 'cloth', 'mask']]
        
        # [修改点 2/3] 手动添加模糊逻辑 (模仿 app.py 的 blur_factor=9)
        # 这一步对于消除“贴图感”至关重要
        mask = self.mask_processor.blur(mask, blur_factor=9)

        return {
            'index': idx,
            'person_name': data['person_name'],
            'person': self.vae_processor.preprocess(person, self.args.height, self.args.width)[0],
            'cloth': self.vae_processor.preprocess(cloth, self.args.height, self.args.width)[0],
            'mask': self.mask_processor.preprocess(mask, self.args.height, self.args.width)[0]
        }

class VITONHDTestDataset(InferenceDataset):
    def load_data(self):
        assert os.path.exists(pair_txt:=os.path.join(self.args.data_root_path, 'test_pairs_unpaired.txt')), f"File {pair_txt} does not exist."
        with open(pair_txt, 'r') as f:
            lines = f.readlines()
        self.args.data_root_path = os.path.join(self.args.data_root_path, "test")
        output_dir = os.path.join(self.args.output_dir, "vitonhd", 'unpaired' if not self.args.eval_pair else 'paired')
        data = []
        for line in lines:
            person_img, cloth_img = line.strip().split(" ")
            if os.path.exists(os.path.join(output_dir, person_img)):
                continue
            if self.args.eval_pair:
                cloth_img = person_img
            data.append({
                'person_name': person_img,
                'person': os.path.join(self.args.data_root_path, 'image', person_img),
                'cloth': os.path.join(self.args.data_root_path, 'cloth', cloth_img),
                'mask': os.path.join(self.args.data_root_path, 'agnostic-mask', person_img.replace('.jpg', '_mask.png')),
            })
        return data

class DressCodeTestDataset(InferenceDataset):
    def load_data(self):
        data = []
        for sub_folder in ['upper_body', 'lower_body', 'dresses']:
            assert os.path.exists(os.path.join(self.args.data_root_path, sub_folder)), f"Folder {sub_folder} does not exist."
            pair_txt = os.path.join(self.args.data_root_path, sub_folder, 'test_pairs_paired.txt' if self.args.eval_pair else 'test_pairs_unpaired.txt')
            assert os.path.exists(pair_txt), f"File {pair_txt} does not exist."
            with open(pair_txt, 'r') as f:
                lines = f.readlines()

            output_dir = os.path.join(self.args.output_dir, f"dresscode-{self.args.height}", 
                                      'unpaired' if not self.args.eval_pair else 'paired', sub_folder)
            for line in lines:
                person_img, cloth_img = line.strip().split(" ")
                if os.path.exists(os.path.join(output_dir, person_img)):
                    continue
                data.append({
                    'person_name': os.path.join(sub_folder, person_img),
                    'person': os.path.join(self.args.data_root_path, sub_folder, 'images', person_img),
                    'cloth': os.path.join(self.args.data_root_path, sub_folder, 'images', cloth_img),
                    'mask': os.path.join(self.args.data_root_path, sub_folder, 'agnostic_masks', person_img.replace('.jpg', '.png'))
                })
        return data
                    
       
def parse_args():
    parser = argparse.ArgumentParser(description="Simple example of a training script.")
    parser.add_argument(
        "--base_model_path",
        type=str,
        default="booksforcharlie/stable-diffusion-inpainting",  # Change to a copy repo as runawayml delete original repo
        help=(
            "The path to the base model to use for evaluation. This can be a local path or a model identifier from the Model Hub."
        ),
    )
    parser.add_argument(
        "--resume_path",
        type=str,
        default="zhengchong/CatVTON",
        help=(
            "The Path to the checkpoint of trained tryon model."
        ),
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        required=True,
        help="The datasets to use for evaluation.",
    )
    parser.add_argument(
        "--data_root_path", 
        type=str, 
        required=True,
        help="Path to the dataset to evaluate."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="The output directory where the model predictions will be written.",
    )

    parser.add_argument(
        "--seed", type=int, default=555, help="A seed for reproducible evaluation."
    )
    parser.add_argument(
        "--batch_size", type=int, default=8, help="The batch size for evaluation."
    )
    
    parser.add_argument(
        "--num_inference_steps",
        type=int,
        default=50,
        help="Number of inference steps to perform.",
    )
    parser.add_argument(
        "--guidance_scale",
        type=float,
        default=2.5,
        help="The scale of classifier-free guidance for inference.",
    )

    # [修改点 3/3] 修改默认分辨率为 Demo 同款 (768x1024)
    parser.add_argument(
        "--width",
        type=int,
        default=768, 
        help=(
            "The resolution for input images, all the images in the train/validation dataset will be resized to this"
            " resolution"
        ),
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1024,
        help=(
            "The resolution for input images, all the images in the train/validation dataset will be resized to this"
            " resolution"
        ),
    )
    parser.add_argument(
        "--repaint", 
        action="store_true", 
        help="Whether to repaint the result image with the original background."
    )
    parser.add_argument(
        "--eval_pair",
        action="store_true",
        help="Whether or not to evaluate the pair.",
    )
    parser.add_argument