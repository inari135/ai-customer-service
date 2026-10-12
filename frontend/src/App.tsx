import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { api } from "./api/client";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";
import AnalyticsPage from "./pages/AnalyticsPage";

function Protected({ children }: { children: React.ReactNode }) {
  if (!api.isLoggedIn()) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
          <Route path="/chat" element={<Protected><ChatPage /></Protected>} />
          <Route path="/analytics" element={<Protected><AnalyticsPage /></Protected>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
