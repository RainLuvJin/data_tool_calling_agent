import json
import os
from pathlib import Path
from functools import partial

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from data_tool_calling_agent.function_tools.csv_tool import (
    inspect_dataset,
    filter_jobs,
    analyze_salary,
)
# 1. 读取项目根目录的 .env 文件
# agent.py 位于 src/data_tool_calling_agent/ 下，
# parents[2] 对应项目根目录。
root = Path(__file__).resolve().parents[2]
load_dotenv(root/".env")

# 2. 创建 LLM API 客户端
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

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

# 6. 向 LLM 描述工具的用途和参数。
# 这是 JSON Schema，不是函数本身。
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_dataset",
            "description": (
                "查看岗位数据集的列名、前几行或随机样本。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["columns", "head", "random"],
                        "description": "查看方式",
                    },
                    "n": {
                        "type": "integer",
                        "description": "返回的行数，默认 5",
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_jobs",
            "description": (
                "按地点、技能、工作类型和最低年薪筛选岗位。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": ["string", "null"],
                        "description": "地点关键词，例如 Tokyo",
                    },
                    "skill": {
                        "type": ["string", "null"],
                        "description": "技能关键词，例如 Python",
                    },
                    "employment_type": {
                        "type": ["string", "null"],
                        "description": "工作类型关键词",
                    },
                    "min_salary_usd": {
                        "type": ["number", "null"],
                        "description": "最低年薪下限，美元",
                    },
                },
                "required": [
                    "location",
                    "skill",
                    "employment_type",
                    "min_salary_usd",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_salary",
            "description": (
                "统计年薪的有效记录数、平均值、中位数、"
                "最低值和最高值，可按字段分组。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": ["string", "null"],
                        "description": (
                            "分组字段，例如 employment_type；"
                            "不分组时传 null"
                        ),
                    },
                },
                "required": ["group_by"],
                "additionalProperties": False,
            },
        },
    },
]


# 7. 将 pandas 数据中的缺失值转换为 JSON null，
# 保证结果能作为标准 JSON 字符串交给模型。
def to_json(data):
    if isinstance(data, pd.DataFrame):
        data = data.astype(object).where(
            pd.notna(data), None
        ).to_dict(orient="records")

    return json.dumps(
        data,
        ensure_ascii=False,
        default=str,
        allow_nan=False,
    )


# 8. Agent 主入口：接收用户的自然语言问题。
def ask_agent(question):
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个岗位数据分析助手。"
                "根据用户问题选择合适的工具。"
                "不要编造工具没有返回的数据。"
                "如果用户的问题不需要查询数据，可以直接回答。"
            ),
        },
        {"role": "user", "content": question},
    ]

    # 最多执行 5 轮模型请求，避免工具调用无限循环。
    for _ in range(20):
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # 保存模型消息，以便后续把工具结果交还给模型。
        messages.append(message)

        # 如果模型没有请求工具，说明它已生成最终回答。
        if not message.tool_calls:
            return message.content or "模型没有返回文本。"

        # 9. 执行模型请求的工具。
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"\n[Tool Call] {name}")
            print(f"[Arguments] {arguments}")

            # 不允许模型调用未注册的函数。
            if name not in TOOL_FUNCTIONS:
                result = {"error": f"Unknown tool: {name}"}
            else:
                try:
                    # 由 Python 真正执行函数。
                    output = TOOL_FUNCTIONS[name](**arguments)
                    result = {"result": output}
                except (ValueError, TypeError, KeyError) as exc:
                    result = {"error": str(exc)}

            # 把工具执行结果添加到对话历史。
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": to_json(result),
                }
            )

    return "工具调用轮数达到上限，请缩小问题范围后重试。"


# 10. 直接运行本文件时，进入命令行对话。
if __name__ == "__main__":
    while True:
        question = input("\n你想查询什么？输入 quit 退出：")

        if question.strip().lower() in {"quit", "exit"}:
            break

        try:
            print("\nAgent：")
            print(ask_agent(question))
        except Exception as exc:
            print(f"运行失败：{type(exc).__name__}: {exc}")
