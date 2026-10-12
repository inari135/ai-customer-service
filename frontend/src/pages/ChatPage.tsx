import { useEffect, useState, useRef } from "react";
import { api } from "../api/client";

interface Conv {
  id: number; visitor_name: string; status: string;
  message_count: number; created_at: string;
}

interface Msg {
  role: string; content: string; confidence?: string;
}

export default function ChatPage() {
  const [convId, setConvId] = useState<number | null>(null);
  const [convs, setConvs] = useState<Conv[]>([]);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [stats, setStats] = useState({ document_count: 0, chunk_count: 0 });

  const loadConvs = async () => {
    const r = await api.listConversations();
    if (r.ok) setConvs(r.data);
  };

  const loadMessages = async (id: number) => {
    const r = await api.getMessages(id);
    if (r.ok) setMessages(r.data.map((m: any) => ({
      role: m.role, content: m.content, confidence: m.confidence,
    })));
  };

  useEffect(() => {
    loadConvs();
    api.getStats().then(r => { if (r.ok) setStats(r.data); });
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: Msg = { role: "user", content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const r = await api.sendMessage(input, convId);
      if (r.ok) {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: r.data.reply,
          confidence: r.data.confidence,
        }]);
        setConvId(r.data.conversation_id);
        loadConvs();
      } else {
        setMessages(prev => [...prev, { role: "assistant", content: `[错误] ${r.data?.detail}` }]);
      }
    } catch {
      setMessages(prev => [...prev, { role: "assistant", content: "[错误] 请求失败，请检查后端是否启动" }]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const confidenceColor = (c?: string) =>
    c === "high" ? "text-green-600" : c === "low" ? "text-red-500" : "text-orange-500";

  return (
    <div className="flex h-[calc(100vh-100px)] gap-4">
      {/* Sidebar */}
      <div className="w-64 bg-white rounded-lg shadow-sm border flex flex-col flex-shrink-0">
        <div className="p-3 border-b">
          <button
            onClick={() => { setConvId(null); setMessages([]); }}
            className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors cursor-pointer"
          >
            + 新建对话
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {convs.map(c => (
            <button
              key={c.id}
              onClick={() => { setConvId(c.id); loadMessages(c.id); }}
              className={`w-full text-left px-3 py-2 text-sm border-b hover:bg-gray-50 cursor-pointer ${
                convId === c.id ? "bg-indigo-50 border-l-2 border-l-indigo-600" : ""
              }`}
            >
              <div className="truncate text-gray-700">
                {c.status === "active" ? "🟢" : "⚫"} 对话 {c.id}
              </div>
              <div className="text-xs text-gray-400">{c.message_count} 条消息</div>
            </button>
          ))}
          {convs.length === 0 && <p className="p-3 text-xs text-gray-400">暂无对话</p>}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 bg-white rounded-lg shadow-sm border flex flex-col">
        {/* Stats bar */}
        <div className="flex gap-4 px-4 py-2 border-b text-xs text-gray-400">
          <span>文档: {stats.document_count}</span>
          <span>片段: {stats.chunk_count}</span>
          <span>模型: DeepSeek V4 Flash</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[70%] rounded-xl px-4 py-2 ${
                m.role === "user"
                  ? "bg-indigo-600 text-white"
                  : m.content.startsWith("[错误]")
                    ? "bg-red-50 text-red-600 border border-red-200"
                    : "bg-gray-100 text-gray-800"
              }`}>
                <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                {m.confidence && (
                  <div className={`text-xs mt-1 ${confidenceColor(m.confidence)}`}>
                    置信度: {m.confidence}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && <div className="text-center text-gray-400 text-sm">AI 思考中...</div>}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入你的问题..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors cursor-pointer text-sm"
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
