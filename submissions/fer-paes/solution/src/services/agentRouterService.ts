import { supabase } from '../lib/supabaseClient';
import type { RouterResult, RouteMessagePayload } from '../types';

const ROUTING_RULES: { keywords: string[]; agentType: string; label: string }[] = [
  {
    keywords: ['refund', 'payment', 'billing', 'invoice', 'charge', 'charged', 'overcharged', 'subscription', 'money back', 'cancel subscription'],
    agentType: 'billing_agent',
    label: 'Billing keywords',
  },
  {
    keywords: ['bug', 'error', 'not working', 'broken', 'crash', 'technical', 'issue', 'glitch', 'fix', '404', '500', 'outage', 'down'],
    agentType: 'technical_agent',
    label: 'Technical keywords',
  },
  {
    keywords: ['pricing', 'plans', 'buy', 'upgrade', 'discount', 'trial', 'demo', 'purchase', 'quote', 'enterprise'],
    agentType: 'sales_agent',
    label: 'Sales keywords',
  },
  {
    keywords: ['quality', 'test', 'testing', 'qa', 'review', 'check', 'verify', 'validation'],
    agentType: 'qa_agent',
    label: 'QA keywords',
  },
  {
    keywords: ['help', 'support', 'question', 'how to', 'how do', 'assist', 'info', 'information'],
    agentType: 'support_agent',
    label: 'Support keywords',
  },
];

export { ROUTING_RULES };

export async function routeMessage(payload: RouteMessagePayload): Promise<RouterResult> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;

  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const response = await fetch(`${supabaseUrl}/functions/v1/agent-router`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token ?? anonKey}`,
      'Apikey': anonKey,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(err.error ?? `Router returned ${response.status}`);
  }

  return response.json() as Promise<RouterResult>;
}

export function ruleRouterLocal(message: string): { agentType: string; matchedKeyword: string; rule: string } | null {
  const lower = message.toLowerCase();
  for (const rule of ROUTING_RULES) {
    const hit = rule.keywords.find((kw) => lower.includes(kw));
    if (hit) {
      return { agentType: rule.agentType, matchedKeyword: hit, rule: rule.label };
    }
  }
  return null;
}
