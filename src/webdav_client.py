import io
from webdav3.client import Client
from fastapi import HTTPException, UploadFile
from config import Config

class WebDAVClient:
    def __init__(self, webdav_config: dict):
        options = {
            'webdav_hostname': webdav_config['url'],
            'webdav_login': webdav_config['username'],
            'webdav_password': webdav_config['password']
        }
        self.client = Client(options)
        self.app_upload_path = webdav_config['app_upload_path']
        self.screenshot_path = webdav_config['screenshot_path']
        self.avatar_path = webdav_config['avatar_path']
        self.changelog_path = webdav_config.get('changelog_path', '/changelogs/')
        
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        for path in [self.app_upload_path, self.screenshot_path, self.avatar_path, self.changelog_path]:
            try:
                if not self.client.check(path):
                    self.client.mkdir(path)
            except:
                pass
    
    async def upload_file(self, file, remote_path: str) -> str:
        try:
            if hasattr(file, 'read'):
                content = await file.read()
                file_obj = io.BytesIO(content)
            else:
                file_obj = file
            self.client.upload_sync(remote_path=remote_path, file_obj=file_obj)
            return remote_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"WebDAV upload failed: {str(e)}")
    
    def download_file(self, remote_path: str) -> bytes:
        try:
            content = self.client.download_sync(remote_path=remote_path)
            return content
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    
    def delete_file(self, remote_path: str) -> bool:
        try:
            if self.client.check(remote_path):
                self.client.clean(remote_path)
                return True
            return False
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
    
    def file_exists(self, remote_path: str) -> bool:
        try:
            return self.client.check(remote_path)
        except:
            return False

webdav_client = None

def init_webdav_client():
    global webdav_client
    webdav_client = WebDAVClient(Config.WEBDAV_CONFIG)
    return webdav_client

def get_webdav_client() -> WebDAVClient:
    global webdav_client
    if webdav_client is None:
        raise HTTPException(status_code=500, detail="WebDAV client not initialized")
    return webdav_client