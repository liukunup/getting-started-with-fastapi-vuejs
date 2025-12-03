# Getting started with FastAPI & Vue.js

for AI Coding with FastAPI &amp; Vue 3

目标是在AI Coding加持下，快速实现单体应用程序

## 技术栈

- FastAPI
- Vue 3
- PrimeVue

## 功能路线

- 注册（邮箱、密码、昵称可选）
- 登陆（邮箱/用户名、密码）邮箱前缀提取用户名
- 找回密码（邮箱，限制每天最多3次）
- 支持 jwt， access token
- 管理员功能
  - 用户的新增、删除、禁用、强制退出登陆态（通过redis黑名单实现），前端表格展示
  - 修改用户角色
- 我的（支持头像、邮箱、密码、昵称、用户名的修改，头像存储到minio）
- RBAC权限（后端管控，有对应功能点才能拉取到数据，否则前端展示无权限空态图）casbin
- 支持minio、redis、postgresql
- 数据库支持了"sqlite", "mysql", "postgres", "mariadb"
- 健康检查
- demo功能
  - 定时任务 支持corntab
  - 请求时异步执行后台长任务（提交/查询/取消）
  - items 增删查改/表格展示（一个user对应多个items）
  - groups 增删查改/表格展示（与user多对多）
- 支持生成app_id app_key来访问系统开发接口
- 前后端打包到一个docker镜像


## 数据库表

- id uuid4
- created_at
- updated_at
- deleted_at

## 部署

- makefile
- docker-compose.yml
- 支持https

## 步骤

1. 设计数据库表（启动）
2. 实现功能
3. 代码善后
4. 生成文档，方便后续ai开发

docker compose 优化

AI对话接入
权限与动态菜单
强制登出
整体测试
