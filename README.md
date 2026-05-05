# FantasyStore

FantasyStore 是一个基于 FastAPI 构建的应用商店平台，支持应用的发布、版本管理、用户评价等功能。
> 使用DeepSeek配合Builder开发本应用市场api

## 项目简介

FantasyStore 为开发者提供了一个完整的应用分发和管理系统，支持 OAuth 第三方登录、应用审核、版本管理、用户评价等功能。系统采用前后端分离架构，前端使用原生 HTML/CSS/JavaScript 构建的管理后台。

- [**API文档**](API_DOCS.MD)

## 技术栈

- **后端**: FastAPI (Python)
- **数据库**: SQLAlchemy ORM
- **认证**: JWT + OAuth (Cdifit)
- **存储**: WebDAV 文件存储
- **前端**: 原生 HTML + CSS + JavaScript

## 主要功能

### 用户功能
- OAuth 第三方登录
- 查看和搜索应用
- 下载应用及版本记录
- 提交应用评价（1-5星评分）
- 为评价点赞/回复
- 管理个人资料

### 开发者功能
- 创建和发布应用
- 上传应用截图和封面
- 管理应用版本
- 更新应用信息和变更日志
- 查看个人应用和评价

### 管理员功能
- 审核待批准的应用
- 管理应用版本
- 查看和隐藏用户评价
- 查看平台统计数据
- 用户管理

## 项目结构

```
src/
├── main.py           # 主 API 入口
├── admin.py         # 管理员 API
├── auth.py          # 认证和 OAuth
├── crud.py          # 数据库操作
├── models.py        # 数据模型
├── database.py      # 数据库配置
├── markdown.py     # Markdown 转换
├── webdav_client.py # WebDAV 文件客户端
├── static/         # 静态文件
│   ├── admin.html
│   ├── admin.css
│   └── admin.js
├── config.json     # JSON 配置
├── config.toml    # TOML 配置
└── requirements.txt # 依赖列表
```

## 数据模型

- **User**: 用户（角色：普通用户/管理员）
- **App**: 应用（状态：待审核/已批准/已拒绝/已下架）
- **AppVersion**: 应用版本
- **Review**: 用户评价
- **ReviewLike**: 评价点赞
- **ReviewReply**: 评价回复
- **DownloadRecord**: 下载记录
- **AuditLog**: 审计日志

## API 端点

### 认证相关
- `POST /api/oauth/url` - 获取 OAuth 登录 URL
- `POST /api/oauth/login` - OAuth 登录回调
- `POST /api/me` - 获取当前用户信息
- `POST /api/me/update` - 更新用户资料

### 应用相关
- `POST /api/apps/create` - 创建应用
- `POST /api/apps/list` - 获取应用列表
- `GET /api/apps/{app_id}` - 获取应用详情
- `POST /api/apps/{app_id}/update` - 更新应用信息
- `POST /api/apps/{app_id}/version/add` - 添加版本
- `POST /api/my/apps` - 获取我的应用

### 评价相关
- `POST /api/apps/{app_id}/review/add` - 提交评价
- `POST /api/apps/{app_id}/reviews` - 获取评价列表
- `POST /api/reviews/{review_id}/like` - 点赞
- `POST /api/reviews/{review_id}/unlike` - 取消点赞
- `POST /api/reviews/{review_id}/reply/add` - 添加回复

### 上传相关
- `POST /api/upload/image` - 上传图片
- `POST /api/upload/app` - 上传应用文件

### 管理员
- `POST /api/admin/apps` - 获取应用列表
- `POST /api/admin/apps/{app_id}/approve` - 批准应用
- `POST /api/admin/apps/{app_id}/reject` - 拒绝应用
- `POST /api/admin/versions/pending` - 待审核版本
- `POST /api/admin/versions/{version_id}/approve` - 批准版本
- `POST /api/admin/statistics` - 统计信息

## 安装配置

### 1. 安装依赖

```bash
pip install -r src/requirements.txt
```

### 2. 配置数据库

在 `config.json` 或 `config.toml` 中配置数据库连接信息。

### 3. 配置 OAuth

在配置文件中添加 OAuth 相关配置：
- 客户端 ID
- 客户端密钥
- 回调地址

### 4. 配置存储

配置 WebDAV 存储服务用于存放应用文件和图片。

### 5. 启动服务

```bash
bash start.sh
# 或
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 使用说明

1. 访问管理后台 `/admin` 登录管理员账户
2. 通过 OAuth 登录普通用户账户
3. 开发者可以创建和管理自己的应用
4. 用户可以搜索、下载应用并提交评价
5. 管理员审核应用和评价内容

## 许可证

请查看 LICENSE 文件了解具体的许可证条款。

## 贡献者

感谢所有为该项目做出贡献的开发者。