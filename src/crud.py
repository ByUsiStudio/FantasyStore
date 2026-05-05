from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import User, App, AppVersion, Review, ReviewLike, ReviewReply, AuditLog, AppStatus, VersionStatus, ReviewStatus, DownloadRecord
from datetime import datetime
import json
from typing import Optional, List, Dict, Any

# ==================== 用户操作 ====================
def create_or_update_user(db: Session, cdifit_user_id: str, user_info: Dict[str, Any]) -> User:
    user = db.query(User).filter(User.cdifit_user_id == cdifit_user_id).first()
    
    if user:
        user.username = user_info.get('username', user.username)
        user.email = user_info.get('email', user.email)
        user.avatar = user_info.get('avatar', user.avatar)
        user.last_login = datetime.utcnow()
    else:
        user = User(
            cdifit_user_id=cdifit_user_id,
            username=user_info.get('username', f"user_{cdifit_user_id[:8]}"),
            email=user_info.get('email'),
            avatar=user_info.get('avatar'),
            last_login=datetime.utcnow()
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def update_user(db: Session, user_id: int, **kwargs):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

# ==================== 应用操作 ====================
def create_app(db: Session, name: str, description: str, category: str, 
               developer_id: int, cover_image: str = None, screenshots: list = None) -> App:
    db_app = App(
        name=name,
        description=description,
        category=category,
        cover_image=cover_image,
        screenshots=json.dumps(screenshots) if screenshots else None,
        developer_id=developer_id,
        status=AppStatus.PENDING,
        is_approved=False
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

def get_app(db: Session, app_id: int):
    return db.query(App).filter(App.id == app_id).first()

def get_apps(db: Session, skip: int = 0, limit: int = 100, 
             status: Optional[AppStatus] = None, 
             category: Optional[str] = None, 
             developer_id: Optional[int] = None,
             search: Optional[str] = None):
    query = db.query(App)
    
    if status:
        query = query.filter(App.status == status)
    if category:
        query = query.filter(App.category == category)
    if developer_id:
        query = query.filter(App.developer_id == developer_id)
    if search:
        query = query.filter(
            (App.name.contains(search)) | (App.description.contains(search))
        )
    
    return query.order_by(desc(App.created_at)).offset(skip).limit(limit).all()

def update_app(db: Session, app_id: int, **kwargs):
    app = db.query(App).filter(App.id == app_id).first()
    if app:
        for key, value in kwargs.items():
            if value is not None:
                if key == 'screenshots' and isinstance(value, list):
                    value = json.dumps(value)
                setattr(app, key, value)
        db.commit()
        db.refresh(app)
    return app

def delete_app(db: Session, app_id: int):
    app = db.query(App).filter(App.id == app_id).first()
    if app:
        db.delete(app)
        db.commit()
        return True
    return False

def approve_app(db: Session, app_id: int):
    """审核通过应用（首次通过后不再需要审核）"""
    app = db.query(App).filter(App.id == app_id).first()
    if app:
        app.status = AppStatus.APPROVED
        app.is_approved = True
        app.published_at = datetime.utcnow()
        db.commit()
        return True
    return False

# ==================== 版本操作 ====================
def create_app_version(db: Session, app_id: int, version: str, version_code: int,
                       download_url: str, file_name: str, file_size: str,
                       developer_id: int, release_notes: str = None,
                       changelog_md: str = None, changelog_html: str = None,
                       is_current: bool = False) -> AppVersion:
    # 检查版本号是否重复
    existing = db.query(AppVersion).filter(
        AppVersion.app_id == app_id,
        AppVersion.version == version
    ).first()
    if existing:
        raise ValueError(f"Version {version} already exists")
    
    app = get_app(db, app_id)
    # 如果应用已通过审核，版本自动通过；否则需要审核
    status = VersionStatus.APPROVED if app and app.is_approved else VersionStatus.PENDING
    
    db_version = AppVersion(
        app_id=app_id,
        version=version,
        version_code=version_code,
        release_notes=release_notes,
        changelog_md=changelog_md,
        changelog_html=changelog_html,
        download_url=download_url,
        file_name=file_name,
        file_size=file_size,
        developer_id=developer_id,
        status=status,
        is_current=is_current
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    
    # 如果自动通过，设置为当前版本
    if status == VersionStatus.APPROVED and is_current:
        set_current_version(db, app_id, db_version.id)
    
    return db_version

def get_version(db: Session, version_id: int):
    return db.query(AppVersion).filter(AppVersion.id == version_id).first()

def get_app_versions(db: Session, app_id: int, status: Optional[VersionStatus] = None):
    query = db.query(AppVersion).filter(AppVersion.app_id == app_id)
    if status:
        query = query.filter(AppVersion.status == status)
    return query.order_by(desc(AppVersion.version_code)).all()

def update_version_changelog(db: Session, version_id: int, changelog_md: str, changelog_html: str):
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if version:
        version.changelog_md = changelog_md
        version.changelog_html = changelog_html
        db.commit()
        return version
    return None

def set_current_version(db: Session, app_id: int, version_id: int) -> bool:
    """设置当前版本"""
    app = db.query(App).filter(App.id == app_id).first()
    if not app:
        return False
    
    # 将所有版本设为非当前
    db.query(AppVersion).filter(AppVersion.app_id == app_id).update({"is_current": False})
    
    # 设置指定版本为当前
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if version:
        version.is_current = True
        version.status = VersionStatus.ACTIVE
        app.current_version_id = version_id
        db.commit()
        return True
    return False

def update_version_download_count(db: Session, version_id: int):
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if version:
        version.download_count += 1
        db.commit()
    return version

# ==================== 评论操作 ====================
def create_review(db: Session, app_id: int, rating: int, user_id: int, 
                  title: str = None, content: str = None, 
                  device_model: str = None, device_os: str = None, version: str = None) -> Review:
    db_review = Review(
        rating=rating,
        title=title,
        content=content,
        device_model=device_model,
        device_os=device_os,
        version=version,
        user_id=user_id,
        app_id=app_id,
        status=ReviewStatus.APPROVED
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # 更新应用评分
    update_app_rating(db, app_id)
    
    return db_review

def get_review(db: Session, review_id: int):
    return db.query(Review).filter(Review.id == review_id).first()

def get_app_reviews(db: Session, app_id: int, skip: int = 0, limit: int = 100):
    return db.query(Review).filter(
        Review.app_id == app_id,
        Review.status == ReviewStatus.APPROVED
    ).order_by(desc(Review.created_at)).offset(skip).limit(limit).all()

def get_reviews(db: Session, app_id: int, skip: int = 0, limit: int = 100):
    """获取应用评论（兼容旧接口名）"""
    return get_app_reviews(db, app_id, skip, limit)

def update_review(db: Session, review_id: int, **kwargs):
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        for key, value in kwargs.items():
            if value is not None:
                setattr(review, key, value)
        review.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(review)
        update_app_rating(db, review.app_id)
    return review

def delete_review(db: Session, review_id: int):
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        app_id = review.app_id
        db.delete(review)
        db.commit()
        update_app_rating(db, app_id)
        return True
    return False

def update_app_rating(db: Session, app_id: int):
    """更新应用平均评分"""
    result = db.query(func.avg(Review.rating), func.count(Review.id)).filter(
        Review.app_id == app_id,
        Review.status == ReviewStatus.APPROVED
    ).first()
    
    app = db.query(App).filter(App.id == app_id).first()
    if app:
        app.average_rating = float(result[0]) if result[0] else 0
        app.review_count = result[1] or 0
        db.commit()
    return app

def get_user_review_for_app(db: Session, user_id: int, app_id: int):
    return db.query(Review).filter(
        Review.user_id == user_id,
        Review.app_id == app_id
    ).first()

# ==================== 评论点赞 ====================
def like_review(db: Session, review_id: int, user_id: int):
    # 检查是否已点赞
    existing = db.query(ReviewLike).filter(
        ReviewLike.review_id == review_id,
        ReviewLike.user_id == user_id
    ).first()
    
    if existing:
        return False, "Already liked"
    
    like = ReviewLike(review_id=review_id, user_id=user_id)
    db.add(like)
    
    # 更新点赞数
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        review.like_count += 1
        db.commit()
        return True, "Liked"
    
    db.commit()
    return True, "Liked"

def unlike_review(db: Session, review_id: int, user_id: int):
    like = db.query(ReviewLike).filter(
        ReviewLike.review_id == review_id,
        ReviewLike.user_id == user_id
    ).first()
    
    if not like:
        return False, "Not liked"
    
    db.delete(like)
    
    # 更新点赞数
    review = db.query(Review).filter(Review.id == review_id).first()
    if review and review.like_count > 0:
        review.like_count -= 1
        db.commit()
        return True, "Unliked"
    
    db.commit()
    return True, "Unliked"

def check_user_liked_review(db: Session, review_id: int, user_id: int) -> bool:
    return db.query(ReviewLike).filter(
        ReviewLike.review_id == review_id,
        ReviewLike.user_id == user_id
    ).first() is not None

# ==================== 评论回复 ====================
def create_reply(db: Session, review_id: int, user_id: int, content: str) -> ReviewReply:
    reply = ReviewReply(
        review_id=review_id,
        user_id=user_id,
        content=content
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply

def create_review_reply(db: Session, review_id: int, user_id: int, content: str) -> ReviewReply:
    """创建评论回复（兼容旧接口名）"""
    return create_reply(db, review_id, user_id, content)

def get_review_replies(db: Session, review_id: int, skip: int = 0, limit: int = 100):
    return db.query(ReviewReply).filter(
        ReviewReply.review_id == review_id
    ).order_by(ReviewReply.created_at).offset(skip).limit(limit).all()

def delete_reply(db: Session, reply_id: int, user_id: int, is_admin: bool = False):
    reply = db.query(ReviewReply).filter(ReviewReply.id == reply_id).first()
    if reply and (reply.user_id == user_id or is_admin):
        db.delete(reply)
        db.commit()
        return True
    return False

# ==================== 下载记录 ====================
def record_download(db: Session, app_id: int, version_id: int = None, 
                    user_id: int = None, ip: str = None, user_agent: str = None):
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first() if version_id else None
    
    record = DownloadRecord(
        app_id=app_id,
        version_id=version_id,
        version=version.version if version else None,
        user_id=user_id,
        ip_address=ip,
        user_agent=user_agent
    )
    db.add(record)
    db.commit()
    
    # 更新版本下载数
    if version:
        version.download_count += 1
        db.commit()
    
    # 更新应用下载数
    app = db.query(App).filter(App.id == app_id).first()
    if app:
        app.total_downloads += 1
        db.commit()
    
    return record

def download_app(db: Session, app_id: int, version_id: int = None, user_id: int = None, ip: str = None, user_agent: str = None):
    """下载应用（兼容旧接口名）"""
    return record_download(db, app_id, version_id, user_id, ip, user_agent)

def create_download_record(db: Session, app_id: int, version_id: int = None, user_id: int = None, ip: str = None, user_agent: str = None):
    """创建下载记录（兼容旧接口名）"""
    return record_download(db, app_id, version_id, user_id, ip, user_agent)

def get_download_count(db: Session, app_id: int):
    """获取应用下载总数"""
    app = db.query(App).filter(App.id == app_id).first()
    return app.total_downloads if app else 0

def get_user_download_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """获取用户下载历史"""
    return db.query(DownloadRecord).filter(
        DownloadRecord.user_id == user_id
    ).order_by(desc(DownloadRecord.created_at)).offset(skip).limit(limit).all()

def delete_version(db: Session, version_id: int):
    """删除版本"""
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if version:
        db.delete(version)
        db.commit()
        return True
    return False

def approve_version(db: Session, version_id: int):
    """审核通过版本"""
    version = db.query(AppVersion).filter(AppVersion.id == version_id).first()
    if version:
        version.status = VersionStatus.APPROVED
        db.commit()
        return True
    return False

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """获取用户列表（管理员用）"""
    return db.query(User).order_by(desc(User.created_at)).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int):
    """删除用户（管理员用）"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def get_reviews_for_admin(db: Session, skip: int = 0, limit: int = 100, status: Optional[ReviewStatus] = None):
    """获取评论列表（管理员用）"""
    query = db.query(Review)
    if status:
        query = query.filter(Review.status == status)
    return query.order_by(desc(Review.created_at)).offset(skip).limit(limit).all()

def delete_review_admin(db: Session, review_id: int):
    """删除评论（管理员用）"""
    return delete_review(db, review_id)

def update_review_status(db: Session, review_id: int, status: ReviewStatus):
    """更新评论状态（管理员用）"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        review.status = status
        db.commit()
        db.refresh(review)
        update_app_rating(db, review.app_id)
    return review

# ==================== 审计日志 ====================
def create_audit_log(db: Session, user_id: int, action: str, target_type: str, target_id: int = None, details: Dict[str, Any] = None):
    """创建审计日志"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100, user_id: int = None):
    """获取审计日志列表"""
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()