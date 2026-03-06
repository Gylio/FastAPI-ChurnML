from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.schemas import ModelVersionResponse, ModelSwitchRequest, ErrorResponse
from app.models.model_manager import list_models, load_model, get_model_version
from app.services.stats_service import record_request
from app.core.logging import setup_logging
import time
import uuid

# 初始化日志器
logger = setup_logging("app")

# 创建路由器
router = APIRouter(
    prefix="/api/model",
    tags=["model"],
    responses={404: {"description": "Not found"}},
)

@router.get("/version", response_model=ModelVersionResponse, summary="查看可用模型版本")
async def get_model_versions():
    """
    查看可用模型版本
    
    返回所有可用的模型版本列表和当前使用的模型版本
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 获取可用模型版本
        models = list_models()
        
        # 获取当前模型版本
        current_version = get_model_version()
        
        # 转换为响应格式
        versions = []
        for model in models:
            versions.append({
                "version": model["version"],
                "filename": model["filename"],
                "path": model["path"]
            })
        
        response = ModelVersionResponse(
            versions=versions,
            current_version=current_version
        )
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录请求
        record_request(successful=True, response_time=response_time)
        
        logger.info(f"查看模型版本成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒")
        return response
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录失败请求
        record_request(successful=False, response_time=response_time)
        
        logger.error(f"查看模型版本失败，请求ID: {request_id}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="查看模型版本失败",
                request_id=request_id,
                details=str(e)
            ).dict()
        )

@router.post("/switch", response_model=ModelVersionResponse, summary="切换默认模型")
async def switch_model(
    request: ModelSwitchRequest
):
    """
    切换默认模型
    
    - **version**: 要切换的模型版本号
    
    返回切换后的模型版本信息
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 加载指定版本的模型
        load_model(request.version)
        
        # 获取可用模型版本
        models = list_models()
        
        # 获取当前模型版本
        current_version = get_model_version()
        
        # 转换为响应格式
        versions = []
        for model in models:
            versions.append({
                "version": model["version"],
                "filename": model["filename"],
                "path": model["path"]
            })
        
        response = ModelVersionResponse(
            versions=versions,
            current_version=current_version
        )
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录请求
        record_request(successful=True, response_time=response_time)
        
        logger.info(f"切换模型成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 新模型版本: {current_version}")
        return response
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录失败请求
        record_request(successful=False, response_time=response_time)
        
        logger.error(f"切换模型失败，请求ID: {request_id}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="切换模型失败",
                request_id=request_id,
                details=str(e)
            ).dict()
        )
