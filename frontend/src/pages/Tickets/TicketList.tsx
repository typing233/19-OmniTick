import React, { useState } from 'react';
import { Table, Tag, Space, Select, Button, Modal, Form, Input, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { ticketApi, labelApi, userApi } from '../../api';
import type { Ticket, TicketStatus } from '../../types';

const STATUS_MAP: Record<TicketStatus, { color: string; label: string }> = {
  new: { color: 'blue', label: '新建' },
  in_progress: { color: 'orange', label: '处理中' },
  pending_response: { color: 'gold', label: '待回应' },
  resolved: { color: 'green', label: '已解决' },
  closed: { color: 'default', label: '已关闭' },
};

const PRIORITY_MAP: Record<string, { color: string; label: string }> = {
  low: { color: 'default', label: '低' },
  medium: { color: 'blue', label: '中' },
  high: { color: 'orange', label: '高' },
  urgent: { color: 'red', label: '紧急' },
};

const TicketList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [assigneeFilter, setAssigneeFilter] = useState<string | undefined>();
  const [labelFilter, setLabelFilter] = useState<string | undefined>();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['tickets', page, statusFilter, assigneeFilter, labelFilter],
    queryFn: () => ticketApi.list({ page, page_size: 20, status: statusFilter, assignee_id: assigneeFilter, label_id: labelFilter }),
  });

  const { data: labels } = useQuery({ queryKey: ['labels'], queryFn: labelApi.list });
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: userApi.list });

  const createMutation = useMutation({
    mutationFn: ticketApi.create,
    onSuccess: () => {
      message.success('工单创建成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
    },
  });

  const columns = [
    {
      title: '主题',
      dataIndex: 'subject',
      key: 'subject',
      ellipsis: true,
      render: (text: string, record: Ticket) => (
        <a onClick={() => navigate(`/tickets/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TicketStatus) => {
        const s = STATUS_MAP[status];
        return <Tag color={s.color}>{s.label}</Tag>;
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => {
        const p = PRIORITY_MAP[priority];
        return <Tag color={p.color}>{p.label}</Tag>;
      },
    },
    {
      title: '处理人',
      key: 'assignee',
      width: 120,
      render: (_: unknown, record: Ticket) => record.assignee?.display_name || '-',
    },
    {
      title: '标签',
      key: 'labels',
      width: 200,
      render: (_: unknown, record: Ticket) => (
        <Space size={[0, 4]} wrap>
          {record.labels.map((l) => <Tag key={l.id} color={l.color}>{l.name}</Tag>)}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <Select
          allowClear placeholder="状态筛选" style={{ width: 140 }}
          value={statusFilter} onChange={setStatusFilter}
          options={Object.entries(STATUS_MAP).map(([k, v]) => ({ value: k, label: v.label }))}
        />
        <Select
          allowClear placeholder="处理人筛选" style={{ width: 160 }}
          value={assigneeFilter} onChange={setAssigneeFilter}
          options={users?.map((u) => ({ value: u.id, label: u.display_name })) || []}
        />
        <Select
          allowClear placeholder="标签筛选" style={{ width: 160 }}
          value={labelFilter} onChange={setLabelFilter}
          options={labels?.map((l) => ({ value: l.id, label: l.name })) || []}
        />
        <div style={{ flex: 1 }} />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          创建工单
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items || []}
        loading={isLoading}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.total || 0,
          onChange: setPage,
          showTotal: (total) => `共 ${total} 条`,
        }}
        onRow={(record) => ({ onClick: () => navigate(`/tickets/${record.id}`), style: { cursor: 'pointer' } })}
      />

      <Modal
        title="创建工单" open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => createMutation.mutate(v)}>
          <Form.Item name="subject" label="主题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="requester_email" label="请求者邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select options={Object.entries(PRIORITY_MAP).map(([k, v]) => ({ value: k, label: v.label }))} />
          </Form.Item>
          <Form.Item name="assignee_id" label="处理人">
            <Select allowClear options={users?.map((u) => ({ value: u.id, label: u.display_name })) || []} />
          </Form.Item>
          <Form.Item name="label_ids" label="标签">
            <Select mode="multiple" options={labels?.map((l) => ({ value: l.id, label: l.name })) || []} />
          </Form.Item>
          <Form.Item name="body" label="描述">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TicketList;
