# app/core/logging.py
# 实现分级日志

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings, LOG_DIR


def setup_logging() -> logging.Logger:
    """
    配置全局日志系统：
    1. 日志级别：由settings.LOG_LEVEL控制（默认INFO）
    2. 输出目标：控制台 + 文件（logs/app.log）
    3. 日志分割：单个文件最大10MB，保留10个备份
    4. 日志格式：包含时间、模块、级别、请求ID（可选）、消息
    """
    # 1. 定义日志格式
    # 详细格式（文件输出）：时间 - 模块 - 级别 - 消息
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # 简化格式（控制台输出）：时间 - 级别 - 消息
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 2. 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.handlers.clear()  # 清空默认处理器，避免重复输出

    # 3. 添加文件处理器（按大小分割）
    log_file_path = LOG_DIR / "app.log"
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=settings.LOG_FILE_MAX_SIZE,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding=settings.LOG_ENCODING
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 4. 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 5. 为第三方库降低日志级别（避免FastAPI/uvicorn日志刷屏）
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("pandas").setLevel(logging.WARNING)
    logging.getLogger("sklearn").setLevel(logging.WARNING)

    return root_logger


# ===================== 自定义日志适配器（添加请求ID） =====================
class RequestIDLogger(logging.LoggerAdapter):
    """
    自定义日志适配器：为每条日志添加请求ID，便于追踪单次请求的所有日志
    使用示例：
    logger = RequestIDLogger(root_logger, {"request_id": "123456"})
    logger.info("预测请求开始")  # 日志会包含request_id=123456
    """
    def process(self, msg, kwargs):
        return f"{msg}", {"extra": {"request_id": self.extra.get("request_id", "unknown")}}


# ===================== 初始化日志系统（项目启动时自动执行） =====================
# 全局日志器实例（项目中所有地方直接导入这个logger即可）
logger = setup_logging()


# ===================== 便捷日志函数（按业务场景封装） =====================
def get_request_logger(request_id: str) -> RequestIDLogger:
    """获取带请求ID的日志器（用于API请求追踪）"""
    return RequestIDLogger(logger, {"request_id": request_id})


def log_prediction_info(request_id: str, model_version: str, input_data: dict, result: dict):
    """记录预测日志（标准化格式）"""
    req_logger = get_request_logger(request_id)
    req_logger.info(
        f"模型预测完成 | 模型版本：{model_version} | 输入特征：{input_data} | 预测结果：{result}"
    )


def log_prediction_error(request_id: str, error_msg: str):
    """记录预测异常日志（ERROR级别）"""
    req_logger = get_request_logger(request_id)
    req_logger.error(f"模型预测失败 | 错误信息：{error_msg}")


def log_api_request(request_id: str, method: str, path: str, params: dict):
    """记录API请求日志（INFO级别）"""
    req_logger = get_request_logger(request_id)
    req_logger.info(f"API请求接收 | 方法：{method} | 路径：{path} | 参数：{params}")