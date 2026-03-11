import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from app.core.config import BASE_DIR
from app.core.logging import setup_logging
import os

# 设置matplotlib支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 初始化探索专用日志器
logger = setup_logging("explore")

class DataExplorer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = None
        self.encoded_data = None
        self.label_encoders = {}
        self.reports_dir = BASE_DIR / 'ml_pipeline' / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self):
        """加载数据集"""
        logger.info(f"正在加载数据: {self.data_path}")
        self.data = pd.read_csv(self.data_path)
        logger.info(f"数据集加载成功，形状为: {self.data.shape}")
        logger.info(f"列名: {list(self.data.columns)}")
        logger.info(f"数据类型:")
        logger.info(self.data.dtypes)
        return self.data
    
    def handle_missing_values(self):
        """处理缺失值"""
        logger.info("\n=== 缺失值分析 ===")
        missing_data = self.data.isnull().sum()
        missing_percentage = (missing_data / len(self.data) * 100).round(2)
        missing_df = pd.DataFrame({'缺失值数量': missing_data, '缺失率(%)': missing_percentage})
        missing_df = missing_df[missing_df['缺失值数量'] > 0]
        
        if not missing_df.empty:
            logger.info("缺失值情况:")
            logger.info(missing_df)
        else:
            logger.info("无缺失值")
        
        # 检查TotalCharges列的缺失值
        if 'TotalCharges' in self.data.columns:
            # 转换为数值型，将空值设为NaN
            self.data['TotalCharges'] = pd.to_numeric(self.data['TotalCharges'], errors='coerce')
            # 用均值填充缺失值
            self.data['TotalCharges'] = self.data['TotalCharges'].fillna(self.data['TotalCharges'].mean())
            logger.info("\nTotalCharges列的缺失值已用均值填充")
        
        return self.data
    
    def detect_outliers(self):
        """检测异常值"""
        logger.info("\n=== 异常值检测 ===")
        numeric_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
        
        for col in numeric_cols:
            if col in self.data.columns:
                # 使用3σ原则检测异常值
                mean = self.data[col].mean()
                std = self.data[col].std()
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
                
                outliers = self.data[(self.data[col] < lower_bound) | (self.data[col] > upper_bound)]
                logger.info(f"{col}列异常值数量: {len(outliers)}")
                logger.info(f"{col}列异常值范围: [{lower_bound:.2f}, {upper_bound:.2f}]")
        
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
        logger.info("\n=== 数值特征分析 ===")
        numeric_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
        
        logger.info("数值特征描述性统计:")
        logger.info(self.data[numeric_cols].describe())
        
        # 生成数值特征分布图表
        plt.figure(figsize=(15, 10))
        for i, col in enumerate(numeric_cols, 1):
            plt.subplot(3, 2, 2*i-1)
            sns.histplot(self.data[col], kde=True)
            plt.title(f'{col} 分布')
            
            plt.subplot(3, 2, 2*i)
            sns.boxplot(x=self.data[col])
            plt.title(f'{col} 箱线图')
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'numeric_features.png')
        plt.close()
        logger.info("数值特征分布图已保存到 reports/numeric_features.png")
    
    def analyze_categorical_features(self):
        """分析分类特征"""
        logger.info("\n=== 分类特征分析 ===")
        categorical_cols = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'PhoneService', 
                           'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup', 
                           'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies', 
                           'Contract', 'PaperlessBilling', 'PaymentMethod']
        
        # 生成分类特征分布图表
        plt.figure(figsize=(20, 15))
        for i, col in enumerate(categorical_cols, 1):
            plt.subplot(4, 4, i)
            sns.countplot(x=col, data=self.data)
            plt.title(f'{col} 分布')
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'categorical_features.png')
        plt.close()
        logger.info("分类特征分布图已保存到 reports/categorical_features.png")
        
        # 分析分类特征与Churn的关系
        logger.info("\n分类特征与Churn的关系:")
        plt.figure(figsize=(20, 15))
        for i, col in enumerate(categorical_cols, 1):
            plt.subplot(4, 4, i)
            sns.countplot(x=col, hue='Churn', data=self.data)
            plt.title(f'{col} 与 Churn 的关系')
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'categorical_churn_relation.png')
        plt.close()
        logger.info("分类特征与Churn关系图已保存到 reports/categorical_churn_relation.png")
    
    def analyze_correlation(self):
        """分析特征与Churn的相关性"""
        logger.info("\n=== 相关性分析 ===")
        correlation = self.encoded_data.corr()['Churn'].sort_values(ascending=False)
        logger.info("特征与Churn的相关性:")
        logger.info(correlation)
        
        # 生成相关性热力图
        plt.figure(figsize=(15, 10))
        # 只显示与Churn相关性前20的特征
        top_features = correlation.abs().nlargest(20).index
        sns.heatmap(self.encoded_data[top_features].corr(), annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('特征相关性热力图')
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'correlation_heatmap.png')
        plt.close()
        logger.info("相关性热力图已保存到 reports/correlation_heatmap.png")
    
    def analyze_churn_rate(self):
        """分析流失率"""
        logger.info("\n=== 流失率分析 ===")
        churn_rate = self.data['Churn'].value_counts(normalize=True) * 100
        logger.info("流失率:")
        logger.info(churn_rate)
        
        # 生成流失率饼图
        plt.figure(figsize=(8, 6))
        plt.pie(churn_rate, labels=['No', 'Yes'], autopct='%1.1f%%', startangle=90)
        plt.title('流失率分布')
        plt.axis('equal')
        plt.savefig(self.reports_dir / 'churn_rate.png')
        plt.close()
        logger.info("流失率饼图已保存到 reports/churn_rate.png")
    
    def generate_eda_report(self):
        """生成完整的EDA报告"""
        logger.info("\n=== 开始生成EDA报告 ===")
        
        # 加载数据
        self.load_data()
        
        # 处理缺失值
        self.handle_missing_values()
        
        # 检测异常值
        self.detect_outliers()
        
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
        
        # 生成HTML报告
        self._generate_html_report()
        
        logger.info("\n=== EDA报告生成完成 ===")
    
    def _generate_html_report(self):
        """生成HTML格式的EDA报告"""
        report_path = self.reports_dir / 'eda_report.html'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>用户流失预测数据集EDA报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                .section {{ margin-bottom: 30px; }}
                .image {{ margin: 20px 0; }}
                img {{ max-width: 100%; height: auto; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>用户流失预测数据集EDA报告</h1>
            
            <div class="section">
                <h2>1. 数据基本信息</h2>
                <p>数据集形状: {self.data.shape}</p>
                <p>特征数量: {len(self.data.columns)}</p>
                <p>样本数量: {len(self.data)}</p>
            </div>
            
            <div class="section">
                <h2>2. 数值特征分布</h2>
                <div class="image">
                    <img src="numeric_features.png" alt="数值特征分布">
                </div>
            </div>
            
            <div class="section">
                <h2>3. 分类特征分布</h2>
                <div class="image">
                    <img src="categorical_features.png" alt="分类特征分布">
                </div>
            </div>
            
            <div class="section">
                <h2>4. 分类特征与流失的关系</h2>
                <div class="image">
                    <img src="categorical_churn_relation.png" alt="分类特征与流失的关系">
                </div>
            </div>
            
            <div class="section">
                <h2>5. 特征相关性分析</h2>
                <div class="image">
                    <img src="correlation_heatmap.png" alt="特征相关性热力图">
                </div>
            </div>
            
            <div class="section">
                <h2>6. 流失率分析</h2>
                <div class="image">
                    <img src="churn_rate.png" alt="流失率分布">
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML格式的EDA报告已保存到: {report_path}")

if __name__ == "__main__":
    # 使用绝对路径
    data_path = BASE_DIR / 'ml_pipeline' / 'data' / 'WA_Fn-UseC_-Telco-Customer-Churn.csv'
    logger.info(f"数据文件路径: {data_path}")
    logger.info(f"文件是否存在: {data_path.exists()}")
    
    explorer = DataExplorer(data_path)
    explorer.generate_eda_report()