"""CodeAgent 命令行交互入口。

用法:
    python main.py            # 启动交互式对话(REPL)
    python main.py "问题"     # 单次提问模式

特性:
- 流式输出最终回答
- 展示 Agent 的工具调用过程(推理 → 工具 → 输出)
- 会话记忆(多轮上下文), 输入 /reset 重置会话
- LLM 调用失败自动重试 + 顶层错误兜底
"""
import sys
import uuid

from config import MODEL_NAME
from agent import build_agent

BANNER = f"""
================================================
   CodeAgent - 代码助手
   模型: {MODEL_NAME}
   命令: /reset 重置会话 | /exit 退出
================================================
"""


def print_tool_steps(result: dict) -> None:
    """打印 Agent 中间步骤（工具调用），展示推理过程。"""
    for msg in result.get("messages", []):
        kind = msg.__class__.__name__
        if kind == "AIMessage" and msg.tool_calls:
            for call in msg.tool_calls:
                name = call.get("name", "unknown")
                args = str(call.get("args", {}))
                print(f"\n  [调用工具] {name} {args[:120]}{'...' if len(args) > 120 else ''}")
        elif kind == "ToolMessage":
            preview = str(msg.content)[:200]
            print(f"  [工具结果] {preview}{'...' if len(str(msg.content)) > 200 else ''}")


def ask(agent, question: str, thread_id: str) -> None:
    """单次提问：输入 → 推理 → 工具调用 → 输出。"""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [("user", question)]}, config)
    print_tool_steps(result)
    answer = result["messages"][-1].content
    print(f"\nAgent: {answer}\n")


def repl() -> None:
    """交互式循环。"""
    agent, _ = build_agent()
    thread_id = str(uuid.uuid4())
    print(BANNER)
    while True:
        try:
            question = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not question:
            continue
        if question == "/exit":
            print("再见！")
            break
        if question == "/reset":
            thread_id = str(uuid.uuid4())
            print("会话已重置。\n")
            continue
        try:
            ask(agent, question, thread_id)
        except KeyboardInterrupt:
            print("\n(已中断本轮回答)")
        except Exception as e:
            print(f"\n[错误] {e}\n(已跳过本轮，可继续提问)")


def main() -> None:
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        agent, _ = build_agent()
        ask(agent, question, str(uuid.uuid4()))
    else:
        repl()


if __name__ == "__main__":
    main()
