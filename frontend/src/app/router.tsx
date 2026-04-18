import type { ReactNode } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { useSelector } from "react-redux";

import type { RootState } from "./store";
import { AdminAuditPage } from "../pages/AdminAuditPage";
import { LoginPage } from "../pages/LoginPage";
import { MerchantLocationPage } from "../pages/MerchantLocationPage";
import { MerchantReviewPage } from "../pages/MerchantReviewPage";
import { MerchantSessionPage } from "../pages/MerchantSessionPage";
import { MerchantUploadPage } from "../pages/MerchantUploadPage";
import { ResultsPage } from "../pages/ResultsPage";
import { UnderwriterCasePage } from "../pages/UnderwriterCasePage";
import { UnderwriterQueuePage } from "../pages/UnderwriterQueuePage";


function Layout({ children }: { children: ReactNode }) {
  const user = useSelector((state: RootState) => state.auth.user);
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#f7f1df,transparent_40%),linear-gradient(180deg,#f2f0e8_0%,#e6dccd_100%)]">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
        <Link to="/" className="text-xl font-semibold tracking-tight">Kirana Underwriting</Link>
        <nav className="flex gap-3 text-sm">
          <Link to="/merchant/session" className="button-secondary">Merchant</Link>
          <Link to="/underwriter/queue" className="button-secondary">Underwriter</Link>
          <Link to="/admin/audit" className="button-secondary">Admin</Link>
          <span className="rounded-full bg-white/70 px-4 py-2">{user?.role || "guest"}</span>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-6 pb-12">{children}</main>
    </div>
  );
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = useSelector((state: RootState) => state.auth.accessToken);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/merchant/session" replace />} />
          <Route path="/merchant/session" element={<ProtectedRoute><MerchantSessionPage /></ProtectedRoute>} />
          <Route path="/merchant/upload" element={<ProtectedRoute><MerchantUploadPage /></ProtectedRoute>} />
          <Route path="/merchant/location" element={<ProtectedRoute><MerchantLocationPage /></ProtectedRoute>} />
          <Route path="/merchant/review" element={<ProtectedRoute><MerchantReviewPage /></ProtectedRoute>} />
          <Route path="/results/:predictionId" element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />
          <Route path="/underwriter/queue" element={<ProtectedRoute><UnderwriterQueuePage /></ProtectedRoute>} />
          <Route path="/underwriter/case/:predictionId" element={<ProtectedRoute><UnderwriterCasePage /></ProtectedRoute>} />
          <Route path="/admin/audit" element={<ProtectedRoute><AdminAuditPage /></ProtectedRoute>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
