# 🤖 AI 智能客服平台

企业级 AI 客服 SaaS。上传知识库文档 → AI 基于文档内容回答用户问题 → 管理后台 + 数据分析。

---

## 技术架构

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

## 项目结构

```
ai-customer-service/
├── frontend/                  ← 前端（React + TypeScript + Vite + Tailwind）
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts          HTTP 客户端 + JWT localStorage 持久化
│   │   ├── components/
│   │   │   └── Layout.tsx         导航栏 + 路由守卫
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx      登录/注册（双Tab切换）
│   │   │   ├── DashboardPage.tsx  知识库管理（上传/列表/删除 + 统计）
│   │   │   ├── ChatPage.tsx       AI 客服对话 + 历史对话侧边栏
│   │   │   └── AnalyticsPage.tsx  数据 Dashboard（文档分布/健康度）
│   │   ├── App.tsx               路由配置（React Router）
│   │   └── main.tsx              React 入口
│   ├── vite.config.ts            Vite 配置（含代理 + Tailwind 插件）
│   ├── package.json
│   └── tsconfig.json
├── backend/                   ← 后端（FastAPI REST API）
│   ├── main.py                应用入口 + 路由注册 + 生命周期
│   ├── config.py              从 .env 加载所有配置
│   ├── models.py              5 张 SQLAlchemy 数据模型（含向量分块）
│   ├── schemas.py             Pydantic 请求/响应校验
│   ├── auth.py                JWT 认证 + PBKDF2 密码哈希（标准库实现）
│   ├── upload.py              文档上传 + PDF/Word/TXT 解析 + 触发向量化
│   ├── embedding.py           文本分块 + Embedding API 调用
│   ├── vector_store.py        NumPy 余弦相似度检索引擎
│   ├── rag.py                 RAG 检索接口
│   └── agent.py               AI 对话编排（检索 + Prompt + LLM 调用 + 置信度）
├── data/                      ← 运行时自动生成
│   └── customer_service.db    唯一 SQLite 数据库
├── requirements.txt            Python 依赖
├── .env / .env.example        环境变量
└── README.md
```

## 各模块职责

### 后端（backend/）

| 文件 | 职责 | 依赖 |
|------|------|------|
| `main.py` | FastAPI 入口，注册 17 个路由，生命周期管理 | 所有子模块 |
| `config.py` | 从 .env 加载配置 | python-dotenv |
| `models.py` | 5 张表定义 + 数据库引擎 + 会话管理 | SQLAlchemy |
| `schemas.py` | API 请求/响应数据结构校验 | Pydantic |
| `auth.py` | 注册/登录/JWT/鉴权中间件 | models, hashlib |
| `upload.py` | 文档上传、TXT/PDF/Word 解析、入库 | models, embedding |
| `embedding.py` | 文本分块（500字+50重叠）、调 API 向量化 | vector_store |
| `vector_store.py` | NumPy 余弦相似度检索 | models (ChunkVector) |
| `rag.py` | 检索接口：query→embed→search→结果 | embedding, vector_store |
| `agent.py` | 对话编排：记忆管理→检索→Prompt→LLM→解析置信度 | rag, models |

**5 张表：** `companies` → `documents` → `chunk_vectors` / `conversations` → `messages`

## 数据库表结构

```
┌─────────────────────────────────────────────────────┐
│                    companies                          │
│  id (PK) | name | email (UQ) | password_hash         │
│  welcome_message | ai_tone | created_at              │
└────────┬────────────────────────┬───────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────────┐  ┌──────────────────────────┐
│     documents        │  │     conversations         │
│  id (PK)             │  │  id (PK)                  │
│  company_id (FK)─────│──│  company_id (FK)─────────│──→ companies
│  filename            │  │  visitor_name             │
│  file_type           │  │  status (active/closed/)   │
│  content (TEXT)      │  │  satisfaction (1-5)       │
│  chunk_count         │  │  created_at               │
│  uploaded_at         │  └────────┬──────────────────┘
└────────┬─────────────┘           │
         │                         ▼
         │               ┌──────────────────────────┐
         │               │      messages             │
         ▼               │  id (PK)                  │
┌─────────────────────┐  │  conversation_id (FK)─────│──→ conversations
│   chunk_vectors      │  │  role (user/assistant)    │
│  id (PK)             │  │  content (TEXT)           │
│  document_id (FK)────│──│  confidence (high/med/low)│
│  company_id (FK)─────│──│  sources (JSON)           │
│  chunk_index         │  │  created_at               │
│  content (TEXT)      │  └──────────────────────────┘
│  embedding (JSON)    │
│  token_count         │
└─────────────────────┘
```

### 表详细字段

**companies（企业）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | VARCHAR(200) | 企业名称 |
| email | VARCHAR(200) UQ | 登录邮箱，唯一 |
| password_hash | VARCHAR(200) | PBKDF2-SHA256 密码哈希 |
| welcome_message | VARCHAR(500) | AI 欢迎语 |
| ai_tone | VARCHAR(100) | AI 语气：professional/friendly/concise |
| created_at | DATETIME | 注册时间 |

**documents（知识库文档）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| company_id | INTEGER FK | 所属企业 → companies.id |
| filename | VARCHAR(500) | 原始文件名 |
| file_type | VARCHAR(20) | txt / pdf / docx |
| content | TEXT | 文档完整纯文本 |
| chunk_count | INTEGER | 分块数量 |
| uploaded_at | DATETIME | 上传时间 |

**chunk_vectors（向量分块）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| document_id | INTEGER FK | 所属文档 → documents.id |
| company_id | INTEGER FK | 所属企业 → companies.id |
| chunk_index | INTEGER | 分块序号（0开始） |
| content | TEXT | 分块文本（~500字） |
| embedding | TEXT | 1024维向量（JSON数组字符串） |
| token_count | INTEGER | 字符数估算 |

**conversations（对话会话）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| company_id | INTEGER FK | 所属企业 → companies.id |
| visitor_name | VARCHAR(100) | 访客名称（默认"匿名用户"） |
| status | VARCHAR(20) | active / closed / transferred |
| satisfaction | INTEGER | 满意度 1-5（可空） |
| created_at | DATETIME | 创建时间 |

**messages（对话消息）**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| conversation_id | INTEGER FK | 所属对话 → conversations.id |
| role | VARCHAR(20) | user / assistant / system |
| content | TEXT | 消息内容 |
| confidence | VARCHAR(20) | AI 置信度：high / medium / low |
| sources | TEXT | 引用的知识库片段（JSON） |
| created_at | DATETIME | 发送时间 |

### 前端（frontend/src/）

| 文件 | 功能 |
|------|------|
| `api/client.ts` | 封装后端 12 个 API + JWT 存 localStorage（刷新不掉登录） |
| `components/Layout.tsx` | 顶部导航 + 路由守卫（未登录重定向到 /） |
| `pages/LoginPage.tsx` | 登录/注册双 Tab 表单 |
| `pages/DashboardPage.tsx` | 文档上传、列表、删除 + 统计卡片 |
| `pages/ChatPage.tsx` | 左侧对话列表 + 右侧 AI 对话框 + 置信度标签 |
| `pages/AnalyticsPage.tsx` | 文档数量/片段/类型分布/文档详情 |

## 依赖

### Python（requirements.txt）

| 类别 | 包 | 用途 |
|------|-----|------|
| Web | `fastapi`, `uvicorn` | REST API 服务 |
| 数据库 | `sqlalchemy` | ORM + SQLite |
| AI | `openai` | 调 DeepSeek + SiliconFlow（OpenAI 兼容协议） |
| 认证 | `python-jose` | JWT 签发验证 |
| 文档 | `PyPDF2`, `python-docx` | PDF/Word 解析 |
| 向量 | `numpy` | 自建余弦相似度检索引擎 |
| 校验 | `pydantic`, `email-validator` | 请求参数校验 |
| 工具 | `python-dotenv`, `python-multipart`, `httpx` | 配置/上传/HTTP |

### Node.js（frontend/package.json）

| 类别 | 包 | 用途 |
|------|-----|------|
| 框架 | `react`, `react-dom`, `react-router-dom` | UI + 路由 |
| 语言 | `typescript` | 类型安全 |
| 构建 | `vite`, `@vitejs/plugin-react` | 秒级热更新 |
| CSS | `tailwindcss`, `@tailwindcss/vite` | 原子化样式 |
| HTTP | `axios` | HTTP 客户端 |

### 外部 API

| API | 提供商 | 模型 | 用途 | 费用 |
|-----|--------|------|------|------|
| LLM 对话 | DeepSeek | `deepseek-v4-flash` | 生成客服回答 | 按量付费 |
| Embedding | SiliconFlow 硅基流动 | `BAAI/bge-large-zh-v1.5` | 文本向量化 | **免费** |

---

## 快速开始

### 1. 环境准备

**Python 后端：**
```bash
cd ai-customer-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Node.js 前端：**
```bash
cd frontend
npm install
```

### 2. 配置 API Key

```bash
copy .env.example .env
```

编辑 `.env`，填入真实 Key：
```env
DEEPSEEK_API_KEY=sk-你的key        # https://platform.deepseek.com → API Keys
SILICONFLOW_API_KEY=sk-你的key     # https://cloud.siliconflow.cn → API 密钥
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
EMBEDDING_PROVIDER=siliconflow
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
API_PORT=8001
```

### 3. 启动（两个终端）

**终端 1 — 后端：**
```bash
cd ai-customer-service
venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```
启动成功标志：`[OK] 数据库初始化完成（含向量分块表）`

**终端 2 — 前端：**
```bash
cd ai-customer-service/frontend
npm run dev
```
打开 `http://localhost:5173`

### 4. 使用流程

1. 浏览器打开 `http://localhost:5173` → 注册企业账号
2. 进入管理后台 → 上传知识库文档（TXT/PDF/Word）
3. 切换到客服对话 → 输入问题 → AI 基于文档回答

## API 接口一览

后端启动后访问 `http://localhost:8001/docs` 查看 Swagger。

| 模块 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/auth/register` | 企业注册 |
| 认证 | POST | `/api/auth/login` | 企业登录，返回 JWT |
| 认证 | GET | `/api/auth/me` | 当前企业信息 |
| 知识库 | POST | `/api/knowledge/upload` | 上传文档，自动分块+向量化 |
| 知识库 | GET | `/api/knowledge/list` | 文档列表 |
| 知识库 | DELETE | `/api/knowledge/{id}` | 删除文档及关联向量 |
| 检索 | POST | `/api/rag/search` | 语义检索知识库 |
| 检索 | GET | `/api/rag/stats` | 知识库统计 |
| 对话 | POST | `/api/chat/send` | 发送消息，RAG+LLM 生成回复 |
| 对话 | GET | `/api/chat/conversations` | 对话列表 |
| 对话 | GET | `/api/chat/conversations/{id}/messages` | 某对话消息历史 |

## 面试可讲的技术点

1. **自建向量检索引擎** — NumPy 实现余弦相似度，不依赖 ChromaDB/Pinecone
2. **RAG 完整链路** — 文档解析 → 分块策略 → Embedding → 检索 → Prompt 组装 → LLM 生成
3. **PBKDF2 自实现密码哈希** — hashlib 标准库，理解安全原理
4. **真正的前后端分离** — React + TypeScript 前端（Vite + Tailwind）←HTTP JSON→ FastAPI 后端
5. **模块低耦合** — LLM/Embedding 可热切换任意厂商，不改业务代码
6. **统一数据模型** — 5 张表在同一 SQLite，事务一致性 + 单文件备份
7. **JWT 持久化** — localStorage 存 token，刷新页面不掉登录态
