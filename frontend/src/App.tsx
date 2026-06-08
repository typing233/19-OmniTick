import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AdminLayout from './layouts/AdminLayout';
import PortalLayout from './layouts/PortalLayout';
import Login from './pages/Login';
import TicketList from './pages/Tickets/TicketList';
import TicketDetail from './pages/Tickets/TicketDetail';
import LabelList from './pages/Labels/LabelList';
import UserList from './pages/Users/UserList';
import EmailAccountList from './pages/EmailAccounts/EmailAccountList';
import SearchPage from './pages/Search/SearchPage';
import ArticleList from './pages/KB/ArticleList';
import ArticleEditor from './pages/KB/ArticleEditor';
import RuleList from './pages/Automation/RuleList';
import RuleEditor from './pages/Automation/RuleEditor';
import SlaList from './pages/Automation/SlaList';
import PortalLogin from './pages/Portal/PortalLogin';
import PortalTicketList from './pages/Portal/PortalTicketList';
import PortalTicketDetail from './pages/Portal/PortalTicketDetail';
import PortalKBHome from './pages/Portal/PortalKBHome';
import PortalKBArticle from './pages/Portal/PortalKBArticle';

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  if (loading) return null;
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PortalProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('portal_token');
  if (!token) return <Navigate to="/portal/login" replace />;
  return <>{children}</>;
}

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />

              {/* Admin/Agent routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/tickets" replace />} />
                <Route path="tickets" element={<TicketList />} />
                <Route path="tickets/:id" element={<TicketDetail />} />
                <Route path="labels" element={<LabelList />} />
                <Route path="users" element={<UserList />} />
                <Route path="email-accounts" element={<EmailAccountList />} />
                <Route path="search" element={<SearchPage />} />
                <Route path="kb" element={<ArticleList />} />
                <Route path="kb/:id/edit" element={<ArticleEditor />} />
                <Route path="automation/rules" element={<RuleList />} />
                <Route path="automation/rules/new" element={<RuleEditor />} />
                <Route path="automation/rules/:id" element={<RuleEditor />} />
                <Route path="automation/sla" element={<SlaList />} />
              </Route>

              {/* Customer Portal routes */}
              <Route path="/portal" element={<PortalLayout />}>
                <Route path="login" element={<PortalLogin />} />
                <Route path="tickets" element={<PortalProtectedRoute><PortalTicketList /></PortalProtectedRoute>} />
                <Route path="tickets/:id" element={<PortalProtectedRoute><PortalTicketDetail /></PortalProtectedRoute>} />
                <Route path="kb" element={<PortalKBHome />} />
                <Route path="kb/:slug" element={<PortalKBArticle />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
