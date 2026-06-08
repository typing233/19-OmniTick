import React, { useState } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, Switch, message, Space, Tag, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { emailAccountApi, type EmailAccount } from '../../api';

const EmailAccountList: React.FC = () => {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<EmailAccount | null>(null);
  const [form] = Form.useForm();

  const { data: accounts, isLoading } = useQuery({
    queryKey: ['email-accounts'],
    queryFn: emailAccountApi.list,
  });

  const createMutation = useMutation({
    mutationFn: emailAccountApi.create,
    onSuccess: () => { message.success('邮箱账号已创建'); closeModal(); queryClient.invalidateQueries({ queryKey: ['email-accounts'] }); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Record<string, unknown>) => emailAccountApi.update(id, data),
    onSuccess: () => { message.success('邮箱账号已更新'); closeModal(); queryClient.invalidateQueries({ queryKey: ['email-accounts'] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: emailAccountApi.delete,
    onSuccess: () => { message.success('邮箱账号已删除'); queryClient.invalidateQueries({ queryKey: ['email-accounts'] }); },
  });

  const closeModal = () => { setModalOpen(false); setEditing(null); form.resetFields(); };

  const openEdit = (account: EmailAccount) => {
    setEditing(account);
    form.setFieldsValue({
      name: account.name,
      email_address: account.email_address,
      imap_host: account.imap_host,
      imap_port: account.imap_port,
      smtp_host: account.smtp_host,
      smtp_port: account.smtp_port,
      username: account.username,
      password: '',
      poll_interval_seconds: account.poll_interval_seconds,
      is_active: account.is_active,
    });
    setModalOpen(true);
  };

  const onFinish = (values: Record<string, unknown>) => {
    if (editing) {
      const data: Record<string, unknown> = { ...values, id: editing.id };
      if (!data.password) delete data.password;
      updateMutation.mutate(data as { id: string } & Record<string, unknown>);
    } else {
      createMutation.mutate(values as any);
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '邮箱地址', dataIndex: 'email_address', key: 'email_address' },
    { title: 'IMAP', key: 'imap', render: (_: unknown, r: EmailAccount) => `${r.imap_host}:${r.imap_port}` },
    { title: 'SMTP', key: 'smtp', render: (_: unknown, r: EmailAccount) => `${r.smtp_host}:${r.smtp_port}` },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (active: boolean) => <Tag color={active ? 'green' : 'default'}>{active ? '启用' : '停用'}</Tag>,
    },
    {
      title: '最后拉取', dataIndex: 'last_polled_at', key: 'last_polled_at', width: 170,
      render: (t: string | null) => t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作', key: 'actions', width: 120,
      render: (_: unknown, record: EmailAccount) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm title="确认删除?" onConfirm={() => deleteMutation.mutate(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>邮件渠道管理</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          添加邮箱账号
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={accounts || []} loading={isLoading} pagination={false} />

      <Modal
        title={editing ? '编辑邮箱账号' : '添加邮箱账号'}
        open={modalOpen} onCancel={closeModal} onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="name" label="显示名称" rules={[{ required: true }]}>
            <Input placeholder="如：客服邮箱" />
          </Form.Item>
          <Form.Item name="email_address" label="邮箱地址" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="support@company.com" />
          </Form.Item>
          <Space size={16} style={{ display: 'flex' }}>
            <Form.Item name="imap_host" label="IMAP 主机" rules={[{ required: true }]}>
              <Input placeholder="imap.gmail.com" />
            </Form.Item>
            <Form.Item name="imap_port" label="IMAP 端口" initialValue={993}>
              <InputNumber min={1} max={65535} />
            </Form.Item>
          </Space>
          <Space size={16} style={{ display: 'flex' }}>
            <Form.Item name="smtp_host" label="SMTP 主机" rules={[{ required: true }]}>
              <Input placeholder="smtp.gmail.com" />
            </Form.Item>
            <Form.Item name="smtp_port" label="SMTP 端口" initialValue={587}>
              <InputNumber min={1} max={65535} />
            </Form.Item>
          </Space>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label={editing ? '密码（留空则不修改）' : '密码'} rules={editing ? [] : [{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="poll_interval_seconds" label="拉取间隔（秒）" initialValue={60}>
            <InputNumber min={10} max={3600} />
          </Form.Item>
          {editing && (
            <Form.Item name="is_active" label="启用" valuePropName="checked">
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default EmailAccountList;
