import React, { useState } from 'react';
import { Table, Button, Tag, Space, Select, Input, Modal, Form, message } from 'antd';
import { PlusOutlined, EditOutlined, SendOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { kbApi } from '../../api';
import type { KBArticle, ArticleStatus } from '../../types';

const statusColors: Record<string, string> = {
  draft: 'default',
  in_review: 'processing',
  published: 'success',
  archived: 'warning',
};

const statusLabels: Record<string, string> = {
  draft: '草稿',
  in_review: '审核中',
  published: '已发布',
  archived: '已归档',
};

const ArticleList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['kb-articles', page, statusFilter],
    queryFn: () => kbApi.listArticles({ page, page_size: 20, status: statusFilter }),
  });

  const createMutation = useMutation({
    mutationFn: kbApi.createArticle,
    onSuccess: (article) => {
      message.success('文章创建成功');
      setCreateOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['kb-articles'] });
      navigate(`/kb/${article.id}/edit`);
    },
  });

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', render: (t: string, r: KBArticle) => <a onClick={() => navigate(`/kb/${r.id}/edit`)}>{t}</a> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: ArticleStatus) => <Tag color={statusColors[s]}>{statusLabels[s]}</Tag> },
    { title: '可见性', dataIndex: 'visibility', key: 'visibility', render: (v: string) => v === 'public' ? '公开' : '内部' },
    { title: '版本', dataIndex: 'current_version', key: 'version' },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', render: (d: string) => new Date(d).toLocaleString() },
    {
      title: '操作', key: 'actions', render: (_: unknown, r: KBArticle) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => navigate(`/kb/${r.id}/edit`)}>编辑</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Select
            placeholder="状态筛选"
            allowClear
            style={{ width: 140 }}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { value: 'draft', label: '草稿' },
              { value: 'in_review', label: '审核中' },
              { value: 'published', label: '已发布' },
              { value: 'archived', label: '已归档' },
            ]}
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          新建文章
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data?.items}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          total: data?.total,
          pageSize: 20,
          onChange: setPage,
        }}
      />

      <Modal
        title="新建文章"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(values) => createMutation.mutate(values)}>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="slug" label="URL标识" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="visibility" label="可见性" initialValue="public">
            <Select options={[{ value: 'public', label: '公开' }, { value: 'internal', label: '内部' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ArticleList;
