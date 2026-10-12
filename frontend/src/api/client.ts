/**
 * API HTTP 客户端
 * 后端所有接口的封装 + JWT localStorage 持久化
 */
const BASE = "";  // Vite proxy 代理，同域调用

interface ApiResult {
  ok: boolean;
  data: any;
}

class ApiClient {
  token: string | null = null;
  companyId: number | null = null;
  companyName: string | null = null;

  constructor() {
    this._loadSession();
  }

  // --- Session ---

  _saveSession() {
    localStorage.setItem("jwt_token", this.token || "");
    localStorage.setItem("company_id", String(this.companyId || ""));
    localStorage.setItem("company_name", this.companyName || "");
  }

  _loadSession() {
    this.token = localStorage.getItem("jwt_token") || null;
    this.companyId = Number(localStorage.getItem("company_id")) || null;
    this.companyName = localStorage.getItem("company_name") || null;
    if (this.token) {
      // 异步验证 token 是否过期
      fetch(`${BASE}/api/auth/me`, { headers: this._headers() })
        .then(r => { if (!r.ok) this.clearSession(); });
    }
  }

  clearSession() {
    this.token = null;
    this.companyId = null;
    this.companyName = null;
    localStorage.removeItem("jwt_token");
    localStorage.removeItem("company_id");
    localStorage.removeItem("company_name");
  }

  _headers(): Record<string, string> {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (this.token) h["Authorization"] = `Bearer ${this.token}`;
    return h;
  }

  isLoggedIn(): boolean {
    return this.token !== null;
  }

  // --- Auth ---

  async register(name: string, email: string, password: string): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/auth/register`, {
      method: "POST", headers: this._headers(),
      body: JSON.stringify({ name, email, password }),
    });
    const data = await r.json();
    if (r.ok) {
      this.token = data.access_token;
      this.companyId = data.company_id;
      this.companyName = data.company_name;
      this._saveSession();
    }
    return { ok: r.ok, data };
  }

  async login(email: string, password: string): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/auth/login`, {
      method: "POST", headers: this._headers(),
      body: JSON.stringify({ email, password }),
    });
    const data = await r.json();
    if (r.ok) {
      this.token = data.access_token;
      this.companyId = data.company_id;
      this.companyName = data.company_name;
      this._saveSession();
    }
    return { ok: r.ok, data };
  }

  logout() {
    this.clearSession();
  }

  // --- Knowledge Base ---

  async uploadDocument(file: File): Promise<ApiResult> {
    const form = new FormData();
    form.append("file", file);
    const r = await fetch(`${BASE}/api/knowledge/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${this.token}` },
      body: form,
    });
    return { ok: r.ok, data: await r.json() };
  }

  async listDocuments(): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/knowledge/list`, { headers: this._headers() });
    return { ok: r.ok, data: await r.json() };
  }

  async deleteDocument(id: number): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/knowledge/${id}`, {
      method: "DELETE", headers: this._headers(),
    });
    return { ok: r.ok, data: await r.json() };
  }

  // --- RAG ---

  async getStats(): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/rag/stats`, { headers: this._headers() });
    return { ok: r.ok, data: await r.json() };
  }

  // --- Chat ---

  async sendMessage(message: string, conversationId: number | null): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/chat/send`, {
      method: "POST", headers: this._headers(),
      body: JSON.stringify({ company_id: this.companyId, message, conversation_id: conversationId }),
    });
    return { ok: r.ok, data: await r.json() };
  }

  async listConversations(): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/chat/conversations`, { headers: this._headers() });
    return { ok: r.ok, data: await r.json() };
  }

  async getMessages(conversationId: number): Promise<ApiResult> {
    const r = await fetch(`${BASE}/api/chat/conversations/${conversationId}/messages`, { headers: this._headers() });
    return { ok: r.ok, data: await r.json() };
  }
}

export const api = new ApiClient();
