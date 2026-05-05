# 应用市场API完整文档

## 基本信息

- **Base URL**: `http://0.0.0.0:56320`
- **认证方式**: Bearer Token (JWT)
- **请求方式**: 仅支持 GET 和 POST
- **返回格式**: JSON

## 通用响应格式

```json
{
    "code": 200,
    "message": "success",
    "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，200成功，其他失败 |
| message | string | 消息说明 |
| data | object/array | 返回数据 |

---

## 一、认证相关

### 1.1 获取OAuth授权URL

**请求方式**: POST

**URL**: `/api/oauth/url`

**Content-Type**: `application/x-www-form-urlencoded`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| redirect_uri | string | 是 | 回调地址，必须在允许的白名单中 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "token": "a1b2c3d4e5f67890abcdef1234567890",
        "oauth_url": "https://www.cdifit.cn/session/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&scope=xxx&state=xxx&code_challenge=xxx&code_challenge_method=S256"
    }
}
```

**允许的回调地址**:
- `https://games.cdifit.cn/oauth.php`
- `https://your-app.com/callback`
- `http://localhost:3000/callback`

### 1.2 OAuth登录

**请求方式**: POST

**URL**: `/api/oauth/login`

**Content-Type**: `application/x-www-form-urlencoded`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | OAuth授权码 |
| token | string | 是 | 获取授权URL时返回的token |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": "zhangsan",
            "email": "zhangsan@example.com",
            "avatar": "/uploads/avatars/xxx.jpg",
            "role": "user",
            "created_at": "2026-01-01T00:00:00"
        }
    }
}
```

### 1.3 刷新访问令牌

**请求方式**: POST

**URL**: `/api/oauth/refresh`

**Content-Type**: `application/x-www-form-urlencoded`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
    }
}
```

---

## 二、用户相关

### 2.1 获取当前用户信息

**请求方式**: POST

**URL**: `/api/me`

**请求头**: `Authorization: Bearer {access_token}`

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "username": "zhangsan",
        "email": "zhangsan@example.com",
        "avatar": "/uploads/avatars/xxx.jpg",
        "role": "user",
        "created_at": "2026-01-01T00:00:00"
    }
}
```

### 2.2 更新用户信息

**请求方式**: POST

**URL**: `/api/me/update`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 用户名，3-50字符 |
| email | string | 否 | 邮箱 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "username": "newusername",
        "email": "new@example.com",
        "avatar": "/uploads/avatars/xxx.jpg",
        "role": "user"
    }
}
```

---

## 三、应用管理

### 3.1 获取应用列表

**请求方式**: POST

**URL**: `/api/apps/list`

**请求头**: `Authorization: Bearer {access_token}` (可选)

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | int | 否 | 跳过数量，默认0 |
| limit | int | 否 | 返回数量，默认100 |
| category | string | 否 | 分类筛选 |
| search | string | 否 | 搜索关键词 |

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "name": "我的应用",
            "description": "这是一个很棒的应用...",
            "icon": "/apps/icon.png",
            "category": "工具",
            "status": "approved",
            "download_count": 1234,
            "current_version": "2.0.0",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-10T00:00:00"
        }
    ],
    "total": 50
}
```

### 3.2 获取应用详情

**请求方式**: POST

**URL**: `/api/apps/detail`

**请求头**: `Authorization: Bearer {access_token}` (可选)

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| app_id | int | 是 | 应用ID |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "name": "我的应用",
        "description": "这是一个很棒的应用",
        "icon": "/apps/icon.png",
        "category": "工具",
        "status": "approved",
        "download_count": 1234,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-10T00:00:00",
        "current_version": {
            "id": 3,
            "version": "2.0.0",
            "changelog": "修复bug，添加新功能",
            "download_url": "/apps/app_v2.apk",
            "file_size": "10MB",
            "released_at": "2026-01-10T00:00:00"
        },
        "reviews": [
            {
                "id": 1,
                "user_id": 2,
                "username": "lisi",
                "rating": 5,
                "content": "很好用！",
                "created_at": "2026-01-05T00:00:00",
                "likes": 10,
                "replies": []
            }
        ],
        "review_count": 89,
        "avg_rating": 4.5,
        "is_purchased": true
    }
}
```

### 3.3 下载应用

**请求方式**: POST

**URL**: `/api/apps/download`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| app_id | int | 是 | 应用ID |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "download_url": "https://webdav.example.com/apps/app_v2.apk",
        "app_id": 1,
        "version_id": 3,
        "version": "2.0.0"
    }
}
```

---

## 四、评论系统

### 4.1 获取应用评论

**请求方式**: POST

**URL**: `/api/apps/reviews`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| app_id | int | 是 | 应用ID |
| skip | int | 否 | 跳过数量，默认0 |
| limit | int | 否 | 返回数量，默认50 |

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "user_id": 2,
            "username": "lisi",
            "rating": 5,
            "content": "很好用！",
            "created_at": "2026-01-05T00:00:00",
            "likes": 10,
            "replies": [
                {
                    "id": 1,
                    "user_id": 1,
                    "username": "zhangsan",
                    "content": "谢谢支持！",
                    "created_at": "2026-01-06T00:00:00"
                }
            ]
        }
    ],
    "total": 89
}
```

### 4.2 添加评论

**请求方式**: POST

**URL**: `/api/apps/review`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| app_id | int | 是 | 应用ID |
| rating | int | 是 | 评分，1-5 |
| content | string | 否 | 评论内容 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 90,
        "rating": 5,
        "content": "非常棒！",
        "created_at": "2026-01-15T00:00:00"
    }
}
```

### 4.3 更新评论

**请求方式**: POST

**URL**: `/api/apps/review/update`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| review_id | int | 是 | 评论ID |
| rating | int | 否 | 评分，1-5 |
| content | string | 否 | 评论内容 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "message": "Review updated"
    }
}
```

### 4.4 删除评论

**请求方式**: POST

**URL**: `/api/apps/review/delete`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| review_id | int | 是 | 评论ID |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "message": "Review deleted"
    }
}
```

### 4.5 点赞评论

**请求方式**: POST

**URL**: `/api/apps/review/like`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| review_id | int | 是 | 评论ID |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "message": "Like toggled"
    }
}
```

### 4.6 回复评论

**请求方式**: POST

**URL**: `/api/apps/review/reply`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| review_id | int | 是 | 评论ID |
| content | string | 是 | 回复内容 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 5,
        "content": "感谢您的反馈！",
        "created_at": "2026-01-16T00:00:00"
    }
}
```

---

## 五、分类列表

### 5.1 获取分类列表

**请求方式**: POST

**URL**: `/api/categories`

**请求参数**: 无

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {"id": "tool", "name": "工具"},
        {"id": "game", "name": "游戏"},
        {"id": "social", "name": "社交"},
        {"id": "productivity", "name": "生产力"}
    ]
}
```

---

## 六、错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权或Token无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |