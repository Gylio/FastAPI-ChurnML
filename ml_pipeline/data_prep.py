import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from app.core.config import BASE_DIR
from app.core.logging import setup_logging

# 初始化预处理专用日志器
logger = setup_logging("explore")

class DataPreprocessor:
    def __init__(self):
        self.label_encoders = {}
        self.onehot_encoder = None
        self.scaler = None
        self.feature_selector = None
        self.feature_names = None
    
    def load_data(self, data_path):
        """加载数据集"""
        logger.info(f"正在加载数据: {data_path}")
        data = pd.read_csv(data_path)
        logger.info(f"数据集加载成功，形状为: {data.shape}")
        return data
    
    def clean_data(self, data, remove_outliers=True):
        """数据清洗
        
        Args:
            data: 原始数据集
            remove_outliers: 是否移除异常值
            
        Returns:
            清洗后的数据集
        """
        logger.info("\n=== 数据清洗 ===")
        
        # 复制数据
        cleaned_data = data.copy()
        
        # 处理TotalCharges列的缺失值
        if 'TotalCharges' in cleaned_data.columns:
            # 转换为数值型，将空值设为NaN
            cleaned_data['TotalCharges'] = pd.to_numeric(cleaned_data['TotalCharges'], errors='coerce')
            # 用均值填充缺失值
            cleaned_data['TotalCharges'] = cleaned_data['TotalCharges'].fillna(cleaned_data['TotalCharges'].mean())
            logger.info("TotalCharges列的缺失值已用均值填充")
        
        # 处理类别型特征的缺失值
        categorical_cols = cleaned_data.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if cleaned_data[col].isnull().sum() > 0:
                # 用众数填充类别型特征的缺失值
                mode_value = cleaned_data[col].mode()[0]
                cleaned_data[col] = cleaned_data[col].fillna(mode_value)
                logger.info(f"{col}列的缺失值已用众数填充")
        
        # 移除异常值（3σ原则）
        if remove_outliers:
            numeric_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
            for col in numeric_cols:
                if col in cleaned_data.columns:
                    mean = cleaned_data[col].mean()
                    std = cleaned_data[col].std()
                    lower_bound = mean - 3 * std
                    upper_bound = mean + 3 * std
                    
                    # 计算异常值数量
                    outliers_count = len(cleaned_data[(cleaned_data[col] < lower_bound) | (cleaned_data[col] > upper_bound)])
                    if outliers_count > 0:
                        # 移除异常值
                        cleaned_data = cleaned_data[(cleaned_data[col] >= lower_bound) & (cleaned_data[col] <= upper_bound)]
                        logger.info(f"{col}列移除了{outliers_count}个异常值")
        
        logger.info(f"清洗后的数据形状: {cleaned_data.shape}")
        return cleaned_data
    
    def encode_categorical(self, data, encoding_type='label'):
        """类别特征编码
        
        Args:
            data: 数据集
            encoding_type: 编码类型，'label'或'onehot'
            
        Returns:
            编码后的数据集
        """
        logger.info("\n=== 类别特征编码 ===")
        
        # 复制数据
        encoded_data = data.copy()
        
        # 移除customerID列
        if 'customerID' in encoded_data.columns:
            encoded_data = encoded_data.drop('customerID', axis=1)
        
        # 确定类别特征
        categorical_cols = encoded_data.select_dtypes(include=['object']).columns
        logger.info(f"类别特征: {list(categorical_cols)}")
        
        if encoding_type == 'label':
            # 使用LabelEncoder编码
            for col in categorical_cols:
                self.label_encoders[col] = LabelEncoder()
                encoded_data[col] = self.label_encoders[col].fit_transform(encoded_data[col])
                logger.info(f"{col}列已使用LabelEncoder编码")
        elif encoding_type == 'onehot':
            # 使用OneHotEncoder编码
            encoded_data = pd.get_dummies(encoded_data, columns=categorical_cols, drop_first=True)
            logger.info("类别特征已使用OneHot编码")
        
        logger.info(f"编码后的数据形状: {encoded_data.shape}")
        return encoded_data
    
    def normalize_numeric(self, data, normalization_type='standard'):
        """数值特征标准化/归一化
        
        Args:
            data: 数据集
            normalization_type: 标准化类型，'standard'或'minmax'
            
        Returns:
            标准化后的数据集
        """
        logger.info("\n=== 数值特征标准化 ===")
        
        # 复制数据
        normalized_data = data.copy()
        
        # 确定数值特征
        numeric_cols = normalized_data.select_dtypes(include=[np.number]).columns
        # 排除目标变量Churn
        if 'Churn' in numeric_cols:
            numeric_cols = numeric_cols.drop('Churn')
        
        logger.info(f"数值特征: {list(numeric_cols)}")
        
        if len(numeric_cols) > 0:
            if normalization_type == 'standard':
                # 使用StandardScaler标准化
                self.scaler = StandardScaler()
                normalized_data[numeric_cols] = self.scaler.fit_transform(normalized_data[numeric_cols])
                logger.info("数值特征已使用StandardScaler标准化")
            elif normalization_type == 'minmax':
                # 使用MinMaxScaler归一化
                self.scaler = MinMaxScaler()
                normalized_data[numeric_cols] = self.scaler.fit_transform(normalized_data[numeric_cols])
                logger.info("数值特征已使用MinMaxScaler归一化")
        
        return normalized_data
    
    def select_features(self, X, y, k=19, method='f_classif'):
        """特征筛选
        
        Args:
            X: 特征矩阵
            y: 目标变量
            k: 选择的特征数量
            method: 特征选择方法，'f_classif'或'mutual_info'
            
        Returns:
            筛选后的特征矩阵
        """
        logger.info("\n=== 特征筛选 ===")
        
        if method == 'f_classif':
            # 使用方差分析进行特征选择
            self.feature_selector = SelectKBest(f_classif, k=k)
        elif method == 'mutual_info':
            # 使用互信息进行特征选择
            self.feature_selector = SelectKBest(mutual_info_classif, k=k)
        
        X_selected = self.feature_selector.fit_transform(X, y)
        
        # 获取选中的特征名称
        if self.feature_selector.get_support().any():
            self.feature_names = X.columns[self.feature_selector.get_support()]
            logger.info(f"选中的特征: {list(self.feature_names)}")
        
        logger.info(f"特征筛选后的数据形状: {X_selected.shape}")
        return X_selected
    
    def split_data(self, X, y, test_size=0.2, val_size=0.1, random_state=42):
        """数据拆分
        
        Args:
            X: 特征矩阵
            y: 目标变量
            test_size: 测试集比例
            val_size: 验证集比例
            random_state: 随机种子
            
        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        logger.info("\n=== 数据拆分 ===")
        
        # 首先拆分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # 然后从训练集中拆分验证集
        # 计算验证集相对于原始数据的比例
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=val_ratio, random_state=random_state, stratify=y_train
        )
        
        logger.info(f"训练集形状: {X_train.shape}")
        logger.info(f"验证集形状: {X_val.shape}")
        logger.info(f"测试集形状: {X_test.shape}")
        
        # 检查数据分布
        logger.info("\n数据分布:")
        logger.info(f"训练集Churn分布: {y_train.value_counts(normalize=True).round(4)}")
        logger.info(f"验证集Churn分布: {y_val.value_counts(normalize=True).round(4)}")
        logger.info(f"测试集Churn分布: {y_test.value_counts(normalize=True).round(4)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def preprocess_pipeline(self, data_path, encoding_type='label', normalization_type='standard', 
                           remove_outliers=True, feature_selection=True, k=19, 
                           test_size=0.2, val_size=0.1, random_state=42):
        """完整的预处理 pipeline
        
        Args:
            data_path: 数据文件路径
            encoding_type: 类别特征编码类型
            normalization_type: 数值特征标准化类型
            remove_outliers: 是否移除异常值
            feature_selection: 是否进行特征筛选
            k: 特征筛选数量
            test_size: 测试集比例
            val_size: 验证集比例
            random_state: 随机种子
            
        Returns:
            X_train, X_val, X_test, y_train, y_val, y_test
        """
        logger.info("\n=== 开始预处理 pipeline ===")
        
        # 1. 加载数据
        data = self.load_data(data_path)
        
        # 2. 数据清洗
        cleaned_data = self.clean_data(data, remove_outliers)
        
        # 3. 类别特征编码
        encoded_data = self.encode_categorical(cleaned_data, encoding_type)
        
        # 4. 分离特征和目标变量
        if 'Churn' in encoded_data.columns:
            X = encoded_data.drop('Churn', axis=1)
            y = encoded_data['Churn']
        else:
            raise ValueError("数据集中缺少Churn列")
        
        # 5. 数值特征标准化
        X = self.normalize_numeric(X, normalization_type)
        
        # 6. 特征筛选
        if feature_selection:
            X = self.select_features(X, y, k)
        
        # 7. 数据拆分
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(
            X, y, test_size, val_size, random_state
        )
        
        logger.info("\n=== 预处理完成 ===")
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def transform(self, data):
        """对新数据进行预处理（用于预测时）
        
        Args:
            data: 新数据
            
        Returns:
            预处理后的新数据
        """
        # 复制数据
        transformed_data = data.copy()
        
        # 处理缺失值
        transformed_data = self.clean_data(transformed_data, remove_outliers=False)
        
        # 类别特征编码
        if self.label_encoders:
            for col, encoder in self.label_encoders.items():
                if col in transformed_data.columns:
                    # 处理编码过程中可能出现的新类别
                    try:
                        transformed_data[col] = encoder.transform(transformed_data[col])
                    except ValueError:
                        # 对于新类别，使用默认值
                        transformed_data[col] = 0
        
        # 数值特征标准化
        if self.scaler:
            numeric_cols = transformed_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                transformed_data[numeric_cols] = self.scaler.transform(transformed_data[numeric_cols])
        
        # 特征筛选
        if self.feature_selector:
            transformed_data = self.feature_selector.transform(transformed_data)
        
        return transformed_data

if __name__ == "__main__":
    # 测试预处理 pipeline
    data_path = BASE_DIR / 'ml_pipeline' / 'data' / 'WA_Fn-UseC_-Telco-Customer-Churn.csv'
    
    preprocessor = DataPreprocessor()
    X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.preprocess_pipeline(
        data_path,
        encoding_type='label',
        normalization_type='standard',
        remove_outliers=True,
        feature_selection=True,
        k=19
    )
    
    logger.info("\n预处理测试完成！")
    logger.info(f"训练集形状: {X_train.shape}")
    logger.info(f"验证集形状: {X_val.shape}")
    logger.info(f"测试集形状: {X_test.shape}")