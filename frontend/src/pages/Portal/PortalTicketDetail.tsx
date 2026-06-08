import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Tag, Button, Input, List, Descriptions, message, Spin } from 'antd';
import { ArrowLeftOutlined, SendOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { portalTicketApi } from '../../api/portal';

const { TextArea } = Input;

const statusLabels: Record<string, string> = {
  new: '新建', in_progress: '处理中', pending_response: '等待回复', resolved: '已解决', closed: '已关闭',
};

const PortalTicketDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [replyText, setReplyText] = useState('');

  const { data: ticket, isLoading } = useQuery({
    queryKey: ['portal-ticket', id],
    queryFn: () => portalTicketApi.get(id!),
    enabled: !!id,
  });

  const { data: messages } = useQuery({
    queryKey: ['portal-ticket-messages', id],
    queryFn: () => portalTicketApi.getMessages(id!),
    enabled: !!id,
  });

  const replyMutation = useMutation({
    mutationFn: () => portalTicketApi.reply(id!, replyText),
    onSuccess: () => {
      message.success('回复发送成功');
      setReplyText('');
      queryClient.invalidateQueries({ queryKey: ['portal-ticket-messages', id] });
    },
  });

  if (isLoading) return <Spin />;
  if (!ticket) return null;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/portal/tickets')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card title={ticket.subject} extra={<Tag>{statusLabels[ticket.status] || ticket.status}</Tag>}>
        <Descriptions column={2}>
          <Descriptions.Item label="状态">{statusLabels[ticket.status]}</Descriptions.Item>
          <Descriptions.Item label="优先级">{ticket.priority}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(ticket.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{new Date(ticket.updated_at).toLocaleString()}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="沟通记录" style={{ marginTop: 16 }}>
        <List
          dataSource={messages}
          renderItem={(msg) => (
            <List.Item>
              <div style={{
                width: '100%',
                textAlign: msg.sender_type === 'customer' ? 'right' : 'left',
              }}>
                <div style={{
                  display: 'inline-block',
                  padding: '8px 16px',
                  borderRadius: 8,
                  background: msg.sender_type === 'customer' ? '#e6f7ff' : '#f5f5f5',
                  maxWidth: '70%',
                  textAlign: 'left',
                }}>
                  <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>
                    {msg.sender_type === 'customer' ? '我' : '客服'} · {new Date(msg.created_at).toLocaleString()}
                  </div>
                  <div>{msg.body_text}</div>
                </div>
              </div>
            </List.Item>
          )}
        />

        {ticket.status !== 'closed' && (
          <div style={{ marginTop: 16 }}>
            <TextArea
              rows={3}
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="输入回复内容..."
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={() => replyMutation.mutate()}
              loading={replyMutation.isPending}
              disabled={!replyText.trim()}
              style={{ marginTop: 8 }}
            >
              发送
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default PortalTicketDetail;
