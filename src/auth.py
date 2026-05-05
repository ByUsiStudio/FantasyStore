import httpx
import secrets
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
        self.base_url = config['base_url']
        self.api_base_url = config['api_base_url']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.redirect_uri = config['redirect_uri']
        self.scope = config['scope']
        self.token_cache = {}
        self.user_token_cache = {}
    
    def generate_local_token(self) -> str:
        return secrets.token_hex(32)
    
    def generate_state(self) -> str:
        return secrets.token_hex(16)
    
    def get_oauth_url(self) -> Dict[str, str]:
        local_token = self.generate_local_token()
        state = self.generate_state()
        
        import urllib.parse
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': f"{state}_{local_token}"
        }
        oauth_url = f"https://www.cdifit.cn/session/authorize?{urllib.parse.urlencode(params)}"
        
        self.token_cache[local_token] = {
            'state': state,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        
        return {"token": local_token, "oauth_url": oauth_url}
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/session/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code
                },
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
                f"{self.api_base_url}/user/info",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user info"
                )
            
            result = response.json()
            if result.get('code') == 0:
                return result.get('data', {})
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get('msg', 'Failed to get user info')
                )
    
    def cache_user_token(self, user_id: int, token_data: Dict[str, Any]):
        self.user_token_cache[user_id] = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
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