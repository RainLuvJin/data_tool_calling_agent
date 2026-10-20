from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from uuid import uuid4


from .agent import ask_agent

app = FastAPI()
class InputQuestion(BaseModel):
    username : str
    datetime : date
    question : str

sessions = {}

@app.post("/sessions")
def create_session():
    session_id = str(uuid4())
    return {"session_id":session_id, "status":"created!"}

@app.post("/sessions/{session_id}/messages")
# 原来写成了InputQuestion.question 但是InputQuestion是类，input才是类的实例对象，类有字段 写的那些叫字段声明 实例才有声明的那些字段属性
def ask_question(session_id: str, input: InputQuestion):
    msg, all_used_tools = ask_agent(input.question)
    sessions[session_id] = {"message":msg}
    return {"session_id":session_id, "answer": msg,"tool_used":all_used_tools,"status":"success"}

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