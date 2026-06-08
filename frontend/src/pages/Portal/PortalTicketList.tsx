import React, { useState } from 'react';
import { Table, Button, Tag, Space, Modal, Form, Input, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { portalTicketApi } from '../../api/portal';

const { TextArea } = Input;

const statusLabels: Record<string, string> = {
  new: '新建',
  in_progress: '处理中',
  pending_response: '等待回复',
  resolved: '已解决',
  closed: '已关闭',
};

const statusColors: Record<string, string> = {
  new: 'blue',
  in_progress: 'processing',
  pending_response: 'warning',
  resolved: 'success',
  closed: 'default',
};

const PortalTicketList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['portal-tickets', page],
    queryFn: () => portalTicketApi.list({ page, page_size: 20 }),
  });

  const createMutation = useMutation({
    mutationFn: portalTicketApi.create,
    onSuccess: () => {
      message.success('工单提交成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['portal-tickets'] });
    },
  });

  const columns = [
    { title: '主题', dataIndex: 'subject', key: 'subject', render: (s: string, r: { id: string }) => <a onClick={() => navigate(`/portal/tickets/${r.id}`)}>{s}</a> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={statusColors[s]}>{statusLabels[s] || s}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (d: string) => new Date(d).toLocaleString() },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', render: (d: string) => new Date(d).toLocaleString() },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>我的工单</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>提交工单</Button>
      </div>

      <Table
        columns={columns}
        dataSource={data?.items}
        rowKey="id"
        loading={isLoading}
        pagination={{ current: page, total: data?.total, pageSize: 20, onChange: setPage }}
      />

      <Modal
        title="提交新工单"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="subject" label="主题" rules={[{ required: true }]}>
            <Input placeholder="简要描述您的问题" />
          </Form.Item>
          <Form.Item name="body" label="详细描述" rules={[{ required: true }]}>
            <TextArea rows={6} placeholder="请详细描述您遇到的问题..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PortalTicketList;
