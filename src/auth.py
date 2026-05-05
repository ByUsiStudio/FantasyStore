import httpx
import secrets
import urllib.parse
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from config import Config
from database import get_db
from models import User, UserRole

security = HTTPBearer(auto_error=False)

class CdifitOAuth:
    def __init__(self, config: dict):
        self.authorize_url = config['authorize_url']
        self.token_url = config['token_url']
        self.userinfo_url = config['userinfo_url']
        self.refresh_url = config['refresh_url']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.allowed_redirect_uris = config['allowed_redirect_uris']
        self.scope = config['scope']
        self.token_cache = {}
        self.user_token_cache = {}
    
    def generate_local_token(self) -> str:
        return secrets.token_hex(32)
    
    def generate_state(self) -> str:
        return secrets.token_hex(16)
    
    def generate_code_verifier(self) -> str:
        return secrets.token_urlsafe(32)
    
    def generate_code_challenge(self, code_verifier: str) -> str:
        digest = hashlib.sha256(code_verifier.encode()).digest()
        import base64
        return base64.urlsafe_b64encode(digest).decode().rstrip('=')
    
    def validate_redirect_uri(self, redirect_uri: str) -> bool:
        return redirect_uri in self.allowed_redirect_uris
    
    def get_oauth_url(self, redirect_uri: str) -> Dict[str, str]:
        if not self.validate_redirect_uri(redirect_uri):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect_uri. Must be one of the allowed URIs."
            )
        
        local_token = self.generate_local_token()
        state = self.generate_state()
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': self.scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        oauth_url = f"{self.authorize_url}?{urllib.parse.urlencode(params)}"
        
        self.token_cache[local_token] = {
            'state': state,
            'code_verifier': code_verifier,
            'redirect_uri': redirect_uri,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        
        return {"token": local_token, "oauth_url": oauth_url}
    
    async def exchange_code_for_token(self, code: str, code_verifier: Optional[str] = None, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code
            }
            
            if code_verifier:
                data["code_verifier"] = code_verifier
            
            if redirect_uri:
                data["redirect_uri"] = redirect_uri
            
            response = await client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange code for token"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user info"
                )
            
            result = response.json()
            return result
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.refresh_url,
                json={"refresh_token": refresh_token},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh token"
                )
            
            result = response.json()
            if result.get('code') != 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get('msg', 'Failed to refresh token')
                )
            
            return result.get('data', {})
    
    def cache_user_token(self, user_id: int, token_data: Dict[str, Any]):
        expires_in = token_data.get('expires_in', 3600)
        self.user_token_cache[user_id] = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': datetime.utcnow() + timedelta(seconds=expires_in)
        }

oauth_client = None

def init_oauth():
    global oauth_client
    oauth_client = CdifitOAuth(Config.OAUTH_CONFIG)
    return oauth_client

def get_oauth_client() -> CdifitOAuth:
    global oauth_client
    if oauth_client is None:
        raise HTTPException(status_code=500, detail="OAuth client not initialized")
    return oauth_client

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id, "role": payload.get("role")}
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    token_data = decode_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == token_data['user_id']).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not credentials:
        return None
    
    token = credentials.credentials
    token_data = decode_token(token)
    if token_data is None:
        return None
    
    user = db.query(User).filter(User.id == token_data['user_id']).first()
    return user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def verify_admin_password(password: str) -> bool:
    return password == Config.ADMIN_PASSWORD
