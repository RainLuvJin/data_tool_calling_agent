
# 从 pathlib 导入 Path，用于拼接和检查文件路径。
from pathlib import Path

# 导入 pandas，用于读取和比较 CSV 数据。
import pandas as pd

# 导入 pytest，用于组织测试、创建临时目录和跳过不适用的测试。
import pytest

# 导入我们自己编写的三个待测试函数。
from data_tool_calling_agent.function_tools.csv_tool import (
    load_dataset,
    inspect_dataset,
    filter_jobs,
)

# 获取当前测试文件所在的 tests 文件夹的路径。
TESTS_DIR = Path(__file__).resolve().parent

# 获取项目根目录；这里假设 tests 和 src 是同级文件夹。
PROJECT_ROOT = TESTS_DIR.parent

# 设置原始 CSV 的路径；如果你的文件位置不同，请修改这一行。
DATASET_PATH = PROJECT_ROOT / "data" / "jobs.csv"


# 创建一个测试数据夹具，供下面的测试函数重复使用。
@pytest.fixture
def sample_csv_path(tmp_path):
    # 检查原始 CSV 是否存在，避免因路径错误而产生误导性的测试结果。
    assert DATASET_PATH.is_file(), (
        f"找不到 CSV 文件：{DATASET_PATH}。请修改 DATASET_PATH。"
    )

    # 只从原始 CSV 读取前 20 行，不把整个数据集加载进测试内存。
    sample_df = pd.read_csv(
        DATASET_PATH,
        encoding="utf-8",
        nrows=20,
    )

    # 确认测试数据不是空的。
    assert not sample_df.empty, "原始 CSV 没有可供测试的数据。"

    # 使用 pytest 提供的临时目录，创建一个小型测试 CSV 文件。
    temp_csv = tmp_path / "sample_jobs.csv"

    # 把前 20 行保存到临时文件中，供实际函数读取。
    sample_df.to_csv(temp_csv, index=False, encoding="utf-8")

    # 返回临时 CSV 路径，让每个测试函数都能使用它。
    return temp_csv


# 测试一：load_dataset 是否能读取完整的测试文件。
def test_load_dataset(sample_csv_path):
    # 调用实际的读取函数；这里的文件只有前 20 行。
    df = load_dataset(sample_csv_path)

    # 检查函数是否成功返回 Pandas DataFrame。
    assert isinstance(df, pd.DataFrame)

    # 检查读取到的行数是否与测试文件一致。
    assert len(df) == 20

    # 检查读取结果是否包含原始数据集的字段。
    assert len(df.columns) > 0


# 测试二：inspect_dataset 是否能正确查看前 N 行。
def test_inspect_head(sample_csv_path):
    # 请求查看前 5 行，检查函数是否正确处理 n 参数。
    result = inspect_dataset(sample_csv_path, action="head", n=5)

    # 确认返回结果是 DataFrame。
    assert isinstance(result, pd.DataFrame)

    # 确认返回的行数正好是 5。
    assert len(result) == 5


# 测试三：inspect_dataset 是否能正确读取字段名称。
def test_inspect_columns(sample_csv_path):
    # 调用字段查看功能，获取 CSV 的字段名称列表。
    result = inspect_dataset(sample_csv_path, action="columns")

    # 确认返回结果是列表。
    assert isinstance(result, list)

    # 确认字段列表不是空列表。
    assert len(result) > 0

    # 确认关键字段存在，防止数据格式变化后测试仍然误通过。
    assert "location_raw" in result
    assert "title_en" in result
    assert "employment_type" in result
    assert "salary_annual_min_usd" in result


# 测试四：filter_jobs 不指定条件时，是否保留全部测试记录。
def test_filter_jobs_without_conditions(sample_csv_path):
    # 先使用读取函数加载这份只有 20 行的测试文件。
    df = load_dataset(sample_csv_path)

    # 不传筛选条件，检查函数是否返回所有记录。
    result = filter_jobs(df)

    # 确认结果仍然是 DataFrame。
    assert isinstance(result, pd.DataFrame)

    # 确认没有筛选条件时，记录数量不应减少。
    assert len(result) == len(df)

    # 确认筛选结果与原数据一致，包括行和列。
    pd.testing.assert_frame_equal(result, df)


# 测试五：filter_jobs 是否能根据地点筛选岗位。
def test_filter_jobs_by_location(sample_csv_path):
    # 加载完整的测试样本；这里的完整是指测试文件中的全部 20 行。
    df = load_dataset(sample_csv_path)

    # 获取地点字段，转换为字符串并去掉首尾空格。
    locations = df["location_raw"].dropna().astype(str).str.strip()

    # 排除空字符串，避免拿空值作为筛选条件。
    locations = locations[locations != ""]

    # 如果前 20 行恰好没有有效地点，就跳过这个测试并说明原因。
    if locations.empty:
        pytest.skip("前 20 行没有有效地点，无法验证地点筛选。")

    # 选取一个真实存在于测试数据中的地点作为筛选条件。
    target_location = locations.iloc[0]

    # 调用实际筛选函数，只保留匹配该地点的岗位。
    result = filter_jobs(df, location=target_location)

    # 确认筛选结果至少包含一条记录。
    assert not result.empty

    # 确认所有返回记录的地点都包含指定关键词，忽略大小写。
    matched_locations = result["location_raw"].fillna("").astype(str)

    # 逐行验证筛选结果没有混入不符合地点条件的记录。
    assert matched_locations.str.contains(
        target_location,
        case=False,
        regex=False,
    ).all()
