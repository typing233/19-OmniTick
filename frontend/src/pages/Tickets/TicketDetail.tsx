import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Descriptions, Tag, Button, Space, Select, Tabs, Timeline,
  Input, message, Popconfirm, Spin, Divider,
} from 'antd';
import {
  ArrowLeftOutlined, SendOutlined, DeleteOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { ticketApi, labelApi, userApi } from '../../api';
import type { TicketStatus, TicketMessage, AuditLog } from '../../types';

const STATUS_MAP: Record<TicketStatus, { color: string; label: string }> = {
  new: { color: 'blue', label: '新建' },
  in_progress: { color: 'orange', label: '处理中' },
  pending_response: { color: 'gold', label: '待回应' },
  resolved: { color: 'green', label: '已解决' },
  closed: { color: 'default', label: '已关闭' },
};

const TRANSITIONS: Record<TicketStatus, { value: TicketStatus; label: string }[]> = {
  new: [{ value: 'in_progress', label: '开始处理' }, { value: 'closed', label: '关闭' }],
  in_progress: [{ value: 'pending_response', label: '等待回应' }, { value: 'resolved', label: '标记解决' }, { value: 'closed', label: '关闭' }],
  pending_response: [{ value: 'in_progress', label: '继续处理' }, { value: 'resolved', label: '标记解决' }, { value: 'closed', label: '关闭' }],
  resolved: [{ value: 'in_progress', label: '重新打开' }, { value: 'closed', label: '关闭' }],
  closed: [{ value: 'in_progress', label: '重新打开' }],
};

const TicketDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [replyText, setReplyText] = useState('');

  const { data: ticket, isLoading } = useQuery({
    queryKey: ['ticket', id],
    queryFn: () => ticketApi.get(id!),
    enabled: !!id,
  });

  const { data: messages } = useQuery({
    queryKey: ['ticket-messages', id],
    queryFn: () => ticketApi.getMessages(id!),
    enabled: !!id,
  });

  const { data: auditLog } = useQuery({
    queryKey: ['ticket-audit', id],
    queryFn: () => ticketApi.getAuditLog(id!),
    enabled: !!id,
  });

  const { data: labels } = useQuery({ queryKey: ['labels'], queryFn: labelApi.list });
  const { data: users } = useQuery({ queryKey: ['users'], queryFn: userApi.list });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['ticket', id] });
    queryClient.invalidateQueries({ queryKey: ['ticket-messages', id] });
    queryClient.invalidateQueries({ queryKey: ['ticket-audit', id] });
  };

  const transitionMutation = useMutation({
    mutationFn: (status: string) => ticketApi.transition(id!, status),
    onSuccess: () => { message.success('状态已更新'); invalidate(); },
  });

  const assignMutation = useMutation({
    mutationFn: (assigneeId: string | null) => ticketApi.assign(id!, assigneeId),
    onSuccess: () => { message.success('已指派'); invalidate(); },
  });

  const labelMutation = useMutation({
    mutationFn: (labelIds: string[]) => ticketApi.attachLabels(id!, labelIds),
    onSuccess: () => { message.success('标签已更新'); invalidate(); },
  });

  const detachLabelMutation = useMutation({
    mutationFn: (labelId: string) => ticketApi.detachLabel(id!, labelId),
    onSuccess: () => { invalidate(); },
  });

  const replyMutation = useMutation({
    mutationFn: () => ticketApi.createMessage(id!, { body_text: replyText, direction: 'outbound' }),
    onSuccess: () => { message.success('回复已发送'); setReplyText(''); invalidate(); },
  });

  const deleteMutation = useMutation({
    mutationFn: () => ticketApi.delete(id!),
    onSuccess: () => { message.success('工单已删除'); navigate('/tickets'); },
  });

  if (isLoading || !ticket) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const statusInfo = STATUS_MAP[ticket.status];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tickets')}>返回</Button>
        <h2 style={{ margin: 0, flex: 1 }}>{ticket.subject}</h2>
        <Popconfirm title="确认删除此工单?" onConfirm={() => deleteMutation.mutate()}>
          <Button danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={3} size="small">
          <Descriptions.Item label="状态">
            <Tag color={statusInfo.color}>{statusInfo.label}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag>{ticket.priority}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="请求者">{ticket.requester_email || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{dayjs(ticket.created_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{dayjs(ticket.updated_at).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
        </Descriptions>

        <Divider style={{ margin: '12px 0' }} />

        <Space wrap size={[8, 8]}>
          <span>状态流转:</span>
          {TRANSITIONS[ticket.status]?.map((t) => (
            <Button key={t.value} size="small" onClick={() => transitionMutation.mutate(t.value)}>
              {t.label}
            </Button>
          ))}
        </Space>

        <Divider style={{ margin: '12px 0' }} />

        <Space size={16} wrap>
          <span>指派处理人:</span>
          <Select
            allowClear placeholder="选择处理人" style={{ width: 180 }}
            value={ticket.assignee_id}
            onChange={(v) => assignMutation.mutate(v || null)}
            options={users?.map((u) => ({ value: u.id, label: u.display_name })) || []}
          />

          <span>标签:</span>
          <Space size={[4, 4]} wrap>
            {ticket.labels.map((l) => (
              <Tag
                key={l.id} color={l.color} closable
                onClose={(e) => { e.preventDefault(); detachLabelMutation.mutate(l.id); }}
              >
                {l.name}
              </Tag>
            ))}
          </Space>
          <Select
            placeholder="添加标签" style={{ width: 140 }}
            value={undefined}
            onChange={(v) => { if (v) labelMutation.mutate([v]); }}
            options={labels?.filter((l) => !ticket.labels.find((tl) => tl.id === l.id))
              .map((l) => ({ value: l.id, label: l.name })) || []}
          />
        </Space>
      </Card>

      <Tabs items={[
        {
          key: 'conversation',
          label: '会话记录',
          children: (
            <div>
              <div style={{ maxHeight: 500, overflow: 'auto', marginBottom: 16 }}>
                {messages?.map((msg: TicketMessage) => (
                  <div
                    key={msg.id}
                    style={{
                      padding: 12,
                      marginBottom: 8,
                      borderRadius: 8,
                      background: msg.direction === 'outbound' ? '#e6f7ff' : '#f6f6f6',
                      marginLeft: msg.direction === 'outbound' ? 60 : 0,
                      marginRight: msg.direction === 'inbound' ? 60 : 0,
                    }}
                  >
                    <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>
                      <strong>{msg.sender_type === 'agent' ? '客服' : '客户'}</strong>
                      {msg.sender_email && ` <${msg.sender_email}>`}
                      <span style={{ float: 'right' }}>{dayjs(msg.created_at).format('YYYY-MM-DD HH:mm')}</span>
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{msg.body_text}</div>
                  </div>
                ))}
                {(!messages || messages.length === 0) && <div style={{ color: '#999', textAlign: 'center' }}>暂无会话记录</div>}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Input.TextArea
                  rows={3} value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="输入回复内容..."
                />
                <Button
                  type="primary" icon={<SendOutlined />}
                  onClick={() => replyMutation.mutate()}
                  loading={replyMutation.isPending}
                  disabled={!replyText.trim()}
                  style={{ alignSelf: 'flex-end' }}
                >
                  发送
                </Button>
              </div>
            </div>
          ),
        },
        {
          key: 'audit',
          label: '操作记录',
          children: (
            <Timeline
              items={auditLog?.map((log: AuditLog) => ({
                children: (
                  <div>
                    <strong>{formatAction(log.action)}</strong>
                    {log.field_name && (
                      <span>: {log.old_value || '-'} → {log.new_value || '-'}</span>
                    )}
                    <div style={{ fontSize: 12, color: '#999' }}>
                      {dayjs(log.created_at).format('YYYY-MM-DD HH:mm:ss')}
                    </div>
                  </div>
                ),
              })) || []}
            />
          ),
        },
      ]} />
    </div>
  );
};

function formatAction(action: string): string {
  const map: Record<string, string> = {
    created: '创建工单',
    created_from_email: '从邮件创建',
    status_change: '状态变更',
    assign: '指派处理人',
    field_change: '字段修改',
    label_add: '添加标签',
    label_remove: '移除标签',
    reply: '回复',
  };
  return map[action] || action;
}

export default TicketDetail;
