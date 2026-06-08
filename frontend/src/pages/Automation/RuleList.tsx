import React, { useState } from 'react';
import { Table, Button, Tag, Space, Switch, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { automationApi } from '../../api';
import type { AutomationRule } from '../../types';

const triggerLabels: Record<string, string> = {
  on_ticket_create: '工单创建',
  on_ticket_update: '工单更新',
  on_status_change: '状态变更',
  on_sla_breach: 'SLA违约',
  on_time_elapsed: '时间触发',
};

const RuleList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: rules, isLoading } = useQuery({
    queryKey: ['automation-rules'],
    queryFn: automationApi.listRules,
  });

  const createMutation = useMutation({
    mutationFn: automationApi.createRule,
    onSuccess: () => {
      message.success('规则创建成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['automation-rules'] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      automationApi.updateRule(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['automation-rules'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: automationApi.deleteRule,
    onSuccess: () => {
      message.success('已删除');
      queryClient.invalidateQueries({ queryKey: ['automation-rules'] });
    },
  });

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', render: (n: string, r: AutomationRule) => <a onClick={() => navigate(`/automation/rules/${r.id}`)}>{n}</a> },
    { title: '触发事件', dataIndex: 'trigger_event', key: 'trigger_event', render: (t: string) => <Tag>{triggerLabels[t] || t}</Tag> },
    { title: '优先级', dataIndex: 'priority', key: 'priority' },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (active: boolean, r: AutomationRule) => (
        <Switch checked={active} onChange={(v) => toggleMutation.mutate({ id: r.id, is_active: v })} />
      ),
    },
    {
      title: '操作', key: 'actions', render: (_: unknown, r: AutomationRule) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/automation/rules/${r.id}`)}>编辑</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => deleteMutation.mutate(r.id)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>自动化规则</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建规则</Button>
      </div>

      <Table columns={columns} dataSource={rules} rowKey="id" loading={isLoading} pagination={false} />

      <Modal
        title="新建规则"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="trigger_event" label="触发事件" rules={[{ required: true }]}>
            <Select options={Object.entries(triggerLabels).map(([v, l]) => ({ value: v, label: l }))} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={0}>
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RuleList;
