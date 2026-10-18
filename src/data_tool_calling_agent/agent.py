import json


import pandas as pd

from .schemas import TOOLS
from .registry import TOOL_FUNCTIONS
from .config import client



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
