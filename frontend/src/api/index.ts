import client from './client';
import type { Ticket, TicketListResponse, TicketMessage, AuditLog, Label, User } from '../types';

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
    client.post<{ access_token: string; token_type: string }>('/auth/login', { email, password }).then((r) => r.data),
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
