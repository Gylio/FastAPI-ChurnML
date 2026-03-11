# API 文档概览

> 说明：系统完整的交互式接口文档可通过运行服务后访问 `/docs`（Swagger UI）或 `/redoc` 查看。本文件给出关键接口的一览和使用示例。

## 1. 认证相关

### 1.1 用户注册

- **URL**: `POST /api/auth/register`
- **说明**: 创建新用户账户
- **请求体 (JSON)**:

```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

- **响应体**:

```json
{
  "success": true,
  "message": "注册成功"
}
```

### 1.2 用户登录

- **URL**: `POST /api/auth/login`
- **说明**: 登录成功后由服务端设置 `session_id` HttpOnly Cookie
- **请求体 (JSON)**:

```json
{
  "username": "string",
  "password": "string"
}
```

- **响应体**:

```json
{
  "success": true,
  "message": "登录成功",
  "user_id": 1,
  "username": "demo",
  "session_id": "uuid-..."
}
```

### 1.3 获取当前用户

- **URL**: `GET /api/auth/me`
- **说明**: 基于 Cookie 中的 `session_id` 返回当前登录用户；未登录返回 401。

### 1.4 退出登录

- **URL**: `POST /api/auth/logout`
- **说明**: 清理服务端会话并删除 Cookie。

---

## 2. 预测相关

### 2.1 单条预测

- **URL**: `POST /api/predict`
- **说明**: 提交单个用户特征，预测是否流失（需要登录）
- **请求体 (JSON)**: 对应 `ChurnPredictInput`，字段较多，示例：

```json
{
  "gender": "Male",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 12,
  "PhoneService": "Yes",
  "MultipleLines": "No",
  "InternetService": "DSL",
  "OnlineSecurity": "No",
  "OnlineBackup": "Yes",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "No",
  "StreamingMovies": "No",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 70.35,
  "TotalCharges": 845.5
}
```

- **查询参数**（可选）:
  - `model_version: int` 指定模型版本号（如 `1` 或 `2`）

- **响应体**:

```json
{
  "prediction": "Yes",
  "probability": 0.73,
  "features": { "...": "..." },
  "model_version": "v2"
}
```

### 2.2 批量预测

- **URL**: `POST /api/batch-predict`
- **说明**: 通过 CSV/Excel 文件进行批量预测（需要登录）
- **表单字段**:
  - `file`: CSV/Excel 文件
- **查询参数（可选）**:
  - `model_version: int` 指定使用 `v1` 或 `v2`

- **响应体**:

```json
{
  "items": [
    {
      "customerID": "1234-AAAA",
      "prediction": "No",
      "probability": 0.12
    }
  ],
  "total_count": 1,
  "churn_count": 0,
  "non_churn_count": 1,
  "download_url": "/api/download?file=..."
}
```

- **容错错误示例**（字段不匹配等）:

```json
{
  "detail": {
    "error_code": 500,
    "error_message": "上传的数据列与模型期望差异过大，无法进行批量预测，请检查字段名和格式是否正确",
    "request_id": "...",
    "details": "..."
  }
}
```

### 2.3 下载批量结果

- **URL**: `GET /api/download?file=...`
- **说明**: 下载批量预测结果 CSV。

---

## 3. 模型版本管理

### 3.1 查看可用模型版本

- **URL**: `GET /api/model/version`
- **响应体**:

```json
{
  "versions": [
    {
      "version": 1,
      "filename": "churn_pred_v1.pkl",
      "path": "..."
    },
    {
      "version": 2,
      "filename": "churn_pred_v2.pkl",
      "path": "..."
    }
  ],
  "current_version": 2
}
```

### 3.2 切换模型版本

- **URL**: `POST /api/model/switch`
- **请求体 (JSON)**:

```json
{
  "version": 1
}
```

- **说明**: 切换后新的预测会使用该版本模型，并在预测日志里记录为 `v1` / `v2`。

---

## 4. 监控与健康检查

### 4.1 监控统计

- **URL**: `GET /api/stats`
- **响应体**（精简）:

```json
{
  "total_requests": 100,
  "successful_requests": 95,
  "failed_requests": 5,
  "accuracy": 0.86,
  "average_response_time": 0.045,
  "last_update": "2026-03-11T11:00:00"
}
```

### 4.2 健康检查

- **URL**: `GET /api/health`
- **响应体**:

```json
{
  "status": "健康",
  "model_status": "健康",
  "timestamp": "2026-03-11T11:00:00"
}
```

---

## 5. 错误响应格式

所有业务错误尽量使用统一的 `ErrorResponse`：

```json
{
  "detail": {
    "error_code": 500,
    "error_message": "批量预测失败",
    "request_id": "uuid-...",
    "details": "具体错误信息"
  }
}
```

前端通常只需要展示 `detail.error_message` 即可向用户说明问题。

