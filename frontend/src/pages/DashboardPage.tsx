import { useEffect, useState } from "react";
import { api } from "../api/client";

interface Doc {
  id: number; filename: string; file_type: string;
  chunk_count: number; uploaded_at: string;
}

export default function DashboardPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [stats, setStats] = useState({ document_count: 0, chunk_count: 0 });
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    const [d, s] = await Promise.all([api.listDocuments(), api.getStats()]);
    if (d.ok) setDocs(d.data);
    if (s.ok) setStats(s.data);
  };

  useEffect(() => { load(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMsg("");
    const r = await api.uploadDocument(file);
    setMsg(r.ok ? `${file.name} 上传成功` : r.data?.detail || "上传失败");
    setUploading(false);
    e.target.value = "";
    load();
  };

  const handleDelete = async (id: number) => {
    const r = await api.deleteDocument(id);
    if (r.ok) load();
  };

  const typeIcon: Record<string, string> = { txt: "📝", pdf: "📕", docx: "📘" };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">知识库管理</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-4 border">
          <div className="text-3xl font-bold text-indigo-600">{stats.document_count}</div>
          <div className="text-sm text-gray-500">文档数量</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4 border">
          <div className="text-3xl font-bold text-green-600">{stats.chunk_count}</div>
          <div className="text-sm text-gray-500">知识片段</div>
        </div>
      </div>

      {/* Upload */}
      <div className="bg-white rounded-lg shadow-sm p-6 border mb-6">
        <h2 className="font-semibold text-gray-700 mb-3">上传知识库文档</h2>
        <p className="text-sm text-gray-400 mb-3">支持 TXT、PDF、Word 格式，最大 10MB</p>
        <label className="inline-block bg-indigo-600 text-white px-4 py-2 rounded-lg cursor-pointer hover:bg-indigo-700 transition-colors text-sm">
          {uploading ? "上传中..." : "选择文件"}
          <input type="file" accept=".txt,.pdf,.docx" onChange={handleUpload} className="hidden" disabled={uploading} />
        </label>
        {msg && <p className={`mt-2 text-sm ${msg.includes("失败") ? "text-red-500" : "text-green-600"}`}>{msg}</p>}
      </div>

      {/* Document List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <h2 className="font-semibold text-gray-700 p-4 border-b">已上传文档</h2>
        {docs.length === 0 ? (
          <p className="p-4 text-gray-400 text-sm">暂无文档，请上传</p>
        ) : (
          docs.map(doc => (
            <div key={doc.id} className="flex items-center justify-between px-4 py-3 border-b last:border-0 hover:bg-gray-50">
              <div>
                <span className="mr-2">{typeIcon[doc.file_type] || "📄"}</span>
                <span className="font-medium text-sm">{doc.filename}</span>
                <span className="ml-3 text-xs text-gray-400">
                  {doc.file_type} · {doc.chunk_count} 块 · {doc.uploaded_at?.slice(0, 19)}
                </span>
              </div>
              <button
                onClick={() => handleDelete(doc.id)}
                className="text-red-400 hover:text-red-600 text-sm cursor-pointer"
              >
                删除
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
