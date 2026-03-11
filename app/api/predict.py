from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.schemas import ChurnPredictInput, ChurnPredictOutput, ErrorResponse
from app.services.predict_service import predict_single
from app.services.stats_service import record_request
from app.core.logging import setup_logging
import time
import uuid

# 初始化日志器
logger = setup_logging("app")

# 创建路由器
router = APIRouter(
    prefix="/api",
    tags=["predict"],
    responses={404: {"description": "Not found"}},
)

@router.post("/predict", response_model=ChurnPredictOutput, summary="单条预测接口")
async def predict(
    input_data: ChurnPredictInput,
    model_version: Optional[int] = Query(None, description="模型版本号")
):
    """
    单条预测接口
    
    - **input_data**: 预测输入数据，包含用户的各种特征
    - **model_version**: 可选，指定使用的模型版本
    
    返回预测结果，包括预测标签、流失概率、输入特征值和使用的模型版本
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 执行预测
        result = predict_single(input_data, model_version)
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录请求
        record_request(request_type="single", successful=True, response_time=response_time, request_id=request_id)
        
        logger.info(f"单条预测成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒")
        return result
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录失败请求
        record_request(request_type="single", successful=False, response_time=response_time, request_id=request_id)
        
        logger.error(f"单条预测失败，请求ID: {request_id}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="预测失败",
                request_id=request_id,
                details=str(e)
            ).dict()
        )
