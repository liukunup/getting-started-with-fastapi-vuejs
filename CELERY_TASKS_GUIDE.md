# Celery任务管理系统使用指南

## 功能概述

本系统为FastAPI+Vue.js项目添加了完整的Celery任务管理功能，包括：

### 1. 任务类型
- **异步任务 (async)**
  - 创建后立即执行
  - 适用于一次性的后台任务

- **定时任务 (scheduled)**
  - 在指定时间执行
  - 适用于需要在特定时间点执行的任务

- **周期任务 (periodic)**
  - **Crontab调度**：通过Crontab表达式配置执行时间（如：每天凌晨2点、每周一等）
  - **Interval调度**：通过固定时间间隔配置（如：每5分钟、每2小时、每天等）
  - 支持复杂的定时规则

### 2. 主要功能
- ✅ 创建、编辑、删除任务
- ✅ 启用/禁用任务
- ✅ 手动触发任务执行
- ✅ 查看任务执行状态
- ✅ 查看任务执行历史记录
- ✅ 详细的执行记录追踪
- ✅ 配置任务参数（args和kwargs）
- ✅ Crontab可视化配置
- ✅ Interval可视化配置
- ✅ 获取已注册的Celery任务列表

## 数据库迁移

在使用前需要运行数据库迁移创建tasks表：

```bash
cd backend
# 运行迁移
alembic upgrade head
```

## 后端API

### 任务管理API (`/api/v1/tasks`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tasks/registered` | 获取已注册的Celery任务列表 |
| GET | `/tasks/` | 获取任务列表 |
| POST | `/tasks/` | 创建新任务 |
| GET | `/tasks/{task_id}` | 获取任务详情 |
| PUT | `/tasks/{task_id}` | 更新任务 |
| DELETE | `/tasks/{task_id}` | 删除任务 |
| POST | `/tasks/{task_id}/execute` | 手动触发任务 |
| POST | `/tasks/{task_id}/enable` | 启用任务 |
| POST | `/tasks/{task_id}/disable` | 禁用任务 |
| GET | `/tasks/{task_id}/status` | 获取任务执行状态 |
| GET | `/tasks/{task_id}/executions` | 获取任务执行记录列表 |
| GET | `/tasks/executions/{execution_id}` | 获取执行记录详情 |

## 前端界面

访问路径：`/tasks`

### 任务列表
- 显示所有任务的基本信息
- 支持搜索和排序
- 批量删除功能
- 导出CSV功能

### 创建/编辑任务

#### 基本信息
- **名称**：任务的显示名称（必填）
- **描述**：任务的详细描述（可选）

#### 任务配置
- **任务类型**：异步任务/定时任务/周期任务
- **Celery任务名称**：要执行的Celery任务（必填）
  - 从下拉列表中选择已注册的任务
  - 预定义示例任务：
    - `app.api.tasks.demo_async_task` - 演示异步任务
    - `app.api.tasks.demo_periodic_task` - 演示周期任务
    - `app.api.tasks.demo_scheduled_task` - 演示定时任务
    - `app.api.tasks.demo_dynamic_task` - 演示动态参数任务

#### 参数配置
- **Task Args**：JSON数组格式的位置参数
  - 示例：`["Hello", "World"]`
- **Task Kwargs**：JSON对象格式的关键字参数
  - 示例：`{"key": "value", "timeout": 30}`

#### 时间配置

**定时任务**
- 选择具体的执行日期和时间
- 支持手动输入或选择器选择

**周期任务**

1. **Crontab调度**
   - 分钟（0-59）：指定分钟，`*` 表示每分钟
   - 小时（0-23）：指定小时，`*` 表示每小时
   - 日期（1-31）：指定月份中的日期，`*` 表示每天
   - 月份（1-12）：指定月份，`*` 表示每月
   - 星期（0-6）：指定星期几（0=周日），`*` 表示每天

   **Crontab示例**：
   - `0 9 * * *` - 每天上午9点执行
   - `*/5 * * * *` - 每5分钟执行
   - `0 0 * * 0` - 每周日午夜执行
   - `0 0 1 * *` - 每月1号午夜执行
   - `0 */2 * * *` - 每2小时执行

2. **Interval调度**
   - 天：间隔天数（0-365）
   - 小时：间隔小时数（0-23）
   - 分钟：间隔分钟数（0-59）
   - 秒：间隔秒数（0-59）
   
   **Interval示例**：
   - 每5分钟：设置"分钟"为5
   - 每2小时：设置"小时"为2
   - 每天：设置"天"为1
   - 每30秒：设置"秒"为30
   - 每1小时30分钟：设置"小时"为1，"分钟"为30

   **注意**：至少需要设置一个时间间隔值

#### 任务控制
### 任务操作

每个任务支持以下操作：
- **查看执行记录**（📜）：查看任务的所有执行历史
- **执行**（▶️）：手动触发任务执行
- **启用/禁用**（⏸️/▶️）：切换任务启用状态
- **编辑**（✏️）：编辑任务配置
- **删除**（🗑️）：删除任务

## 执行记录

### 查看执行记录

点击任务列表中的"查看执行记录"按钮，可以看到该任务的所有执行历史，包括：

- **Celery Task ID**：Celery分配的任务ID
- **状态**：执行状态（等待中、已开始、成功、失败、重试、已撤销）
- **开始时间**：任务开始执行的时间
- **完成时间**：任务完成的时间
- **执行时长**：任务运行的时间（秒或毫秒）
- **Worker**：执行任务的Worker名称
- **结果/错误**：
  - 成功时显示执行结果（JSON格式）
  - 失败时显示错误堆栈信息

### 执行记录状态

- **pending**：等待中 - 任务已创建但尚未开始
- **started**：已开始 - 任务正在执行中
- **success**：成功 - 任务执行成功
- **failure**：失败 - 任务执行失败
- **retry**：重试 - 任务正在重试
- **revoked**：已撤销 - 任务已被撤销

### 自动记录

系统会自动为每次任务执行创建记录：
1. 任务触发时创建执行记录
2. 记录任务参数（args和kwargs）
3. 记录执行过程中的状态变化
4. 保存执行结果或错误信息
5. 计算并保存执行时长：切换任务启用状态
- **编辑**（✏️）：编辑任务配置
- **删除**（🗑️）：删除任务

## 使用示例

### 示例1：创建立即执行的单次任务

```json
{
  "name": "测试任务",
  "description": "这是一个测试任务",
  "task_type": "once",
  "execution_type": "immediate",
  "celery_task_name": "app.worker.test_celery",
  "task_args": "[\"Hello World\"]",
  "task_kwargs": "{}",
  "enabled": true
}
```

### 示例2：创建定时执行的单次任务

```json
{
  "name": "定时任务",
  "description": "在指定时间执行",
  "task_type": "once",
  "execution_type": "scheduled",
  "celery_task_name": "app.worker.long_running_task",
  "task_args": "[60]",
  "task_kwargs": "{}",
  "scheduled_time": "2025-12-02T15:00:00",
  "enabled": true
}
```

### 示例3：创建每天执行的循环任务

```json
{
  "name": "每日任务",
  "description": "每天凌晨1点执行",
  "task_type": "periodic",
  "celery_task_name": "app.worker.test_celery",
  "task_args": "[\"Daily Task\"]",
  "task_kwargs": "{}",
  "crontab_minute": "0",
  "crontab_hour": "1",
  "crontab_day_of_month": "*",
  "crontab_month_of_year": "*",
  "crontab_day_of_week": "*",
  "enabled": true
}
```

### 示例4：创建每5分钟执行的循环任务

```json
{
  "name": "频繁任务",
### 数据库
- **表名**：`tasks`, `task_executions`
- **迁移文件**：
  - `backend/app/alembic/versions/add_tasks_table.py` - 创建tasks表
  - `backend/app/alembic/versions/add_task_executions.py` - 创建task_executions表
  "task_args": "[]",
  "task_kwargs": "{\"check\": \"health\"}",
  "crontab_minute": "*/5",
  "crontab_hour": "*",
  "crontab_day_of_month": "*",
  "crontab_month_of_year": "*",
  "crontab_day_of_week": "*",
  "enabled": true
}
```

## 注意事项

1. **Celery Worker必须运行**：任务执行需要Celery Worker在后台运行
2. **任务名称必须存在**：确保指定的Celery任务名称已在worker中注册
3. **JSON格式验证**：task_args和task_kwargs必须是有效的JSON格式
4. **时区问题**：定时任务使用UTC时间，需要注意时区转换
5. **权限控制**：普通用户只能管理自己创建的任务，超级用户可以管理所有任务

## 技术架构

### 后端
- **模型**：`app/model/task.py` - 任务数据模型定义
- **CRUD**：`app/crud/task.py` - 数据库操作
- **API**：`app/api/routes/task.py` - REST API接口
- **Worker**：`app/worker.py` - Celery任务定义

### 前端
- **页面**：`frontend/src/views/management/Tasks.vue` - 任务管理页面
- **路由**：已添加到`/tasks`路径
- **API客户端**：`frontend/src/client/sdk.gen.ts` - TaskService

### 数据库
- **表名**：`tasks`
- **迁移文件**：`backend/app/alembic/versions/add_tasks_table.py`

## 扩展开发

### 添加新的Celery任务

1. 在`backend/app/worker.py`中定义新任务：

```python
@celery_app.task(acks_late=True)
def my_custom_task(param1: str, param2: int) -> dict:
    # 任务逻辑
    return {"result": "success"}
```

2. 在前端`Tasks.vue`的`predefinedTasks`中添加选项：

```javascript
const predefinedTasks = [
    // ... 现有任务
    { label: 'My Custom Task', value: 'app.worker.my_custom_task' }
];
```

### 自定义任务调度

对于需要更复杂调度逻辑的场景，可以：
1. 使用Celery Beat定期扫描数据库中的任务
2. 根据任务配置动态创建Celery任务
3. 更新任务的执行状态和下次执行时间

## 故障排查

### 任务无法执行
1. 检查Celery Worker是否运行
2. 检查Redis连接是否正常
3. 查看Celery日志确认错误信息

### 定时任务不执行
1. 对于单次定时任务，检查scheduled_time是否正确
2. 对于循环任务，检查crontab配置是否正确
3. 确认任务的enabled状态为true

### 前端显示异常
1. 检查浏览器控制台错误信息
2. 确认API返回数据格式正确
3. 检查TaskService是否正确导入
