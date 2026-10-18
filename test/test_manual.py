
# 导入 Path，用于构建项目中的文件路径。
from pathlib import Path

# 导入 pandas，用于读取 CSV 数据。
import pandas as pd

# 导入项目中已经实现的三个工具函数。
from data_tool_calling_agent.function_tools.csv_tool import (
    load_dataset,
    inspect_dataset,
    filter_jobs,
)

# 获取 tests 文件夹的路径。
TESTS_DIR = Path(__file__).resolve().parent

# 获取项目根目录，因为 tests 和 src 是同级目录。
PROJECT_ROOT = TESTS_DIR.parent

# 设置原始 CSV 文件路径，请根据你的实际文件名修改。
DATASET_PATH = PROJECT_ROOT / "data" / "jobs.csv"

# 创建一个只读取前 20 行的临时测试数据文件。
SAMPLE_PATH = TESTS_DIR / "sample_jobs.csv"

# 从原始 CSV 读取前 20 行，避免加载整个大文件。
sample_df = pd.read_csv(
    DATASET_PATH,
    encoding="utf-8",
    nrows=20,
)

# 将这 20 行保存为临时测试文件，方便测试现有工具函数。
sample_df.to_csv(SAMPLE_PATH, index=False, encoding="utf-8")

# 打印标题，区分不同工具的测试结果。
print("\n========== 1. 测试 load_dataset ==========")

# 调用读取函数，加载这份 20 行的测试数据。
df = load_dataset(SAMPLE_PATH)

# 打印实际读取到的行数。
print(f"读取行数：{len(df)}")

# 打印实际读取到的字段名称。
print(f"字段名称：{df.columns.tolist()}")

# 打印前 5 行，直观检查数据内容。
print(df.head().to_string(index=False))

# 打印标题，开始测试查看工具。
print("\n========== 2. 测试 inspect_dataset ==========")

# 调用工具，查看前 5 行。
head_result = inspect_dataset(
    SAMPLE_PATH,
    action="head",
    n=5,
)

# 打印实际返回的行数。
print(f"返回行数：{len(head_result)}")

# 打印实际返回的数据内容。
print(head_result.to_string(index=False))

# 调用工具，查看所有字段名称。
columns_result = inspect_dataset(
    SAMPLE_PATH,
    action="columns",
)

# 打印字段查看结果。
print(f"\n字段列表：{columns_result}")

# 打印标题，开始测试岗位筛选工具。
print("\n========== 3. 测试 filter_jobs ==========")

# 先从测试数据中寻找一个真实存在的地点。
locations = (
    df["location_raw"]
    .dropna()
    .astype(str)
    .str.strip()
)

# 去掉空字符串，避免使用无效地点进行测试。
locations = locations[locations != ""]

# 只有存在有效地点时，才运行地点筛选测试。
if not locations.empty:
    # 选取测试数据中的第一个有效地点作为筛选条件。
    target_location = locations.iloc[0]

    # 打印实际使用的筛选条件。
    print(f"筛选地点：{target_location}")

    # 调用岗位筛选工具，筛选符合地点条件的岗位。
    filtered_df = filter_jobs(
        df,
        location=target_location,
    )

    # 打印符合条件的岗位数量。
    print(f"匹配岗位数：{len(filtered_df)}")

    # 打印实际匹配到的岗位，方便人工核对。
    print(filtered_df.to_string(index=False))
else:
    # 如果前 20 行没有有效地点，提示无法执行本次地点筛选。
    print("前 20 行没有有效地点，跳过地点筛选测试。")

# 打印结束提示，方便确认脚本已经运行完毕。
print("\n========== 测试脚本执行完毕 ==========")