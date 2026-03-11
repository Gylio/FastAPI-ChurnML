# app/core/logging.py
# 集中管理可配置参数（模型路径、端口、数据校验规则等）

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


# ===================== 基础路径配置 =====================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = BASE_DIR / "saved_models"

LOG_DIR = BASE_DIR / "logs"

# TEMP_DIR = BASE_DIR / "temp"

TEST_DATA_DIR = BASE_DIR / "tests" / "test_data"

# 确保目录存在
for dir_path in [MODEL_DIR, LOG_DIR, TEST_DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


# ===================== 数据校验规则配置（用户流失预测场景） =====================
class DataValidationRules(BaseModel):
    """用户流失预测数据的校验规则（与Pydantic模型联动）"""
    numeric_rules: Dict[str, dict] = Field(
        default={
            "monthly_consume": {"min": 0, "max": 10000, "default": 0},
            "service_usage_months": {"min": 1, "max": 120, "default": 0},
        }
    )

    categorical_rules: Dict[str, List[str]] = Field(
        default={
            "gender": ["male", "female"],
            "contract_type": ["Month-to-month", "One year", "Two year"],
            "payment_method": ["Electronic check", "Mailed check",
                               "Bank transfer (automatic)", "Credit card (automatic)"],
            "service_type": ["DSL", "Fiber optic", "No"],
        }
    )

    required_features: List[str] = Field(
        default=["customerID", "Contract", "tenure"]
    )

    missing_value_strategy: str = Field(default="default")


# ===================== 项目核心配置类（支持环境变量覆盖） =====================
class Settings(BaseModel):
    """项目全局配置类（Pydantic保证类型安全）"""
    # API服务配置
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")  # 绑定所有网卡
    API_PORT: int = Field(default=8000, env="API_PORT")  # 默认端口8000，可通过环境变量修改
    API_RELOAD: bool = Field(default=True, env="API_RELOAD")  # 开发环境热重载，生产环境设为False
    API_TIMEOUT: float = Field(default=0.5, env="API_TIMEOUT")  # 接口响应超时时间（秒）

    # 模型配置
    DEFAULT_MODEL_VERSION: str = Field(default="v0.1", env="DEFAULT_MODEL_VERSION")  # 默认使用的模型版本
    MODEL_FILE_SUFFIX: str = Field(default=".pkl")  # 模型文件后缀
    MODEL_LOAD_TIMEOUT: float = Field(default=5.0)  # 模型加载超时时间（秒）

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")  # 默认INFO级别，生产环境可设为WARNING
    LOG_FILE_MAX_SIZE: int = Field(default=10 * 1024 * 1024)  # 单个日志文件最大大小：10MB
    LOG_FILE_BACKUP_COUNT: int = Field(default=10)  # 日志文件备份数量：最多保留10个
    LOG_ENCODING: str = Field(default="utf-8")

    # 批量预测配置
    BATCH_MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)  # 批量上传文件最大10MB
    BATCH_ALLOWED_EXTENSIONS: List[str] = Field(default=["csv", "xlsx"])  # 允许的文件格式

    # 监控配置
    STATS_CACHE_TTL: int = Field(default=300)  # 监控统计缓存过期时间（5分钟）
    ACCURACY_THRESHOLD: float = Field(default=0.85)  # 模型准确率告警阈值

    # 数据校验规则
    # data_validation: DataValidationRules = Field(default_factory=DataValidationRules)


    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """校验日志级别是否合法"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是：{valid_levels}")
        return v.upper()


# ===================== 实例化配置（全局唯一） =====================
settings = Settings()


# ===================== 便捷导出常用配置（可选） =====================
# API服务配置快捷变量
API_CONFIG = {
    "host": settings.API_HOST,
    "port": settings.API_PORT,
    "reload": settings.API_RELOAD,
}

# 模型路径快捷变量
def get_model_path(version: Optional[str] = None) -> Path:
    """获取指定版本模型的路径（默认使用配置的默认版本）"""
    version = version or settings.DEFAULT_MODEL_VERSION
    return MODEL_DIR / f"churn_pred_{version}{settings.MODEL_FILE_SUFFIX}"

