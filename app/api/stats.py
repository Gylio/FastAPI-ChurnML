from fastapi import APIRouter, HTTPException
from app.schemas.schemas import StatsResponse, HealthCheckResponse, ErrorResponse
from app.services.stats_service import get_stats
from app.models.model_manager import get_current_model
from app.core.logging import setup_logging
import time
import uuid
from datetime import datetime

# 初始化日志器
logger = setup_logging("app")

# 创建路由器
router = APIRouter(
    prefix="/api",
    tags=["stats"],
    responses={404: {"description": "Not found"}},
)

@router.get("/stats", response_model=StatsResponse, summary="监控统计接口")
async def get_statistics():
    """
    监控统计接口
    
    返回模型请求量、准确率、异常请求数等统计数据
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 获取统计数据
        stats = get_stats()
        
        # 构建响应
        response = StatsResponse(
            total_requests=stats.get('total_requests', 0),
            successful_requests=stats.get('successful_requests', 0),
            failed_requests=stats.get('failed_requests', 0),
            accuracy=stats.get('accuracy'),
            average_response_time=stats.get('average_response_time', 0.0),
            last_update=stats.get('last_update', datetime.now().isoformat())
        )
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        logger.info(f"获取统计数据成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒")
        return response
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        logger.error(f"获取统计数据失败，请求ID: {request_id}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="获取统计数据失败",
                request_id=request_id,
                details=str(e)
            ).dict()
        )

@router.get("/health", response_model=HealthCheckResponse, summary="健康检查接口")
async def health_check():
    """
    健康检查接口
    
    返回服务状态和模型状态
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 检查模型状态
        model = get_current_model()
        model_status = "健康" if model else "未加载"
        
        # 构建响应
        response = HealthCheckResponse(
            status="健康",
            model_status=model_status,
            timestamp=datetime.now().isoformat()
        )
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        logger.info(f"健康检查成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 模型状态: {model_status}")
        return response
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        logger.error(f"健康检查失败，请求ID: {request_id}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="健康检查失败",
                request_id=request_id,
                details=str(e)
            ).dict()
        )
