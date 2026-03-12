from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.api import predict, batch, model, stats, auth
from app.core.logging import setup_logging
from app.core.config import BASE_DIR as PROJECT_ROOT
from app.core.middleware import auth_middleware
from app.models.model_manager import model_manager
import uvicorn
from pathlib import Path

# 初始化日志器
logger = setup_logging("app")

# 获取应用根目录（app 目录）
BASE_DIR = Path(__file__).resolve().parent

# 创建FastAPI应用实例
app = FastAPI(
    title="用户流失预测API",
    description="基于FastAPI的用户流失预测Web服务，支持单条预测、批量预测、模型管理和监控统计",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "syntaxHighlight": {
            "activated": True,
            "theme": "monokai"
        },
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True
    }
)

# 配置静态文件
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

ML_REPORTS_DIR = PROJECT_ROOT / "ml_pipeline" / "reports"
ML_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/ml-reports", StaticFiles(directory=ML_REPORTS_DIR), name="ml_reports")

# 配置模板引擎
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册认证中间件
app.middleware("http")(auth_middleware)

# 注册API路由
app.include_router(predict.router)
app.include_router(batch.router)
app.include_router(model.router)
app.include_router(stats.router)
app.include_router(auth.router)

# 前端页面路由
@app.get("/", tags=["frontend"])
async def home(request: Request):
    """
    首页
    
    重定向到单条预测页面
    """
    return templates.TemplateResponse("predict.html", {"request": request})

@app.get("/predict", tags=["frontend"])
async def predict_page(request: Request):
    """
    单条预测页面
    """
    return templates.TemplateResponse("predict.html", {"request": request})

@app.get("/batch", tags=["frontend"])
async def batch_page(request: Request):
    """
    批量预测页面
    """
    return templates.TemplateResponse("batch.html", {"request": request})

@app.get("/monitor", tags=["frontend"])
async def monitor_page(request: Request):
    """
    监控可视化页面
    """
    return templates.TemplateResponse("monitor.html", {"request": request})

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时加载模型"""
    logger.info("应用启动，加载模型...")
    try:
        # 尝试加载最新版本的模型
        model_manager.get_current_model()
        logger.info("模型加载成功")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("应用关闭，清理资源...")



# 运行应用
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
