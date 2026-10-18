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