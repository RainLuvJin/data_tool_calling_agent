import os
from openai import OpenAI

# 2. 创建 LLM API 客户端
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)