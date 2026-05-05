from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import User, App, AppVersion, Review, AppStatus, VersionStatus, ReviewStatus, UserRole, DownloadRecord
from auth import verify_admin_password
from crud import (
    get_apps, get_app, get_app_versions, get_version,
    approve_app, update_app, set_current_version
)
from webdav_client import get_webdav_client

router = APIRouter(prefix="/admin/api", tags=["Admin API"])

def verify_admin(request, db: Session):
    password = request.headers.get("X-Admin-Password")
    if not password or not verify_admin_password(password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# ==================== 应用管理 ====================
@router.post("/apps")
async def admin_get_apps(
    skip: int = Query(0),
    limit: int = Query(100),
    status: Optional[str] = None,
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    app_status = None
    if status and status != "all":
        try:
            app_status = AppStatus(status)
        except:
            pass
    
    apps = get_apps(db, skip=skip, limit=limit, status=app_status)
    result = []
    for app in apps:
        result.append({
            "id": app.id,
            "name": app.name,
            "category": app.category,
            "status": app.status.value,
            "is_approved": app.is_approved,
            "developer_name": app.developer.username,
            "total_downloads": app.total_downloads,
            "average_rating": app.average_rating,
            "created_at": app.created_at.isoformat(),
            "versions_count": len(app.versions)
        })
    
    return {"code": 200, "data": result, "total": len(result)}

@router.post("/apps/{app_id}/approve")
async def admin_approve_app(
    app_id: int,
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    app = get_app(db, app_id)
    if not app:
        return {"code": 404, "message": "App not found"}
    
    success = approve_app(db, app_id)
    if success:
        return {"code": 200, "message": "App approved successfully"}
    return {"code": 500, "message": "Failed to approve app"}

@router.post("/apps/{app_id}/reject")
async def admin_reject_app(
    app_id: int,
    reason: str = Form(None),
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    app = get_app(db, app_id)
    if not app:
        return {"code": 404, "message": "App not found"}
    
    app.status = AppStatus.REJECTED
    db.commit()
    
    return {"code": 200, "message": "App rejected"}

@router.post("/apps/{app_id}/remove")
async def admin_remove_app(
    app_id: int,
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    app = get_app(db, app_id)
    if not app:
        return {"code": 404, "message": "App not found"}
    
    app.status = AppStatus.REMOVED
    db.commit()
    
    return {"code": 200, "message": "App removed"}

# ==================== 版本管理 ====================
@router.post("/versions/pending")
async def admin_get_pending_versions(
    skip: int = Query(0),
    limit: int = Query(100),
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    versions = db.query(AppVersion).filter(
        AppVersion.status == VersionStatus.PENDING
    ).order_by(AppVersion.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for version in versions:
        app = get_app(db, version.app_id)
        result.append({
            "id": version.id,
            "app_id": version.app_id,
            "app_name": app.name if app else "Unknown",
            "version": version.version,
            "version_code": version.version_code,
            "release_notes": version.release_notes,
            "file_size": version.file_size,
            "developer_name": version.developer.username,
            "created_at": version.created_at.isoformat()
        })
    
    return {"code": 200, "data": result, "total": len(result)}

@router.post("/versions/{version_id}/approve")
async def admin_approve_version(
    version_id: int,
    set_as_current: bool = Query(False),
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    version = get_version(db, version_id)
    if not version:
        return {"code": 404, "message": "Version not found"}
    
    version.status = VersionStatus.APPROVED
    if set_as_current:
        version.is_current = True
        set_current_version(db, version.app_id, version_id)
    db.commit()
    
    return {"code": 200, "message": "Version approved"}

@router.post("/versions/{version_id}/reject")
async def admin_reject_version(
    version_id: int,
    reason: str = Form(None),
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    version = get_version(db, version_id)
    if not version:
        return {"code": 404, "message": "Version not found"}
    
    version.status = VersionStatus.REJECTED
    db.commit()
    
    return {"code": 200, "message": "Version rejected"}

# ==================== 评论管理 ====================
@router.post("/reviews")
async def admin_get_reviews(
    skip: int = Query(0),
    limit: int = Query(100),
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    reviews = db.query(Review).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for review in reviews:
        app = get_app(db, review.app_id)
        result.append({
            "id": review.id,
            "app_id": review.app_id,
            "app_name": app.name if app else "Unknown",
            "rating": review.rating,
            "title": review.title,
            "content": review.content[:100] if review.content else "",
            "user_name": review.user.username,
            "like_count": review.like_count,
            "created_at": review.created_at.isoformat()
        })
    
    return {"code": 200, "data": result, "total": len(result)}

@router.post("/reviews/{review_id}/hide")
async def admin_hide_review(
    review_id: int,
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        return {"code": 404, "message": "Review not found"}
    
    review.status = ReviewStatus.HIDDEN
    db.commit()
    
    return {"code": 200, "message": "Review hidden"}

# ==================== 用户管理 ====================
@router.post("/users")
async def admin_get_users(
    skip: int = Query(0),
    limit: int = Query(100),
    request = None,
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    users = db.query(User).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "apps_count": len(user.apps),
            "reviews_count": len(user.reviews),
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
    
    return {"code": 200, "data": result, "total": len(result)}

# ==================== 统计信息 ====================
@router.post("/statistics")
async def admin_get_statistics(
    request: Request,
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    verify_admin(request, db)
    
    total_apps = db.query(App).count()
    pending_apps = db.query(App).filter(App.status == AppStatus.PENDING).count()
    approved_apps = db.query(App).filter(App.status == AppStatus.APPROVED).count()
    
    total_versions = db.query(AppVersion).count()
    pending_versions = db.query(AppVersion).filter(AppVersion.status == VersionStatus.PENDING).count()
    
    total_reviews = db.query(Review).count()
    total_users = db.query(User).count()
    new_users_7d = db.query(User).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    total_downloads = db.query(DownloadRecord).count()
    downloads_7d = db.query(DownloadRecord).filter(
        DownloadRecord.downloaded_at >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    daily_downloads = []
    for i in range(days):
        date = datetime.utcnow().date() - timedelta(days=i)
        next_date = date + timedelta(days=1)
        count = db.query(DownloadRecord).filter(
            DownloadRecord.downloaded_at >= datetime.combine(date, datetime.min.time()),
            DownloadRecord.downloaded_at < datetime.combine(next_date, datetime.min.time())
        ).count()
        daily_downloads.append({"date": date.isoformat(), "downloads": count})
    
    return {
        "code": 200,
        "data": {
            "apps": {
                "total": total_apps,
                "pending": pending_apps,
                "approved": approved_apps
            },
            "versions": {
                "total": total_versions,
                "pending": pending_versions
            },
            "reviews": {"total": total_reviews},
            "users": {
                "total": total_users,
                "new_last_7_days": new_users_7d
            },
            "downloads": {
                "total": total_downloads,
                "last_7_days": downloads_7d,
                "daily": daily_downloads
            }
        }
    }