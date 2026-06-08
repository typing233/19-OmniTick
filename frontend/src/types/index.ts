export type TicketStatus = 'new' | 'in_progress' | 'pending_response' | 'resolved' | 'closed';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type ArticleStatus = 'draft' | 'in_review' | 'published' | 'archived';

export interface Label {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  role?: string;
  tenant_id?: string;
}

export interface Ticket {
  id: string;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  assignee_id: string | null;
  assignee: { id: string; display_name: string; email: string } | null;
  requester_email: string | null;
  email_account_id: string | null;
  labels: Label[];
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  sender_type: 'agent' | 'customer' | 'system';
  sender_id: string | null;
  sender_email: string | null;
  body_text: string;
  body_html: string | null;
  direction: 'inbound' | 'outbound' | 'internal';
  created_at: string;
}

export interface AuditLog {
  id: string;
  ticket_id: string;
  actor_id: string | null;
  action: string;
  field_name: string | null;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export interface KBCategory {
  id: string;
  tenant_id: string;
  parent_id: string | null;
  name: string;
  slug: string;
  sort_order: number;
  created_at: string;
  children?: KBCategory[];
}

export interface KBTag {
  id: string;
  name: string;
  created_at: string;
}

export interface KBArticle {
  id: string;
  tenant_id: string;
  category_id: string | null;
  author_id: string;
  title: string;
  slug: string;
  body_markdown: string;
  body_html: string;
  status: ArticleStatus;
  visibility: string;
  current_version: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  tags: KBTag[];
}

export interface KBArticleListResponse {
  items: KBArticle[];
  total: number;
  page: number;
  page_size: number;
}

export interface KBVersion {
  id: string;
  article_id: string;
  version_number: number;
  title: string;
  body_markdown: string;
  body_html: string;
  author_id: string;
  change_summary: string | null;
  created_at: string;
}

export interface KBReview {
  id: string;
  article_id: string;
  version_number: number;
  reviewer_id: string | null;
  status: string;
  comment: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface SearchResultItem {
  type: 'ticket' | 'article';
  id: string;
  title: string;
  snippet: string;
  score: number;
  metadata: Record<string, string>;
}

export interface SearchResponse {
  items: SearchResultItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AutomationRule {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  trigger_event: string;
  conditions: Record<string, unknown>;
  actions: Array<Record<string, unknown>>;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AutomationLog {
  id: string;
  rule_id: string;
  ticket_id: string;
  trigger_event: string;
  event_id: string;
  status: string;
  actions_executed: Record<string, unknown> | null;
  error_detail: string | null;
  execution_chain_depth: number;
  created_at: string;
}

export interface AutomationLogListResponse {
  items: AutomationLog[];
  total: number;
  page: number;
  page_size: number;
}

export interface SlaPolicy {
  id: string;
  tenant_id: string;
  name: string;
  conditions: Record<string, unknown>;
  first_response_minutes: number | null;
  resolution_minutes: number | null;
  is_active: boolean;
  created_at: string;
}
