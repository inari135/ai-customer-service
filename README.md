# 🤖 AI 智能客服平台

一个企业级 AI 客服 SaaS 系统。企业上传知识库文档后，AI 基于文档内容回答客户问题，支持多轮对话、对话历史管理和数据分析。

**技术栈：** FastAPI + React + TypeScript + SQLite + NumPy 向量检索 + DeepSeek + SiliconFlow

## ✨ 功能特性

- 🏢 **多租户 SaaS** — 企业独立注册，所有数据按 `company_id` 隔离
- 📄 **知识库管理** — 上传 TXT/PDF/Word 文档，自动解析、分块、向量化
- 🔍 **RAG 智能问答** — 检索增强生成，回答带置信度评估，低置信度建议转人工
- 💬 **多轮对话** — 完整会话管理，支持历史对话切换与加载
- 📊 **数据分析** — 知识库规模、文档类型分布、健康度 Dashboard
- 🔐 **安全认证** — JWT + PBKDF2 密码哈希，前后端完全分离

## 🏗️ 技术架构

```
┌──────────────────────────────────────────────────────────┐
│                 前端（React + TypeScript）                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ 登录/注册 │  │ 知识库管理│  │ 客服对话  │  ┌──────────┐ │
│  │          │  │ 文档上传  │  │ 历史侧栏  │  │ 数据分析  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│       │             │             │             │         │
│       └─────────────┴──────┬──────┴─────────────┘         │
│                            │ HTTP (JSON REST API)          │
│                   Vite Proxy → localhost:8001              │
└────────────────────────────┼──────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────┐
│              后端（FastAPI REST API）                       │
│                            ▼                                │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐    │
│  │  auth   │  │  upload  │  │   rag    │  │  agent  │    │
│  │ JWT 认证 │  │ 文档解析  │  │ 检索知识  │  │ AI 对话  │    │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬────┘    │
│       │            │             │             │           │
│       └────────────┴──────┬──────┴─────────────┘           │
│                           │                                 │
│              ┌────────────┴────────────┐                    │
│              ▼                         ▼                    │
│     ┌──────────────┐     ┌─────────────────────┐           │
│     │   SQLite     │     │    NumPy 向量引擎    │           │
│     │ (所有业务数据) │     │ (余弦相似度 + JSON向量)│          │
│     └──────────────┘     └─────────────────────┘           │
└────────────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ DeepSeek │ │SiliconFlow│ │  PyPDF2  │
   │ (对话生成) │ │(文本向量化)│ │ python-  │
   │ V4-Flash │ │ BGE-Large │ │  docx    │
   └──────────┘ └──────────┘ └──────────┘
```

**核心 RAG 管道：**

```
上传：文件 → 解析纯文本 → 分块(500字+50重叠) → Embedding API → 向量入库
对话：问题 → 向量化 → 余弦相似度检索(Top-3) → 拼 Prompt → LLM 生成 → 置信度评估
```

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+

### 1. 安装依赖

```bash
# Python 后端
python -m venv venv
venv\Scripts\activate        # Windows（Mac/Linux: source venv/bin/activate）
pip install -r requirements.txt

# Node.js 前端
cd frontend
npm install
cd ..
```

### 2. 配置 API Key

> ⚠️ 出于安全考虑，仓库中**不包含** `.env` 文件（已在 `.gitignore` 中忽略）。首次使用需从模板自行创建：

```bash
copy .env.example .env       # Mac/Linux: cp .env.example .env
```

编辑 `.env`，填入你的 Key：

```env
# LLM 对话（https://platform.deepseek.com → API Keys）
DEEPSEEK_API_KEY=sk-你的key
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash

# Embedding 向量化（https://cloud.siliconflow.cn → API 密钥，免费）
SILICONFLOW_API_KEY=sk-你的key
EMBEDDING_PROVIDER=siliconflow
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# 服务端口
API_PORT=8001
```

### 3. 启动（两个终端）

```bash
# 终端 1 — 后端（http://localhost:8001/docs 可看 API 文档）
venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# 终端 2 — 前端（http://localhost:5173）
cd frontend
npm run dev
```

### 4. 使用

1. 打开 `http://localhost:5173`，注册企业账号
2. 管理后台上传知识库文档（TXT/PDF/Word）
3. 进入客服对话，开始提问——AI 基于你的文档回答

## 📁 项目结构

```
ai-customer-service/
├── frontend/                  ← React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── api/client.ts      HTTP 客户端 + JWT localStorage 持久化
│       ├── components/        Layout（导航 + 路由守卫）
│       └── pages/             Login / Dashboard / Chat / Analytics
├── backend/                   ← FastAPI REST API
│   ├── main.py                路由注册 + 生命周期
│   ├── config.py              配置管理（.env）
│   ├── models.py              5 张 SQLAlchemy 数据模型
│   ├── schemas.py             Pydantic 请求/响应校验
│   ├── auth.py                JWT 认证 + PBKDF2 密码哈希
│   ├── upload.py              文档上传 + PDF/Word/TXT 解析
│   ├── embedding.py           文本分块 + Embedding API
│   ├── vector_store.py        NumPy 余弦相似度检索引擎
│   ├── rag.py                 RAG 检索接口
│   └── agent.py               AI 对话编排 + 置信度解析
├── tests/                     pytest 测试
├── alembic/                   数据库迁移
├── data/                      运行时自动生成（SQLite）
├── requirements.txt
└── .env.example
```

## 🗄️ 数据库设计

单 SQLite 文件，5 张表，两条外键链：

```
companies ──┬──→ documents ──→ chunk_vectors
            └──→ conversations ──→ messages
```

| 表 | 职责 | 关键字段 |
|----|------|---------|
| `companies` | 企业/租户 | email (唯一), password_hash, ai_tone |
| `documents` | 知识库文档 | filename, content, chunk_count |
| `chunk_vectors` | 向量分块 | content, embedding (1024维 JSON 数组) |
| `conversations` | 对话会话 | status, satisfaction |
| `messages` | 对话消息 | role, content, confidence, sources |

## 📡 API 接口

后端启动后访问 `http://localhost:8001/docs` 查看交互式 Swagger 文档。

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/register` / `login` / `GET /me` | JWT 认证 |
| 知识库 | `POST /api/knowledge/upload` / `GET /list` / `DELETE /{id}` | 文档管理 |
| 检索 | `POST /api/rag/search` / `GET /api/rag/stats` | 语义检索 |
| 对话 | `POST /api/chat/send` / `GET /conversations` / `GET /conversations/{id}/messages` | AI 对话 |

## 🧪 测试

```bash
pytest tests/ -v
```

## 💡 项目亮点

1. **零外部向量数据库** — NumPy 手写余弦相似度检索引擎，不依赖 ChromaDB/Pinecone，面试可深讲检索原理
2. **完整 RAG 链路自实现** — 文档解析 → 分块策略（500字+50重叠）→ Embedding → 检索 → Prompt 组装 → LLM 生成
3. **PBKDF2 密码哈希自实现** — hashlib 标准库，无 passlib/bcrypt 依赖
4. **真正的前后端分离** — React + TypeScript（Vite + Tailwind）↔ FastAPI，纯 HTTP JSON 通信
5. **模块低耦合** — LLM/Embedding 厂商可热切换（DeepSeek/OpenAI/Anthropic），不改业务代码
6. **多租户数据隔离** — 所有查询带 company_id 过滤，SaaS 架构基础

## 📄 License

[MIT](LICENSE)
