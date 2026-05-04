from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class AppStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REMOVED = "removed"

class VersionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    DEPRECATED = "deprecated"

class ReviewStatus(str, enum.Enum):
    APPROVED = "approved"
    HIDDEN = "hidden"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    cdifit_user_id = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), index=True, nullable=True)
    avatar = Column(String(500), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    apps = relationship("App", back_populates="developer", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    review_likes = relationship("ReviewLike", back_populates="user", cascade="all, delete-orphan")
    review_replies = relationship("ReviewReply", back_populates="user", cascade="all, delete-orphan")
    app_versions = relationship("AppVersion", back_populates="developer", cascade="all, delete-orphan")

class App(Base):
    __tablename__ = "apps"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    cover_image = Column(String(500), nullable=True)
    screenshots = Column(Text, nullable=True)
    status = Column(Enum(AppStatus), default=AppStatus.PENDING)
    is_approved = Column(Boolean, default=False)  # 是否已通过审核（首次通过后为True）
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    total_downloads = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    developer = relationship("User", back_populates="apps")
    reviews = relationship("Review", back_populates="app", cascade="all, delete-orphan")
    versions = relationship("AppVersion", back_populates="app", cascade="all, delete-orphan")
    current_version_id = Column(Integer, nullable=True)

class AppVersion(Base):
    __tablename__ = "app_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    version_code = Column(Integer, nullable=False)
    release_notes = Column(Text, nullable=True)
    changelog_md = Column(Text, nullable=True)  # Markdown格式更新日志
    changelog_html = Column(Text, nullable=True)  # 转换后的HTML
    download_url = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=True)
    file_size = Column(String(20), nullable=False)
    file_hash = Column(String(100), nullable=True)
    
    status = Column(Enum(VersionStatus), default=VersionStatus.PENDING)
    is_current = Column(Boolean, default=False)
    
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    download_count = Column(Integer, default=0)
    
    app = relationship("App", back_populates="versions")
    developer = relationship("User", back_populates="app_versions")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    version = Column(String(20), nullable=True)
    device_model = Column(String(100), nullable=True)
    device_os = Column(String(100), nullable=True)
    
    status = Column(Enum(ReviewStatus), default=ReviewStatus.APPROVED)
    like_count = Column(Integer, default=0)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    version_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="reviews")
    app = relationship("App", back_populates="reviews")
    likes = relationship("ReviewLike", back_populates="review", cascade="all, delete-orphan")
    replies = relationship("ReviewReply", back_populates="review", cascade="all, delete-orphan")

class ReviewLike(Base):
    __tablename__ = "review_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    review = relationship("Review", back_populates="likes")
    user = relationship("User", back_populates="review_likes")

class ReviewReply(Base):
    __tablename__ = "review_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    review = relationship("Review", back_populates="replies")
    user = relationship("User", back_populates="review_replies")

class DownloadRecord(Base):
    __tablename__ = "download_records"
    
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)
    version_id = Column(Integer, nullable=True)
    version = Column(String(20), nullable=True)
    user_id = Column(Integer, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    downloaded_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    admin_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)