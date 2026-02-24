# 智能穿搭推荐系统

## 项目分工

#### 沈乐涵

- 项目架构设计与核心框架搭建
- 多模态大语言模型集成（Qwen3-VL）
- 衣橱管理模块开发（衣物识别、分类、存储）
- 场景推荐系统核心算法
- 衣橱管理页面设计（Wardrobe.jsx）
- 获取推荐页面设计（Recommendations.jsx）
- 数据库设计与ORM配置
- 用户认证与权限管理
- 部署脚本开发
- 项目文档编写与维护

#### 田彬豪

- 虚拟试衣系统开发（CatVTON集成）
- AutoMasker人体掩码生成（DensePose + SCHP）
- Paste Back融合技术实现
- 批量试穿功能开发（穿衣顺序优化、类别优先级）
- 试衣服务API设计（FastAPI独立服务，端口8001）
- 图像预处理与后处理优化（resize_and_padding、边缘羽化）
- 试衣模型性能调优

#### 朱俊逸

- 实时天气API集成（OpenWeatherMap）
- Redis缓存系统设计（2小时缓存、降级方案）
- 全国城市名称映射配置（覆盖所有地级市）
- 多模态RAG语义检索实现（ChromaDB + Sentence-BERT + CLIP）
- 融合向量生成算法（1536维 = 文本768维 + 图像768维）
- 类别平衡检索策略
- 多轮对话系统开发（会话持久化、消息管理、批量删除）
- 对话历史跨页面共享机制
- 定时任务调度（APScheduler清理过期会话）
- 前端开发（React 19 + Vite）
- 我的衣橱页面优化（Wardrobe.jsx）
- 获取推荐页面优化（Recommendations.jsx）
- 对话调整页面设计（Conversation.jsx）
- 个人资料页面设计（Profile.jsx）

## 增量内容

### 实时天气系统
- 集成OpenWeatherMap API，支持全国所有地级市及以上城市天气查询
- 实现Redis缓存机制，2小时缓存周期，降低API调用开销
- 设计降级方案：Redis不可用时自动切换到内存缓存，API失败时返回mock数据
- 天气数据细分：支持最高最低温、湿度、风速、降水概率等指标
- 降水强度细分：根据中国气象标准，区分小雨/中雨/大雨/暴雨、小雪/中雪/大雪/暴雪
- 天气趋势分析：自动检测并标注天气转变（如"多云转晴"）

### 多模态向量检索（RAG）
- 文本语义嵌入：使用Sentence-BERT（paraphrase-multilingual-mpnet-base-v2）生成768维向量
- 图像语义嵌入：使用CLIP（openai/clip-vit-base-patch32）生成768维向量
- 融合向量：拼接文本和图像向量，生成1536维多模态向量
- ChromaDB向量数据库：持久化存储，支持高效相似度检索
- 类别平衡检索：7个类别各取top-3，确保推荐结果搭配完整
- 混合检索策略：向量相似度 + 精确过滤（季节、颜色、材质）+ 重排序
- 降级容错：模型加载失败时标记为不可用，向量检索失败时返回空列表触发全量查询
- 完全离线加载：强制从本地缓存加载模型，避免网络依赖

### 多轮对话系统
- 会话管理：支持创建、查询、删除会话，每个用户可拥有多个独立会话
- 对话持久化：会话存储在数据库，支持跨页面状态共享
- 消息管理：支持单条消息删除和批量删除（成对删除用户-助手消息）
- 对话历史限制：每个会话最多保留20轮对话，超出自动删除最早记录
- 会话有效期：3天未更新的会话自动清理，节省存储空间
- 定时清理任务：每天凌晨3点自动执行过期会话清理（APScheduler）
- 会话列表：支持分页加载用户的所有会话，按更新时间倒序排列
- 消息折叠：支持折叠展开长消息，优化阅读体验

### 前端UI/UX设计
- 对话式调整页面：聊天界面风格，支持多轮对话，实时显示推荐结果
- 会话列表侧边栏：支持快速切换会话、删除会话、批量删除所有会话
- 消息管理模式：批量选择并删除消息对，支持撤销错误操作
- 虚拟试衣集成：上传全身照，一键试穿当前推荐的所有衣物
- 响应式布局：适配不同屏幕尺寸，移动端友好
- 交互优化：加载动画、错误提示、成功反馈等
- 推荐结果展示：卡片式布局，支持查看衣物详情、虚拟试衣
- 衣橱管理界面：网格布局展示衣物，支持筛选、搜索、批量删除
- 用户个人资料：头像上传、基本信息编辑、全身照管理

### 虚拟试衣系统
- CatVTON模型集成：基于Stable Diffusion Inpainting的轻量级扩散模型
- 参数规模：899M总参数，49.57M可训练参数，显存需求<8GB
- 推理优化：50步推理，guidance_scale=2.5，支持固定随机种子确保结果一致性

### AutoMasker自动掩码生成
- DensePose人体姿态估计：精确定位人体各部位
- SCHP语义分割：高质量衣物区域分割
- 多类型掩码：支持upper（上半身）、lower（下半身）、outer（外套）、overall（全身）
- 边缘羽化：使用高斯模糊柔化掩码边缘，提升融合自然度

### Paste Back融合技术
- 回贴算法：将生成的衣服区域融合回原图，保留原图脸部和背景
- 防止模糊：只替换衣物区域，确保脸部和背景清晰不变
- 无缝融合：掩码腐蚀处理，防止白边和融合痕迹

### 批量试穿功能
- 智能排序：按服装层次顺序试穿（内层上装→中层上装→外层上装→下装）
- 顺序生成：每次试穿结果作为下一次的输入，确保穿搭自然合理
- 类别优先级：inner_top(10) < mid_top(20) < outer_top(30) < bottom(40) < full_body(50)
- 支持类型：暂不支持鞋子和配饰试穿（模型限制）
- 中间结果保存：每一步生成结果保存到debug目录，支持调试

### 试衣服务API
- 独立服务：FastAPI独立运行在8001端口，与主后端服务解耦
- `/process_tryon`：单件衣物试穿接口
- `/batch_tryon`：批量试穿接口，支持一次试穿多件衣物
- 图像预处理：智能缩放（resize_and_padding），保持原图比例，避免变形
- 调试支持：自动保存输入图、掩码、中间结果到debug目录
- 异常处理：完善的错误处理和堆栈追踪，支持问题定位

## 项目简介

基于多模态大语言模型的智能穿搭推荐系统，集成衣橱管理、语义搜索、场景推荐、虚拟试衣等功能，为用户提供个性化穿搭建议。

## 核心功能

1. 智能衣橱管理 - AI自动识别衣物并分类
2. 语义搜索 - 支持自然语言和图像向量检索
3. 场景推荐 - 基于天气、场合、风格的智能推荐
4. 虚拟试衣 - 实时预览穿搭效果，支持单件和整套批量试穿
5. 对话式调整 - 选择方案后支持多轮对话精细化调整搭配

## 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM数据库操作
- Redis - 天气数据缓存
- APScheduler - 定时任务调度
- httpx - 异步HTTP客户端，用于试衣服务代理
- OpenWeatherMap API - 天气数据源

### 前端
- React 19 - UI框架
- Vite - 构建工具
- React Router - 路由管理
- Axios - HTTP客户端

### 人工智能模块

#### 多模态大语言模型
- Qwen3-VL (8B) - 衣物识别、语义理解、推荐生成
- qwen_vl_utils - 图像预处理工具库

#### 语义检索 (RAG)
- sentence-transformers - 多语言文本嵌入 (768维)
- CLIP (openai/clip-vit-base-patch32) - 图像嵌入 (768维)
- ChromaDB - 向量数据库
- 融合向量 (1536维 = 文本768 + 图像768)

#### 虚拟试衣
- CatVTON - 虚拟试衣主模型 (ICLR 2025)
- AutoMasker - 自动掩码生成器 (DensePose + SCHP)
- Stable Diffusion Inpainting - 图像修复基础模型
- Paste Back - 融合技术，保证脸部和背景清晰

## 系统架构

```
用户交互层 (React Frontend - 端口6006)
    |
    v
API网关层 (FastAPI Backend - 端口6008)
    |
    +-- 用户认证模块
    +-- 衣橱管理模块
    +-- 推荐服务模块
    +-- 试衣服务代理 (转发至8001端口)
    |
    v
AI服务层
    +-- Qwen3-VL服务 (衣物识别/推荐生成)
    +-- 向量检索服务 (RAG语义搜索)
    +-- CatVTON服务 (虚拟试衣 - 独立端口8001)
    |
    v
数据存储层
    +-- SQLite (用户/衣物数据)
    +-- ChromaDB (向量数据)
    +-- 文件系统 (图像存储)
```

## 核心算法

### 多模态语义检索

采用RAG技术实现智能衣物检索，解决大规模衣橱场景下的推荐质量问题：

- 文本特征提取：衣物名称、颜色、材质、季节、类别 → 768维向量
- 图像特征提取：CLIP编码器处理衣物图像 → 768维向量
- 特征融合：文本向量 + 图像向量 → 1536维多模态向量
- 分类平衡检索：7个类别各取top-3，确保搭配完整性
- 降级保障：模型加载失败时标记为不可用，向量检索失败返回空列表触发全量查询降级（自动使用全量查询，不影响推荐功能）

### 场景感知推荐

结合多维度信息生成个性化推荐：

- 实时天气数据（OpenWeatherMap API提供温度、降水、湿度等数据）
- 用户场合需求（商务、日常、约会等）
- 个人风格偏好（经典、现代、休闲等）
- 色调倾向（中性、暖色、冷色）
- 多轮对话历史

### 虚拟试衣技术

基于CatVTON轻量级扩散模型：

- 参数规模：899M (总参数) / 49.57M (可训练)
- 显存要求：< 8GB (768x1024分辨率)
- 人体解析：AutoMasker自动掩码生成 (集成DensePose + SCHP)
- 试衣生成：Stable Diffusion Inpainting + CatVTON注意力权重
- 融合技术：Paste Back回贴，保证脸部和背景不模糊
- 批量试穿：支持按内层上装→中层上装→外层上装→下装顺序依次生成 (暂不支持鞋子和饰品等类型试穿)

## 项目特色

1. 轻量级部署：模型优化，支持消费级GPU运行
2. 多模态理解：融合文本和图像语义，检索精度高
3. 类别平衡：避免单一类别主导，确保搭配合理性
4. 降级容错：核心功能具备降级策略，保证系统稳定性
5. 对话交互：支持多轮调整，会话持久化，跨页面状态共享
6. 批量试穿：智能顺序排序，一键生成完整穿搭效果
7. 定时清理：每天凌晨3点自动清理3天前过期会话，节省存储空间

## 系统要求

- GPU: RTX 4090 (24GB) / A100 (40GB+)
- 内存: 30GB+
- 存储: 80GB+
- 操作系统: Linux / Windows

## 项目结构

```
fashion-recommendation/
├── backend/             # FastAPI后端
│   ├── app/
│   │   ├── core/        # 配置与数据库
│   │   ├── models/      # 数据模型
│   │   ├── routes/      # API路由
│   │   ├── schemas/     # 数据验证
│   │   └── services/    # 业务逻辑
├── frontend/            # React前端
│   └── src/
│       ├── pages/       # 页面组件
│       └── services/    # API调用
├── ml/                  # AI服务
│   ├── CatVTON/         # 虚拟试衣模型
│   └── vton_server.py   # 试衣服务
└── scripts/             # 部署脚本
```

## 技术创新点

1. 多模态RAG检索：文本+图像双语义融合，提升检索准确度
2. 分类平衡策略：避免Prompt过载，优化推荐质量
3. 场景增强查询：温度特征、天气映射、场合语义扩展
4. 轻量级试衣：CatVTON模型优化，降低硬件门槛
5. 对话式调整：多轮交互（最多20轮），会话持久化（3天有效期），支持消息管理和批量删除
6. Paste Back技术：融合生成结果与原图，防止脸部和背景模糊
7. 批量试穿优化：按服装层次顺序生成，确保穿搭自然合理

## 参考文献

- CatVTON: Concatenation Is All You Need for Virtual Try-On with Diffusion Models (ICLR 2025)
- CLIP: Learning Transferable Visual Models From Natural Language Supervision
- Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks

## 源码概览

本项目作为一个全栈 AI 应用，集成了多模态理解、向量检索与扩散模型生成等前沿技术。

### 1. 后端业务架构与多模态 RAG 引擎

后端基于 FastAPI 构建，其核心挑战在于如何将非结构化的用户需求转化为结构化的穿搭建议。我们实现了一套基于检索增强生成（RAG）的推荐流水线。

在处理推荐请求时，系统首先通过 OpenWeatherMap 接口获取气温、湿度、降雨概率等维度数据。后端逻辑会根据气温计算体感指数，并动态构建检索 Query。为了避免传统关键词匹配的局限性，我们引入了"分类平衡检索策略"：系统会分别在内层、中层、外层、下装等 7 个独立向量簇中执行相似度搜索,确保生成的候选集涵盖一套完整穿搭的所有组件。

在多轮对话中，我们实现了复杂的上下文注入机制。系统会将当前的穿搭方案 ID、最近三轮的对话历史以及过滤后的衣橱元数据整合进 Prompt，调用 Qwen3-VL 模型进行逻辑推理，从而实现类似"把这件外套换成更保暖的"这种具备语义理解能力的反馈调整。

**核心代码导读：**
*   **推荐与检索策略**：[backend/app/routes/recommendation.py](file:///C:/Users/22232/Desktop/fashion-recommendation/backend/app/routes/recommendation.py) 中的 `get_outfit_recommendations` 函数。重点关注其如何根据天气构建 query 并调用 `embedding_service` 进行多类别检索。
*   **会话状态机**：[backend/app/services/conversation_manager.py](file:///C:/Users/22232/Desktop/fashion-recommendation/backend/app/services/conversation_manager.py) 负责处理基于 SQLAlchemy 的 JSON 字段更新（使用了 flag_modified 机制确保数据库同步），支持多轮对话状态的持久化。
*   **推荐逻辑编排**：[backend/app/services/recommendation_service.py](file:///C:/Users/22232/Desktop/fashion-recommendation/backend/app/services/recommendation_service.py) 封装了 LLM 的调用逻辑与结果解析，具备完善的降级处理机制。

### 2. 机器学习与视觉推理流水线

图像处理部分是本项目的核心技术亮点，主要分为视觉标注服务与虚拟试衣（VTON）服务。

在衣物识别上，我们通过 Qwen3-VL 实现了高精度的自动打标。模型不仅识别颜色和材质，更重要的是通过我们设计的"决策树 Prompt"识别衣物的物理属性（如厚度、袖长、结构），这直接决定了推荐算法中的分层逻辑。

在虚拟试衣环节，我们部署了基于扩散模型的 CatVTON 推理服务。为了实现"工业级"的视觉效果，我们设计了三阶段流水线：
1. 自动化掩码生成：利用 DensePose 进行人体姿态估计，配合 SCHP 进行语义分割，自动生成目标衣物区域的 Mask，无需人工抠图。
2. 顺序迭代推理：支持批量试衣，系统会根据预设的物理优先级（内层 -> 中层 -> 外层 -> 下装）依次进行多次扩散推理，模拟真实的穿衣过程。
3. 图像融合优化：在推理层采用了 Paste Back 技术。由于扩散模型在 768x1024 分辨率下可能导致非重绘区域细节丢失，我们利用原始掩码执行图像合成（Composite），将生成的衣服精准嵌入原图，从而完美保留用户照片的面部特征和背景细节。

**核心代码导读：**
*   **视觉标注流水线**：[ml/inference.py](file:///C:/Users/22232/Desktop/fashion-recommendation/ml/inference.py) 中的 `analyze_clothing_image` 方法，展示了如何通过结构化 Prompt 引导多模态模型输出符合业务逻辑的 JSON 数据。
*   **试衣服务器实现**：[ml/vton_server.py](file:///C:/Users/22232/Desktop/fashion-recommendation/ml/vton_server.py) 是试衣功能的核心。重点关注 `process_tryon` 函数中的 AutoMasker 初始化、推理参数设置以及最后的 `Image.composite` 融合逻辑。
*   **模型单例管理**：在 [ml/inference.py](file:///C:/Users/22232/Desktop/fashion-recommendation/ml/inference.py) 中通过线程安全的单例模式加载大模型，确保了在高并发请求下的显存稳定。

### 3. 前端工程化与状态同步

前端采用 React 19 和 Vite 构建，核心难点在于处理模型推理的长时间异步状态以及海量图片的实时渲染。

我们设计了一套"ID-Metadata 映射机制"。后端在对话中仅传输轻量化的衣物 ID 数组，前端通过维护全局的 `items_map` 将 ID 实时关联到本地缓存或云端 URL。这种解耦设计极大地减少了网络带宽消耗，并提升了 UI 渲染的鲁棒性。

**核心代码导读：**
*   **多轮对话交互**：[frontend/src/pages/Conversation.jsx](file:///C:/Users/22232/Desktop/fashion-recommendation/frontend/src/pages/Conversation.jsx) 实现了对话流的动态展示，通过自定义 Hook 管理对话状态与衣物预览的联动。
*   **异步文件处理**：[frontend/src/pages/Wardrobe.jsx](file:///C:/Users/22232/Desktop/fashion-recommendation/frontend/src/pages/Wardrobe.jsx) 封装了文件上传与后端标注接口的调用流。

### 4. 数据建模与工程支撑

系统采用 SQLite 作为存储介质，通过 SQLAlchemy ORM 实现了优雅的数据访问层。

数据库 Schema 设计充分考虑了扩展性：`WardrobeItem` 表存储了详尽的视觉特征，`ConversationSession` 表则通过 JSONB 字段存储动态的对话树。这种设计能够适应未来增加更多穿搭约束或历史行为分析的需求。

**核心代码导读：**
*   **ORM 模型设计**：[backend/app/models/](file:///C:/Users/22232/Desktop/fashion-recommendation/backend/app/models/) 目录。可以观察 `User`、`WardrobeItem` 和 `ConversationSession` 之间的外键关联与逻辑设计。
*   **环境与任务管理**：[backend/app/main.py](file:///C:/Users/22232/Desktop/fashion-recommendation/backend/app/main.py) 配置了跨域中间件（CORS）以及 APScheduler 异步任务，用于定期清理过期的临时文件与会话数据。
