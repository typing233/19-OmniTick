import React, { useState } from 'react';
import { Card, List, Input, Empty, Spin, Button, Modal, Form, message } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { portalKbApi, portalTicketApi } from '../../api/portal';

const { Search } = Input;
const { TextArea } = Input;

const PortalKBHome: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [submitOpen, setSubmitOpen] = useState(false);
  const [form] = Form.useForm();

  const hasToken = !!localStorage.getItem('portal_token');

  const { data: articles, isLoading } = useQuery({
    queryKey: ['portal-kb-articles'],
    queryFn: () => portalKbApi.listArticles({ page: 1, page_size: 50 }),
  });

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ['portal-kb-search', searchQuery],
    queryFn: () => portalKbApi.search({ query: searchQuery }),
    enabled: searchQuery.length > 0,
  });

  const guestSubmitMutation = useMutation({
    mutationFn: portalTicketApi.createGuest,
    onSuccess: () => {
      message.success('工单提交成功，我们会通过邮件回复您');
      setSubmitOpen(false);
      form.resetFields();
    },
  });

  const displayItems = searchQuery && searchResults ? searchResults.items : articles?.items;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>帮助中心</h2>
        {!hasToken && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setSubmitOpen(true)}>
            提交工单
          </Button>
        )}
      </div>

      <Search
        placeholder="搜索文章..."
        size="large"
        enterButton={<><SearchOutlined /> 搜索</>}
        onSearch={setSearchQuery}
        style={{ marginBottom: 24 }}
      />

      {isLoading || searching ? (
        <Spin />
      ) : displayItems && displayItems.length > 0 ? (
        <List
          grid={{ gutter: 16, column: 2 }}
          dataSource={displayItems}
          renderItem={(item: { title: string; slug: string; snippet?: string }) => (
            <List.Item>
              <Card
                hoverable
                onClick={() => navigate(`/portal/kb/${item.slug}`)}
                style={{ height: '100%' }}
              >
                <Card.Meta
                  title={item.title}
                  description={item.snippet ? <span dangerouslySetInnerHTML={{ __html: item.snippet }} /> : null}
                />
              </Card>
            </List.Item>
          )}
        />
      ) : (
        <Empty description="暂无文章" />
      )}

      <Modal
        title="提交工单（访客）"
        open={submitOpen}
        onCancel={() => setSubmitOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={guestSubmitMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={(v) => guestSubmitMutation.mutate(v)}>
          <Form.Item name="email" label="您的邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="用于接收回复" />
          </Form.Item>
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

export default PortalKBHome;
