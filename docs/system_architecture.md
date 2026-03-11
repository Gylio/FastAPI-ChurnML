# 系统架构与部署说明

## 1. 总体架构

系统采用典型的「前后端一体 + 模型服务内嵌」架构：

- **前端视图**：Jinja2 模板 + 原生 JS，运行在 FastAPI 同一进程内
- **API 层**：FastAPI 路由，提供认证、预测、模型管理、监控等接口
- **服务层 (Service)**：封装预测、统计、认证/会话与预测日志逻辑
- **模型层 (ModelManager)**：统一管理模型文件的加载、切换与预测
- **离线任务 (ml_pipeline)**：数据预处理、EDA 与模型训练，产出模型文件与报告
- **存储**：
  - SQLite (`auth.db`)：用户表 + 预测日志表
  - 文件系统：模型文件、日志文件、训练/EDA 报告

### 目录与模块关系

- `app/main.py`：应用入口，挂载静态资源、模板和 API Router，注册认证中间件
- `app/api/*`：每个文件对应一个业务域：
  - `predict.py`：单条预测
  - `batch.py`：批量预测与结果下载
  - `model.py`：模型版本查询与切换
  - `stats.py`：监控与健康检查
  - `auth.py`：注册、登录、登出与认证页面
- `app/services/*`：
  - `predict_service.py`：单条/批量预测预处理 + 调用 `ModelManager`
  - `stats_service.py`：请求统计
  - `auth_service.py`：用户表读写（SQLite）
  - `session_service.py`：内存会话管理
  - `prediction_log_service.py`：预测日志写入与反馈
- `ml_pipeline/*`：离线数据流（不在在线请求路径内）

## 2. 请求流转示例

### 2.1 单条预测

1. 浏览器访问 `/predict` 页面，填写特征并点击提交
2. JS 调用 `POST /api/predict`，带上 JSON 请求体
3. 认证中间件读取 `session_id` Cookie，校验用户是否登录
4. `app/api/predict.py` 接收请求，调用 `predict_service.predict_single`
5. `PredictService`：
   - 使用 `DataPreprocessor` 预处理输入（编码、标准化）
   - 通过 `ModelManager` 加载当前模型并进行预测
6. 将结果包装成 `ChurnPredictOutput`，返回给前端
7. 同时调用 `prediction_log_service.log_single_prediction` 写入预测日志

### 2.2 批量预测

1. 浏览器在 `/batch` 页面选择 CSV/Excel 文件上传
2. JS 调用 `POST /api/batch-predict` 上传文件
3. 中间件校验登录态
4. `app/api/batch.py` 保存上传文件到临时目录，并调用 `predict_service.predict_batch`
5. `PredictService`：
   - 使用 pandas 读取文件，进行缺失值/类型处理
   - 尝试对齐列到模型训练特征；如失败则返回空结果
6. API 层检查 `total_count`，为 0 时返回友好错误提示
7. 正常情况下，结果通过 `save_batch_results` 写入临时 CSV，并生成下载链接
8. `prediction_log_service.log_batch_prediction` 记录本次批量预测的批次和明细日志

## 3. 模型版本管理机制

- 模型文件命名：`saved_models/churn_pred_v{version}.pkl`
- `ModelManager` 负责：
  - 扫描 `MODEL_DIR` 获取可用版本列表
  - 根据版本号加载对应模型（以及预处理器）
  - 缓存当前模型与版本号（`current_model` / `current_version`）
- API 层：
  - `GET /api/model/version` 返回可用版本和当前版本
  - `POST /api/model/switch` 调用 `ModelManager.load_model` 切换版本
- 预测日志中 `model_version` 的写入策略：
  - 若用户在请求中指定 `model_version`，日志记录为 `v{model_version}`
  - 否则读取 `ModelManager.current_version` 记录为 `v{current_version}`
  - 若仍为空，则默认写入 `v2`

## 4. 部署与运行

### 4.1 本地开发环境

1. 克隆代码并进入项目目录
2. 创建虚拟环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt
```

3. 启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. 可选：运行 `ml_pipeline/train.py` 和 `ml_pipeline/explore_data.py` 更新模型与报告。

### 4.2 生产部署建议

- 使用 `gunicorn + uvicorn workers` 或 `uvicorn` behind Nginx：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- 建议：
  - 将 `logs/` 和 `saved_models/` 目录挂载到持久化存储
  - 配置 Nginx 反向代理与静态资源缓存（`/static`、`/ml-reports`）
  - 若流量较大，可将模型预测拆分为独立服务（微服务化）

## 5. 安全与权限

- 用户密码使用 PBKDF2 + 随机盐存储在 SQLite 中
- 会话使用 UUID 作为 `session_id`，保存在内存的 `SessionService` 中，有过期时间
- 中间件对以下路径放行：
  - `/api/auth/*`、`/docs`、`/redoc`、`/openapi.json`、`/static`、`/ml-reports`
- 其余 `/api/*` 请求必须携带有效 `session_id` Cookie，否则返回 401

## 6. 日志与监控

- 所有模块使用统一的日志封装 `setup_logging`，输出到 `logs/*/app.log`
- 监控统计由 `stats_service` 维护，并通过 `/api/stats` 对外暴露
- 监控页面使用 ECharts 展示请求趋势、准确率与异常分布，同时提供入口查看训练/EDA 报告

