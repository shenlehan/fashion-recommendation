# Fashion Recommendation System - 前端

基于 React 的时尚推荐系统前端。

## 功能特性

1. **用户认证** - 登录和注册页面
2. **我的衣橱** - 查看、上传和管理衣物
3. **获取推荐** - 基于天气和衣橱的 AI 穿搭推荐
4. **自定义推荐** - 根据用户偏好重新生成推荐

## 技术栈

- **React 19** - UI 框架
- **React Router** - 客户端路由
- **Axios** - HTTP 客户端，用于 API 通信
- **Vite** - 构建工具和开发服务器

## 快速开始

### 前置要求

- 已安装 Node.js 16+
- 后端服务运行在 `http://localhost:8000`

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 `http://localhost:3000` 访问

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
│   ├── Auth.css
│   ├── Wardrobe.css
│   └── Recommendations.css
├── services/        # API 服务层
│   └── api.js
├── App.jsx          # 主应用组件（包含路由）
├── App.css          # 应用级样式
├── main.jsx         # 入口文件
└── index.css        # 全局样式
```

## API 集成

前端通过 `http://localhost:8000/api/v1` 连接后端 API。API 调用通过 `services/api.js` 模块处理。

### 可用的 API 函数

- `registerUser(userData)` - 注册新用户
- `loginUser(username, password)` - 用户登录
- `getUserProfile(userId)` - 获取用户个人信息
- `uploadClothingItem(userId, formData)` - 上传衣物图片
- `getUserWardrobe(userId)` - 获取用户衣橱
- `deleteClothingItem(itemId)` - 删除衣橱物品
- `getOutfitRecommendations(userId, preferences)` - 获取穿搭推荐

## 用户流程

1. **注册/登录** - 创建账户或使用现有凭据登录
2. **添加物品** - 上传衣物图片来构建你的衣橱
3. **查看衣橱** - 浏览所有衣物，包括分类、颜色和季节
4. **获取推荐** - 接收个性化穿搭建议
5. **自定义** - 按场合、风格和颜色偏好筛选推荐
6. **重新生成** - 根据你的反馈获取新建议

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
- 从衣橱物品中组合穿搭
- 缺失物品分析
- 可自定义筛选：
  - 场合（休闲、商务、正式、运动、聚会）
  - 风格（经典、潮流、极简、波希米亚、街头）
  - 颜色偏好
- 一键重新生成

## 注意事项

- 认证较为基础（尚未使用 JWT token）
- 图片由后端服务 `http://localhost:8000/uploads/`
- 用户会话通过 localStorage 持久化
- 响应式设计，支持移动端和桌面端

## 未来增强

- [ ] 基于 JWT 的认证
- [ ] 个人信息页面，用于更新用户信息
- [ ] 穿搭收藏/保存功能
- [ ] 穿搭社交分享
- [ ] 高级筛选和搜索
- [ ] 穿搭历史/日历
