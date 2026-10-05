"""Agent 构建：基于 LangChain/LangGraph 的 ReAct Agent。

架构：
  用户输入 → LLM 推理(含工具调用决策) → 工具执行 → 结果回传 LLM → 最终输出
  使用 MemorySaver 持久化会话记忆，支持多轮上下文对话。
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from config import API_KEY, BASE_URL, MAX_RETRIES, MODEL_NAME, REQUEST_TIMEOUT
from tools import ALL_TOOLS

SYSTEM_PROMPT = """你是一位专业、严谨的编程助手 CodeAgent，擅长代码审查、代码解释、代码生成与单元测试生成。

## 工作流程
1. 收到与本地代码相关的请求时，优先使用工具收集事实：
   - `list_files` 了解项目结构
   - `read_file` 读取具体文件
   - `search_code` 定位关键字/函数
   - `python_execute` 运行验证代码、执行测试
2. 基于工具返回的真实内容进行分析，不要凭空猜测文件内容。
3. 生成的代码若可验证，用 python_execute 运行确认后再交付。

## 回答要求
- 中文回答，条理清晰，关键结论加粗。
- 涉及代码时使用 Markdown 代码块并注明语言。
- 审查代码时按【问题 → 位置 → 影响 → 建议】结构输出。
- 若工具返回错误，分析原因后修正参数重试，而不是直接放弃。"""


def build_agent():
    """构建带记忆、带重试的 ReAct Agent。

    Returns:
        (agent, memory): agent 为编译后的 LangGraph 应用；
        memory 为 MemorySaver，负责跨多轮对话的会话记忆。
    """
    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0,
        max_retries=MAX_RETRIES,
        timeout=REQUEST_TIMEOUT,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("messages"),
    ])

    memory = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=prompt,
        checkpointer=memory,
    )
    return agent, memory
