from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from typing import Optional
from app.schemas.schemas import BatchPredictOutput, ErrorResponse
from app.services.predict_service import predict_batch, save_batch_results
from app.services.stats_service import record_request
from app.services.prediction_log_service import log_batch_prediction
from app.models.model_manager import model_manager
from app.core.logging import setup_logging
import time
import uuid
import os
import tempfile

# 初始化日志器
logger = setup_logging("app")

# 创建路由器
router = APIRouter(
    prefix="/api",
    tags=["batch"],
    responses={404: {"description": "Not found"}},
)

@router.post("/batch-predict", response_model=BatchPredictOutput, summary="批量预测接口")
async def batch_predict(
    request: Request,
    file: UploadFile = File(..., description="要预测的CSV或Excel文件"),
    model_version: Optional[int] = Query(None, description="模型版本号"),
):
    """
    批量预测接口
    
    - **file**: 要预测的CSV或Excel文件，包含用户的各种特征
    - **model_version**: 可选，指定使用的模型版本
    
    返回批量预测结果，包括预测标签、流失概率和结果下载链接
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 检查文件格式
        if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
            raise ValueError("不支持的文件格式，仅支持CSV和Excel文件")
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(file.filename)[1], delete=False) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # 执行批量预测
        result = predict_batch(temp_file_path)

        # 如果模型无法对该数据集进行有效预测（例如列差异过大），返回可读错误给前端
        if result.total_count == 0:
            raise ValueError("上传的数据列与模型期望差异过大，无法进行批量预测，请检查字段名和格式是否正确")

        # 计算本次使用的模型版本（字符串），用于日志：
        # 1. 如果显式指定 model_version，则使用 v{model_version}
        # 2. 否则使用当前模型管理器版本
        # 3. 兜底 v2（预测日志服务内部也会再次兜底）
        current_version = model_manager.get_model_version()
        if model_version is not None:
            effective_version = f"v{model_version}"
        elif current_version is not None:
            effective_version = f"v{current_version}"
        else:
            effective_version = "v2"

        # 日志：批量预测
        user = getattr(request.state, "user", None)
        user_id = user.get("user_id") if isinstance(user, dict) else None
        try:
            log_batch_prediction(
                user_id=user_id,
                model_version=effective_version,
                items=[
                    {
                        "features": {},  # 如需完整特征可在服务层回传
                        "prediction_label": item.prediction,
                        "prediction_probability": item.probability,
                    }
                    for item in result.items
                ],
                churn_count=result.churn_count,
                non_churn_count=result.non_churn_count,
            )
        except Exception as log_err:
            logger.error(f"记录批量预测日志失败: {log_err}")
        
        # 保存预测结果
        download_path = save_batch_results(result, 'csv')
        
        # 更新下载链接
        result.download_url = f"/api/download?file={os.path.basename(download_path)}"
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录请求
        record_request(request_type="batch", successful=True, response_time=response_time, request_id=request_id)
        
        logger.info(f"批量预测成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 预测数量: {result.total_count}")
        return result
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录失败请求
        record_request(request_type="batch", successful=False, response_time=response_time, request_id=request_id)
        
        logger.error(f"批量预测失败，请求ID: {request_id}, 错误: {e}")
        # 尝试提取可读错误信息
        message = str(e)
        if "差异过大" in message or "无法进行批量预测" in message:
            error_message = message
        else:
            error_message = "批量预测失败"
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message=error_message,
                request_id=request_id,
                details=str(e)
            ).dict()
        )

@router.get("/download", summary="下载批量预测结果")
async def download_result(
    file: str = Query(..., description="要下载的文件名")
):
    """
    下载批量预测结果
    
    - **file**: 要下载的文件名
    
    返回预测结果文件
    """
    from fastapi.responses import FileResponse
    
    try:
        # 构建文件路径
        file_path = os.path.join(tempfile.gettempdir(), file)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=f"batch_predict_result_{int(time.time())}.csv",
            media_type="text/csv"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败，错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="文件下载失败",
                request_id=str(uuid.uuid4()),
                details=str(e)
            ).dict()
        )
