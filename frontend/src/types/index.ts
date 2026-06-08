export type TicketStatus = 'new' | 'in_progress' | 'pending_response' | 'resolved' | 'closed';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';

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
