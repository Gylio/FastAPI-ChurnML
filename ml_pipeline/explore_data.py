import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
import os
import warnings
from pathlib import Path
from app.core.config import BASE_DIR
from app.core.logging import logger

warnings.filterwarnings('ignore')


class DataExplorer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = None
        self.encoded_data = None
        self.label_encoders = {}
        self.reports_dir = BASE_DIR / 'ml_pipeline' / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"报告保存目录: {self.reports_dir}")

    def load_data(self):
        """加载数据集"""
        self.data = pd.read_csv(self.data_path)
        logger.info(f"数据集加载成功，形状为: {self.data.shape}")
        logger.info(f"列名: {list(self.data.columns)}")
        return self.data

    def handle_missing_values(self):
        """处理缺失值"""
        logger.info("\n缺失值情况:")
        missing_data = self.data.isnull().sum()
        logger.info(missing_data[missing_data > 0])

        # 检查TotalCharges列的缺失值
        if 'TotalCharges' in self.data.columns:
            # 转换为数值型，将空值设为NaN
            self.data['TotalCharges'] = pd.to_numeric(self.data['TotalCharges'], errors='coerce')
            # 用均值填充缺失值
            self.data['TotalCharges'] = self.data['TotalCharges'].fillna(self.data['TotalCharges'].mean())
            logger.info("\nTotalCharges列的缺失值已用均值填充")

        return self.data

    def encode_categorical(self):
        """编码分类变量"""
        # 复制数据并删除customerID列
        self.encoded_data = self.data.copy()
        if 'customerID' in self.encoded_data.columns:
            self.encoded_data = self.encoded_data.drop('customerID', axis=1)

        # 对二元分类变量进行编码
        binary_cols = ['gender', 'Partner', 'Dependents', 'PhoneService', 'PaperlessBilling', 'Churn']
        for col in binary_cols:
            if col in self.encoded_data.columns:
                self.label_encoders[col] = LabelEncoder()
                self.encoded_data[col] = self.label_encoders[col].fit_transform(self.encoded_data[col])

        # 对多分类变量进行独热编码
        categorical_cols = ['MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
                            'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
                            'Contract', 'PaymentMethod']
        self.encoded_data = pd.get_dummies(self.encoded_data, columns=categorical_cols, drop_first=True)

        logger.info(f"\n编码后的数据形状: {self.encoded_data.shape}")
        return self.encoded_data

    def analyze_numeric_features(self):
        """分析数值特征"""
        logger.info("\n数值特征描述性统计:")
        numeric_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
        logger.info(self.data[numeric_cols].describe())

        # 绘制数值特征的分布
        plt.figure(figsize=(15, 5))
        for i, col in enumerate(numeric_cols, 1):
            plt.subplot(1, 3, i)
            sns.histplot(self.data[col], kde=True)
            plt.title(f'{col} 分布')
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'numeric_distributions.png')
        plt.close()
        logger.info(f"数值特征分布图已保存到 {self.reports_dir / 'numeric_distributions.png'}")

    def analyze_categorical_features(self):
        """分析分类特征"""
        logger.info("\n分类特征分布:")
        categorical_cols = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'PhoneService',
                            'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
                            'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
                            'Contract', 'PaperlessBilling', 'PaymentMethod']

        # 绘制分类特征与Churn的关系
        plt.figure(figsize=(20, 30))
        for i, col in enumerate(categorical_cols, 1):
            plt.subplot(8, 2, i)
            sns.countplot(x=col, hue='Churn', data=self.data)
            plt.title(f'{col} 与 Churn 的关系')
            plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'categorical_vs_churn.png')
        plt.close()
        logger.info(f"分类特征与Churn关系图已保存到 {self.reports_dir / 'categorical_vs_churn.png'}")

    def analyze_correlation(self):
        """分析特征与Churn的相关性"""
        logger.info("\n特征与Churn的相关性:")
        correlation = self.encoded_data.corr()['Churn'].sort_values(ascending=False)
        logger.info(correlation)

        # 绘制相关性热力图
        plt.figure(figsize=(20, 15))
        corr_matrix = self.encoded_data.corr()
        sns.heatmap(corr_matrix, annot=False, cmap='coolwarm')
        plt.title('特征相关性热力图')
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'correlation_heatmap.png')
        plt.close()
        logger.info(f"相关性热力图已保存到 {self.reports_dir / 'correlation_heatmap.png'}")

    def analyze_churn_rate(self):
        """分析流失率"""
        logger.info("\n流失率分析:")
        churn_rate = self.data['Churn'].value_counts(normalize=True) * 100
        logger.info(churn_rate)

        # 绘制流失率饼图
        plt.figure(figsize=(8, 6))
        plt.pie(churn_rate, labels=['No', 'Yes'], autopct='%1.1f%%', startangle=90)
        plt.title('客户流失率')
        plt.axis('equal')
        plt.savefig(self.reports_dir / 'churn_rate.png')
        plt.close()
        logger.info(f"流失率饼图已保存到 {self.reports_dir / 'churn_rate.png'}")

    def generate_eda_report(self):
        """生成完整的EDA报告"""
        logger.info("\n=== 开始生成EDA报告 ===")

        # 加载数据
        self.load_data()

        # 处理缺失值
        self.handle_missing_values()

        # 编码分类变量
        self.encode_categorical()

        # 分析数值特征
        self.analyze_numeric_features()

        # 分析分类特征
        self.analyze_categorical_features()

        # 分析相关性
        self.analyze_correlation()

        # 分析流失率
        self.analyze_churn_rate()

        logger.info("\n=== EDA报告生成完成 ===")
        logger.info(f"所有图表已保存到 {self.reports_dir} 目录")


if __name__ == "__main__":
    # 使用绝对路径
    data_path = BASE_DIR / 'ml_pipeline' / 'data' / 'WA_Fn-UseC_-Telco-Customer-Churn.csv'
    logger.info(f"数据文件路径: {data_path}")
    logger.info(f"文件是否存在: {data_path.exists()}")

    explorer = DataExplorer(data_path)
    explorer.generate_eda_report()