from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Optional
from app.schemas.schemas import BatchPredictOutput, ErrorResponse
from app.services.predict_service import predict_batch, save_batch_results
from app.services.stats_service import record_request
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
    file: UploadFile = File(..., description="要预测的CSV或Excel文件"),
    model_version: Optional[int] = Query(None, description="模型版本号")
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
        
        # 保存预测结果
        download_path = save_batch_results(result, 'csv')
        
        # 更新下载链接
        result.download_url = f"/api/download?file={os.path.basename(download_path)}"
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录请求
        record_request(successful=True, response_time=response_time)
        
        logger.info(f"批量预测成功，请求ID: {request_id}, 响应时间: {response_time:.4f}秒, 预测数量: {result.total_count}")
        return result
    except Exception as e:
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录失败请求
        record_request(successful=False, response_time=response_time)
        
        logger.error(f"批量预测失败，请求ID: {request_id}, 错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=500,
                error_message="批量预测失败",
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
