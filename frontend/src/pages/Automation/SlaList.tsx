import React, { useState } from 'react';
import { Table, Tag, Button, Modal, Form, Input, message } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { automationApi } from '../../api';
import type { SlaPolicy } from '../../types';

const SlaList: React.FC = () => {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: policies, isLoading } = useQuery({
    queryKey: ['sla-policies'],
    queryFn: automationApi.listSlaPolicies,
  });

  const createMutation = useMutation({
    mutationFn: automationApi.createSlaPolicy,
    onSuccess: () => {
      message.success('SLA策略创建成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['sla-policies'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: automationApi.deleteSlaPolicy,
    onSuccess: () => {
      message.success('已删除');
      queryClient.invalidateQueries({ queryKey: ['sla-policies'] });
    },
  });

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '首次响应(分钟)', dataIndex: 'first_response_minutes', key: 'fr', render: (v: number | null) => v || '-' },
    { title: '解决时限(分钟)', dataIndex: 'resolution_minutes', key: 'res', render: (v: number | null) => v || '-' },
    { title: '状态', dataIndex: 'is_active', key: 'active', render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '禁用'}</Tag> },
    {
      title: '操作', key: 'actions', render: (_: unknown, r: SlaPolicy) => (
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => deleteMutation.mutate(r.id)}>删除</Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>SLA策略</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建策略</Button>
      </div>

      <Table columns={columns} dataSource={policies} rowKey="id" loading={isLoading} pagination={false} />

      <Modal
        title="新建SLA策略"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate({ ...v, first_response_minutes: v.first_response_minutes ? Number(v.first_response_minutes) : undefined, resolution_minutes: v.resolution_minutes ? Number(v.resolution_minutes) : undefined })}>
          <Form.Item name="name" label="策略名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="first_response_minutes" label="首次响应时限(分钟)">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="resolution_minutes" label="解决时限(分钟)">
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SlaList;
