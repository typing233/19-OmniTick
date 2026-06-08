import React from 'react';
import { Layout, Menu } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  FileTextOutlined,
  TagsOutlined,
  TeamOutlined,
  LogoutOutlined,
  MailOutlined,
  SearchOutlined,
  ReadOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Header, Sider, Content } = Layout;

const AdminLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const menuItems = [
    { key: '/tickets', icon: <FileTextOutlined />, label: '工单管理' },
    { key: '/search', icon: <SearchOutlined />, label: '搜索' },
    { key: '/kb', icon: <ReadOutlined />, label: '知识库' },
    { key: '/labels', icon: <TagsOutlined />, label: '标签管理' },
    { key: '/users', icon: <TeamOutlined />, label: '用户管理' },
    { key: '/email-accounts', icon: <MailOutlined />, label: '邮件渠道' },
    { key: '/automation/rules', icon: <ThunderboltOutlined />, label: '自动化' },
  ];

  const pathParts = location.pathname.split('/');
  let selectedKey = '/' + pathParts[1];
  if (pathParts[1] === 'automation') selectedKey = '/automation/rules';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={200}>
        <div style={{ height: 48, margin: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ color: '#fff', fontSize: 18, fontWeight: 'bold' }}>OmniTick</span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <span style={{ marginRight: 16 }}>{user?.display_name}</span>
          <LogoutOutlined onClick={logout} style={{ cursor: 'pointer', fontSize: 16 }} />
        </Header>
        <Content style={{ margin: 24, padding: 24, background: '#fff', borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AdminLayout;
