import portalClient from './portalClient';

export interface PortalTicket {
  id: string;
  subject: string;
  status: string;
  priority: string;
  requester_email: string | null;
  created_at: string;
  updated_at: string;
}

export interface PortalMessage {
  id: string;
  sender_type: string;
  body_text: string | null;
  body_html: string | null;
  created_at: string;
}

export interface PortalArticle {
  id: string;
  title: string;
  slug: string;
  body_html: string;
  category_id: string | null;
  published_at: string | null;
}

export const portalAuthApi = {
  register: (data: { email: string; password: string; display_name?: string }) =>
    portalClient.post<{ access_token: string }>('/portal/auth/register', data).then(r => r.data),
  login: (data: { email: string; password: string }) =>
    portalClient.post<{ access_token: string }>('/portal/auth/login', data).then(r => r.data),
  me: () => portalClient.get('/portal/auth/me').then(r => r.data),
};

export const portalTicketApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    portalClient.get<{ items: PortalTicket[]; total: number; page: number; page_size: number }>('/portal/tickets', { params }).then(r => r.data),
  create: (data: { subject: string; body: string }) =>
    portalClient.post<PortalTicket>('/portal/tickets', data).then(r => r.data),
  createGuest: (data: { email: string; subject: string; body: string }) =>
    portalClient.post<PortalTicket>('/portal/tickets/guest', data).then(r => r.data),
  get: (id: string) => portalClient.get<PortalTicket>(`/portal/tickets/${id}`).then(r => r.data),
  getMessages: (id: string) => portalClient.get<PortalMessage[]>(`/portal/tickets/${id}/messages`).then(r => r.data),
  reply: (id: string, body_text: string) =>
    portalClient.post<PortalMessage>(`/portal/tickets/${id}/reply`, { body_text }).then(r => r.data),
};

export const portalKbApi = {
  listArticles: (params?: { page?: number; page_size?: number; category_id?: string }) =>
    portalClient.get<{ items: PortalArticle[]; total: number; page: number; page_size: number }>('/portal/kb/articles', { params }).then(r => r.data),
  getArticle: (slug: string) => portalClient.get<PortalArticle>(`/portal/kb/articles/${slug}`).then(r => r.data),
  listCategories: () => portalClient.get('/portal/kb/categories').then(r => r.data),
  search: (data: { query: string; page?: number; page_size?: number }) =>
    portalClient.post('/portal/kb/search', data).then(r => r.data),
};
