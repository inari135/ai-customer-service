import { Link, useLocation } from "react-router-dom";
import { api } from "../api/client";

interface Props {
  children: React.ReactNode;
}

export default function Layout({ children }: Props) {
  const location = useLocation();
  const isLoginPage = location.pathname === "/";

  const navItems = [
    { path: "/dashboard", label: "管理后台" },
    { path: "/chat", label: "客服对话" },
    { path: "/analytics", label: "数据分析" },
  ];

  if (isLoginPage) return <>{children}</>;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="font-bold text-lg text-indigo-600">
              AI 客服平台
            </Link>
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm px-3 py-1 rounded-md transition-colors ${
                  location.pathname === item.path
                    ? "bg-indigo-100 text-indigo-700"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{api.companyName}</span>
            <button
              onClick={() => { api.logout(); window.location.href = "/"; }}
              className="text-sm text-red-500 hover:text-red-700 cursor-pointer"
            >
              退出
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
