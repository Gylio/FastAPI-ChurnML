# 用户流失预测系统（FastAPI + ML）

## 一、项目简介

本项目实现了一个完整的 **用户流失预测 Web 系统**，包含：
- 基于 `Telco Customer Churn` 数据集训练的机器学习模型（随机森林，多版本管理）  
- 使用 **FastAPI** 提供的 RESTful API 层  
- 基于 Jinja2 + 原生 JS + ECharts 的前端界面  
- 简单的用户注册 / 登录与会话管理  
- 预测日志记录、模型版本切换、监控可视化等工程能力

功能覆盖：
- 单条预测：通过表单输入用户特征，实时返回流失概率
- 批量预测：上传 CSV/Excel 文件，进行批量预测并支持结果下载
- 模型管理：列出模型版本、在线切换当前 serving 模型（v1/v2）
- 监控可视化：展示请求统计、模型准确率走势，并挂载离线训练/EDA 报告
- 认证与授权：未登录不能访问预测/监控等核心页面和 API

## 二、项目结构

```text
app/
  api/           # API 路由层（predict、batch、model、stats、auth）
  core/          # 配置、日志、中间件
  models/        # 模型管理（加载、预测、版本管理）
  schemas/       # Pydantic 数据模型与 API schema
  services/      # 业务服务：预测、统计、认证、会话、预测日志等
  static/        # 前端静态资源（CSS / JS）
  templates/     # Jinja2 模板（页面）
  main.py        # FastAPI 应用入口

ml_pipeline/
  data/          # 原始数据集
  data_prep.py   # 预处理与特征工程
  explore_data.py / simple_explore.py  # EDA 与可视化
  train.py / simple_train.py           # 模型训练、调参与模型导出

docs/
  model_design.md        # 模型设计与训练文档
  api_reference.md       # API 说明（由本次补充）
  system_architecture.md # 系统架构与部署说明（由本次补充）

tests/
  test_basic_api.py      # 基础 API 测试用例

saved_models/            # 训练好的模型文件（churn_pred_v1.pkl / v2.pkl）
logs/                    # 按模块划分的日志（app / train / explore / prediction_log）
```

## 三、运行与调试

### 1. 环境准备

- Python ≥ 3.12
- 建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements/base.txt
```

### 2. 启动 Web 服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后可访问：
- 前端页面：首页（单条预测）：`http://localhost:8000/`
- 批量预测页面：`http://localhost:8000/batch`
- 监控可视化：`http://localhost:8000/monitor`
- API 文档：`http://localhost:8000/docs`

首次访问需要先注册 / 登录：
- 注册页面：`/api/auth/register`
- 登录页面：`/api/auth/login`

系统使用 **HttpOnly Cookie（session_id）+ 自定义中间件** 做登录态校验，未登录访问受保护 API 会返回 `401 Unauthorized`。

### 3. 训练模型与生成报告（可选）

在本地重新训练模型、生成报告：

```bash
python -m ml_pipeline.train          # 完整训练 pipeline，生成 v1/v2 模型和报告
python -m ml_pipeline.explore_data   # 生成 EDA 报告和图片
```

输出：
- 模型文件：`saved_models/churn_pred_v1.pkl`、`saved_models/churn_pred_v2.pkl`
- 报告与图：`ml_pipeline/reports/*.png`、`ml_pipeline/reports/eda_report.html`

在应用启动时，`app.main` 会将 `ml_pipeline/reports` 挂载为静态目录：
- 访问路径前缀：`/ml-reports`
- 例如：`/ml-reports/eda_report.html`、`/ml-reports/model_comparison.png`

监控页面中提供按钮可以直接打开这些报告。

### 4. 运行测试

使用 `pytest` 运行基础用例：

```bash
pytest
```

当前覆盖：
- `/api/health`、`/api/stats` 基础可用性
- 注册 + 登录全流程（包含 session_id cookie）
- 未登录访问 `/api/predict` 被中间件拦截
- 批量上传不支持的文件类型时，API 返回结构化错误

## 四、核心功能说明

### 1. 单条预测

- 接口：`POST /api/predict`
- 请求体：`ChurnPredictInput`（Pydantic 校验）
- 响应体：`ChurnPredictOutput`，字段包括：
  - `prediction`: `"Yes"` / `"No"`
  - `probability`: 流失概率（0–1）
  - `features`: 原始输入特征
  - `model_version`: 当前使用的模型版本（如 `"v2"`）

预测流程：
1. 认证中间件校验登录与会话
2. `PredictService.preprocess_input` 做数值转换、缺失值填补与编码
3. `ModelManager` 加载指定/当前模型并预测
4. 将结果写入 SQLite 的 `prediction_items` 表（包含特征、标签、概率、模型版本等）

### 2. 批量预测

- 接口：`POST /api/batch-predict`
- 入参：`file`（CSV/Excel），可选 `model_version`
- 响应体：`BatchPredictOutput`（列表 + 汇总统计 + 下载链接）

容错逻辑：
- 自动预处理 `TotalCharges` 缺失值和其他缺失值
- 对字符串列做简单编码，移除 `customerID`，必要时丢弃/补齐列并与模型训练列对齐
- 若模型完全无法处理（列差异过大等），返回带中文错误信息的 `ErrorResponse`，前端会直接展示：

> 上传的数据列与模型期望差异过大，无法进行批量预测，请检查字段名和格式是否正确

日志记录：
- 在 `prediction_batches` / `prediction_items` 中记录整批预测统计与每条记录，默认模型版本写入 `v2`，如在监控页面切换到 `v1`，则新日志会写入 `v1`。

### 3. 模型版本管理

- 接口：
  - `GET /api/model/version`：列出所有模型版本、当前版本
  - `POST /api/model/switch`：切换默认模型（如 v1 ↔ v2）
- 前端在监控页提供下拉选择与“切换模型”按钮，切换后：
  - 预测服务使用新的模型版本
  - 预测日志中的 `model_version` 同步记录新版本号

### 4. 监控与日志

- `/api/stats` 提供：
  - 总请求数 / 成功数 / 失败数
  - 近似准确率、平均响应时间等
- `/api/health` 提供健康检查（应用/模型状态）
- 日志：
  - `logs/app/app.log`：Web 层与业务日志
  - `logs/train/app.log`：训练流程日志
  - `logs/explore/app.log`：EDA 日志
  - `logs/prediction_log/app.log`：预测日志写入相关

前端监控页使用 ECharts 展示请求趋势、模型准确率变化和异常分布，并通过按钮打开离线报告图片。

## 五、技术栈

- **语言**：Python 3.12
- **Web 框架**：FastAPI
- **模型与数据处理**：scikit-learn、pandas、numpy、joblib
- **配置与校验**：pydantic / pydantic-settings
- **前端可视化**：ECharts + 原生 JS
- **数据库**：SQLite（`auth.db`，用于用户表 + 预测日志）
- **测试**：pytest + FastAPI TestClient
- **日志**：标准库 logging，多 logger 分模块输出

（可选）后续可扩展：
- Docker 镜像打包部署
- 细粒度权限与角色管理
- 更完整的 A/B 测试与模型对比分析
