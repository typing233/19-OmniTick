import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Form, Input, Select, Button, Space, message } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { automationApi } from '../../api';

const { TextArea } = Input;

const triggerOptions = [
  { value: 'on_ticket_create', label: '工单创建' },
  { value: 'on_ticket_update', label: '工单更新' },
  { value: 'on_status_change', label: '状态变更' },
  { value: 'on_sla_breach', label: 'SLA违约' },
  { value: 'on_time_elapsed', label: '时间触发' },
];

const RuleEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const isNew = !id || id === 'new';

  const { data: rule } = useQuery({
    queryKey: ['automation-rule', id],
    queryFn: () => automationApi.getRule(id!),
    enabled: !isNew,
  });

  useEffect(() => {
    if (rule) {
      form.setFieldsValue({
        name: rule.name,
        description: rule.description,
        trigger_event: rule.trigger_event,
        priority: rule.priority,
        conditions_json: JSON.stringify(rule.conditions, null, 2),
        actions_json: JSON.stringify(rule.actions, null, 2),
      });
    }
  }, [rule, form]);

  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      const payload = {
        name: values.name as string,
        description: values.description as string,
        trigger_event: values.trigger_event as string,
        priority: Number(values.priority),
        conditions: JSON.parse(values.conditions_json as string || '{}'),
        actions: JSON.parse(values.actions_json as string || '[]'),
      };
      if (isNew) return automationApi.createRule(payload);
      return automationApi.updateRule(id!, payload);
    },
    onSuccess: () => {
      message.success('保存成功');
      queryClient.invalidateQueries({ queryKey: ['automation-rules'] });
      if (isNew) navigate('/automation/rules');
    },
    onError: () => message.error('保存失败，请检查JSON格式'),
  });

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={() => navigate('/automation/rules')}>返回列表</Button>
        <Button type="primary" icon={<SaveOutlined />} onClick={() => form.submit()}>保存</Button>
      </div>

      <Card>
        <Form form={form} layout="vertical" onFinish={(v) => saveMutation.mutate(v)}>
          <Form.Item name="name" label="规则名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="trigger_event" label="触发事件" rules={[{ required: true }]}>
            <Select options={triggerOptions} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue={0}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="conditions_json" label="条件 (JSON)" initialValue="{}">
            <TextArea rows={8} style={{ fontFamily: 'monospace' }} placeholder='{"status": ["new"], "priority": "urgent"}' />
          </Form.Item>
          <Form.Item name="actions_json" label="动作 (JSON)" initialValue="[]">
            <TextArea rows={8} style={{ fontFamily: 'monospace' }} placeholder='[{"type": "assign", "params": {"assignee_id": "..."}}]' />
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default RuleEditor;
