import type { AgentType, LLMProvider } from '../../types';

export const AGENT_TYPES: { value: AgentType; label: string }[] = [
  { value: 'triage_agent', label: 'Triage Agent' },
  { value: 'support_agent', label: 'Support Agent' },
  { value: 'technical_agent', label: 'Technical Agent' },
  { value: 'billing_agent', label: 'Billing Agent' },
  { value: 'sales_agent', label: 'Sales Agent' },
  { value: 'qa_agent', label: 'QA Agent' },
];

export const AGENT_TYPE_COLORS: Record<AgentType, string> = {
  triage_agent: 'bg-sky-500/15 text-sky-400 ring-sky-500/20',
  support_agent: 'bg-blue-500/15 text-blue-400 ring-blue-500/20',
  technical_agent: 'bg-orange-500/15 text-orange-400 ring-orange-500/20',
  billing_agent: 'bg-emerald-500/15 text-emerald-400 ring-emerald-500/20',
  sales_agent: 'bg-rose-500/15 text-rose-400 ring-rose-500/20',
  qa_agent: 'bg-amber-500/15 text-amber-400 ring-amber-500/20',
};

export const LLM_PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'google', label: 'Google' },
];

export const MODELS_BY_PROVIDER: Record<LLMProvider, string[]> = {
  openai: [
    'gpt-5.4',
    'gpt-5.4-pro',
    'gpt-5',
    'gpt-5-mini',
    'gpt-5-nano',
    'gpt-4.1',
    'gpt-4.1-mini',
    'gpt-4.1-nano',
    'o3',
    'o3-pro',
    'o4-mini',
  ],
  anthropic: [
    'claude-opus-4-6',
    'claude-sonnet-4-6',
    'claude-haiku-4-5',
  ],
  google: [
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-3.1-pro',
    'gemini-3-flash',
  ],
};

export const PROVIDER_COLORS: Record<LLMProvider, string> = {
  openai: 'bg-teal-500/15 text-teal-400',
  anthropic: 'bg-amber-500/15 text-amber-400',
  google: 'bg-blue-500/15 text-blue-400',
};

export const ALL_SKILLS = [
  { name: 'search_knowledge_base', label: 'Search Knowledge Base', description: 'Query the internal knowledge base for answers', category: 'knowledge' },
  { name: 'lookup_customer', label: 'Lookup Customer', description: 'Retrieve customer profile and history', category: 'customer' },
  { name: 'get_ticket_info', label: 'Get Ticket Info', description: 'Fetch detailed information about a support ticket', category: 'ticket' },
  { name: 'update_ticket_status', label: 'Update Ticket Status', description: 'Change the status of a support ticket', category: 'ticket' },
  { name: 'add_ticket_note', label: 'Add Ticket Note', description: 'Add an internal note to a ticket', category: 'ticket' },
  { name: 'create_ticket', label: 'Create Ticket', description: 'Open a new support ticket on behalf of a customer', category: 'ticket' },
  { name: 'lookup_order', label: 'Lookup Order', description: 'Retrieve order status and tracking information', category: 'order' },
  { name: 'escalate_to_human', label: 'Escalate to Human', description: 'Hand off the conversation to a human operator', category: 'system' },
];
