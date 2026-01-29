import os

# 定义目标目录 (根据您的报错路径)
target_dir = os.path.join("CatVTON", "model", "DensePose")
os.makedirs(target_dir, exist_ok=True)

# 1. 创建 Base-DensePose-RCNN-FPN.yaml (基础配置)
base_config_content = """VERSION: 2
MODEL:
  META_ARCHITECTURE: "GeneralizedRCNN"
  BACKBONE:
    NAME: "build_resnet_fpn_backbone"
  RESNETS:
    OUT_FEATURES: ["res2", "res3", "res4", "res5"]
  FPN:
    IN_FEATURES: ["res2", "res3", "res4", "res5"]
  ANCHOR_GENERATOR:
    SIZES: [[32], [64], [128], [256], [512]]
    ASPECT_RATIOS: [[0.5, 1.0, 2.0]]
  RPN:
    IN_FEATURES: ["p2", "p3", "p4", "p5", "p6"]
    PRE_NMS_TOPK_TRAIN: 2000
    PRE_NMS_TOPK_TEST: 1000
    POST_NMS_TOPK_TRAIN: 1000
    POST_NMS_TOPK_TEST: 1000
  DENSEPOSE_ON: True
  ROI_HEADS:
    NAME: "DensePoseROIHeads"
    IN_FEATURES: ["p2", "p3", "p4", "p5"]
    NUM_CLASSES: 1
  ROI_BOX_HEAD:
    NAME: "FastRCNNConvFCHead"
    NUM_FC: 2
    POOLER_RESOLUTION: 7
    POOLER_SAMPLING_RATIO: 2
    POOLER_TYPE: "ROIAlign"
  ROI_DENSEPOSE_HEAD:
    NAME: "DensePoseV1ConvXHead"
    POOLER_TYPE: "ROIAlign"
    NUM_COARSE_SEGM_CHANNELS: 2
DATASETS:
  TRAIN: ("densepose_coco_2014_train", "densepose_coco_2014_valminusminival")
  TEST: ("densepose_coco_2014_minival",)
SOLVER:
  IMS_PER_BATCH: 16
  BASE_LR: 0.01
  STEPS: (60000, 80000)
  MAX_ITER: 90000
  WARMUP_FACTOR: 0.1
INPUT:
  MIN_SIZE_TRAIN: (640, 672, 704, 736, 768, 800)
"""

base_config_path = os.path.join(target_dir, "Base-DensePose-RCNN-FPN.yaml")
with open(base_config_path, "w") as f:
    f.write(base_config_content)
print(f"✅ Created: {base_config_path}")

# 2. 创建 densepose_rcnn_R_50_FPN_s1x.yaml (具体模型配置)
# 注意：这里引用了上面的 Base 配置
model_config_content = """_BASE_: "Base-DensePose-RCNN-FPN.yaml"
MODEL:
  WEIGHTS: "detectron2://ImageNetPretrained/MSRA/R-50.pkl"
  RESNETS:
    DEPTH: 50
SOLVER:
  MAX_ITER: 130000
  STEPS: (100000, 120000)
"""

model_config_path = os.path.join(target_dir, "densepose_rcnn_R_50_FPN_s1x.yaml")
with open(model_config_path, "w") as f:
    f.write(model_config_content)
print(f"✅ Created: {model_config_path}")

print("🎉 配置修复完成！请重新运行 vton_server.py")