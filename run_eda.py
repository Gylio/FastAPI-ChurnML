import subprocess
import os

# 运行数据探索脚本
print("开始运行数据探索脚本...")
result = subprocess.run(['python', 'ml_pipeline/explore_data.py'], capture_output=True, text=True)

print("脚本输出:")
print(result.stdout)

if result.stderr:
    print("错误信息:")
    print(result.stderr)

print(f"脚本执行状态: {result.returncode}")
