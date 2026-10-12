# CLAUDE.md

此文件为 Claude Code（claude.ai/code）在此仓库中工作时提供指导。

## 项目概览

AI 智能客服 SaaS 平台。企业上传知识库文档 → RAG 检索 → LLM 生成回答 → 对话历史 + 数据分析。

前后端分离，两个独立服务：

| 服务 | 技术栈 | 端口 | 目录 |
|------|--------|------|------|
| 后端 | Python FastAPI + SQLAlchemy + SQLite | 8001 | `backend/` |
| 前端 | React + TypeScript + Vite + Tailwind | 5173 | `frontend/` |

前端通过 REST JSON API 与后端通信。Vite 开发服务器将 `/api/*` 代理到 `localhost:8001`（见 `frontend/vite.config.ts`）。

## 启动方式

```bash
# 终端 1 — 后端
cd ai-customer-service
venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# 终端 2 — 前端
cd ai-customer-service/frontend
npm run dev
```

后端 API 文档：`http://localhost:8001/docs` | 前端：`http://localhost:5173`

配置文件为 `.env`（从 `.env.example` 复制）。需要填两个 API Key：`DEEPSEEK_API_KEY`（对话）和 `SILICONFLOW_API_KEY`（向量化，免费）。

## 架构

### 后端模块调用链

```
main.py（路由注册中心）
  ├── auth.py          — JWT 认证（hashlib 标准库 PBKDF2，没引入 passlib）
  ├── upload.py        — 文件上传 → 解析 TXT/PDF/DOCX → 入库 → 触发向量化
  ├── embedding.py     — 文本分块（500字 + 50重叠）→ 调 SiliconFlow API 向量化
  ├── vector_store.py  — NumPy 余弦相似度检索，查 chunk_vectors 表
  ├── rag.py           — 查询 → 向量化 → 向量搜索 → 返回 Top-K 片段
  └── agent.py         — 对话管理 → RAG 检索 → 拼 Prompt → 调 DeepSeek → 提取置信度
```

每个模块有自己的 FastAPI router，在 `main.py` 中统一注册。所有模块共用 `models.py` 中的同一个 SQLite 引擎。

### 核心数据流（RAG 管道）

```
上传：  文件 → 解析纯文本 → 存入 documents 表
             → 分块（500/50）→ get_embedding（SiliconFlow）
             → 分块+向量存入 chunk_vectors 表

对话：  用户消息 → 存入 messages 表
        → get_embedding(问题) → vector_store.search（余弦相似度, top_k=3, 最低分 0.3）
        → _build_prompt（知识片段 + 对话历史 + 企业语气设定）
        → _call_llm（DeepSeek V4 Flash，OpenAI 兼容协议）
        → _parse_response（从回复末行提取置信度 JSON）
        → 保存 AI 回复 + 引用来源
```

### 数据库

单个 SQLite 文件：`data/customer_service.db`（首次启动自动创建）。共 5 张表，两条外键链：

- `companies → documents → chunk_vectors`
- `companies → conversations → messages`

向量以 JSON 数组形式存在 `chunk_vectors.embedding` 字段（1024 维浮点数组）。没有外部向量数据库——NumPy 直接做余弦相似度运算。

### 前端

React Router + 路由守卫（`Protected` 组件，未登录重定向到 `/`）。JWT 存在 `localStorage`（刷新页面不掉登录态）。API 客户端是单例类，在 `frontend/src/api/client.ts`。

页面：`LoginPage`（登录/注册双 Tab）→ `DashboardPage`（文档上传/列表/删除）→ `ChatPage`（左侧对话列表 + 右侧对话框）→ `AnalyticsPage`（统计数据 + 文档类型分布）。

## Windows 常见问题

- **数据库被锁**：删 `data/` 前先用 `taskkill /F /IM python.exe` 杀掉残留 Python 进程
- **端口被占用**：改 `.env` 里的 `API_PORT`，同时改 `vite.config.ts` 里的 proxy 目标端口
- **PDF 上传崩溃 `UnicodeEncodeError: surrogates not allowed`**：`upload.py` 中的 `_sanitize_text()` 已修复此问题——所有解析函数都经过它清洗
- **pip install 报 C++ 编译器缺失**：只能用有预编译 wheel 的包。ChromaDB 和 scikit-learn 因此被砍掉，改用 NumPy 自建检索 + hashlib 标准库做密码哈希

## 技术栈限制

- Python 3.13——包必须有 `cp313` 预编译 wheel。`openai` SDK 同时对接 DeepSeek（改 base_url）和 SiliconFlow
- `streamlit` 不再使用——前端已迁移到 React。旧的 `pages/` 和 `app.py` 已删除
- 暂无测试
