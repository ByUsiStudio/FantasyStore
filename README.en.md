Based on the code map provided, I can see this is a FastAPI-based application store system. Let me analyze the key components and create a comprehensive README.

# FantasyStore

FantasyStore is a FastAPI-based application store platform supporting application publishing, version management, user reviews, and more.

## Project Overview

FantasyStore provides developers with a complete application distribution and management system, featuring OAuth third-party login, application review, version management, user reviews, and more. The system adopts a frontend-backend separation architecture, with an admin dashboard built using native HTML/CSS/JavaScript.

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy ORM
- **Authentication**: JWT + OAuth (Cdifit)
- **Storage**: WebDAV file storage
- **Frontend**: Native HTML + CSS + JavaScript

## Key Features

### User Features
- OAuth third-party login
- Browse and search applications
- Download applications and view version history
- Submit app reviews (1-5 star ratings)
- Like or reply to reviews
- Manage personal profile

### Developer Features
- Create and publish applications
- Upload app screenshots and cover images
- Manage application versions
- Update application information and changelogs
- View personal applications and reviews

### Admin Features
- Review pending applications
- Manage application versions
- View and hide user reviews
- View platform statistics
- Manage users

## Project Structure

```
src/
├── main.py           # Main API entry point
├── admin.py          # Admin API
├── auth.py           # Authentication and OAuth
├── crud.py           # Database operations
├── models.py         # Data models
├── database.py       # Database configuration
├── markdown.py       # Markdown conversion
├── webdav_client.py  # WebDAV file client
├── static/           # Static files
│   ├── admin.html
│   ├── admin.css
│   └── admin.js
├── config.json       # JSON configuration
├── config.toml       # TOML configuration
└── requirements.txt  # Dependencies list
```

## Data Models

- **User**: User (roles: regular user / admin)
- **App**: Application (status: pending review / approved / rejected / archived)
- **AppVersion**: Application version
- **Review**: User review
- **ReviewLike**: Review like
- **ReviewReply**: Review reply
- **DownloadRecord**: Download record
- **AuditLog**: Audit log

## API Endpoints

### Authentication
- `POST /api/oauth/url` - Get OAuth login URL
- `POST /api/oauth/login` - OAuth login callback
- `POST /api/me` - Get current user info
- `POST /api/me/update` - Update user profile

### Applications
- `POST /api/apps/create` - Create an application
- `POST /api/apps/list` - Get application list
- `GET /api/apps/{app_id}` - Get application details
- `POST /api/apps/{app_id}/update` - Update application info
- `POST /api/apps/{app_id}/version/add` - Add a version
- `POST /api/my/apps` - Get my applications

### Reviews
- `POST /api/apps/{app_id}/review/add` - Submit a review
- `POST /api/apps/{app_id}/reviews` - Get review list
- `POST /api/reviews/{review_id}/like` - Like a review
- `POST /api/reviews/{review_id}/unlike` - Unlike a review
- `POST /api/reviews/{review_id}/reply/add` - Add a reply

### Uploads
- `POST /api/upload/image` - Upload image
- `POST /api/upload/app` - Upload application file

### Admin
- `POST /api/admin/apps` - Get application list
- `POST /api/admin/apps/{app_id}/approve` - Approve application
- `POST /api/admin/apps/{app_id}/reject` - Reject application
- `POST /api/admin/versions/pending` - Get pending versions
- `POST /api/admin/versions/{version_id}/approve` - Approve version
- `POST /api/admin/statistics` - Get statistics

## Installation & Configuration

### 1. Install Dependencies

```bash
pip install -r src/requirements.txt
```

### 2. Configure Database

Set up database connection details in `config.json` or `config.toml`.

### 3. Configure OAuth

Add OAuth configuration to the config file:
- Client ID
- Client Secret
- Redirect URI

### 4. Configure Storage

Configure WebDAV storage service for storing application files and images.

### 5. Start the Service

```bash
bash start.sh
# or
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Usage Instructions

1. Access the admin panel at `/admin` and log in as an admin
2. Log in as a regular user via OAuth
3. Developers can create and manage their own applications
4. Users can search, download applications, and submit reviews
5. Admins review applications and user reviews

## License

See the LICENSE file for specific license terms.

## Contributors

Thank you to all developers who have contributed to this project.