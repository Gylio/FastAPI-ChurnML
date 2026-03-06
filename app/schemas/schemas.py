from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum

# 定义枚举类型
class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

class YesNo(str, Enum):
    YES = "Yes"
    NO = "No"

class PhoneServiceType(str, Enum):
    YES = "Yes"
    NO = "No"

class MultipleLinesType(str, Enum):
    YES = "Yes"
    NO = "No"
    NO_PHONE_SERVICE = "No phone service"

class InternetServiceType(str, Enum):
    DSL = "DSL"
    FIBER_OPTIC = "Fiber optic"
    NO = "No"

class ContractType(str, Enum):
    MONTH_TO_MONTH = "Month-to-month"
    ONE_YEAR = "One year"
    TWO_YEAR = "Two year"

class PaymentMethodType(str, Enum):
    ELECTRONIC_CHECK = "Electronic check"
    MAILED_CHECK = "Mailed check"
    BANK_TRANSFER = "Bank transfer (automatic)"
    CREDIT_CARD = "Credit card (automatic)"

# 单条预测输入模型
class ChurnPredictInput(BaseModel):
    gender: Gender = Field(..., description="性别")
    SeniorCitizen: int = Field(..., ge=0, le=1, description="是否为老年公民 (0: 否, 1: 是)")
    Partner: YesNo = Field(..., description="是否有配偶")
    Dependents: YesNo = Field(..., description="是否有家属")
    tenure: int = Field(..., ge=0, description="使用时长（月）")
    PhoneService: PhoneServiceType = Field(..., description="是否有电话服务")
    MultipleLines: MultipleLinesType = Field(..., description="是否有多条线路")
    InternetService: InternetServiceType = Field(..., description="互联网服务类型")
    OnlineSecurity: YesNo = Field(..., description="是否有在线安全服务")
    OnlineBackup: YesNo = Field(..., description="是否有在线备份服务")
    DeviceProtection: YesNo = Field(..., description="是否有设备保护服务")
    TechSupport: YesNo = Field(..., description="是否有技术支持服务")
    StreamingTV: YesNo = Field(..., description="是否有流媒体电视服务")
    StreamingMovies: YesNo = Field(..., description="是否有流媒体电影服务")
    Contract: ContractType = Field(..., description="合同类型")
    PaperlessBilling: YesNo = Field(..., description="是否使用无纸化账单")
    PaymentMethod: PaymentMethodType = Field(..., description="支付方式")
    MonthlyCharges: float = Field(..., ge=0, description="月费用")
    TotalCharges: float = Field(..., ge=0, description="总费用")

# 单条预测结果模型
class ChurnPredictOutput(BaseModel):
    prediction: str = Field(..., description="预测结果 (Yes: 流失, No: 未流失)")
    probability: float = Field(..., ge=0, le=1, description="流失概率")
    features: Dict[str, Any] = Field(..., description="输入特征值")
    model_version: str = Field(..., description="使用的模型版本")

# 批量预测结果模型
class BatchPredictItem(BaseModel):
    customerID: Optional[str] = Field(None, description="客户ID")
    prediction: str = Field(..., description="预测结果 (Yes: 流失, No: 未流失)")
    probability: float = Field(..., ge=0, le=1, description="流失概率")

class BatchPredictOutput(BaseModel):
    items: List[BatchPredictItem] = Field(..., description="批量预测结果列表")
    total_count: int = Field(..., description="总预测数量")
    churn_count: int = Field(..., description="预测为流失的数量")
    non_churn_count: int = Field(..., description="预测为未流失的数量")
    download_url: Optional[str] = Field(None, description="结果下载链接")

# 异常响应模型
class ErrorResponse(BaseModel):
    error_code: int = Field(..., description="错误码")
    error_message: str = Field(..., description="错误信息")
    request_id: str = Field(..., description="请求ID")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

# 模型版本响应
class ModelVersion(BaseModel):
    version: int = Field(..., description="模型版本号")
    filename: str = Field(..., description="模型文件名")
    path: str = Field(..., description="模型文件路径")

class ModelVersionResponse(BaseModel):
    versions: List[ModelVersion] = Field(..., description="可用模型版本列表")
    current_version: Optional[int] = Field(None, description="当前使用的模型版本")

# 模型切换请求
class ModelSwitchRequest(BaseModel):
    version: int = Field(..., description="要切换的模型版本号")

# 统计数据响应
class StatsResponse(BaseModel):
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="模型准确率")
    average_response_time: float = Field(..., ge=0, description="平均响应时间（秒）")
    last_update: str = Field(..., description="最后更新时间")

# 健康检查响应
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="服务状态")
    model_status: str = Field(..., description="模型状态")
    timestamp: str = Field(..., description="检查时间戳")
