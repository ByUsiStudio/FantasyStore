import os
import sys
import time
import logging
from datetime import timedelta, datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Depends, Query, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from rich.logging import RichHandler
from rich.console import Console
from rich.panel import Panel

from database import get_db, init_db
from models import User, App, AppVersion, Review, AppStatus, VersionStatus, UserRole, ReviewStatus
from auth import (
    create_access_token, get_current_user, get_current_user_optional, get_current_admin,
    init_oauth, get_oauth_client, verify_admin_password
)
from crud import (
    create_or_update_user, get_apps, get_app, get_app_versions, get_version,
    get_reviews, create_review, update_review, delete_review, like_review,
    create_review_reply, download_app, create_app, create_app_version,
    delete_app, delete_version, get_download_count, get_user_download_history,
    create_download_record, approve_app, approve_version, set_current_version,
    update_app, get_users, delete_user, get_reviews_for_admin, delete_review_admin,
    update_review_status, get_audit_logs, create_audit_log
)
from webdav_client import init_webdav_client, get_webdav_client
from admin import router as admin_router
from config import Config

console = Console()
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_time=True, show_path=False)]
)
log = logging.getLogger("rich")

# 初始化
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')

log.info("Initializing database...")
init_db()

log.info("Initializing OAuth...")
init_oauth()

log.info("Initializing WebDAV client...")
init_webdav_client()

app = FastAPI(title="App Store API", version="1.0.0")

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    client = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code
        status_color = "green" if status_code < 400 else "red" if status_code >= 500 else "yellow"
        log.info(f"[{client}] {method} {path} [bold {status_color}]{status_code}[/bold {status_color}] ({process_time}ms)")
        return response
    except Exception as e:
        process_time = round((time.time() - start_time) * 1000, 2)
        log.error(f"[{client}] {method} {path} ERROR ({process_time}ms) - {str(e)}")
        raise

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

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail if hasattr(exc, 'detail') else str(exc),
            "data": {}
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "data": {}
        }
    )

# 404 路由不存在
@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    return JSONResponse(
        content={
            "code": 404,
            "message": f"Route /{path} not found",
            "data": {}
        }
    )

# 根路径
@app.get("/")
async def root():
    return JSONResponse(
        content={
            "code": 200,
            "message": "success",
            "data": {
                "name": "App Store API",
                "version": "1.0.0"
            }
        }
    )

# ==================== OAuth认证 ====================
@app.post("/api/oauth/url")
async def get_oauth_url(redirect_uri: str = Form(...)):
    oauth = get_oauth_client()
    return JSONResponse(content=oauth.get_oauth_url(redirect_uri))

@app.post("/api/oauth/login")
async def oauth_login(
    code: str = Form(...),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    oauth = get_oauth_client()
    
    cached_data = oauth.token_cache.get(token)
    if not cached_data:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    code_verifier = cached_data.get('code_verifier')
    redirect_uri = cached_data.get('redirect_uri')
    token_data = await oauth.exchange_code_for_token(code, code_verifier, redirect_uri)
    user_info = await oauth.get_user_info(token_data['access_token'])
    
    user = create_or_update_user(db, user_info.get('id'), {
        'username': user_info.get('username') or user_info.get('name'),
        'email': user_info.get('email'),
        'avatar': user_info.get('avatar')
    })
    
    oauth.cache_user_token(user.id, token_data)
    del oauth.token_cache[token]
    
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
                "role": user.role.value,
                "created_at": user.created_at.isoformat()
            }
        }
    })

@app.post("/api/oauth/refresh")
async def oauth_refresh(
    refresh_token: str = Form(...),
    db: Session = Depends(get_db)
):
    oauth = get_oauth_client()
    token_data = await oauth.refresh_token(refresh_token)
    
    access_token = create_access_token(
        data={"sub": token_data.get('user_id'), "role": "user"},
        expires_delta=timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": token_data.get('refresh_token')
        }
    })

# ==================== OAuth回调 ====================
@app.get("/api/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    oauth = get_oauth_client()
    
    cached_data = oauth.token_cache.get(state)
    if not cached_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    code_verifier = cached_data.get('code_verifier')
    redirect_uri = cached_data.get('redirect_uri')
    token_data = await oauth.exchange_code_for_token(code, code_verifier, redirect_uri)
    user_info = await oauth.get_user_info(token_data['access_token'])
    
    user = create_or_update_user(db, user_info.get('id'), {
        'username': user_info.get('username') or user_info.get('name'),
        'email': user_info.get('email'),
        'avatar': user_info.get('avatar')
    })
    
    oauth.cache_user_token(user.id, token_data)
    del oauth.token_cache[state]
    
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
                "role": user.role.value,
                "created_at": user.created_at.isoformat()
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if username:
        current_user.username = username
    if email:
        current_user.email = email
    
    db.commit()
    db.refresh(current_user)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "avatar": current_user.avatar,
            "role": current_user.role.value
        }
    })

# ==================== 应用列表 ====================
@app.post("/api/apps/list")
async def list_apps(
    skip: int = Query(0),
    limit: int = Query(100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    apps = get_apps(db, skip, limit, category, search, current_user)
    
    result = []
    for app in apps:
        versions = get_app_versions(db, app.id)
        current_version = next((v for v in versions if v.is_current), None)
        
        result.append({
            "id": app.id,
            "name": app.name,
            "description": app.description,
            "icon": app.icon,
            "category": app.category,
            "status": app.status.value,
            "download_count": get_download_count(db, app.id),
            "current_version": current_version.version if current_version else None,
            "created_at": app.created_at.isoformat(),
            "updated_at": app.updated_at.isoformat()
        })
    
    return JSONResponse(content={
        "code": 200,
        "data": result,
        "total": len(result)
    })

@app.post("/api/apps/detail")
async def get_app_detail(
    app_id: int = Query(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found", "data": {}})
    
    if app.status == AppStatus.PENDING and (not current_user or current_user.role != UserRole.ADMIN):
        return JSONResponse(content={"code": 404, "message": "App not found", "data": {}})
    
    versions = get_app_versions(db, app_id)
    current_version = next((v for v in versions if v.is_current), None)
    
    reviews = get_reviews(db, app_id)
    review_count = len(reviews)
    avg_rating = sum(r.rating for r in reviews) / review_count if review_count > 0 else 0
    
    is_purchased = False
    if current_user:
        download_history = get_user_download_history(db, current_user.id)
        is_purchased = app_id in [d.app_id for d in download_history]
    
    result = {
        "id": app.id,
        "name": app.name,
        "description": app.description,
        "icon": app.icon,
        "category": app.category,
        "status": app.status.value,
        "download_count": get_download_count(db, app_id),
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat(),
        "current_version": {
            "id": current_version.id,
            "version": current_version.version,
            "changelog": current_version.changelog,
            "download_url": current_version.download_url,
            "file_size": current_version.file_size,
            "released_at": current_version.released_at.isoformat()
        } if current_version else None,
        "reviews": [{
            "id": r.id,
            "user_id": r.user_id,
            "username": r.user.username,
            "rating": r.rating,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
            "likes": r.likes,
            "is_liked": False,
            "replies": [{
                "id": reply.id,
                "user_id": reply.user_id,
                "username": reply.user.username,
                "content": reply.content,
                "created_at": reply.created_at.isoformat()
            } for reply in r.replies]
        } for r in reviews],
        "review_count": review_count,
        "avg_rating": round(avg_rating, 1),
        "is_purchased": is_purchased
    }
    
    return JSONResponse(content={"code": 200, "data": result})

# ==================== 下载应用 ====================
@app.post("/api/apps/download")
async def download_app_endpoint(
    app_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found", "data": {}})
    
    if app.status != AppStatus.APPROVED:
        return JSONResponse(content={"code": 403, "message": "App not approved", "data": {}})
    
    version = get_version(db, app.current_version_id) if app.current_version_id else None
    if not version:
        return JSONResponse(content={"code": 404, "message": "No version available", "data": {}})
    
    download_url = download_app(app_id, version.id)
    
    create_download_record(db, current_user.id, app_id, version.id)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "download_url": download_url,
            "app_id": app_id,
            "version_id": version.id,
            "version": version.version
        }
    })

# ==================== 应用评论 ====================
@app.post("/api/apps/reviews")
async def get_app_reviews(
    app_id: int = Query(...),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    reviews = get_reviews(db, app_id, skip, limit)
    
    result = []
    for r in reviews:
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": r.user.username,
            "rating": r.rating,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
            "likes": r.likes,
            "replies": [{
                "id": reply.id,
                "user_id": reply.user_id,
                "username": reply.user.username,
                "content": reply.content,
                "created_at": reply.created_at.isoformat()
            } for reply in r.replies]
        })
    
    return JSONResponse(content={"code": 200, "data": result, "total": len(result)})

@app.post("/api/apps/review")
async def add_review(
    app_id: int = Query(...),
    rating: int = Query(...),
    content: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = get_app(db, app_id)
    if not app:
        return JSONResponse(content={"code": 404, "message": "App not found", "data": {}})
    
    if not (1 <= rating <= 5):
        return JSONResponse(content={"code": 400, "message": "Rating must be between 1 and 5", "data": {}})
    
    review = create_review(db, current_user.id, app_id, rating, content)
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": review.id,
            "rating": review.rating,
            "content": review.content,
            "created_at": review.created_at.isoformat()
        }
    })

@app.post("/api/apps/review/update")
async def update_review_endpoint(
    review_id: int = Query(...),
    rating: Optional[int] = Query(None),
    content: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = update_review(db, review_id, current_user.id, rating, content)
    if not review:
        return JSONResponse(content={"code": 403, "message": "Not authorized", "data": {}})
    
    return JSONResponse(content={"code": 200, "data": {"message": "Review updated"}})

@app.post("/api/apps/review/delete")
async def delete_review_endpoint(
    review_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = delete_review(db, review_id, current_user.id)
    if not success:
        return JSONResponse(content={"code": 403, "message": "Not authorized", "data": {}})
    
    return JSONResponse(content={"code": 200, "data": {"message": "Review deleted"}})

@app.post("/api/apps/review/like")
async def like_review_endpoint(
    review_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = like_review(db, review_id, current_user.id)
    if not success:
        return JSONResponse(content={"code": 404, "message": "Review not found", "data": {}})
    
    return JSONResponse(content={"code": 200, "data": {"message": "Like toggled"}})

@app.post("/api/apps/review/reply")
async def reply_to_review(
    review_id: int = Query(...),
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reply = create_review_reply(db, review_id, current_user.id, content)
    if not reply:
        return JSONResponse(content={"code": 404, "message": "Review not found", "data": {}})
    
    return JSONResponse(content={
        "code": 200,
        "data": {
            "id": reply.id,
            "content": reply.content,
            "created_at": reply.created_at.isoformat()
        }
    })

# ==================== 分类列表 ====================
@app.post("/api/categories")
async def get_categories():
    return JSONResponse(content={"code": 200, "data": Config.APP_CATEGORIES})

# ==================== 后台管理页面 ====================
from fastapi.responses import HTMLResponse

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    
    console.print(Panel.fit(
        f"[bold cyan]App Store API Server[/bold cyan]\n\n"
        f"[yellow]Local Access:[/yellow]   http://localhost:{Config.PORT}\n"
        f"[yellow]Network Access:[/yellow] http://0.0.0.0:{Config.PORT}\n"
        f"[yellow]Admin Panel:[/yellow]    http://localhost:{Config.PORT}/admin\n\n"
        f"[green]Press Ctrl+C to stop[/green]",
        border_style="bright_blue"
    ))
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=False
    )