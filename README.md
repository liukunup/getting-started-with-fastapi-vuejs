# Getting started with FastAPI & Vue.js

for AI Coding with FastAPI &amp; Vue 3

目标是在AI Coding加持下，快速实现单体应用程序。

## 技术栈 (Tech Stack)

### Backend
- **Framework**: FastAPI
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Auth**: OAuth2 (JWT), Casbin (RBAC)
- **Task Queue**: Celery
- **Storage**: Minio (S3 Compatible)
- **Database**: PostgreSQL (Default), MySQL, MariaDB, SQLite

### Frontend
- **Framework**: Vue 3
- **UI Library**: PrimeVue
- **Build Tool**: Vite
- **Styling**: TailwindCSS

### Infrastructure
- Docker & Docker Compose
- Redis (Cache & Broker)
- Nginx (Reverse Proxy)

## 功能特性 (Features)

### 认证与授权 (Authentication & Authorization)
- **多方式登录**: 支持邮箱/密码登录，OIDC (OpenID Connect) 登录，LDAP 登录。
- **注册与找回密码**: 完整的注册流程，支持邮箱找回密码（含频率限制）。
- **JWT & Access Token**: 标准的 OAuth2 流程。
- **RBAC 权限控制**: 基于 Casbin 的角色权限控制，支持后端 API 粒度的权限管理。
- **强制登出**: 基于 Redis 黑名单机制，支持管理员强制用户下线。

### 系统管理 (System Management)
- **用户管理**: 用户的增删改查、禁用/启用、角色分配。
- **角色管理**: 自定义角色及其权限配置。
- **菜单管理**: 动态菜单配置，前端路由由后端根据用户权限动态生成。
- **API 管理**: 系统 API 的管理与权限关联。
- **系统设置**: 系统级别的参数配置。

### 业务功能 (Business Features)
- **应用管理 (Applications)**: 生成 App ID 和 App Key，用于外部系统接入。
- **任务管理 (Tasks)**:
  - **定时任务**: 支持 Crontab 表达式的定时任务调度。
  - **异步任务**: 基于 Celery 的后台长任务处理，支持任务状态查询与取消。
- **示例模块**:
  - **Items**: 基础的增删改查示例（一对多关系）。
  - **Groups**: 多对多关系示例。

### 个人中心 (User Profile)
- **个人信息**: 修改昵称、邮箱、头像（上传至 Minio）。
- **安全设置**: 修改密码。

### 基础设施与运维 (Infrastructure & DevOps)
- **数据库支持**: 兼容 PostgreSQL, MySQL, MariaDB, SQLite，通过配置切换。
- **对象存储**: 集成 Minio，支持文件上传与预签名 URL。
- **健康检查**: 系统健康状态监控。
- **Sentry 集成**: 错误追踪与监控。
- **Docker 部署**: 提供完整的 Docker Compose 编排与 Makefile 快捷命令。

## 数据库模型 (Database Models)

所有模型均继承自基础模型，包含以下通用字段：
- `id`: UUID4
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `deleted_at`: 软删除时间

## 快速开始 (Getting Started)

### 本地开发

1. **启动后端**:
   ```bash
   cd backend
   # 配置 .env 文件
   bash scripts/start-dev.sh
   ```

2. **启动前端**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Docker 部署

```bash
make up
# 或者
docker-compose up -d
```

## 目录结构 (Project Structure)

- `backend/`: FastAPI 后端代码
  - `app/api/`: API 路由定义
  - `app/core/`: 核心配置、安全、中间件
  - `app/model/`: 数据库模型 (SQLModel)
  - `app/worker/`: Celery 任务与调度
- `frontend/`: Vue 3 前端代码
  - `src/views/`: 页面视图
  - `src/store/`: Pinia 状态管理
  - `src/layout/`: 页面布局
