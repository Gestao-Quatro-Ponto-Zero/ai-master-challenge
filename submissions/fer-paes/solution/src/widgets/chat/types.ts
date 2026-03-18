export interface ChatMessage {
  id: string;
  content: string;
  sender: 'customer' | 'system';
  timestamp: Date;
}

export interface ChatWidgetConfig {
  sessionId: string;
  name?: string;
  email?: string;
  phone?: string;
  title?: string;
  subtitle?: string;
  accentColor?: string;
}
