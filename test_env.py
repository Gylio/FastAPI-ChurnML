import os
import sys

print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")

# 检查文件路径
base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, 'ml_pipeline', 'data', 'WA_Fn-UseC_-Telco-Customer-Churn.csv')
print(f"数据文件路径: {data_path}")
print(f"文件是否存在: {os.path.exists(data_path)}")

# 尝试导入必要的库
try:
    import pandas
    print("pandas导入成功")
except ImportError:
    print("pandas导入失败")

try:
    import numpy
    print("numpy导入成功")
except ImportError:
    print("numpy导入失败")

try:
    import matplotlib
    print("matplotlib导入成功")
except ImportError:
    print("matplotlib导入失败")

try:
    import seaborn
    print("seaborn导入成功")
except ImportError:
    print("seaborn导入失败")

try:
    from sklearn.preprocessing import LabelEncoder
    print("scikit-learn导入成功")
except ImportError:
    print("scikit-learn导入失败")
