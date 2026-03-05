import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
from pathlib import Path
from app.core.config import BASE_DIR, MODEL_DIR, settings
from app.core.logging import logger


class ModelTrainer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        # 使用全局配置的模型保存路径
        self.model_dir = MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"模型保存目录: {self.model_dir}")

    def load_data(self):
        """加载数据集"""
        logger.info(f"正在加载数据: {self.data_path}")
        self.data = pd.read_csv(self.data_path)
        logger.info(f"数据集加载成功，形状为: {self.data.shape}")
        return self.data

    def preprocess_data(self):
        """预处理数据"""
        # 处理缺失值
        if 'TotalCharges' in self.data.columns:
            self.data['TotalCharges'] = pd.to_numeric(self.data['TotalCharges'], errors='coerce')
            # 修复pandas inplace用法
            self.data['TotalCharges'] = self.data['TotalCharges'].fillna(self.data['TotalCharges'].mean())

        # 编码目标变量
        self.label_encoders['Churn'] = LabelEncoder()
        self.data['Churn'] = self.label_encoders['Churn'].fit_transform(self.data['Churn'])

        # 分离特征和目标变量
        X = self.data.drop(['customerID', 'Churn'], axis=1)
        y = self.data['Churn']

        # 编码分类特征
        categorical_cols = ['gender', 'Partner', 'Dependents', 'PhoneService', 'MultipleLines',
                            'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                            'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
                            'PaperlessBilling', 'PaymentMethod']

        for col in categorical_cols:
            if col in X.columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col])
                self.label_encoders[col] = le

        # 特征标准化
        self.scaler = StandardScaler()
        X = pd.DataFrame(self.scaler.fit_transform(X), columns=X.columns)

        # 划分训练集和测试集
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        logger.info(f"训练集形状: {self.X_train.shape}")
        logger.info(f"测试集形状: {self.X_test.shape}")
        return X, y

    def train_model(self):
        """训练模型"""
        logger.info("开始训练模型...")

        # 简化模型参数，减少计算时间
        param_grid = {
            'n_estimators': [100],
            'max_depth': [10],
            'min_samples_split': [5]
        }

        # 使用网格搜索进行参数调优
        grid_search = GridSearchCV(
            RandomForestClassifier(random_state=42),
            param_grid,
            cv=3,  # 减少交叉验证折数
            scoring='f1'
        )

        grid_search.fit(self.X_train, self.y_train)
        self.model = grid_search.best_estimator_

        logger.info(f"最佳参数: {grid_search.best_params_}")
        logger.info(f"最佳交叉验证分数: {grid_search.best_score_:.4f}")
        return self.model

    def evaluate_model(self):
        """评估模型"""
        logger.info("开始评估模型...")

        y_pred = self.model.predict(self.X_test)

        accuracy = accuracy_score(self.y_test, y_pred)
        precision = precision_score(self.y_test, y_pred)
        recall = recall_score(self.y_test, y_pred)
        f1 = f1_score(self.y_test, y_pred)
        cm = confusion_matrix(self.y_test, y_pred)

        logger.info(f"准确率是: {accuracy:.4f}")
        logger.info(f"精确率是: {precision:.4f}")
        logger.info(f"召回率是: {recall:.4f}")
        logger.info(f"F1分数是: {f1:.4f}")
        logger.info("混淆矩阵:")
        logger.info(cm)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm
        }

    def save_model(self, version=None):
        """保存模型"""
        # 使用配置中的默认版本
        version = version or settings.DEFAULT_MODEL_VERSION
        model_path = self.model_dir / f'churn_pred_{version}{settings.MODEL_FILE_SUFFIX}'
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders
        }, model_path)
        logger.info(f"模型已保存到: {model_path}")
        return model_path

    def run_pipeline(self, version=None):
        """运行完整的训练 pipeline"""
        logger.info("=== 开始模型训练 pipeline ===")

        # 加载数据
        self.load_data()

        # 预处理数据
        self.preprocess_data()

        # 训练模型
        self.train_model()

        # 评估模型
        self.evaluate_model()

        # 保存模型
        self.save_model(version)

        logger.info("=== 模型训练 pipeline 完成 ===")


if __name__ == "__main__":
    # 使用绝对路径
    data_path = BASE_DIR / 'ml_pipeline' / 'data' / 'WA_Fn-UseC_-Telco-Customer-Churn.csv'

    trainer = ModelTrainer(data_path)
    trainer.run_pipeline()