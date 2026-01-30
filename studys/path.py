from pathlib import Path
import os
from datetime import datetime

# 示例1: 获取当前文件所在目录的父目录（项目根目录）
project_root = Path(__file__).parent.parent
print(f"项目根目录: {project_root}")

# 示例2: 创建时间戳格式的文件名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"时间戳: {timestamp}")

# 示例3: 组合路径和文件名
symbol = "AAPL"
output_file = project_root / f"czsc_chart_{symbol}_{timestamp}.html"
print(f"输出文件完整路径: {output_file}")

# 示例4: 路径基本操作
print("\n--- 路径基本操作 ---")

# 创建路径对象
path_obj = Path("folder/subfolder/file.txt")
print(f"路径对象: {path_obj}")

# 获取文件名
print(f"文件名: {path_obj.name}")

# 获取文件名（不含扩展名）
print(f"文件名（无扩展名）: {path_obj.stem}")

# 获取文件扩展名
print(f"文件扩展名: {path_obj.suffix}")

# 获取父目录
print(f"父目录: {path_obj.parent}")

# 示例5: 检查路径是否存在
print("\n--- 检查路径是否存在 ---")
test_path = Path("test_folder/test.txt")
print(f"路径是否存在: {test_path.exists()}")
print(f"是文件吗: {test_path.is_file()}")
print(f"是目录吗: {test_path.is_dir()}")

# 示例6: 创建目录
print("\n--- 创建目录 ---")
new_dir = Path("my_new_folder")
new_dir.mkdir(exist_ok=True)  # 如果目录已存在不会报错
print(f"创建目录: {new_dir}")

# 示例7: 写入文件
print("\n--- 写入文件 ---")
output_file = Path("output.txt")
output_file.write_text("Hello, Python Path!")
print(f"写入文件: {output_file}")

# 示例8: 读取文件
content = output_file.read_text()
print(f"文件内容: {content}")

# 示例9: 路径拼接的多种方式
print("\n--- 路径拼接方式 ---")
base_path = Path("/home/user")
# 方式1: 使用 / 运算符
path1 = base_path / "documents" / "file.txt"
print(f"方式1 (使用/): {path1}")

# 方式2: 使用 joinpath
path2 = base_path.joinpath("documents", "file.txt")
print(f"方式2 (joinpath): {path2}")

# 方式3: 使用 os.path.join (传统方式)
path3 = os.path.join(base_path, "documents", "file.txt")
print(f"方式3 (os.path.join): {path3}")

# 示例10: 获取绝对路径
print("\n--- 绝对路径 ---")
relative_path = Path("folder/file.txt")
absolute_path = relative_path.absolute()
print(f"相对路径: {relative_path}")
print(f"绝对路径: {absolute_path}")

# 示例11: 遍历目录
print("\n--- 遍历目录 ---")
# 创建测试目录结构
test_root = Path("test_project")
(test_root / "src").mkdir(parents=True, exist_ok=True)
(test_root / "docs").mkdir(exist_ok=True)
(test_root / "src" / "__init__.py").write_text("")
(test_root / "src" / "main.py").write_text("print('hello')")
(test_root / "docs" / "readme.md").write_text("# Documentation")

# 遍历所有文件和目录
print("所有项目文件:")
for item in test_root.rglob("*"):  # rglob递归遍历
    if item.is_file():
        print(f"  文件: {item.relative_to(test_root)}")

# 示例12: 路径解析
print("\n--- 路径解析 ---")
example_path = Path("/home/user/project/src/utils/__init__.py")
parts = example_path.parts
print(f"路径各部分: {parts}")
print(f"路径深度: {len(parts)}")

# 示例13: 实际应用 - 创建完整的文件保存函数
print("\n--- 实际应用示例 ---")

def save_chart_data(symbol: str, data: str, chart_type: str = "czsc"):
    """保存图表数据到文件"""
    
    # 获取项目根目录（假设此文件在项目src目录下）
    project_root = Path(__file__).parent.parent
    
    # 创建输出目录
    output_dir = project_root / "output" / chart_type
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{chart_type}_chart_{symbol}_{timestamp}.html"
    
    # 完整输出路径
    output_path = output_dir / filename
    
    # 写入数据
    output_path.write_text(data)
    
    print(f"图表已保存到: {output_path}")
    print(f"相对路径: {output_path.relative_to(project_root)}")
    
    return output_path

# 使用示例
# 假设这是图表数据
chart_data = """
<!DOCTYPE html>
<html>
<head>
    <title>Chart for AAPL</title>
</head>
<body>
    <h1>Stock Chart: AAPL</h1>
    <div id="chart-container"></div>
</body>
</html>
"""

# 调用函数
saved_path = save_chart_data("AAPL", chart_data)

# 清理示例文件（可选）
print("\n--- 清理示例文件 ---")
import shutil

# 删除创建的测试文件和目录
test_files = ["output.txt", "my_new_folder", "test_project"]
for item in test_files:
    path_item = Path(item)
    if path_item.exists():
        if path_item.is_file():
            path_item.unlink()
            print(f"删除文件: {item}")
        else:
            shutil.rmtree(path_item)
            print(f"删除目录: {item}")

# 如果有保存的图表文件也删除
if saved_path.exists():
    # 删除文件
    saved_path.unlink()
    # 如果目录为空，也删除
    if saved_path.parent.exists() and len(list(saved_path.parent.iterdir())) == 0:
        saved_path.parent.rmdir()
    print(f"删除图表文件: {saved_path}")