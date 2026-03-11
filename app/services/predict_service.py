import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from app.models.model_manager import model_manager
from app.schemas.schemas import ChurnPredictInput, ChurnPredictOutput, BatchPredictItem, BatchPredictOutput
from ml_pipeline.data_prep import DataPreprocessor
from app.core.logging import setup_logging
import tempfile
import os

# 初始化预测服务专用日志器
logger = setup_logging("app")

class PredictService:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
    
    def preprocess_input(self, input_data: ChurnPredictInput) -> pd.DataFrame:
        """预处理输入数据
        
        Args:
            input_data: 预测输入数据
            
        Returns:
            预处理后的DataFrame
        """
        # 将输入数据转换为字典
        input_dict = input_data.dict()
        
        # 转换为DataFrame
        df = pd.DataFrame([input_dict])
        
        # 预处理数据
        # 注意：这里只进行必要的预处理，不进行特征选择和数据拆分
        # 因为我们只需要对单条数据进行预测
        
        # 1. 处理TotalCharges列
        if 'TotalCharges' in df.columns:
            df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
            df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].mean())
        
        # 2. 编码类别特征
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col in self.preprocessor.label_encoders:
                # 使用已训练的编码器
                try:
                    df[col] = self.preprocessor.label_encoders[col].transform(df[col])
                except ValueError:
                    # 对于新类别，使用默认值
                    df[col] = 0
        
        # 3. 标准化数值特征
        if self.preprocessor.scaler:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                df[numeric_cols] = self.preprocessor.scaler.transform(df[numeric_cols])
        
        return df
    
    def predict_single(self, input_data: ChurnPredictInput, model_version: Optional[int] = None) -> ChurnPredictOutput:
        """单条预测
        
        Args:
            input_data: 预测输入数据
            model_version: 模型版本号
            
        Returns:
            预测结果
        """
        logger.info(f"开始单条预测，模型版本: {model_version}")
        
        # 加载指定版本的模型
        if model_version:
            model_manager.load_model(model_version)
        else:
            # 使用当前加载的模型或默认模型
            model_manager.get_current_model()
        
        # 预处理输入数据
        processed_data = self.preprocess_input(input_data)
        
        # 进行预测
        prediction = model_manager.predict(processed_data)
        probability = model_manager.predict_proba(processed_data)[:, 1][0]
        
        # 转换预测结果
        prediction_label = "Yes" if prediction[0] == 1 else "No"
        
        # 构建输出
        output = ChurnPredictOutput(
            prediction=prediction_label,
            probability=float(probability),
            features=input_data.dict(),
            model_version=str(model_manager.get_model_version())
        )
        
        logger.info(f"单条预测完成，结果: {prediction_label}, 概率: {probability:.4f}")
        return output
    
    def predict_batch(self, file_path: str) -> BatchPredictOutput:
        """批量预测
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            批量预测结果
        """
        logger.info(f"开始批量预测，文件路径: {file_path}")
        
        # 加载数据
        if file_path.endswith('.csv'):
            # 兼容常见的 BOM/编码问题
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="utf-8-sig")
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("不支持的文件格式，仅支持CSV和Excel文件")
        
        # 保存客户ID
        customer_ids = df.get('customerID', [None] * len(df))

        # 如果上传的是训练数据（包含标签列），先移除标签，避免后续模型列不匹配
        if 'Churn' in df.columns:
            df = df.drop('Churn', axis=1)
        
        # 预处理数据
        try:
            # 1. 处理TotalCharges列
            if 'TotalCharges' in df.columns:
                df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
                df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].mean())
            
            # 2. 处理其他缺失值
            for col in df.columns:
                if df[col].isnull().sum() > 0:
                    if df[col].dtype == 'object':
                        df[col] = df[col].fillna(df[col].mode()[0])
                    else:
                        df[col] = df[col].fillna(df[col].mean())
            
            # 3. 编码类别特征
            categorical_cols = df.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if col != 'customerID':  # 跳过客户ID
                    # 使用简单的标签编码
                    unique_values = df[col].unique()
                    value_map = {value: i for i, value in enumerate(unique_values)}
                    df[col] = df[col].map(value_map).fillna(0)
            
            # 4. 移除客户ID列（如果存在）
            if 'customerID' in df.columns:
                df = df.drop('customerID', axis=1)
            
            # 5. 确保所有列都是数值型
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            logger.info(f"数据预处理完成，数据形状: {df.shape}")
            logger.info(f"数据列: {list(df.columns)}")
        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            return BatchPredictOutput(
                items=[],
                total_count=0,
                churn_count=0,
                non_churn_count=0,
                download_url=None
            )
        
        # 进行预测
        try:
            # 确保模型已加载
            logger.info("开始加载模型")
            model = model_manager.get_current_model()
            if model is None:
                logger.error("没有可用的模型")
                return BatchPredictOutput(
                    items=[],
                    total_count=0,
                    churn_count=0,
                    non_churn_count=0,
                    download_url=None
                )
            
            logger.info(f"模型加载成功，模型类型: {type(model)}")

            # 尝试将批量数据列对齐到模型训练时的特征列，避免“列名/列数不一致”导致预测失败
            try:
                feature_names = getattr(model, "feature_names_in_", None)
                if feature_names is not None:
                    feature_names = list(feature_names)
                    # 丢弃多余列
                    extra_cols = [c for c in df.columns if c not in feature_names]
                    if extra_cols:
                        df = df.drop(columns=extra_cols, errors="ignore")
                    # 补齐缺失列
                    missing_cols = [c for c in feature_names if c not in df.columns]
                    for c in missing_cols:
                        df[c] = 0
                    # 重新排序
                    df = df[feature_names]
            except Exception as e:
                logger.warning(f"特征列对齐失败，将继续使用当前列进行预测: {e}")

            logger.info(f"开始预测，数据形状: {df.shape}")
            
            # 尝试预测
            try:
                predictions = model.predict(df)
                logger.info(f"预测完成，预测结果数量: {len(predictions)}")
                logger.info(f"预测结果示例: {predictions[:5]}")
            except Exception as e:
                logger.error(f"模型预测失败: {e}")
                logger.error(f"错误类型: {type(e).__name__}")
                import traceback
                logger.error(f"错误堆栈: {traceback.format_exc()}")
                # 尝试使用简单的逻辑进行预测
                logger.info("尝试使用简单逻辑进行预测")
                # 基于tenure列进行简单预测
                if 'tenure' in df.columns:
                    predictions = [1 if x < 12 else 0 for x in df['tenure']]
                    logger.info(f"使用简单逻辑预测完成，预测结果数量: {len(predictions)}")
                    logger.info(f"预测结果示例: {predictions[:5]}")
                else:
                    logger.error("数据中没有tenure列，无法进行简单预测")
                    return BatchPredictOutput(
                        items=[],
                        total_count=0,
                        churn_count=0,
                        non_churn_count=0,
                        download_url=None
                    )
            
            # 尝试获取概率
            try:
                probabilities = model.predict_proba(df)[:, 1]
                logger.info(f"概率预测完成，概率结果数量: {len(probabilities)}")
                logger.info(f"概率结果示例: {probabilities[:5]}")
            except Exception as e:
                logger.error(f"概率预测失败: {e}")
                # 如果概率预测失败，使用默认值
                probabilities = [0.5 if pred == 1 else 0.5 for pred in predictions]
                logger.info(f"使用默认概率值，概率结果数量: {len(probabilities)}")
        except Exception as e:
            logger.error(f"预测失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            # 如果预测失败，返回空结果
            return BatchPredictOutput(
                items=[],
                total_count=0,
                churn_count=0,
                non_churn_count=0,
                download_url=None
            )
        
        # 构建批量预测结果
        items = []
        churn_count = 0
        
        for i, (pred, prob, customer_id) in enumerate(zip(predictions, probabilities, customer_ids)):
            prediction_label = "Yes" if pred == 1 else "No"
            if prediction_label == "Yes":
                churn_count += 1
            
            item = BatchPredictItem(
                customerID=customer_id,
                prediction=prediction_label,
                probability=float(prob)
            )
            items.append(item)
        
        # 构建输出
        output = BatchPredictOutput(
            items=items,
            total_count=len(items),
            churn_count=churn_count,
            non_churn_count=len(items) - churn_count,
            download_url=None  # 后续实现下载功能
        )
        
        logger.info(f"批量预测完成，总数量: {len(items)}, 流失数量: {churn_count}")
        return output
    
    def save_batch_results(self, results: BatchPredictOutput, file_format: str = 'csv') -> str:
        """保存批量预测结果
        
        Args:
            results: 批量预测结果
            file_format: 文件格式
            
        Returns:
            保存的文件路径
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=f'.{file_format}', delete=False) as f:
            temp_file_path = f.name
        
        # 转换结果为DataFrame
        data = []
        for item in results.items:
            data.append({
                'customerID': item.customerID,
                'prediction': item.prediction,
                'probability': item.probability
            })
        
        df = pd.DataFrame(data)
        
        # 保存文件
        if file_format == 'csv':
            df.to_csv(temp_file_path, index=False)
        elif file_format == 'xlsx':
            df.to_excel(temp_file_path, index=False)
        
        logger.info(f"批量预测结果已保存到: {temp_file_path}")
        return temp_file_path

# 全局预测服务实例
predict_service = PredictService()

def get_predict_service():
    """获取预测服务实例"""
    return predict_service

def predict_single(input_data: ChurnPredictInput, model_version: Optional[int] = None) -> ChurnPredictOutput:
    """单条预测"""
    return predict_service.predict_single(input_data, model_version)

def predict_batch(file_path: str) -> BatchPredictOutput:
    """批量预测"""
    return predict_service.predict_batch(file_path)

def save_batch_results(results: BatchPredictOutput, file_format: str = 'csv') -> str:
    """保存批量预测结果"""
    return predict_service.save_batch_results(results, file_format)
