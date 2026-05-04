from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import json
import uuid
import hashlib
import os
from datetime import timedelta, datetime

from config import Config
from database import get_db, init_db
from models import User, App, AppVersion, Review, AppStatus, VersionStatus, UserRole, ReviewStatus
from auth import (
    create_access_token, get_current_user, get_current_admin,
    init_oauth, get_oauth_client, verify_admin_password
)
from webdav_client import init_webdav_client, get_webdav_client
from markdown import markdown_to_html
from crud import (
    create_or_update_user, get_user, update_user,
    create_app, get_apps, get_app, update_app, delete_app, approve_app,
    create_app_version, get_version, get_app_versions, update_version_changelog,
    set_current_version, update_version_download_count,
    create_review, get_review, get_app_reviews, update_review, delete_review,
    like_review, unlike_review, check_user_liked_review,
    create_reply, get_review_replies, delete_reply,
    record_download, update_app_rating, get_user_review_for_app
)
from admin import router as admin_router

# 初始化
init_db()
init_oauth()
init_webdav_client()

app = FastAPI(title="App Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(admin_router)

# 静态文件
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==================== OAuth认证 ====================
@app.post("/api/oauth/url")
async def get_oauth_url():
    oauth = get_oauth_client()
    return JSONResponse(content=oauth.get_oauth_url())

@app.post("/api/oauth/login")
async def oauth_login(
    code: str = Form(...),
    db: Session = Depends(get_db)
):
    oauth = get_oauth_client()
    token_data = await oauth.exchange_code_for_token(code)
    user_info = await oauth.get_user_info(token_data['access_token'])
    
    user = create_or_update_user(db, user_info.get('id'), {
        'username': user_info.get('username') or user_info.get('name'),
        'email': user_info.get('email'),
        'avatar': user_info.get('avatar')
    })
    
    oauth.cache_user_token(user.id, token_data)
    
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value},
        expires_delta=timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "role": user.role.value
            }
        }
    })

# ==================== 用户信息 ====================
@app.post("/api/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "avatar": current_user.avatar,
            "role": current_user.role.value,
            "created_at": current_user.created_at.isoformat()
        }
    })

@app.post("/api/me/update")
async def update_current_user(
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    avatar: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_user = update_user(db, current_user.id, 
                               username=username, email=email, avatar=avatar)
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": updated_user.id,
            "username": updated_user.username,
            "email": updated_user.email,
            "avatar": updated_user.avatar
        }
    })

# ==================== 文件上传 ====================
def calculate_file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

@app.post("/api/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    file_ext = f".{file.filename.split('.')[-1].lower()}"
    if file_ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
        return JSONResponse(content={"code": 400, "message": "Image type not allowed"}, status_code=400)
    
    content = await file.read()
    file_hash = calculate_file_hash(content)
    
    filename = f"{uuid.uuid4().hex}{file_ext}"
    remote_path = f"{Config.WEBDAV_CONFIG['screenshot_path']}{filename}"
    
    file_obj = type('FileObj', (), {'read': lambda: content, 'filename': file.filename})()
    
    webdav = get_webdav_client()
    await webdav.upload_file(file_obj, remote_path)
    
    return JSONResponse(content={
        "code": 200,
        "data": {"url": remote_path, "filename": filename, "hash": file_hash, "size": len(content)}
    })

@app.post("/api/upload/app")
async def upload_app_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    file_ext = f".{file.filename.split('.')[-1].lower()}"
    if file_ext not in Config.ALLOWED_APP_EXTENSIONS:
        return JSONResponse(content={"code": 400, "message": "App file type not allowed"}, status_code=400)
    
    content = await file.read()
    file_size = len(content)
    file_hash = calculate_file_hash(content)
    
    max_size = Config.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        return JSONResponse(content={"code": 400, "message": f"File too large, max {Config.MAX_FILE_SIZE_MB}MB"}, status_code=400)
    
    filename = f"{uuid.uuid4().hex}{file_ext}"
    remote_path = f"{Config.WEBDAV_CONFIG['app_upload_path']}{filename}"
    
    file_obj = type('FileObj', (), {'read': lambda: content, 'filename': file.filename})()
    
    webdav = get_webdav_client()
    await webdav.upload_file(file_obj, remote_path)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "url": remote_path,
            "filename": filename,
            "original_name": file.filename,
            "size": file_size,
            "hash": file_hash
        }
    })

# ==================== 应用管理 ====================
@app.post("/api/apps/create")
async def create_new_app(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    cover_image: Optional[str] = Form(None),
    screenshots: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    screenshots_list = json.loads(screenshots) if screenshots else []
    
    db_app = create_app(
        db, name, description, category, current_user.id,
        cover_image=cover_image, screenshots=screenshots_list
    )
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": db_app.id,
            "name": db_app.name,
            "description": db_app.description,
            "category": db_app.category,
            "cover_image": db_app.cover_image,
            "screenshots": screenshots_list,
            "status": db_app.status.value,
            "created_at": db_app.created_at.isoformat()
        }
    })

@app.post("/api/apps/list")
async def list_apps(
    skip: int = Query(0),
    limit: int = Query(100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user or current_user.role != UserRole.ADMIN:
        status = AppStatus.APPROVED
    else:
        status = None
    
    apps = get_apps(db, skip=skip, limit=limit, status=status, 
                    category=category, search=search)
    result = []
    for app in apps:
        result.append({
            "id": app.id,
            "name": app.name,
            "description": app.description[:200],
            "category": app.category,
            "cover_image": app.cover_image,
            "status": app.status.value,
            "total_downloads": app.total_downloads,
            "average_rating": app.average_rating,
            "review_count": app.review_count,
            "developer_name": app.developer.username,
            "created_at": app.created_at.isoformat()
        })
    
    return JSONResponse(content={"code": 200, "data": result, "total": len(result)})

@app.post("/api/apps/{app_id}")
async def get_app_detail(
    app_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found"}, status_code=404)
    
    auth_header = request.headers.get("Authorization")
    current_user = None
    if auth_header:
        try:
            from auth import decode_token
            token = auth_header.replace("Bearer ", "")
            token_data = decode_token(token)
            if token_data:
                current_user = get_user(db, token_data['user_id'])
        except:
            pass
    
    if app.status != AppStatus.APPROVED and (not current_user or current_user.role != UserRole.ADMIN):
        return JSONResponse(content={"code": 403, "message": "App not available"}, status_code=403)
    
    # 增加浏览量
    app.total_views += 1
    db.commit()
    
    # 获取版本列表
    versions = get_app_versions(db, app_id, status=VersionStatus.APPROVED)
    versions_data = []
    current_version_info = None
    for version in versions:
        version_data = {
            "id": version.id,
            "version": version.version,
            "version_code": version.version_code,
            "release_notes": version.release_notes,
            "changelog_html": version.changelog_html,
            "file_size": version.file_size,
            "download_count": version.download_count,
            "is_current": version.is_current,
            "created_at": version.created_at.isoformat()
        }
        versions_data.append(version_data)
        if version.is_current:
            current_version_info = version_data
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": app.id,
            "name": app.name,
            "description": app.description,
            "category": app.category,
            "cover_image": app.cover_image,
            "screenshots": eval(app.screenshots) if app.screenshots else [],
            "status": app.status.value,
            "total_downloads": app.total_downloads,
            "total_views": app.total_views,
            "average_rating": app.average_rating,
            "review_count": app.review_count,
            "developer_id": app.developer_id,
            "developer_name": app.developer.username,
            "created_at": app.created_at.isoformat(),
            "published_at": app.published_at.isoformat() if app.published_at else None,
            "current_version": current_version_info,
            "versions": versions_data
        }
    })

@app.post("/api/apps/{app_id}/update")
async def update_app_info(
    app_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    cover_image: Optional[str] = Form(None),
    screenshots: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found"}, status_code=404)
    
    if app.developer_id != current_user.id and current_user.role != UserRole.ADMIN:
        return JSONResponse(content={"code": 403, "message": "Not authorized"}, status_code=403)
    
    screenshots_list = json.loads(screenshots) if screenshots else None
    
    updated_app = update_app(db, app_id, 
                            name=name, description=description, 
                            category=category, cover_image=cover_image,
                            screenshots=screenshots_list)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": updated_app.id,
            "name": updated_app.name,
            "description": updated_app.description,
            "category": updated_app.category,
            "cover_image": updated_app.cover_image,
            "screenshots": eval(updated_app.screenshots) if updated_app.screenshots else []
        }
    })

# ==================== 版本管理 ====================
@app.post("/api/apps/{app_id}/version/add")
async def add_app_version(
    app_id: int,
    version: str = Form(...),
    version_code: int = Form(...),
    download_url: str = Form(...),
    file_name: str = Form(...),
    file_size: str = Form(...),
    release_notes: Optional[str] = Form(None),
    changelog_md: Optional[str] = Form(None),
    is_current: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found"}, status_code=404)
    
    if app.developer_id != current_user.id and current_user.role != UserRole.ADMIN:
        return JSONResponse(content={"code": 403, "message": "Not authorized"}, status_code=403)
    
    # 转换Markdown为HTML
    changelog_html = markdown_to_html(changelog_md) if changelog_md else None
    
    try:
        db_version = create_app_version(
            db, app_id, version, version_code,
            download_url, file_name, file_size,
            current_user.id, release_notes,
            changelog_md, changelog_html, is_current
        )
    except ValueError as e:
        return JSONResponse(content={"code": 400, "message": str(e)}, status_code=400)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": db_version.id,
            "version": db_version.version,
            "version_code": db_version.version_code,
            "release_notes": db_version.release_notes,
            "changelog_html": db_version.changelog_html,
            "status": db_version.status.value,
            "is_current": db_version.is_current,
            "created_at": db_version.created_at.isoformat()
        }
    })

@app.post("/api/versions/{version_id}/changelog")
async def update_version_changelog_api(
    version_id: int,
    changelog_md: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    version = get_version(db, version_id)
    if not version:
        return JSONResponse(content={"code": 404, "message": "Version not found"}, status_code=404)
    
    app = get_app(db, version.app_id)
    if app.developer_id != current_user.id and current_user.role != UserRole.ADMIN:
        return JSONResponse(content={"code": 403, "message": "Not authorized"}, status_code=403)
    
    changelog_html = markdown_to_html(changelog_md)
    updated_version = update_version_changelog(db, version_id, changelog_md, changelog_html)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "changelog_html": updated_version.changelog_html,
            "changelog_md": updated_version.changelog_md
        }
    })

@app.post("/api/versions/{version_id}/download")
async def download_version(
    version_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    version = get_version(db, version_id)
    if not version:
        return JSONResponse(content={"code": 404, "message": "Version not found"}, status_code=404)
    
    app = get_app(db, version.app_id)
    if app.status != AppStatus.APPROVED or version.status != VersionStatus.APPROVED:
        return JSONResponse(content={"code": 403, "message": "Version not available"}, status_code=403)
    
    webdav = get_webdav_client()
    if not webdav.file_exists(version.download_url):
        return JSONResponse(content={"code": 404, "message": "File not found"}, status_code=404)
    
    file_content = webdav.download_file(version.download_url)
    
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    background_tasks.add_task(
        record_download, db, app.id, version_id,
        current_user.id if current_user else None,
        client_ip, user_agent
    )
    
    background_tasks.add_task(update_version_download_count, db, version_id)
    
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={version.file_name or 'app'}"}
    )

# ==================== 评论系统 ====================
@app.post("/api/apps/{app_id}/review/add")
async def add_review(
    app_id: int,
    rating: int = Form(..., ge=1, le=5),
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    device_model: Optional[str] = Form(None),
    device_os: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found"}, status_code=404)
    
    if app.status != AppStatus.APPROVED:
        return JSONResponse(content={"code": 400, "message": "Cannot review unapproved app"}, status_code=400)
    
    # 获取当前版本号
    current_version = None
    if app.current_version_id:
        version = get_version(db, app.current_version_id)
        if version:
            current_version = version.version
    
    db_review = create_review(
        db, app_id, rating, current_user.id,
        title=title, content=content,
        device_model=device_model, device_os=device_os,
        version=current_version
    )
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": db_review.id,
            "rating": db_review.rating,
            "title": db_review.title,
            "content": db_review.content,
            "like_count": db_review.like_count,
            "created_at": db_review.created_at.isoformat()
        }
    })

@app.post("/api/apps/{app_id}/reviews")
async def get_reviews(
    app_id: int,
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    reviews = get_app_reviews(db, app_id, skip, limit)
    result = []
    for review in reviews:
        # 获取回复
        replies = get_review_replies(db, review.id, 0, 10)
        replies_data = []
        for reply in replies:
            replies_data.append({
                "id": reply.id,
                "user_id": reply.user_id,
                "username": reply.user.username,
                "user_avatar": reply.user.avatar,
                "content": reply.content,
                "created_at": reply.created_at.isoformat()
            })
        
        result.append({
            "id": review.id,
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "version": review.version,
            "device_model": review.device_model,
            "device_os": review.device_os,
            "like_count": review.like_count,
            "user_id": review.user_id,
            "username": review.user.username,
            "user_avatar": review.user.avatar,
            "created_at": review.created_at.isoformat(),
            "replies": replies_data
        })
    
    return JSONResponse(content={"code": 200, "data": result, "total": len(result)})

@app.post("/api/reviews/{review_id}/like")
async def like_review_api(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, message = like_review(db, review_id, current_user.id)
    return JSONResponse(content={"code": 200 if success else 400, "message": message})

@app.post("/api/reviews/{review_id}/unlike")
async def unlike_review_api(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success, message = unlike_review(db, review_id, current_user.id)
    return JSONResponse(content={"code": 200 if success else 400, "message": message})

@app.post("/api/reviews/{review_id}/liked")
async def check_review_liked(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    liked = check_user_liked_review(db, review_id, current_user.id)
    return JSONResponse(content={"code": 200, "data": {"liked": liked}})

@app.post("/api/reviews/{review_id}/reply/add")
async def add_reply(
    review_id: int,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = get_review(db, review_id)
    if not review:
        return JSONResponse(content={"code": 404, "message": "Review not found"}, status_code=404)
    
    reply = create_reply(db, review_id, current_user.id, content)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": reply.id,
            "user_id": reply.user_id,
            "username": current_user.username,
            "user_avatar": current_user.avatar,
            "content": reply.content,
            "created_at": reply.created_at.isoformat()
        }
    })

@app.post("/api/reviews/{review_id}/replies")
async def get_replies(
    review_id: int,
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    replies = get_review_replies(db, review_id, skip, limit)
    result = []
    for reply in replies:
        result.append({
            "id": reply.id,
            "user_id": reply.user_id,
            "username": reply.user.username,
            "user_avatar": reply.user.avatar,
            "content": reply.content,
            "created_at": reply.created_at.isoformat()
        })
    
    return JSONResponse(content={"code": 200, "data": result, "total": len(result)})

# ==================== 我的内容 ====================
@app.post("/api/my/apps")
async def get_my_apps(
    skip: int = Query(0),
    limit: int = Query(100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    apps = get_apps(db, skip=skip, limit=limit, developer_id=current_user.id)
    result = []
    for app in apps:
        result.append({
            "id": app.id,
            "name": app.name,
            "category": app.category,
            "status": app.status.value,
            "is_approved": app.is_approved,
            "total_downloads": app.total_downloads,
            "average_rating": app.average_rating,
            "review_count": app.review_count,
            "created_at": app.created_at.isoformat()
        })
    
    return JSONResponse(content={"code": 200, "data": result, "total": len(result)})

@app.post("/api/my/reviews")
async def get_my_reviews(
    skip: int = Query(0),
    limit: int = Query(100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for review in reviews:
        app = get_app(db, review.app_id)
        result.append({
            "id": review.id,
            "app_id": review.app_id,
            "app_name": app.name if app else "Unknown",
            "rating": review.rating,
            "title": review.title,
            "content": review.content,
            "like_count": review.like_count,
            "created_at": review.created_at.isoformat()
        })
    
    return JSONResponse(content={"code": 200, "data": result, "total": len(result)})

# ==================== 分类列表 ====================
@app.post("/api/categories")
async def get_categories():
    return JSONResponse(content={"code": 200, "data": Config.APP_CATEGORIES})

# ==================== 后台管理页面 ====================
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)