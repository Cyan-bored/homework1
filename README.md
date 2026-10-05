# CodeAgent — 代码助手

一个使用 **LangChain + LangGraph** 构建的命令行代码助手 Agent，支持**代码审查、代码解释、代码生成、单元测试生成**等能力，具备工具调用、上下文记忆与错误重试机制。

## 功能特性

| 能力 | 说明 |
|------|------|
| 代码审查 | 分析代码质量、发现潜在 Bug、给出改进建议 |
| 代码解释 | 解释代码逻辑、生成注释、回答代码相关问题 |
| 代码生成 | 根据自然语言描述生成代码，并可自动运行验证 |
| 测试生成 | 根据代码自动生成单元测试并执行验证 |
| 上下文记忆 | 同一会话内多轮对话，Agent 记住之前的讨论内容 |
| 错误处理 | LLM 调用自动重试；工具出错返回友好信息供 Agent 自纠 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 LLM API

复制 `.env.example` 为 `.env`，填入你的 API Key（支持任何 OpenAI 协议兼容的服务商）：

```bash
# DeepSeek 示例
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat

# 通义千问示例
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus

# OpenAI 示例（无需 BASE_URL）
OPENAI_API_KEY=sk-xxxx
MODEL_NAME=gpt-4o-mini
```

### 3. 运行

```bash
# 交互式对话（REPL）
python main.py

# 单次提问模式
python main.py "审查 examples/user_service.py 的代码质量"
```

## 使用示例

```
================================================
   CodeAgent - 代码助手
   模型: deepseek-chat
   命令: /reset 重置会话 | /exit 退出
================================================
你: 帮我审查 examples/user_service.py 的代码质量
  [调用工具] read_file {'file_path': 'examples/user_service.py'}
  [工具结果] """演示用示例代码...
Agent: 该模块存在以下问题：
  1. **密码明文存储**（login/register）—— 安全隐患，建议使用 hashlib 加盐哈希...
  2. **delete 无权限校验** —— ...
  3. **`== True` 冗余比较**（get_count）—— ...

你: 为 register 函数生成单元测试并运行
  [调用工具] python_execute {'code': 'from examples.user_service import ...'}
  [工具结果] ......
  ----------------------------------------------------------------------
  Ran 4 tests in 0.002s
  OK
Agent: 已生成 4 个测试用例并全部运行通过，覆盖了...
```

## 项目结构

```
CodeAgent/
├── main.py                 # 命令行交互入口（REPL / 单次提问）
├── agent.py                # Agent 构建：LLM + Prompt + 工具 + 记忆
├── tools.py                # 工具集：代码执行/文件读取/目录列表/代码搜索
├── config.py               # 配置加载（.env）
├── examples/
│   └── user_service.py     # 演示用示例代码（含故意埋下的问题）
├── requirements.txt        # Python 依赖
├── README.md               # 项目说明（本文件）
├── Design.md               # 设计文档
└── .env.example            # 环境变量模板
```

## 支持的工具

| 工具 | 功能 | 安全措施 |
|------|------|----------|
| `python_execute` | 执行 Python 代码片段 | 子进程隔离、超时限制 |
| `read_file` | 读取指定文件内容 | 路径越权校验、超长截断 |
| `list_files` | 列出目录结构 | 路径越权校验 |
| `search_code` | 关键字代码搜索 | 跳过无关目录、结果数限制 |

## 常见问题

- **启动报 "未检测到 OPENAI_API_KEY"**：请先按上述步骤配置 `.env`。
- **想清空对话重新开始**：在 REPL 中输入 `/reset`。
