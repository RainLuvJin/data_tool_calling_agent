from .agent import ask_agent

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