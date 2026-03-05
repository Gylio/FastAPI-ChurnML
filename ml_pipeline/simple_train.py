import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
from app.core.config import BASE_DIR, MODEL_DIR, settings
from app.core.logging import logger

logger.info("=== 开始简单模型训练 ===")

# 使用绝对路径加载数据
data_path = BASE_DIR / 'ml_pipeline' / 'data' / 'WA_Fn-UseC_-Telco-Customer-Churn.csv'
logger.info(f"加载数据: {data_path}")
data = pd.read_csv(data_path)
logger.info(f"数据形状: {data.shape}")

# 处理缺失值
data['TotalCharges'] = pd.to_numeric(data['TotalCharges'], errors='coerce')
data['TotalCharges'] = data['TotalCharges'].fillna(data['TotalCharges'].mean())

# 编码目标变量
le_churn = LabelEncoder()
data['Churn'] = le_churn.fit_transform(data['Churn'])

# 分离特征和目标变量
X = data.drop(['customerID', 'Churn'], axis=1)
y = data['Churn']

# 编码分类特征
categorical_cols = ['gender', 'Partner', 'Dependents', 'PhoneService', 'MultipleLines',
                  'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
                  'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
                  'PaperlessBilling', 'PaymentMethod']

label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])
    label_encoders[col] = le

# 特征标准化
scaler = StandardScaler()
X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
logger.info(f"训练集形状: {X_train.shape}")
logger.info(f"测试集形状: {X_test.shape}")

# 训练模型
logger.info("训练模型...")
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# 评估模型
logger.info("评估模型...")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

logger.info(f"准确率: {accuracy:.4f}")
logger.info(f"精确率: {precision:.4f}")
logger.info(f"召回率: {recall:.4f}")
logger.info(f"F1分数: {f1:.4f}")

# 保存模型
logger.info("保存模型...")
model_dir = MODEL_DIR
model_dir.mkdir(parents=True, exist_ok=True)
model_path = model_dir / f'churn_pred_{settings.DEFAULT_MODEL_VERSION}{settings.MODEL_FILE_SUFFIX}'

joblib.dump({
    'model': model,
    'scaler': scaler,
    'label_encoders': label_encoders,
    'le_churn': le_churn
}, model_path)

logger.info(f"模型已保存到: {model_path}")
logger.info("=== 简单模型训练完成 ===")