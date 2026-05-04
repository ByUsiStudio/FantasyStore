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

**请求参数**: 无

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "token": "a1b2c3d4e5f67890abcdef1234567890",
        "oauth_url": "https://www.cdifit.cn/session/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&scope=xxx&state=xxx"
    }
}
```

### 1.2 OAuth登录

**请求方式**: POST

**URL**: `/api/oauth/login`

**Content-Type**: `application/x-www-form-urlencoded`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | OAuth授权码 |

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
            "role": "user"
        }
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
| avatar | string | 否 | 头像URL |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "username": "newusername",
        "email": "new@example.com",
        "avatar": "/uploads/avatars/xxx.jpg"
    }
}
```

---

## 三、文件上传

### 3.1 上传图片

**请求方式**: POST

**URL**: `/api/upload/image`

**Content-Type**: `multipart/form-data`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 图片文件（jpg/png/gif/webp） |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "url": "/apps/xxx.jpg",
        "filename": "abc123.jpg",
        "hash": "md5hash",
        "size": 102400
    }
}
```

### 3.2 上传应用文件

**请求方式**: POST

**URL**: `/api/upload/app`

**Content-Type**: `multipart/form-data`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 应用文件（apk/ipa/exe/dmg/zip） |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "url": "/apps/abc123.apk",
        "filename": "abc123.apk",
        "original_name": "myapp.apk",
        "size": 10485760,
        "hash": "md5hash"
    }
}
```

---

## 四、应用管理

### 4.1 创建应用

**请求方式**: POST

**URL**: `/api/apps/create`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 应用名称，1-100字符 |
| description | string | 是 | 应用描述，至少10字符 |
| category | string | 是 | 分类（工具/游戏/社交等） |
| cover_image | string | 否 | 封面图URL |
| screenshots | string | 否 | 截图URL数组的JSON字符串 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "name": "我的应用",
        "description": "这是一个很棒的应用",
        "category": "工具",
        "cover_image": "/apps/cover.jpg",
        "screenshots": ["/apps/s1.jpg", "/apps/s2.jpg"],
        "status": "pending",
        "created_at": "2026-01-01T00:00:00"
    }
}
```

### 4.2 获取应用列表

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
            "category": "工具",
            "cover_image": "/apps/cover.jpg",
            "status": "approved",
            "total_downloads": 1234,
            "average_rating": 4.5,
            "review_count": 89,
            "developer_name": "zhangsan",
            "created_at": "2026-01-01T00:00:00"
        }
    ],
    "total": 50
}
```

### 4.3 获取应用详情

**请求方式**: POST

**URL**: `/api/apps/{app_id}`

**请求头**: `Authorization: Bearer {access_token}` (可选)

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| app_id | int | 应用ID |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "name": "我的应用",
        "description": "这是一个很棒的应用",
        "category": "工具",
        "cover_image": "/apps/cover.jpg",
        "screenshots": ["/apps/s1.jpg", "/apps/s2.jpg"],
        "status": "approved",
        "total_downloads": 1234,
        "total_views": 5678,
        "average_rating": 4.5,
        "review_count": 89,
        "developer_id": 1,
        "developer_name": "zhangsan",
        "created_at": "2026-01-01T00:00:00",
        "published_at": "2026-01-02T00:00:00",
        "current_version": {
            "id": 3,
            "version": "2.0.0",
            "version_code": 200,
            "release_notes": "修复bug，添加新功能",
            "changelog_html": "<h1>更新日志</h1><p>...</p>",
            "file_size": "10MB",
            "download_count": 500,
            "is_current": true
        },
        "versions": [
            {
                "id": 1,
                "version": "1.0.0",
                "version_code": 100,
                "release_notes": "首次发布",
                "changelog_html": "<p>首次发布</p>",
                "file_size": "8MB",
                "download_count": 734,
                "is_current": false,
                "created_at": "2026-01-01T00:00:00"
            }
        ]
    }
}
```

### 4.4 更新应用信息

**请求方式**: POST

**URL**: `/api/apps/{app_id}/update`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| app_id | int | 应用ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 应用名称 |
| description | string | 否 | 应用描述 |
| category | string | 否 | 分类 |
| cover_image | string | 否 | 封面图URL |
| screenshots | string | 否 | 截图URL数组的JSON字符串 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 1,
        "name": "更新后的应用名",
        "description": "更新后的描述",
        "category": "游戏",
        "cover_image": "/apps/new_cover.jpg",
        "screenshots": ["/apps/s1.jpg"]
    }
}
```

---

## 五、版本管理

### 5.1 添加应用版本

**请求方式**: POST

**URL**: `/api/apps/{app_id}/version/add`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| app_id | int | 应用ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | 是 | 版本号，如1.0.0 |
| version_code | int | 是 | 版本代码，数字越大版本越新 |
| download_url | string | 是 | 文件下载URL（WebDAV路径） |
| file_name | string | 是 | 文件名 |
| file_size | string | 是 | 文件大小 |
| release_notes | string | 否 | 发布说明 |
| changelog_md | string | 否 | 更新日志（Markdown格式） |
| is_current | bool | 否 | 是否设为当前版本，默认false |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 5,
        "version": "2.0.0",
        "version_code": 200,
        "release_notes": "重大更新",
        "changelog_html": "<h1>重大更新</h1><ul><li>新功能A</li></ul>",
        "status": "approved",
        "is_current": true,
        "created_at": "2026-01-10T00:00:00"
    }
}
```

### 5.2 更新版本更新日志

**请求方式**: POST

**URL**: `/api/versions/{version_id}/changelog`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| version_id | int | 版本ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| changelog_md | string | 是 | 更新日志（Markdown格式） |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "changelog_html": "<h1>更新内容</h1><p>...</p>",
        "changelog_md": "# 更新内容\n\n..."
    }
}
```

### 5.3 下载版本

**请求方式**: POST

**URL**: `/api/versions/{version_id}/download`

**请求头**: `Authorization: Bearer {access_token}` (可选)

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| version_id | int | 版本ID |

**响应**: 文件流（application/octet-stream）

---

## 六、评论系统

### 6.1 添加评论

**请求方式**: POST

**URL**: `/api/apps/{app_id}/review/add`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| app_id | int | 应用ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| rating | int | 是 | 评分，1-5分 |
| title | string | 否 | 标题，最多200字符 |
| content | string | 否 | 内容，最多1000字符 |
| device_model | string | 否 | 设备型号 |
| device_os | string | 否 | 系统版本 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 10,
        "rating": 5,
        "title": "非常好用",
        "content": "这个应用太棒了",
        "like_count": 0,
        "created_at": "2026-01-10T00:00:00"
    }
}
```

### 6.2 获取应用评论列表

**请求方式**: POST

**URL**: `/api/apps/{app_id}/reviews`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | int | 否 | 跳过数量，默认0 |
| limit | int | 否 | 返回数量，默认100 |

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {
            "id": 10,
            "rating": 5,
            "title": "非常好用",
            "content": "这个应用太棒了",
            "version": "2.0.0",
            "device_model": "iPhone 14",
            "device_os": "iOS 17",
            "like_count": 15,
            "user_id": 2,
            "username": "lisi",
            "user_avatar": "/avatars/lisi.jpg",
            "created_at": "2026-01-10T00:00:00",
            "replies": [
                {
                    "id": 1,
                    "user_id": 1,
                    "username": "zhangsan",
                    "user_avatar": "/avatars/zhangsan.jpg",
                    "content": "感谢支持！",
                    "created_at": "2026-01-10T01:00:00"
                }
            ]
        }
    ],
    "total": 89
}
```

### 6.3 点赞评论

**请求方式**: POST

**URL**: `/api/reviews/{review_id}/like`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| review_id | int | 评论ID |

**响应示例**:
```json
{
    "code": 200,
    "message": "Liked"
}
```

### 6.4 取消点赞

**请求方式**: POST

**URL**: `/api/reviews/{review_id}/unlike`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| review_id | int | 评论ID |

**响应示例**:
```json
{
    "code": 200,
    "message": "Unliked"
}
```

### 6.5 检查是否已点赞

**请求方式**: POST

**URL**: `/api/reviews/{review_id}/liked`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| review_id | int | 评论ID |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "liked": true
    }
}
```

### 6.6 回复评论

**请求方式**: POST

**URL**: `/api/reviews/{review_id}/reply/add`

**Content-Type**: `application/x-www-form-urlencoded`

**请求头**: `Authorization: Bearer {access_token}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| review_id | int | 评论ID |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 回复内容 |

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "id": 5,
        "user_id": 1,
        "username": "zhangsan",
        "user_avatar": "/avatars/zhangsan.jpg",
        "content": "谢谢你的建议！",
        "created_at": "2026-01-10T02:00:00"
    }
}
```

### 6.7 获取评论回复列表

**请求方式**: POST

**URL**: `/api/reviews/{review_id}/replies`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | int | 否 | 跳过数量，默认0 |
| limit | int | 否 | 返回数量，默认100 |

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "user_id": 1,
            "username": "zhangsan",
            "user_avatar": "/avatars/zhangsan.jpg",
            "content": "感谢反馈！",
            "created_at": "2026-01-10T01:00:00"
        }
    ],
    "total": 5
}
```

---

## 七、我的内容

### 7.1 获取我的应用列表

**请求方式**: POST

**URL**: `/api/my/apps`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | int | 否 | 跳过数量，默认0 |
| limit | int | 否 | 返回数量，默认100 |

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {
            "id": 1,
            "name": "我的应用",
            "category": "工具",
            "status": "approved",
            "is_approved": true,
            "total_downloads": 1234,
            "average_rating": 4.5,
            "review_count": 89,
            "created_at": "2026-01-01T00:00:00"
        }
    ],
    "total": 10
}
```

### 7.2 获取我的评论列表

**请求方式**: POST

**URL**: `/api/my/reviews`

**请求头**: `Authorization: Bearer {access_token}`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | int | 否 | 跳过数量，默认0 |
| limit | int | 否 | 返回数量，默认100 |

**响应示例**:
```json
{
    "code": 200,
    "data": [
        {
            "id": 10,
            "app_id": 1,
            "app_name": "我的应用",
            "rating": 5,
            "title": "非常好用",
            "content": "这个应用太棒了",
            "like_count": 15,
            "created_at": "2026-01-10T00:00:00"
        }
    ],
    "total": 5
}
```

---

## 八、其他

### 8.1 获取分类列表

**请求方式**: POST

**URL**: `/api/categories`

**响应示例**:
```json
{
    "code": 200,
    "data": ["工具", "游戏", "社交", "娱乐", "教育", "办公", "摄影", "音乐", "阅读", "购物", "生活", "健康"]
}
```

---

## 九、后台管理API

后台管理API需要添加请求头 `X-Admin-Password: QQ@gxshg2e3i4T5f`

### 9.1 获取统计信息

**请求方式**: POST

**URL**: `/admin/api/statistics`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

**响应示例**:
```json
{
    "code": 200,
    "data": {
        "apps": {
            "total": 100,
            "pending": 5,
            "approved": 90
        },
        "versions": {
            "total": 200,
            "pending": 10
        },
        "reviews": {
            "total": 500
        },
        "users": {
            "total": 50,
            "new_last_7_days": 10
        },
        "downloads": {
            "total": 10000,
            "last_7_days": 500,
            "daily": [
                {"date": "2026-01-10", "downloads": 100},
                {"date": "2026-01-09", "downloads": 80}
            ]
        }
    }
}
```

### 9.2 获取应用列表（管理）

**请求方式**: POST

**URL**: `/admin/api/apps`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | int | 否 | 跳过数量 |
| limit | int | 否 | 返回数量 |
| status | string | 否 | 状态过滤（pending/approved/rejected/removed/all） |

### 9.3 审核应用

**请求方式**: POST

**URL**: `/admin/api/apps/{app_id}/approve`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

### 9.4 拒绝应用

**请求方式**: POST

**URL**: `/admin/api/apps/{app_id}/reject`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| reason | string | 否 | 拒绝原因 |

### 9.5 获取待审核版本

**请求方式**: POST

**URL**: `/admin/api/versions/pending`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

### 9.6 审核版本

**请求方式**: POST

**URL**: `/admin/api/versions/{version_id}/approve`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| set_as_current | bool | 否 | 是否设为当前版本 |

### 9.7 获取评论列表（管理）

**请求方式**: POST

**URL**: `/admin/api/reviews`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

### 9.8 隐藏评论

**请求方式**: POST

**URL**: `/admin/api/reviews/{review_id}/hide`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

### 9.9 获取用户列表

**请求方式**: POST

**URL**: `/admin/api/users`

**请求头**: `X-Admin-Password: QQ@gxshg2e3i4T5f`

---

## 十、状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证/Token无效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 十一、应用状态说明

| 状态 | 说明 |
|------|------|
| pending | 待审核 |
| approved | 已通过 |
| rejected | 已拒绝 |
| removed | 已下架 |

## 十二、版本状态说明

| 状态 | 说明 |
|------|------|
| pending | 待审核 |
| approved | 已通过 |
| rejected | 已拒绝 |
| active | 当前活跃版本 |
| deprecated | 已废弃 |

## 十三、评论状态说明

| 状态 | 说明 |
|------|------|
| approved | 已通过 |
| hidden | 已隐藏 |

## 十四、用户角色说明

| 角色 | 说明 |
|------|------|
| user | 普通用户 |
| admin | 管理员 |

---

## 十五、使用流程示例

### 完整应用发布流程

1. **用户登录**
   ```http
   POST /api/oauth/url
   POST /api/oauth/login (带上授权码)
   ```

2. **上传应用文件**
   ```http
   POST /api/upload/app (带apk文件)
   ```

3. **创建应用**
   ```http
   POST /api/apps/create
   ```

4. **添加版本**
   ```http
   POST /api/apps/1/version/add
   ```

5. **管理员审核应用**
   ```
   POST /admin/api/apps/1/approve (带管理员密码)
   ```

6. **用户下载应用**
   ```http
   POST /api/versions/1/download
   ```

7. **用户评论**
   ```
   POST /api/apps/1/review/add
   ```

8. **用户点赞评论**
   ```http
   POST /api/reviews/10/like
   ```

9. **用户回复评论**
   ```http
   POST /api/reviews/10/reply/add
   ```

10. **更新应用版本**
    ```http
    POST /api/apps/1/version/add (新版本)
    ```

**注意**: 应用首次审核通过后，后续添加的版本将自动通过审核，无需再次审核。