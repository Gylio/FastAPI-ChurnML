from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
from app.schemas.schemas import ChurnPredictInput, ChurnPredictOutput, ErrorResponse
from app.services.predict_service import predict_single
from app.services.stats_service import record_request
from app.services.prediction_log_service import log_single_prediction
from app.models.model_manager import model_manager
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
    request: Request,
    input_data: ChurnPredictInput,
    model_version: Optional[int] = Query(None, description="模型版本号"),
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

        # 计算本次使用的模型版本（字符串），用于日志：
        # 1. 优先使用预测结果里返回的版本
        # 2. 否则使用当前模型管理器版本
        # 3. 兜底 v2（预测日志服务内部也会再次兜底）
        current_version = model_manager.get_model_version()
        effective_version = (
            result.model_version
            or (f"v{current_version}" if current_version is not None else "v2")
        )

        # 记录预测日志（单条）
        user = getattr(request.state, "user", None)
        user_id = user.get("user_id") if isinstance(user, dict) else None
        try:
            log_single_prediction(
                user_id=user_id,
                model_version=effective_version,
                features=input_data.dict(),
                prediction_label=result.prediction,
                prediction_probability=result.probability,
            )
        except Exception as log_err:
            logger.error(f"记录单条预测日志失败: {log_err}")
        
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
