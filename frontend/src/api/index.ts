import client from './client';
import type {
  Ticket, TicketListResponse, TicketMessage, AuditLog, Label, User,
  KBArticle, KBArticleListResponse, KBCategory, KBTag, KBVersion, KBReview,
  SearchResponse, AutomationRule, AutomationLogListResponse, SlaPolicy,
} from '../types';

export interface EmailAccount {
  id: string;
  name: string;
  email_address: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  username: string;
  is_active: boolean;
  poll_interval_seconds: number;
  last_polled_at: string | null;
  created_at: string;
}

export interface TicketFilters {
  page?: number;
  page_size?: number;
  status?: string;
  assignee_id?: string;
  label_id?: string;
}

export const ticketApi = {
  list: (filters: TicketFilters) =>
    client.get<TicketListResponse>('/tickets', { params: filters }).then((r) => r.data),
  get: (id: string) => client.get<Ticket>(`/tickets/${id}`).then((r) => r.data),
  create: (data: { subject: string; priority?: string; assignee_id?: string; requester_email?: string; body?: string; label_ids?: string[] }) =>
    client.post<Ticket>('/tickets', data).then((r) => r.data),
  update: (id: string, data: { subject?: string; priority?: string; requester_email?: string; email_account_id?: string }) =>
    client.patch<Ticket>(`/tickets/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/tickets/${id}`),
  transition: (id: string, status: string) =>
    client.post<Ticket>(`/tickets/${id}/transition`, { status }).then((r) => r.data),
  assign: (id: string, assignee_id: string | null) =>
    client.post<Ticket>(`/tickets/${id}/assign`, { assignee_id }).then((r) => r.data),
  attachLabels: (id: string, label_ids: string[]) =>
    client.post<Ticket>(`/tickets/${id}/labels`, { label_ids }).then((r) => r.data),
  detachLabel: (id: string, labelId: string) =>
    client.delete<Ticket>(`/tickets/${id}/labels/${labelId}`).then((r) => r.data),
  getMessages: (id: string) =>
    client.get<TicketMessage[]>(`/tickets/${id}/messages`).then((r) => r.data),
  createMessage: (id: string, data: { body_text: string; body_html?: string; direction?: string }) =>
    client.post<TicketMessage>(`/tickets/${id}/messages`, data).then((r) => r.data),
  getAuditLog: (id: string) =>
    client.get<AuditLog[]>(`/tickets/${id}/audit-log`).then((r) => r.data),
};

export const labelApi = {
  list: () => client.get<Label[]>('/labels').then((r) => r.data),
  create: (data: { name: string; color?: string }) => client.post<Label>('/labels', data).then((r) => r.data),
  update: (id: string, data: { name?: string; color?: string }) => client.patch<Label>(`/labels/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/labels/${id}`),
};

export const userApi = {
  list: () => client.get<User[]>('/users').then((r) => r.data),
  create: (data: { email: string; display_name: string; password: string }) =>
    client.post<User>('/users', data).then((r) => r.data),
};

export const authApi = {
  login: (email: string, password: string) =>
    client.post<{ access_token: string }>('/auth/login', { email, password }).then((r) => r.data),
  me: () => client.get<User>('/auth/me').then((r) => r.data),
};

export const emailAccountApi = {
  list: () => client.get<EmailAccount[]>('/email-accounts').then((r) => r.data),
  create: (data: { name: string; email_address: string; imap_host: string; imap_port?: number; smtp_host: string; smtp_port?: number; username: string; password: string; poll_interval_seconds?: number }) =>
    client.post<EmailAccount>('/email-accounts', data).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    client.patch<EmailAccount>(`/email-accounts/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/email-accounts/${id}`),
};

export const kbApi = {
  listArticles: (params?: { page?: number; page_size?: number; status?: string; category_id?: string; tag_id?: string }) =>
    client.get<KBArticleListResponse>('/kb/articles', { params }).then((r) => r.data),
  getArticle: (id: string) => client.get<KBArticle>(`/kb/articles/${id}`).then((r) => r.data),
  createArticle: (data: { title: string; slug: string; body_markdown?: string; body_html?: string; category_id?: string; visibility?: string; tag_ids?: string[] }) =>
    client.post<KBArticle>('/kb/articles', data).then((r) => r.data),
  updateArticle: (id: string, data: { title?: string; slug?: string; body_markdown?: string; body_html?: string; category_id?: string; visibility?: string; tag_ids?: string[]; change_summary?: string }) =>
    client.patch<KBArticle>(`/kb/articles/${id}`, data).then((r) => r.data),
  deleteArticle: (id: string) => client.delete(`/kb/articles/${id}`),
  listVersions: (id: string) => client.get<KBVersion[]>(`/kb/articles/${id}/versions`).then((r) => r.data),
  getVersion: (id: string, v: number) => client.get<KBVersion>(`/kb/articles/${id}/versions/${v}`).then((r) => r.data),
  rollback: (id: string, version_number: number) =>
    client.post<KBArticle>(`/kb/articles/${id}/rollback`, { version_number }).then((r) => r.data),
  submitReview: (id: string) => client.post<KBReview>(`/kb/articles/${id}/submit-review`).then((r) => r.data),
  approve: (id: string, comment?: string) =>
    client.post<KBArticle>(`/kb/articles/${id}/approve`, { comment }).then((r) => r.data),
  reject: (id: string, comment?: string) =>
    client.post<KBArticle>(`/kb/articles/${id}/reject`, { comment }).then((r) => r.data),
  listPendingReviews: () => client.get<KBReview[]>('/kb/articles/reviews/pending').then((r) => r.data),
  getAuditLog: (id: string) => client.get<Array<{ id: string; article_id: string; actor_id: string | null; action: string; detail: string | null; created_at: string }>>(`/kb/articles/${id}/audit-log`).then((r) => r.data),
  listCategories: () => client.get<KBCategory[]>('/kb/categories').then((r) => r.data),
  createCategory: (data: { name: string; slug: string; parent_id?: string; sort_order?: number }) =>
    client.post<KBCategory>('/kb/categories', data).then((r) => r.data),
  updateCategory: (id: string, data: { name?: string; slug?: string; parent_id?: string; sort_order?: number }) =>
    client.patch<KBCategory>(`/kb/categories/${id}`, data).then((r) => r.data),
  deleteCategory: (id: string) => client.delete(`/kb/categories/${id}`),
  listTags: () => client.get<KBTag[]>('/kb/tags').then((r) => r.data),
  createTag: (data: { name: string }) => client.post<KBTag>('/kb/tags', data).then((r) => r.data),
  deleteTag: (id: string) => client.delete(`/kb/tags/${id}`),
};

export const searchApi = {
  search: (data: { query: string; scope?: string; mode?: string; page?: number; page_size?: number; filters?: Record<string, unknown> }) =>
    client.post<SearchResponse>('/search', data).then((r) => r.data),
};

export const automationApi = {
  listRules: () => client.get<AutomationRule[]>('/automation/rules').then((r) => r.data),
  getRule: (id: string) => client.get<AutomationRule>(`/automation/rules/${id}`).then((r) => r.data),
  createRule: (data: { name: string; trigger_event: string; conditions?: Record<string, unknown>; actions?: Array<Record<string, unknown>>; priority?: number; is_active?: boolean; description?: string }) =>
    client.post<AutomationRule>('/automation/rules', data).then((r) => r.data),
  updateRule: (id: string, data: Partial<AutomationRule>) =>
    client.patch<AutomationRule>(`/automation/rules/${id}`, data).then((r) => r.data),
  deleteRule: (id: string) => client.delete(`/automation/rules/${id}`),
  listLogs: (params?: { page?: number; page_size?: number; rule_id?: string; ticket_id?: string }) =>
    client.get<AutomationLogListResponse>('/automation/logs', { params }).then((r) => r.data),
  listSlaPolicies: () => client.get<SlaPolicy[]>('/automation/sla-policies').then((r) => r.data),
  createSlaPolicy: (data: { name: string; conditions?: Record<string, unknown>; first_response_minutes?: number; resolution_minutes?: number; is_active?: boolean }) =>
    client.post<SlaPolicy>('/automation/sla-policies', data).then((r) => r.data),
  updateSlaPolicy: (id: string, data: Partial<SlaPolicy>) =>
    client.patch<SlaPolicy>(`/automation/sla-policies/${id}`, data).then((r) => r.data),
  deleteSlaPolicy: (id: string) => client.delete(`/automation/sla-policies/${id}`),
};
