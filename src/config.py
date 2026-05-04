import tomli
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent

with open(CONFIG_DIR / "config.toml", "rb") as f:
    toml_data = tomli.load(f)

with open(CONFIG_DIR / "config.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

class Config:
    DATABASE_URL = toml_data["database"]["url"]

    WEBDAV_CONFIG = {
        "url": toml_data["webdav"]["url"],
        "username": toml_data["webdav"]["username"],
        "password": toml_data["webdav"]["password"],
        "app_upload_path": toml_data["webdav"]["app_upload_path"],
        "screenshot_path": toml_data["webdav"]["screenshot_path"],
        "avatar_path": toml_data["webdav"]["avatar_path"],
        "changelog_path": toml_data["webdav"]["changelog_path"],
    }

    OAUTH_CONFIG = {
        "base_url": toml_data["oauth"]["base_url"],
        "api_base_url": toml_data["oauth"]["api_base_url"],
        "client_id": toml_data["oauth"]["client_id"],
        "client_secret": toml_data["oauth"]["client_secret"],
        "redirect_uri": toml_data["oauth"]["redirect_uri"],
        "scope": toml_data["oauth"]["scope"],
    }

    SECRET_KEY = toml_data["app"]["secret_key"]
    ALGORITHM = toml_data["app"]["algorithm"]
    ACCESS_TOKEN_EXPIRE_MINUTES = toml_data["app"]["access_token_expire_minutes"]
    ADMIN_PASSWORD = toml_data["app"]["admin_password"]
    HOST = toml_data["app"]["host"]
    PORT = toml_data["app"]["port"]

    APP_CATEGORIES = json_data["app_categories"]
    MAX_FILE_SIZE_MB = json_data["file_settings"]["max_file_size_mb"]
    ALLOWED_IMAGE_EXTENSIONS = json_data["file_settings"]["allowed_image_extensions"]
    ALLOWED_APP_EXTENSIONS = json_data["file_settings"]["allowed_app_extensions"]
