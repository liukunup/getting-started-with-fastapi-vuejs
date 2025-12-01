# 快速入门指南 (FastAPI & Vue.js)

本项目是一个基于 FastAPI 和 Vue 3 的全栈应用模板，集成了 PostgreSQL, Redis, MinIO 等常用组件，旨在帮助开发者快速搭建现代化的单体应用。

## 📋 目录

- [技术栈](#技术栈)
- [前置要求](#前置要求)
- [🚀 快速启动 (Docker)](#-快速启动-docker-方式---推荐)
- [💻 本地开发指南](#-本地开发指南)
- [📂 项目结构](#-项目结构)
- [✨ 功能特性](#-功能特性)

## 技术栈

- **后端**: FastAPI, SQLModel (SQLAlchemy + Pydantic), PostgreSQL, Redis, MinIO, Celery
- **前端**: Vue 3, Vite, PrimeVue, Tailwind CSS
- **基础设施**: Docker, Docker Compose

## 前置要求

- **Docker & Docker Compose** (推荐，运行完整环境)
- **Node.js** >= 18 (仅本地前端开发需要)
- **Python** >= 3.10 (仅本地后端开发需要)

## 🚀 快速启动 (Docker 方式 - 推荐)

这是运行本项目的最简单方式，无需在本地安装 Python 或 Node.js 环境。

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd getting-started-with-fastapi-vuejs
   ```

2. **配置环境变量**
   项目根目录下包含一个 `.env` 文件，其中定义了数据库密码、密钥等敏感信息。首次运行时请检查并根据需要修改。

3. **启动服务**
   使用 Make 命令一键启动：
   ```bash
   make build  # 构建镜像
   make up     # 启动服务
   ```
   或者直接使用 Docker Compose：
   ```bash
   docker-compose up -d --build
   ```

4. **访问应用**
   服务启动后，可以通过以下地址访问：
   - **前端页面**: http://localhost:5173 (端口可能根据配置有所不同)
   - **后端 API 文档**: http://localhost:8000/docs
   - **MinIO 控制台**: http://localhost:9001 (默认账号密码请查看 docker-compose.yml)

5. **停止服务**
   ```bash
   make down
   ```

## 💻 本地开发指南

如果你希望在本地运行代码以便于调试和开发，请按照以下步骤操作。

### 后端 (Backend)

1. **进入后端目录**
   ```bash
   cd backend
   ```

2. **创建并激活虚拟环境**
   推荐使用 `uv` 进行包管理，也可以使用 `pip`。

   **使用 uv (推荐):**
   ```bash
   # 安装依赖
   uv sync
   # 激活环境
   source .venv/bin/activate
   ```

   **使用 pip:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. **启动依赖服务**
   本地开发时，你仍然需要数据库和缓存服务。可以使用 Docker 仅启动这些服务：
   ```bash
   # 在项目根目录执行
   docker-compose up -d postgres redis minio
   ```

4. **初始化数据库**
   运行 Alembic 迁移以创建数据库表结构：
   ```bash
   # 确保在 backend 目录下且已激活虚拟环境
   alembic upgrade head
   
   # 初始化数据 (可选)
   python app/initial_data.py
   ```

5. **启动后端服务**
   ```bash
   # 开发模式启动
   fastapi dev app/main.py
   
   # 或者使用 uvicorn
   uvicorn app.main:app --reload
   ```

### 前端 (Frontend)

1. **进入前端目录**
   ```bash
   cd frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```
   访问终端输出的本地地址 (通常是 http://localhost:5173) 开始开发。

## 📂 项目结构

```text
.
├── backend/             # FastAPI 后端代码
│   ├── app/             # 应用核心逻辑
│   │   ├── api/         # API 路由定义
│   │   ├── core/        # 核心配置 (Config, Security, DB)
│   │   ├── crud/        # 数据库 CRUD 操作封装
│   │   ├── model/       # SQLModel 数据模型
│   │   └── ...
│   ├── alembic/         # 数据库迁移脚本
│   └── tests/           # 测试用例
├── frontend/            # Vue 3 前端代码
│   ├── src/
│   │   ├── views/       # 页面视图
│   │   ├── components/  # Vue 组件
│   │   ├── service/     # API 请求服务封装
│   │   ├── layout/      # 页面布局组件
│   │   └── ...
├── docker-compose.yml   # Docker 服务编排
├── Makefile             # 常用命令快捷方式
└── README.md            # 项目说明
```

## ✨ 功能特性

- **用户系统**: 完整的注册、登录、找回密码流程。
- **权限控制**: 基于角色的访问控制 (RBAC)，支持管理员管理用户。
- **数据展示**: 封装好的表格展示、增删改查 (CRUD) 界面。
- **后台任务**: 集成 Celery 处理异步任务和定时任务。
- **文件存储**: 支持头像等文件上传至 MinIO。
- **API 安全**: 支持 JWT 认证和 API Key 访问。

---
Happy Coding! 🚀
