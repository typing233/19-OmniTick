import React, { useState } from 'react';
import { Card, Form, Input, Button, Tabs, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { portalAuthApi } from '../../api/portal';

const PortalLogin: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const { access_token } = await portalAuthApi.login(values);
      localStorage.setItem('portal_token', access_token);
      message.success('登录成功');
      navigate('/portal/tickets');
    } catch {
      message.error('登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: { email: string; password: string; display_name?: string }) => {
    setLoading(true);
    try {
      const { access_token } = await portalAuthApi.register(values);
      localStorage.setItem('portal_token', access_token);
      message.success('注册成功');
      navigate('/portal/tickets');
    } catch {
      message.error('注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: 24 }}>
      <h1 style={{ textAlign: 'center', marginBottom: 32 }}>OmniTick 客户门户</h1>
      <Card>
        <Tabs items={[
          {
            key: 'login',
            label: '登录',
            children: (
              <Form layout="vertical" onFinish={handleLogin}>
                <Form.Item name="email" label="邮箱" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="password" label="密码" rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Button type="primary" htmlType="submit" block loading={loading}>登录</Button>
              </Form>
            ),
          },
          {
            key: 'register',
            label: '注册',
            children: (
              <Form layout="vertical" onFinish={handleRegister}>
                <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="display_name" label="显示名称">
                  <Input />
                </Form.Item>
                <Form.Item name="password" label="密码" rules={[{ required: true, min: 6 }]}>
                  <Input.Password />
                </Form.Item>
                <Button type="primary" htmlType="submit" block loading={loading}>注册</Button>
              </Form>
            ),
          },
        ]} />
      </Card>
    </div>
  );
};

export default PortalLogin;
