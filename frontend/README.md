# Fashion Recommendation System - 前端

基于 React 的时尚推荐系统前端。

## 功能特性

1. **用户认证** - 登录和注册页面
2. **我的衣橱** - 查看、上传和管理衣物
3. **获取推荐** - 基于天气和衣橱的 AI 穿搭推荐
4. **对话调整** - 多轮对话优化穿搭方案（独立界面）
5. **个人资料** - 查看和修改用户信息

## 技术栈

- **React 19** - UI 框架
- **React Router** - 客户端路由
- **Axios** - HTTP 客户端，用于 API 通信
- **Vite** - 构建工具和开发服务器

## 快速开始

### 前置要求

- 已安装 Node.js 16+
- 后端服务运行在 `http://localhost:6008`

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 `http://localhost:6006` 访问

### 生产构建

```bash
npm run build
```

## 项目结构

```
src/
├── pages/           # 页面组件
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Wardrobe.jsx
│   ├── Recommendations.jsx
│   ├── Conversation.jsx
│   ├── Profile.jsx
│   ├── Auth.css
│   ├── Wardrobe.css
│   ├── Recommendations.css
│   ├── Conversation.css
│   └── Profile.css
├── services/        # API 服务层
│   └── api.js
├── App.jsx          # 主应用组件（包含路由）
├── App.css          # 应用级样式
├── main.jsx         # 入口文件
└── index.css        # 全局样式
```

## API 集成

前端通过 `http://localhost:6008/api/v1` 连接后端 API。API 调用通过 `services/api.js` 模块处理。

### 可用的 API 函数

#### 用户认证
- `registerUser(userData)` - 注册新用户
- `loginUser(username, password)` - 用户登录
- `getUserProfile(userId)` - 获取用户个人信息
- `updateUserProfile(userId, updateData)` - 更新用户信息

#### 衣橱管理
- `uploadClothingItem(userId, formData)` - 上传单件衣物
- `uploadClothingBatch(userId, formData)` - 批量上传衣物
- `getUserWardrobe(userId)` - 获取用户衣橱
- `deleteClothingItem(itemId)` - 删除单件衣物
- `deleteClothingBatch(itemIds)` - 批量删除衣物
- `getUploadStatus(userId)` - 获取上传状态

#### 推荐功能
- `getOutfitRecommendations(userId, preferences)` - 获取穿搭推荐
- `selectOutfit(sessionId, outfitIndex, outfitData, userId)` - 选择方案（跳转到对话调整）

#### 对话调整
- `adjustOutfit(sessionId, adjustmentRequest, userId)` - 多轮对话调整
- `getUserSessions(userId, limit, offset)` - 获取会话列表
- `getSessionDetail(sessionId, userId)` - 获取会话详情
- `deleteConversationMessage(sessionId, messageIndex, userId)` - 删除消息
- `deleteSession(sessionId, userId)` - 删除会话
- `deleteAllSessions(userId)` - 删除所有会话

#### 虚拟试衣
- `virtualTryOn(personImgBlob, clothImgBlob, category)` - 虚拟试衣
- `fetchImageAsBlob(url)` - 获取图片Blob

## 用户流程

1. **注册/登录** - 创建账户或使用现有凭据登录
2. **添加物品** - 上传衣物图片来构建你的衣橱（支持批量上传）
3. **查看衣橱** - 浏览所有衣物，包括分类、颜色和季节
4. **获取推荐** - 接收个性化穿搭建议
5. **自定义** - 按场合、风格和颜色偏好筛选推荐
6. **选择方案** - 点击「选择这组」进入对话调整界面
7. **对话调整** - 通过多轮对话优化穿搭方案（"换外套"、"更暖色系"）
8. **虚拟试衣** - 在推荐或对话界面预览上身效果

## 详细功能

### 用户认证
- 简单的用户名/密码认证
- 用户数据存储在 localStorage
- 路由保护（未登录则重定向到登录页）

### 衣橱管理
- 上传衣物图片
- 自动图像分析（通过后端 ML 模型）
- 响应式网格布局显示物品
- 删除不需要的物品

### 推荐功能
- 基于用户城市的天气感知建议
- 从衣橱物品中组合穿搭（使用向量检索智能筛选）
- 缺失物品分析
- 可自定义筛选：
  - 场合（日常、通勤、商务、正式、聚会、约会、旅行、户外、居家）
  - 风格（经典、现代、极简、优雅、休闲、街头、潮流、复古、运动、学院）
  - 色调（中性色调、暖色调、冷色调）
  - 特殊要求（自定义文本）
- 一键重新生成
- 选择方案后跳转到对话调整界面

### 对话调整功能（独立界面）
- 多轮对话优化穿搭方案
- 自然语言交互（"换个外套"、"更暖色系"、"不要红色"）
- 对话历史记录（最多20轮）
- 消息成对删除（用户+AI响应）
- 会话持久化（3天有效期）
- 重置对话并返回推荐界面

### 个人资料
- 查看和编辑用户信息（年龄、身高、体重、城市等）
- 上传个人照片（用于虚拟试衣）

## 注意事项

- 认证较为基础（尚未使用 JWT token）
- 图片由后端服务 `http://localhost:6008/uploads/`
- 用户会话通过 localStorage 持久化
- 响应式设计，支持移动端和桌面端

## 未来增强

- [ ] 基于 JWT 的认证
- [ ] 穿搭收藏/保存功能
- [ ] 穿搭社交分享
- [ ] 衣橱高级筛选和搜索
- [ ] 穿搭历史/日历
- [ ] 会话分享功能
- [ ] 语音对话调整
