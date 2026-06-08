import React from 'react';
import { Layout, Menu, Button } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { FileTextOutlined, ReadOutlined, LogoutOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;

const PortalLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('portal_token');
    navigate('/portal/login');
  };

  const hasToken = !!localStorage.getItem('portal_token');
  const selectedKey = location.pathname.startsWith('/portal/kb') ? '/portal/kb' : '/portal/tickets';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <div style={{ fontSize: 18, fontWeight: 'bold', marginRight: 48, cursor: 'pointer' }} onClick={() => navigate('/portal/kb')}>
          OmniTick
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[selectedKey]}
          style={{ flex: 1, border: 'none' }}
          items={[
            ...(hasToken ? [{ key: '/portal/tickets', icon: <FileTextOutlined />, label: '我的工单' }] : []),
            { key: '/portal/kb', icon: <ReadOutlined />, label: '帮助中心' },
          ]}
          onClick={({ key }) => navigate(key)}
        />
        {hasToken ? (
          <LogoutOutlined onClick={handleLogout} style={{ cursor: 'pointer', fontSize: 16 }} />
        ) : (
          <Button type="link" onClick={() => navigate('/portal/login')}>登录</Button>
        )}
      </Header>
      <Content style={{ maxWidth: 1000, margin: '24px auto', padding: 24, width: '100%' }}>
        <Outlet />
      </Content>
    </Layout>
  );
};

export default PortalLayout;
