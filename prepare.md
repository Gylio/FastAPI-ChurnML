# 前期准备



## 技术栈选型

### 核心语言：Python 3.12

### Web框架：FastAPI (满足高性能、异步 和 自动文档生成 需求)

### 机器学习：scikit-learn，pandas，numpy，joblib

### 数据处理：pydantic

### 可视化：ECharts (前端渲染)

### 测试工具：pytest (单元测试)，locust (性能/并发测试)，coverage.py (覆盖率统计)

### 版本控制：Github

### *容器化(可选)：Docker，Docker Compose (便于部署 和 环境隔离)



## 项目结构

```plaintext
project/
├── app/
│   ├── api/            # API路由 (predict, batch, stats)
│   ├── core/           # 配置、日志、异常处理
│   ├── models/         # 模型加载器、版本管理器
│   ├── schemas/        # Pydantic数据模型 (输入/输出校验)
│   ├── services/       # 业务逻辑 (预处理、预测、统计)
│   ├── static/         # 前端页面、JS、CSS
│   └── templates/      # 存放HTML模板（FastAPI+Jinja2可视化页面）
├── ml_pipeline/        # 独立于Web的训练代码
│   ├── data/           # 存放训练/测试数据集（便于版本管理）
│   ├── data_prep.py    # 数据预处理组件
│   ├── train.py        # 模型训练脚本
│   └── reports/        # 生成的训练报告
├── tests/              # 测试代码 (unit, integration, load)
│   ├── unit/           # 单元测试（模型、预处理、接口）
│   ├── integration/    # 集成测试（端到端）
│   └── performance/    # 性能测试（响应时间、并发）
├── logs/               # 运行日志
├── saved_models/       # 存放 .pkl 模型文件 (v1, v2...)
├── requirements/       # 存放依赖
│   ├── base.txt        # 开发环境
│   ├── dev.txt			# 生产环境
├── Dockerfile
├── .gitignore          # Git忽略文件（日志、模型、依赖缓存）
└── docs/               # 工程文档
    ├── model_design.md # 模型设计文档
    ├── api_docs.md     # API接口文档
    └── test_reports/   # 测试报告存放
```

