import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Form, Input, Select, Button, Space, Tag, message, Tabs, List, Modal } from 'antd';
import { SaveOutlined, RollbackOutlined, SendOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { kbApi } from '../../api';
import type { KBVersion } from '../../types';

const { TextArea } = Input;

const ArticleEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [rollbackVersion, setRollbackVersion] = useState<number | null>(null);

  const { data: article, isLoading } = useQuery({
    queryKey: ['kb-article', id],
    queryFn: () => kbApi.getArticle(id!),
    enabled: !!id,
  });

  const { data: versions } = useQuery({
    queryKey: ['kb-article-versions', id],
    queryFn: () => kbApi.listVersions(id!),
    enabled: !!id,
  });

  const { data: categories } = useQuery({
    queryKey: ['kb-categories'],
    queryFn: kbApi.listCategories,
  });

  const { data: tags } = useQuery({
    queryKey: ['kb-tags'],
    queryFn: kbApi.listTags,
  });

  useEffect(() => {
    if (article) {
      form.setFieldsValue({
        title: article.title,
        slug: article.slug,
        body_markdown: article.body_markdown,
        category_id: article.category_id,
        visibility: article.visibility,
        tag_ids: article.tags.map(t => t.id),
      });
    }
  }, [article, form]);

  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => kbApi.updateArticle(id!, values),
    onSuccess: () => {
      message.success('保存成功');
      queryClient.invalidateQueries({ queryKey: ['kb-article', id] });
      queryClient.invalidateQueries({ queryKey: ['kb-article-versions', id] });
    },
  });

  const submitReviewMutation = useMutation({
    mutationFn: () => kbApi.submitReview(id!),
    onSuccess: () => {
      message.success('已提交审核');
      queryClient.invalidateQueries({ queryKey: ['kb-article', id] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => kbApi.approve(id!),
    onSuccess: () => {
      message.success('已审核通过');
      queryClient.invalidateQueries({ queryKey: ['kb-article', id] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => kbApi.reject(id!),
    onSuccess: () => {
      message.success('已驳回');
      queryClient.invalidateQueries({ queryKey: ['kb-article', id] });
    },
  });

  const rollbackMutation = useMutation({
    mutationFn: (version_number: number) => kbApi.rollback(id!, version_number),
    onSuccess: () => {
      message.success('回滚成功');
      setRollbackVersion(null);
      queryClient.invalidateQueries({ queryKey: ['kb-article', id] });
      queryClient.invalidateQueries({ queryKey: ['kb-article-versions', id] });
    },
  });

  const flattenCategories = (cats: typeof categories, level = 0): { value: string; label: string }[] => {
    if (!cats) return [];
    const result: { value: string; label: string }[] = [];
    for (const cat of cats) {
      result.push({ value: cat.id, label: '  '.repeat(level) + cat.name });
      if (cat.children) {
        result.push(...flattenCategories(cat.children, level + 1));
      }
    }
    return result;
  };

  if (isLoading) return null;

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button onClick={() => navigate('/kb')}>返回列表</Button>
          <Tag>{article?.status === 'draft' ? '草稿' : article?.status === 'in_review' ? '审核中' : article?.status === 'published' ? '已发布' : '已归档'}</Tag>
          <span>版本 {article?.current_version}</span>
        </Space>
        <Space>
          {article?.status === 'draft' && (
            <Button icon={<SendOutlined />} onClick={() => submitReviewMutation.mutate()}>提交审核</Button>
          )}
          {article?.status === 'in_review' && (
            <>
              <Button type="primary" icon={<CheckOutlined />} onClick={() => approveMutation.mutate()}>通过</Button>
              <Button danger icon={<CloseOutlined />} onClick={() => rejectMutation.mutate()}>驳回</Button>
            </>
          )}
          <Button type="primary" icon={<SaveOutlined />} onClick={() => form.submit()}>保存</Button>
        </Space>
      </div>

      <Tabs items={[
        {
          key: 'edit',
          label: '编辑',
          children: (
            <Card>
              <Form form={form} layout="vertical" onFinish={(v) => saveMutation.mutate(v)}>
                <Form.Item name="title" label="标题" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="slug" label="URL标识">
                  <Input />
                </Form.Item>
                <Form.Item name="category_id" label="分类">
                  <Select allowClear placeholder="选择分类" options={flattenCategories(categories)} />
                </Form.Item>
                <Form.Item name="visibility" label="可见性">
                  <Select options={[{ value: 'public', label: '公开' }, { value: 'internal', label: '内部' }]} />
                </Form.Item>
                <Form.Item name="tag_ids" label="标签">
                  <Select mode="multiple" placeholder="选择标签" options={tags?.map(t => ({ value: t.id, label: t.name }))} />
                </Form.Item>
                <Form.Item name="body_markdown" label="内容 (Markdown)">
                  <TextArea rows={20} style={{ fontFamily: 'monospace' }} />
                </Form.Item>
                <Form.Item name="change_summary" label="变更说明">
                  <Input placeholder="描述此次修改..." />
                </Form.Item>
              </Form>
            </Card>
          ),
        },
        {
          key: 'versions',
          label: '版本历史',
          children: (
            <Card>
              <List
                dataSource={versions}
                renderItem={(v: KBVersion) => (
                  <List.Item
                    actions={[
                      <Button
                        size="small"
                        icon={<RollbackOutlined />}
                        onClick={() => setRollbackVersion(v.version_number)}
                      >
                        回滚
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={`版本 ${v.version_number} - ${v.title}`}
                      description={`${v.change_summary || '无说明'} | ${new Date(v.created_at).toLocaleString()}`}
                    />
                  </List.Item>
                )}
              />
            </Card>
          ),
        },
      ]} />

      <Modal
        title="确认回滚"
        open={rollbackVersion !== null}
        onCancel={() => setRollbackVersion(null)}
        onOk={() => rollbackVersion && rollbackMutation.mutate(rollbackVersion)}
        confirmLoading={rollbackMutation.isPending}
      >
        确定要回滚到版本 {rollbackVersion} 吗？当前内容将被覆盖（但会保存为新版本）。
      </Modal>
    </div>
  );
};

export default ArticleEditor;
