import { useEffect, useState } from "react";
import { api } from "../api/client";

interface Doc {
  id: number; filename: string; file_type: string;
  chunk_count: number;
}

export default function AnalyticsPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [stats, setStats] = useState({ document_count: 0, chunk_count: 0 });

  useEffect(() => {
    api.getStats().then(r => { if (r.ok) setStats(r.data); });
    api.listDocuments().then(r => { if (r.ok) setDocs(r.data); });
  }, []);

  const typeCounts: Record<string, number> = {};
  docs.forEach(d => { typeCounts[d.file_type] = (typeCounts[d.file_type] || 0) + 1; });

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">数据分析 Dashboard</h1>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-4 border">
          <div className="text-3xl font-bold text-indigo-600">{stats.document_count}</div>
          <div className="text-sm text-gray-500">文档数量</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4 border">
          <div className="text-3xl font-bold text-green-600">{stats.chunk_count}</div>
          <div className="text-sm text-gray-500">知识片段</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-4 border">
          <div className="text-3xl font-bold text-purple-600">{docs.length ? (stats.chunk_count / docs.length).toFixed(1) : "0"}</div>
          <div className="text-sm text-gray-500">平均片段/文档</div>
        </div>
      </div>

      {/* Document Type Distribution */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <h2 className="font-semibold text-gray-700 mb-4">文档类型分布</h2>
        {Object.keys(typeCounts).length === 0 ? (
          <p className="text-gray-400 text-sm">暂无数据</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(typeCounts).map(([type, count]) => (
              <div key={type} className="flex items-center gap-3">
                <span className="text-sm w-12">
                  {type === "txt" ? "📝 TXT" : type === "pdf" ? "📕 PDF" : "📘 DOCX"}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-4">
                  <div
                    className="bg-indigo-500 h-4 rounded-full transition-all"
                    style={{ width: `${(count / docs.length) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <h2 className="font-semibold text-gray-700 p-4 border-b">文档详情</h2>
        {docs.map(d => (
          <div key={d.id} className="flex justify-between px-4 py-2 border-b last:border-0 text-sm">
            <span className="font-medium">{d.filename}</span>
            <span className="text-gray-400">{d.chunk_count} 片段</span>
          </div>
        ))}
      </div>
    </div>
  );
}
