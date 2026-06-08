import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AdminLayout from './layouts/AdminLayout';
import Login from './pages/Login';
import TicketList from './pages/Tickets/TicketList';
import TicketDetail from './pages/Tickets/TicketDetail';
import LabelList from './pages/Labels/LabelList';
import UserList from './pages/Users/UserList';
import EmailAccountList from './pages/EmailAccounts/EmailAccountList';

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  if (loading) return null;
  if (!token) return <Navigate to="/login" replace />;
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
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App;
