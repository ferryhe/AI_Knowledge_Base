# Agentic Search 深度研究报告

> 研究日期：2026-03-25
> 研究人：@ferryhe

---

## 1. 什么是 Agentic Search

### 1.1 核心定义

**Agentic Search**（又称 Agentic Deep Research、Agentic RAG）是信息检索的一次范式跃迁。它将 LLM 作为**自主 Agent** 嵌入检索流程，赋予搜索系统"计划 → 检索 → 反思 → 再检索"的迭代推理能力，而非一次性地返回一批链接或片段。

与传统搜索和 RAG 的最大区别在于：Agentic Search 是**目标导向**（goal-oriented）的，它像一个真实研究员一样拆解任务、自主调用工具、反复验证结果，最终交付完整、可溯源的研究报告或决策建议。

### 1.2 演进路径

```
关键词搜索
  │   BM25 / Elasticsearch 单次检索，返回结果列表
  ▼
RAG（检索增强生成）
  │   向量检索 Top-K → 喂给 LLM → 一次性生成答案
  ▼
Agentic Search / Agentic RAG（2024-2025 主流）
  │   Agent 拆解任务 → 多轮检索 → 工具调用 → 反思 → 合成报告
  ▼
Multi-Agent Deep Research（前沿）
      多个子 Agent 并行探索 → Supervisor 综合 → 结构化输出
```

---

## 2. 三大检索范式对比

| 维度 | 传统搜索 | 静态 RAG | **Agentic Search** |
|------|---------|---------|-------------------|
| 架构核心 | 倒排索引 / 向量数据库 | 检索模块 + LLM | Agent 编排器 + 检索工具集 |
| 查询规划 | 无 | 无（一次检索） | **多步分解**，自动生成子查询 |
| 迭代检索 | 否 | 否 | **是**（计划→检索→反思→再检索） |
| 工具调用 | 否 | 否 | **是**（搜索、代码执行、API 调用等） |
| 记忆/状态 | 无状态 | 无状态 | **有状态**，跨步骤保持上下文 |
| 多源融合 | 否 | 有限 | **是**，动态选择并融合多个数据源 |
| 失败处理 | 无 | 返回空或幻觉 | **自动重试**，切换策略 |
| 输出形式 | 链接列表 | 单段回答 | **结构化报告**，含引用和推理链 |
| 复杂度 | 低 | 中 | 高 |
| 适用场景 | 精确词汇查找 | 简单问答 | **多步推理、决策支持、深度研究** |

---

## 3. 核心技术架构

### 3.1 标准 Agentic Search 流水线

```
用户目标（Goal）
     │
     ▼
┌─────────────────────────────────────────┐
│           规划器（Planner）              │
│  将目标拆解为子任务列表                   │
│  e.g. ["收集监管文件","分析定价模型",...]  │
└─────────────────┬───────────────────────┘
                  │ 子任务
                  ▼
┌─────────────────────────────────────────┐
│          执行器（Executor）              │
│  循环执行：选择工具 → 调用 → 获取结果     │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Web搜索  │ │  向量库  │ │ API调用 │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────┬───────────────────────┘
                  │ 原始结果
                  ▼
┌─────────────────────────────────────────┐
│          反思器（Reflector）             │
│  评估结果是否充分 → 是否需要追加检索      │
│  更新内部记忆（Memory）                  │
└─────────────────┬───────────────────────┘
                  │ 充分 / 不充分
          ┌───────┴───────┐
          │               │
       不充分            充分
          │               │
    回到规划器          ▼
                 ┌─────────────┐
                 │  合成器      │
                 │ 生成最终报告 │
                 └─────────────┘
```

### 3.2 关键组件

| 组件 | 职责 | 技术实现 |
|------|------|---------|
| **规划器** | 拆解复杂查询为子任务 | LLM + ReAct / CoT Prompting |
| **工具集** | 执行各类检索和操作 | 搜索 API、向量数据库、代码执行器 |
| **记忆** | 跨步骤保持上下文 | 短期（工作记忆）+ 长期（向量存储） |
| **反思器** | 评估结果充分性 | LLM 自评分 / 验证 Agent |
| **合成器** | 整合多源信息生成报告 | LLM + 引用追踪 |
| **编排器** | 协调各组件的执行顺序 | LangGraph / LlamaIndex Workflow |

---

## 4. 主流开源框架深度分析

### 4.1 LangGraph

- **定位**：通用 Agent 工作流编排框架，将工作流建模为**有向状态图**
- **核心机制**：每个节点是一个函数，边是基于状态的转换条件；支持循环、分支、并行
- **适用**：构建定制化 Agentic Search 工作流，灵活性最高
- **优缺点**：控制粒度细（优），学习曲线较陡（缺）

```python
# LangGraph 典型 Agentic Search 工作流
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("planner", plan_task)
graph.add_node("search", execute_search)
graph.add_node("reflect", reflect_on_results)
graph.add_node("synthesize", generate_report)

graph.add_conditional_edges("reflect", should_continue, {
    "continue": "search",  # 不充分 → 继续检索
    "done": "synthesize"   # 充分 → 合成报告
})
```

### 4.2 Open Deep Research（LangChain-AI）

- **定位**：生产级深度研究 Agent，基于 LangGraph 构建
- **架构**：Supervisor + 多个并行研究 Agent → 结构化报告输出
- **流程**：Scope（澄清需求）→ Research（并行多 Agent 探索）→ Write（综合报告）
- **特点**：支持 MCP 工具集成、多 LLM 后端（OpenAI/Anthropic/Gemini）
- **适用**：直接部署使用，或作为参考实现

### 4.3 DeerFlow（ByteDance 开源）

- **定位**：模块化多 Agent 深度研究框架
- **架构**：任务规划器 + 搜索 Agent + 代码执行 Agent + 写作 Agent，共用 LangGraph 图
- **特点**：Docker 沙盒、持久记忆、人工审核节点、多模态输出（文本/代码/PPT）
- **适用**：需要代码执行能力的复杂研究场景

### 4.4 LlamaIndex（Agentic RAG）

- **定位**：文档检索与 Agent 推理集成框架
- **架构**：事件驱动工作流 + 分层 Agent（Meta-Agent → Sub-Agents → 文档检索器）
- **特点**：Python 和 TypeScript 双语支持，原生对接向量数据库生态
- **适用**：知识库问答，文档密集型 RAG 场景

### 4.5 框架对比

| 框架 | 编排机制 | 多 Agent | 内存 | 适合场景 | 语言 |
|------|---------|---------|------|---------|------|
| LangGraph | 状态图 | ✅ | ✅ | 定制化复杂工作流 | Python/JS |
| Open Deep Research | LangGraph | ✅ | ✅ | 开箱即用的深度研究 | Python |
| DeerFlow | LangGraph+沙盒 | ✅ | ✅ | 含代码执行的研究 | Python |
| LlamaIndex | 事件工作流 | ✅ | ✅ | 文档密集型知识库 | Python/JS |

---

## 5. 行业产品全景

| 产品 | 公司 | 特点 |
|------|------|------|
| Deep Research | OpenAI | o1/o3 驱动，自主浏览 + 综合报告 |
| Gemini Deep Research | Google | 多步搜索规划，适合学术/商业研究 |
| Perplexity Deep Research | Perplexity | 实时搜索 + 报告生成，用户友好 |
| Copilot Researcher | Microsoft | 企业文档 + 网页搜索融合 |
| Grok Deep Search | xAI | X（Twitter）数据 + 网页搜索 |
| Claude Research | Anthropic | 长上下文 + 多工具调用 |
| DeerFlow | ByteDance | 开源，多 Agent，沙盒执行 |
| Open Deep Research | LangChain | 开源，LangGraph，可自部署 |

---

## 6. 在 ferryhe 整体项目中的角色评估

### 6.1 项目生态全图

```
ferryhe 项目生态
├── AI / 搜索核心层
│   ├── AI_Knowledge_Base    精算 AI 知识库 + RAG 问答 (FAISS + OpenAI)
│   ├── iaa_aitf_agent       IAA-AITF 公开 repo RAG Agent
│   └── web_crawler          GitHub 项目研究报告仓库
│
├── 数据采集层
│   ├── web_listening        网站变动监控 + AI 摘要
│   └── doc_to_md            文档格式转换（PDF/DOCX → MD）
│
├── 领域工具层
│   ├── actuarial_modelling  精算建模（Python）
│   ├── bias_mitigation_insurance_pricing  保险定价偏差分析
│   ├── marathon_calendar    马拉松赛事日历爬虫（TypeScript）
│   ├── football_tracking    足球追踪（Python）
│   ├── meal_score           餐饮评分（TypeScript）
│   └── animal_talk          (TypeScript)
│
└── 研究文档层
    └── research             研究报告仓库（当前所在位置）
```

### 6.2 各项目受益分析

#### 🔴 高度相关（Agentic Search 能显著提升）

**AI_Knowledge_Base**
- **现状**：FAISS 向量索引 + OpenAI Embeddings → 单次 top-k 检索 → 生成回答
- **痛点**：复杂精算问题需要跨多个文档推理；单次检索的召回率和精度有限
- **Agentic Search 升级方案**：
  - 将 `ask.py` 升级为 Agentic RAG 工作流
  - Agent 自动分解"IFRS17 下的准备金计算需要考虑哪些因素"为多个子查询
  - 迭代检索精算准则、监管文件、案例研究，再合成完整回答
  - 效果：回答质量和完整性显著提升，尤其是跨文档推理

**iaa_aitf_agent**
- **现状**：同样是 FAISS RAG，一次检索回答问题
- **痛点**：IAA-AITF 的 repo 内容分散在多个仓库，单次检索难以跨仓库综合
- **Agentic Search 升级方案**：
  - 多 Agent 并行搜索不同 repo
  - Supervisor Agent 综合来自不同 repo 的结果
  - 支持"给我比较不同国家精算准则"这类需要多源综合的问题

**web_crawler**（研究报告仓库）
- **现状**：Copilot Agent 手动研究，写 Markdown 报告
- **Agentic Search 的作用**：
  - 作为 Copilot Agent 的底层能力，自动化研究工作流
  - 自主浏览 GitHub 仓库 + 网页 + 学术论文，生成初稿
  - 配合已有的 `skills/` 和 `templates/` 结构

#### 🟡 中度相关（Agentic Search 可增强）

**web_listening**
- **现状**：网站变动监控 + AI 摘要（OpenAI GPT-4o-mini）
- **升级点**：当监控到监管文件更新时，触发 Agentic Search 自动深度分析该文件与现有知识库的差异，输出影响评估报告

**actuarial_modelling / bias_mitigation_insurance_pricing**
- **升级点**：在建模过程中接入 Agentic Search，自动检索相关精算假设、监管要求，辅助决策

#### 🟢 低相关（暂不适用）

**marathon_calendar、football_tracking、meal_score、animal_talk**
- 功能性/娱乐性工具，业务逻辑明确，暂不需要 Agentic Search

### 6.3 核心价值定位

Agentic Search 在整个项目生态中的最优定位是：

```
┌─────────────────────────────────────────────────────────┐
│                 Agentic Search 能力层                    │
│                                                         │
│   "对复杂问题进行自主、多步、可溯源的信息检索与综合"         │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ AI知识库     │   │ IAA-AITF     │   │ web_crawler│  │
│  │ 精算问答升级  │   │ Agent升级    │   │ 研究自动化  │  │
│  └──────────────┘   └──────────────┘   └────────────┘  │
│                                                         │
│              数据来源（工具集）                           │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────────┐  │
│  │web搜索  │ │FAISS库 │ │GitHub  │ │web_listening监控│  │
│  └────────┘ └────────┘ └────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 是否需要单独建立 Agentic Search Repo？

### 7.1 结论：**建议纳入现有 repo，不单独建立**

### 7.2 理由分析

| 考虑因素 | 结论 |
|---------|------|
| **代码归属** | Agentic Search 能力服务于多个项目，最自然的归宿是作为可共享组件 |
| **维护成本** | 单独 repo 需额外维护 README/CI/Issues，收益不明显 |
| **已有容器** | `AI_Knowledge_Base` 的 `AI_Agent/` 目录天然是 Agentic Search 的演化方向 |
| **研究文档** | `web_crawler` 和 `research` 已承担研究文档职责 |
| **适当规模** | 目前项目规模，单独 repo 会导致碎片化 |

### 7.3 推荐整合方案

```
建议的整合路径：

现在（探索阶段）
  └── research/         ← 研究报告放在这里（当前文件）

短期（实验阶段，1-2周）
  └── AI_Knowledge_Base/AI_Agent/
        ├── scripts/
        │   ├── ask.py              ← 升级为 Agentic RAG 工作流
        │   └── agentic_search.py   ← 新增 Agentic Search 核心模块
        └── AGENTIC_SEARCH.md       ← 设计文档

中期（成熟后可考虑提取）
  └── 若 Agentic Search 逻辑超过 ~500 行且被 3 个以上项目引用
        → 再考虑提取为独立 repo 或 Python package
```

**例外情况**：如果计划将 Agentic Search 能力**开放给外部用户**或构建**独立 SaaS 产品**，则单独建 repo 是合理的。

---

## 8. 具体实施路径

### 8.1 最小可行升级（2-3天）：升级 AI_Knowledge_Base

将现有 FAISS + OpenAI 的单次 RAG 升级为 Agentic RAG：

```python
# AI_Knowledge_Base/AI_Agent/scripts/agentic_ask.py
"""
基于 LangGraph 的 Agentic RAG 工作流
将原 ask.py 的"检索→回答"升级为"规划→迭代检索→合成"
"""
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, List


class ResearchState(TypedDict):
    question: str
    sub_queries: List[str]        # 拆解的子查询
    retrieved_chunks: List[dict]  # 累积检索到的片段
    iteration: int                # 已迭代次数
    answer: str                   # 最终回答


def plan(state: ResearchState) -> ResearchState:
    """将复杂问题拆解为子查询"""
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = f"""将以下问题拆解为2-4个可独立检索的子查询（JSON列表格式）：
问题：{state['question']}"""
    # ... 调用 LLM 生成子查询列表
    return state


def retrieve(state: ResearchState) -> ResearchState:
    """对每个子查询执行 FAISS 检索"""
    # 使用现有的 FAISS index
    # ... 检索逻辑
    return state


def reflect(state: ResearchState) -> str:
    """判断检索结果是否充分"""
    if state["iteration"] >= 3:
        return "synthesize"
    # ... LLM 评估是否需要继续检索
    return "retrieve"  # 或 "synthesize"


def synthesize(state: ResearchState) -> ResearchState:
    """基于所有检索结果生成最终回答"""
    # ... 综合生成
    return state


# 构建图
graph = StateGraph(ResearchState)
graph.add_node("plan", plan)
graph.add_node("retrieve", retrieve)
graph.add_node("reflect", reflect)
graph.add_node("synthesize", synthesize)

graph.set_entry_point("plan")
graph.add_edge("plan", "retrieve")
graph.add_conditional_edges("reflect", reflect, {
    "retrieve": "retrieve",
    "synthesize": "synthesize"
})
graph.add_edge("synthesize", END)
```

### 8.2 中期方案（1-2周）：接入 DeerFlow 或 Open Deep Research

直接使用 ByteDance DeerFlow 或 LangChain Open Deep Research 作为研究引擎，为 web_crawler 的研究工作流提供自动化能力：

```bash
# 部署 DeerFlow 作为本地研究服务
git clone https://github.com/bytedance/deer-flow
cd deer-flow
docker-compose up -d

# 使用其 API 自动生成研究报告
curl -X POST http://localhost:8000/research \
  -d '{"topic": "QMD hybrid search engine analysis", "output_format": "markdown"}'
```

### 8.3 工具选型建议

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 精算知识库问答升级 | LlamaIndex Agentic RAG | 文档密集，原生 FAISS 集成 |
| 自动生成研究报告 | Open Deep Research / DeerFlow | 开箱即用，多 Agent 并行 |
| 定制化业务工作流 | LangGraph | 控制粒度最细 |
| 快速原型验证 | Perplexity / OpenAI Deep Research API | 无需自建，API 直接调用 |

---

## 9. 关键参考资源

| 资源 | 地址 | 说明 |
|------|------|------|
| Awesome Deep Research | [GitHub](https://github.com/DavidZWZ/Awesome-Deep-Research) | 论文/框架/产品汇总 |
| Open Deep Research | [GitHub](https://github.com/langchain-ai/open_deep_research) | LangChain 官方实现 |
| DeerFlow | [GitHub](https://github.com/bytedance/deer-flow) | ByteDance 开源框架 |
| LangGraph 教程 | [Docs](https://langchain-ai.github.io/langgraph/) | 官方文档 |
| LlamaIndex Agentic RAG | [Blog](https://www.llamaindex.ai/blog/agentic-rag-with-llamaindex-2721b8a49ff6) | 设计指南 |
| arXiv: Agentic RAG Survey | [2501.09136](https://arxiv.org/abs/2501.09136) | 学术综述 |
| Google 76页 Agent 白皮书 | [marktechpost](https://www.marktechpost.com/2025/05/06/google-releases-76-page-whitepaper-on-ai-agents-a-deep-technical-dive-into-agentic-rag-evaluation-frameworks-and-real-world-architectures/) | 工程实践深度 |

---

## 10. 结论与行动计划

### 10.1 核心结论

1. **Agentic Search 是 RAG 的正确演进方向**：对于 ferryhe 的精算/AI 知识库场景，它能显著提升多步骤、跨文档推理问题的回答质量
2. **不需要单独建 repo**：现有 `AI_Knowledge_Base` 的 `AI_Agent/` 是最自然的落地位置；研究文档归入 `web_crawler` 或 `research`
3. **最高优先级**：升级 `AI_Knowledge_Base` 的 RAG 为 Agentic RAG，这是影响最大、实施最直接的改进
4. **可复用组件**：Agentic Search 的工具调用层（搜索、FAISS 检索、GitHub API）可以在 `AI_Knowledge_Base` 和 `iaa_aitf_agent` 之间共享

### 10.2 后续行动计划

- [ ] **立即（本周）**：在 `AI_Knowledge_Base/AI_Agent/` 中安装 LangGraph，写 `agentic_ask.py` 原型，用 3-5 个精算问题测试多步检索效果
- [ ] **短期（1-2周）**：在 `web_crawler` 的 Copilot 研究流程中接入 DeerFlow 或 Open Deep Research，自动化生成初稿
- [ ] **中期（1个月）**：评估 `iaa_aitf_agent` 的 Agentic RAG 升级；将 Agentic Search 工具模块提取为 `AI_Knowledge_Base/AI_Agent/tools/agentic_search.py` 供多项目共享
- [ ] **长期评估**：如 Agentic Search 逻辑超过 500 行且 3 个以上项目引用，再考虑提取为独立 repo

---

*报告日期：2026-03-25*
