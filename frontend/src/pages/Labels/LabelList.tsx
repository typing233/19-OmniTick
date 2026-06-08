import React, { useState } from 'react';
import { Table, Button, Modal, Form, Input, ColorPicker, message, Space, Tag, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { labelApi } from '../../api';
import type { Label } from '../../types';

const LabelList: React.FC = () => {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingLabel, setEditingLabel] = useState<Label | null>(null);
  const [form] = Form.useForm();

  const { data: labels, isLoading } = useQuery({ queryKey: ['labels'], queryFn: labelApi.list });

  const createMutation = useMutation({
    mutationFn: labelApi.create,
    onSuccess: () => { message.success('标签已创建'); closeModal(); queryClient.invalidateQueries({ queryKey: ['labels'] }); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; color?: string }) => labelApi.update(id, data),
    onSuccess: () => { message.success('标签已更新'); closeModal(); queryClient.invalidateQueries({ queryKey: ['labels'] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: labelApi.delete,
    onSuccess: () => { message.success('标签已删除'); queryClient.invalidateQueries({ queryKey: ['labels'] }); },
  });

  const closeModal = () => { setModalOpen(false); setEditingLabel(null); form.resetFields(); };

  const openEdit = (label: Label) => {
    setEditingLabel(label);
    form.setFieldsValue({ name: label.name, color: label.color });
    setModalOpen(true);
  };

  const onFinish = (values: { name: string; color: string }) => {
    const color = typeof values.color === 'string' ? values.color : (values.color as any)?.toHexString?.() || '#1677ff';
    if (editingLabel) {
      updateMutation.mutate({ id: editingLabel.id, name: values.name, color });
    } else {
      createMutation.mutate({ name: values.name, color });
    }
  };

  const columns = [
    {
      title: '标签名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Label) => <Tag color={record.color}>{name}</Tag>,
    },
    {
      title: '颜色',
      dataIndex: 'color',
      key: 'color',
      width: 100,
      render: (color: string) => (
        <div style={{ width: 24, height: 24, borderRadius: 4, background: color }} />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: unknown, record: Label) => (
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
        <h3 style={{ margin: 0 }}>标签管理</h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          创建标签
        </Button>
      </div>
      <Table rowKey="id" columns={columns} dataSource={labels || []} loading={isLoading} pagination={false} />

      <Modal
        title={editingLabel ? '编辑标签' : '创建标签'}
        open={modalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="color" label="颜色" initialValue="#1677ff">
            <ColorPicker format="hex" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LabelList;
