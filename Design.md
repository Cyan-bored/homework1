# Design.md — CodeAgent 设计文档

## 1. 项目目标

搭建一个简单的代码助手 Agent，覆盖作业要求的五类方向中的核心能力：**代码审查、代码解释、代码生成、测试生成**，并掌握 LLM 调用、Prompt 设计、工具集成、上下文记忆、错误处理等 Agent 开发基础能力。

## 2. 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 语言 | Python 3.10+ | LangChain 生态最成熟 |
| Agent 框架 | LangChain + LangGraph | 官方推荐的现代 Agent 构建方式，`create_react_agent` 提供 ReAct 循环 |
| LLM 接入 | `langchain-openai`（ChatOpenAI） | 兼容 OpenAI 协议，可无缝切换 DeepSeek / 通义千问 / OpenAI 等 |
| 记忆 | LangGraph `MemorySaver` | 基于 checkpointer 的会话级记忆，自动持久化全部消息（含工具调用） |
| 交互 | Python CLI（标准库） | 零额外依赖，跨平台 |

## 3. 架构设计

```
┌────────────┐
│  用户输入   │  python main.py / REPL
└─────┬──────┘
      ▼
┌─────────────────────────────────────────────┐
│              ReAct Agent (LangGraph)         │
│                                             │
│   System Prompt (角色+工作流程+输出规范)      │
│        │                                    │
│        ▼                                    │
│   ┌──────────┐    tool_calls    ┌───────┐   │
│   │   LLM    │ ───────────────▶│ 工具集 │   │
│   │  (推理)  │◀──────────────── └───┬───┘   │
│   └────┬─────┘    ToolMessage      │       │
│        │  循环直至无需调用工具        │       │
└────────┼────────────────────────────┼───────┘
         ▼                            ▼
   最终回答输出                工具执行(沙箱/受限路径)
         ▲
         │ MemorySaver 检查点(会话记忆)
```

### 3.1 Agent 循环（输入 → 推理 → 工具调用 → 输出）

采用 **ReAct 模式**（LangGraph `create_react_agent`）：

1. 用户输入进入 `messages`；
2. LLM 结合 System Prompt 与历史消息推理，决定直接回答或发起 `tool_calls`；
3. LangGraph 执行对应工具，将结果作为 `ToolMessage` 回传；
4. LLM 根据工具结果继续推理，循环直到产出最终回答；
5. 全部状态由 `MemorySaver` 按会话持久化，实现多轮上下文记忆。

### 3.2 工具集设计

| 工具 | 实现 | 安全/健壮性设计 |
|------|------|----------------|
| `python_execute` | `subprocess` 独立进程执行 `python -c` | 超时上限、捕获 stderr 返回给 Agent 自纠 |
| `read_file` | 读取文本文件 | 工作区路径白名单（防路径穿越）、超长截断 |
| `list_files` | 目录遍历 | 同上路径校验 |
| `search_code` | 递归 glob + 逐行匹配 | 跳过 `.git/__pycache__` 等、结果上限 50 条 |

**关键设计：错误信息返回给 Agent 而非直接抛异常**。例如执行 `1/0` 时返回带 traceback 的文本，Agent 读到后能分析原因并修正代码重试——这本身就是 Agent 循环自纠错能力的体现。

### 3.3 Prompt 设计（tools.py 之上的 agent.py）

System Prompt 定义了三部分：
- **角色定位**：专业编程助手，明确四类任务方向；
- **工作流程**：先收集事实（工具）再分析，禁止臆造文件内容；生成代码需用 `python_execute` 验证后再交付；
- **输出规范**：中文、结构化（审查按【问题→位置→影响→建议】）、代码块标注语言。

### 3.4 记忆机制

- `MemorySaver` 以 `thread_id` 为键保存 graph state（全部对话 + 工具调用消息）；
- CLI 每个会话生成一个 `thread_id`，`/reset` 换新 id 即清空记忆；
- 因此用户可以说"刚才那个函数再补个测试"，Agent 能结合上文理解指代。

### 3.5 错误处理与重试

| 层级 | 机制 |
|------|------|
| LLM 调用 | `ChatOpenAI(max_retries=3)` 自动重试网络/限流错误 |
| 工具执行 | 全部 try/except，返回结构化错误文本供 Agent 自纠 |
| CLI 顶层 | 单轮提问异常被捕获，不终止程序，可继续提问 |

## 4. 模块划分

```
config.py   → 配置层：.env 加载、参数集中管理
tools.py    → 能力层：4 个 @tool 工具 + 路径安全
agent.py    → 编排层：LLM + Prompt + 工具 + 记忆 组装成 Agent
main.py     → 交互层：REPL / 单次提问、工具调用过程可视化
```

依赖方向：`main.py → agent.py → tools.py → config.py`，单向无环，职责单一。

## 5. 边界情况考虑

- 未配置 API Key：启动时给出明确指引并退出；
- 工具访问工作区外路径：直接拒绝并说明；
- 代码死循环/长任务：执行超时上限保护；
- 超大文件/海量搜索结果：截断保护，避免上下文爆炸；
- 用户 Ctrl+C：不崩溃，中断当前轮次后可继续。

## 6. 可扩展方向

- 增加 `write_file` 工具支持代码修改落地；
- 将 MemorySaver 换成 `SqliteSaver` 实现跨会话持久记忆；
- 用 FastAPI 包一层 Web UI（架构上交互层与 Agent 层已解耦，直接复用 `build_agent()`）。
