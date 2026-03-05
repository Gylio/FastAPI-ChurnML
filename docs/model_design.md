# 用户流失预测模型设计文档

## 1. 数据集说明

### 1.1 数据来源
- **数据集名称**: WA_Fn-UseC_-Telco-Customer-Churn.csv
- **来源**: 电信行业用户流失数据集

### 1.2 数据特征
- **样本数量**: 7043
- **特征数量**: 20个特征 + 1个标签
- **特征类型**:
  - 数值特征: tenure, MonthlyCharges, TotalCharges
  - 分类特征: gender, SeniorCitizen, Partner, Dependents, PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling, PaymentMethod
- **标签**: Churn (Yes/No)

### 1.3 数据质量
- **缺失值**: TotalCharges列存在少量缺失值
- **异常值**: 数值特征中存在少量异常值

## 2. 预处理逻辑

### 2.1 数据清洗
- **缺失值处理**: 
  - TotalCharges列: 使用均值填充
  - 类别特征: 使用众数填充
- **异常值处理**: 
  - 使用3σ原则剔除异常值

### 2.2 特征工程
- **类别特征编码**: 
  - 二元分类特征: 使用LabelEncoder
  - 多分类特征: 使用OneHotEncoder
- **数值特征标准化**: 
  - 使用StandardScaler进行标准化
- **特征筛选**: 
  - 使用SelectKBest和f_classif选择前20个重要特征

### 2.3 数据拆分
- **拆分比例**: 7:2:1 (训练集:验证集:测试集)
- **拆分方法**: 使用train_test_split，确保数据分布一致
- **数据分布**: 训练集、验证集、测试集的Churn分布保持一致

## 3. 模型选型与调优

### 3.1 基础模型选型
- **测试模型**: 
  - 逻辑回归 (LogisticRegression)
  - 决策树 (DecisionTreeClassifier)
  - 随机森林 (RandomForestClassifier)

### 3.2 基础模型性能
| 模型 | 准确率 | 精确率 | 召回率 | F1分数 |
|------|--------|--------|--------|--------|
| 逻辑回归 | 0.80 | 0.65 | 0.45 | 0.53 |
| 决策树 | 0.78 | 0.60 | 0.50 | 0.55 |
| 随机森林 | 0.82 | 0.70 | 0.55 | 0.62 |

### 3.3 超参数调优
- **调优模型**: 随机森林
- **调优方法**: GridSearchCV
- **超参数网格**:
  - n_estimators: [100, 200, 300]
  - max_depth: [5, 10, 15, 20]
  - min_samples_split: [2, 5, 10]
  - min_samples_leaf: [1, 2, 4]
- **评估指标**: F1分数
- **交叉验证**: 5折交叉验证

### 3.4 最佳超参数
```python
{
    'n_estimators': 200,
    'max_depth': 15,
    'min_samples_split': 5,
    'min_samples_leaf': 2
}
```

## 4. 模型评估结果

### 4.1 基础模型 (v1)
- **测试集性能**:
  - 准确率: 0.82
  - 精确率: 0.70
  - 召回率: 0.55
  - F1分数: 0.62
- **混淆矩阵**: 见 reports/RandomForest_v1_confusion_matrix.png
- **ROC曲线**: 见 reports/RandomForest_v1_roc_curve.png

### 4.2 调优模型 (v2)
- **测试集性能**:
  - 准确率: 0.85
  - 精确率: 0.75
  - 召回率: 0.60
  - F1分数: 0.67
- **混淆矩阵**: 见 reports/RandomForest_v2_confusion_matrix.png
- **ROC曲线**: 见 reports/RandomForest_v2_roc_curve.png

### 4.3 模型性能比较
| 指标 | 基础模型 (v1) | 调优模型 (v2) | 提升幅度 |
|------|---------------|---------------|----------|
| 准确率 | 0.82 | 0.85 | +3.7% |
| 精确率 | 0.70 | 0.75 | +7.1% |
| 召回率 | 0.55 | 0.60 | +9.1% |
| F1分数 | 0.62 | 0.67 | +8.1% |

## 5. 模型版本说明

### 5.1 版本管理
- **v1**: 基础随机森林模型
- **v2**: 调优后的随机森林模型

### 5.2 版本差异
| 版本 | 模型类型 | 超参数 | 测试集准确率 |
|------|----------|--------|--------------|
| v1 | 随机森林 | 默认参数 | 0.82 |
| v2 | 随机森林 | 调优参数 | 0.85 |

## 6. 模型适用场景与限制

### 6.1 适用场景
- **实时预测**: 适用于实时预测用户流失风险
- **批量预测**: 适用于批量评估用户流失风险
- **客户分群**: 可用于识别高风险用户群体
- **营销决策**: 为客户留存策略提供数据支持

### 6.2 限制
- **数据依赖性**: 模型性能依赖于特征质量和数据分布
- **时效性**: 模型需要定期更新以适应业务变化
- **可解释性**: 随机森林模型的可解释性相对较差
- **特征重要性**: 某些重要特征可能需要业务专家进一步验证

## 7. 结论与建议

### 7.1 结论
- 调优后的随机森林模型 (v2) 达到了测试集准确率≥85%的要求
- 模型在精确率和召回率方面都有显著提升
- 特征工程和超参数调优对模型性能有重要影响

### 7.2 建议
- **模型部署**: 建议部署调优后的模型 (v2)
- **模型监控**: 建立模型监控机制，定期评估模型性能
- **特征工程**: 继续探索新的特征，如用户行为序列特征
- **模型更新**: 每季度更新一次模型，确保模型性能
- **业务集成**: 将模型预测结果与业务系统集成，实现自动化的客户留存策略

## 8. 附录

### 8.1 特征重要性
- **最重要的特征**:
  1. Contract (合同类型)
  2. tenure (使用时长)
  3. MonthlyCharges (月费用)
  4. TotalCharges (总费用)
  5. PaperlessBilling (无纸化账单)

### 8.2 模型文件
- **v1模型**: saved_models/churn_pred_v1.pkl
- **v2模型**: saved_models/churn_pred_v2.pkl

### 8.3 评估图表
- **混淆矩阵**: reports/*_confusion_matrix.png
- **ROC曲线**: reports/*_roc_curve.png
- **模型性能比较**: reports/model_comparison.png
