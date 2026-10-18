from functools import partial
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from ..data_tool_calling_agent.function_tools.csv_tool import (
    inspect_dataset,
    filter_jobs,
    analyze_salary,
    )

# 1. 读取项目根目录的 .env 文件
# agent.py 位于 src/data_tool_calling_agent/ 下，
# parents[2] 对应项目根目录。
root = Path(__file__).resolve().parents[2]
load_dotenv(root/".env")

# 3. 指定data_csv文件路径
data_path = root/"data"/"jobs.csv"

# 4. 程序启动时读取完整数据集
df = pd.read_csv(data_path,encoding="utf-8")

# 5. 工具注册表：Python 函数名 -> 实际执行函数
TOOL_FUNCTIONS = {
    "inspect_dataset": partial(inspect_dataset,df),
    "filter_jobs": partial(filter_jobs,df),
    "analyze_salary": partial(analyze_salary,df),
}