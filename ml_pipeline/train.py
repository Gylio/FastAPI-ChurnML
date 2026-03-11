import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_curve, auc
import joblib
from app.core.config import BASE_DIR, MODEL_DIR, settings
from app.core.logging import setup_logging
from ml_pipeline.data_prep import DataPreprocessor

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 初始化训练专用日志器
logger = setup_logging("train")

class ModelTrainer:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.models = {}
        self.best_model = None
        self.best_params = None
        self.reports_dir = BASE_DIR / 'ml_pipeline' / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self, data_path):
        """加载并预处理数据"""
        logger.info(f"正在加载数据: {data_path}")
        
        # 使用预处理 pipeline
        X_train, X_val, X_test, y_train, y_val, y_test = self.preprocessor.preprocess_pipeline(
            data_path,
            encoding_type='label',
            normalization_type='standard',
            remove_outliers=True,
            feature_selection=True,
            k=19  # 调整为实际特征数量
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def train_baseline_models(self, X_train, y_train, X_val, y_val):
        """训练基础模型"""
        logger.info("\n=== 训练基础模型 ===")
        
        # 定义基础模型
        models = {
            'LogisticRegression': LogisticRegression(random_state=42),
            'DecisionTree': DecisionTreeClassifier(random_state=42),
            'RandomForest': RandomForestClassifier(random_state=42)
        }
        
        # 训练并评估每个模型
        results = {}
        for model_name, model in models.items():
            logger.info(f"\n训练 {model_name}...")
            
            # 训练模型
            model.fit(X_train, y_train)
            
            # 在验证集上评估
            y_val_pred = model.predict(X_val)
            
            # 计算评估指标
            accuracy = accuracy_score(y_val, y_val_pred)
            precision = precision_score(y_val, y_val_pred)
            recall = recall_score(y_val, y_val_pred)
            f1 = f1_score(y_val, y_val_pred)
            
            results[model_name] = {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
            
            logger.info(f"{model_name} 验证集性能:")
            logger.info(f"准确率: {accuracy:.4f}")
            logger.info(f"精确率: {precision:.4f}")
            logger.info(f"召回率: {recall:.4f}")
            logger.info(f"F1分数: {f1:.4f}")
        
        # 保存模型
        self.models = results
        
        # 选择最好的基础模型
        best_model_name = max(results, key=lambda x: results[x]['f1'])
        self.best_model = results[best_model_name]['model']
        logger.info(f"\n最佳基础模型: {best_model_name}")
        
        return results
    
    def tune_hyperparameters(self, X_train, y_train, X_val, y_val):
        """超参数调优"""
        logger.info("\n=== 超参数调优 ===")
        
        # 定义随机森林的超参数网格
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [5, 10, 15, 20],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        # 使用GridSearchCV进行调优
        grid_search = GridSearchCV(
            estimator=RandomForestClassifier(random_state=42),
            param_grid=param_grid,
            cv=5,
            scoring='f1',
            n_jobs=-1
        )
        
        logger.info("开始网格搜索...")
        grid_search.fit(X_train, y_train)
        
        # 获取最佳参数和模型
        self.best_params = grid_search.best_params_
        self.best_model = grid_search.best_estimator_
        
        logger.info(f"\n最佳参数: {self.best_params}")
        
        # 在验证集上评估最佳模型
        y_val_pred = self.best_model.predict(X_val)
        accuracy = accuracy_score(y_val, y_val_pred)
        precision = precision_score(y_val, y_val_pred)
        recall = recall_score(y_val, y_val_pred)
        f1 = f1_score(y_val, y_val_pred)
        
        logger.info("\n调优后模型验证集性能:")
        logger.info(f"准确率: {accuracy:.4f}")
        logger.info(f"精确率: {precision:.4f}")
        logger.info(f"召回率: {recall:.4f}")
        logger.info(f"F1分数: {f1:.4f}")
        
        return self.best_model, self.best_params
    
    def evaluate_model(self, model, X_test, y_test, model_name):
        """评估模型并生成评估指标"""
        logger.info(f"\n=== 评估 {model_name} ===")
        
        # 在测试集上预测
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # 计算评估指标
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        logger.info(f"测试集性能:")
        logger.info(f"准确率: {accuracy:.4f}")
        logger.info(f"精确率: {precision:.4f}")
        logger.info(f"召回率: {recall:.4f}")
        logger.info(f"F1分数: {f1:.4f}")
        
        # 生成混淆矩阵
        self._generate_confusion_matrix(y_test, y_pred, model_name)
        
        # 生成ROC曲线
        self._generate_roc_curve(y_test, y_pred_proba, model_name)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    def _generate_confusion_matrix(self, y_test, y_pred, model_name):
        """生成混淆矩阵"""
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['No Churn', 'Churn'], 
                   yticklabels=['No Churn', 'Churn'])
        plt.title(f'{model_name} 混淆矩阵')
        plt.xlabel('预测值')
        plt.ylabel('真实值')
        plt.tight_layout()
        plt.savefig(self.reports_dir / f'{model_name}_confusion_matrix.png')
        plt.close()
        logger.info(f"混淆矩阵已保存到 reports/{model_name}_confusion_matrix.png")
    
    def _generate_roc_curve(self, y_test, y_pred_proba, model_name):
        """生成ROC曲线"""
        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC曲线 (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='gray', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('假阳性率')
        plt.ylabel('真阳性率')
        plt.title(f'{model_name} ROC曲线')
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(self.reports_dir / f'{model_name}_roc_curve.png')
        plt.close()
        logger.info(f"ROC曲线已保存到 reports/{model_name}_roc_curve.png")
    
    def save_model(self, model, version):
        """保存模型"""
        logger.info(f"\n=== 保存模型 v{version} ===")
        
        # 确保模型目录存在
        model_dir = MODEL_DIR
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存模型文件
        model_path = model_dir / f'churn_pred_v{version}{settings.MODEL_FILE_SUFFIX}'
        
        # 保存模型和预处理对象
        joblib.dump({
            'model': model,
            'preprocessor': self.preprocessor,
            'version': version
        }, model_path)
        
        logger.info(f"模型已保存到: {model_path}")
        return model_path
    
    def run_pipeline(self, data_path):
        """完整的训练 pipeline"""
        logger.info("\n=== 开始模型训练 pipeline ===")
        
        # 1. 加载并预处理数据
        X_train, X_val, X_test, y_train, y_val, y_test = self.load_data(data_path)
        
        # 2. 训练基础模型
        baseline_results = self.train_baseline_models(X_train, y_train, X_val, y_val)
        
        # 3. 保存基础随机森林模型（v1）
        rf_model = baseline_results['RandomForest']['model']
        self.save_model(rf_model, 1)
        
        # 4. 超参数调优
        tuned_model, best_params = self.tune_hyperparameters(X_train, y_train, X_val, y_val)
        
        # 5. 保存调优后的模型（v2）
        self.save_model(tuned_model, 2)
        
        # 6. 评估基础模型
        logger.info("\n=== 评估基础模型 ===")
        baseline_metrics = self.evaluate_model(rf_model, X_test, y_test, 'RandomForest_v1')
        
        # 7. 评估调优模型
        logger.info("\n=== 评估调优模型 ===")
        tuned_metrics = self.evaluate_model(tuned_model, X_test, y_test, 'RandomForest_v2')
        
        # 8. 比较模型性能
        self._compare_models(baseline_metrics, tuned_metrics)
        
        logger.info("\n=== 模型训练 pipeline 完成 ===")
        return baseline_metrics, tuned_metrics
    
    def _compare_models(self, baseline_metrics, tuned_metrics):
        """比较基础模型和调优模型的性能"""
        logger.info("\n=== 模型性能比较 ===")
        
        metrics_df = pd.DataFrame({
            'Metric': ['准确率', '精确率', '召回率', 'F1分数'],
            '基础模型': [baseline_metrics['accuracy'], baseline_metrics['precision'], 
                       baseline_metrics['recall'], baseline_metrics['f1']],
            '调优模型': [tuned_metrics['accuracy'], tuned_metrics['precision'], 
                       tuned_metrics['recall'], tuned_metrics['f1']]
        })
        
        logger.info(metrics_df)
        
        # 生成性能比较图表
        plt.figure(figsize=(10, 6))
        metrics_df.set_index('Metric').plot(kind='bar')
        plt.title('模型性能比较')
        plt.ylim(0, 1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'model_comparison.png')
        plt.close()
        logger.info("模型性能比较图已保存到 reports/model_comparison.png")

if __name__ == "__main__":
    print("开始执行训练脚本")
    # 测试训练 pipeline
    data_path = BASE_DIR / 'ml_pipeline' / 'data' / 'WA_Fn-UseC_-Telco-Customer-Churn.csv'
    print(f"数据文件路径: {data_path}")
    print(f"文件是否存在: {data_path.exists()}")
    
    try:
        trainer = ModelTrainer()
        print("创建ModelTrainer成功")
        
        baseline_metrics, tuned_metrics = trainer.run_pipeline(data_path)
        print("训练完成！")
        print(f"基础模型测试集准确率: {baseline_metrics['accuracy']:.4f}")
        print(f"调优模型测试集准确率: {tuned_metrics['accuracy']:.4f}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()