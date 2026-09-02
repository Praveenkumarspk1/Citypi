export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  content_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface SendMessageParams {
  content: string;
  content_type?: string;
  attachments?: unknown[];
}

export interface Conversation {
  id: string;
  user_id: string;
  title: string | null;
  status: string;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}
