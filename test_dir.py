import os

print("=== 测试目录创建和文件写入 ===")

# 测试当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 测试创建目录
model_dir = 'saved_models'
print(f"尝试创建目录: {model_dir}")

try:
    os.makedirs(model_dir, exist_ok=True)
    print(f"目录创建成功: {model_dir}")
    
    # 测试写入文件
    test_file = os.path.join(model_dir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('Test file')
    print(f"文件写入成功: {test_file}")
    
    # 验证文件存在
    if os.path.exists(test_file):
        print(f"文件存在: {test_file}")
    else:
        print(f"文件不存在: {test_file}")
        
except Exception as e:
    print(f"错误: {e}")

print("=== 测试完成 ===")
