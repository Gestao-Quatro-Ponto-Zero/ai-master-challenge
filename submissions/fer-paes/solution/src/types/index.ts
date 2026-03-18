export interface Profile {
  id: string;
  full_name: string;
  email: string;
  avatar_url: string | null;
  status: string;
  department: string;
  phone: string;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface UserWithProfile {
  id: string;
  email: string;
  status: string;
  profile: Profile | null;
  roles: Role[];
}

export type UserStatus = 'active' | 'suspended' | 'invited';

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  category: string;
  created_at: string;
}

export interface RolePermission {
  role_id: string;
  permission_id: string;
}

export interface UserRole {
  user_id: string;
  role_id: string;
  assigned_by: string | null;
  assigned_at: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource: string;
  resource_id: string | null;
  meta: Record<string, unknown> | null;
  created_at: string;
}

export interface AuthUser {
  id: string;
  email: string;
}

export interface AuthState {
  user: AuthUser | null;
  profile: Profile | null;
  roles: Role[];
  permissions: Permission[];
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthPayload {
  user: AuthUser;
  profile: Profile | null;
  roles: Role[];
  permissions: Permission[];
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[];
}

export type TicketStatus = 'open' | 'in_progress' | 'waiting_customer' | 'resolved' | 'closed';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type ChannelType = 'chat' | 'email' | 'social' | 'phone' | 'api' | 'bot';
export type SenderType = 'customer' | 'operator' | 'agent' | 'system' | 'bot';
export type MessageType = 'text' | 'image' | 'file' | 'audio' | 'video' | 'system';

export interface Customer {
  id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  external_id: string | null;
  external_source: string | null;
  created_at: string;
  updated_at: string;
}

export interface Channel {
  id: string;
  name: string;
  type: ChannelType;
  is_active: boolean;
  config: Record<string, unknown> | null;
  created_at: string;
}

export interface Ticket {
  id: string;
  customer_id: string | null;
  channel_id: string | null;
  subject: string | null;
  description: string | null;
  resolution_notes: string | null;
  status: TicketStatus;
  priority: TicketPriority;
  assigned_user_id: string | null;
  agent_id: string | null;
  source: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface TicketWithRelations extends Ticket {
  customer: Customer | null;
  channel: Channel | null;
  assigned_user: { id: string; email: string; full_name: string | null } | null;
  conversation: Conversation | null;
}

export interface Conversation {
  id: string;
  ticket_id: string;
  started_at: string;
  last_message_at: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: SenderType;
  sender_id: string | null;
  message: string | null;
  message_type: MessageType;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface Attachment {
  id: string;
  message_id: string;
  file_url: string | null;
  file_type: string | null;
  file_size: number | null;
  created_at: string;
}

export interface TicketStatusHistory {
  id: string;
  ticket_id: string;
  old_status: string | null;
  new_status: string | null;
  changed_by: string | null;
  created_at: string;
}

export interface CustomerWithStats extends Customer {
  tickets_count: number;
  last_contact: string | null;
}

export interface CustomerFilters {
  search?: string;
  email?: string;
  phone?: string;
}

export interface IdentifyCustomerPayload {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  external_id?: string | null;
  external_source?: string | null;
}

export interface UpdateCustomerPayload {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
}

export interface CreateTicketPayload {
  customer_id: string;
  channel_id: string;
  subject?: string;
  initial_message: string;
  priority?: TicketPriority;
  source?: string;
}

export interface TicketFilters {
  status?: TicketStatus;
  priority?: TicketPriority;
  channel_id?: string;
  assigned_user_id?: string;
  customer_id?: string;
  search?: string;
}

export interface NormalizedAttachment {
  file_url: string;
  file_type: string;
  file_size: number;
}

export interface NormalizedMessage {
  content: string;
  type: MessageType;
  attachments: NormalizedAttachment[];
}

export interface NormalizedCustomer {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
}

export interface NormalizedPayload {
  channel: ChannelType;
  external_id: string;
  customer: NormalizedCustomer;
  message: NormalizedMessage;
  subject?: string | null;
  priority?: TicketPriority;
}

export interface ChatAdapterPayload {
  session_id: string;
  name?: string;
  email?: string;
  phone?: string;
  message: string;
}

export interface EmailAdapterPayload {
  from_email: string;
  from_name?: string;
  subject?: string;
  body: string;
  attachments?: { file_url: string; file_type: string; file_size: number }[];
}

export interface ApiAdapterPayload {
  external_id: string;
  customer: {
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    external_id?: string | null;
  };
  message: {
    content: string;
    type?: MessageType;
    attachments?: NormalizedAttachment[];
  };
  subject?: string;
  priority?: TicketPriority;
}

export interface ChannelIngestResult {
  ticket_id: string;
  customer_id: string;
  conversation_id: string;
  message_id: string;
  is_new_ticket: boolean;
  is_new_customer: boolean;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface TicketTag {
  id: string;
  ticket_id: string;
  tag_id: string;
  created_at: string;
  tag?: Tag;
}

export type SLAStatus = 'within_sla' | 'breached';

export interface SLAPolicy {
  id: string;
  name: string;
  priority: TicketPriority;
  first_response_minutes: number;
  resolution_minutes: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TicketSLA {
  id: string;
  ticket_id: string;
  sla_policy_id: string;
  first_response_deadline: string;
  resolution_deadline: string;
  first_response_at: string | null;
  resolved_at: string | null;
  status: SLAStatus;
  created_at: string;
}

export type TriggerEvent = 'ticket_created' | 'message_received' | 'ticket_updated';
export type ConditionField = 'priority' | 'tag' | 'channel' | 'status' | 'assigned';
export type ConditionOperator = 'equals' | 'not_equals' | 'contains' | 'is_empty';
export type ActionType = 'assign_user' | 'add_tag' | 'change_priority' | 'change_status';

export interface AutomationCondition {
  field: ConditionField;
  operator: ConditionOperator;
  value: string;
}

export interface AutomationAction {
  type: ActionType;
  value: string;
}

export interface AutomationRule {
  id: string;
  name: string;
  trigger_event: TriggerEvent;
  conditions: AutomationCondition[];
  actions: AutomationAction[];
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface AutomationContext {
  ticket_id: string;
  priority: TicketPriority;
  status: TicketStatus;
  channel_name?: string;
  channel_id?: string;
  tag_ids?: string[];
  assigned_user_id?: string | null;
}

export interface Macro {
  id: string;
  name: string;
  content: string;
  category: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface MacroContext {
  customer_name?: string;
  ticket_id?: string;
  agent_name?: string;
}

export type AgentType = 'triage_agent' | 'support_agent' | 'technical_agent' | 'billing_agent' | 'sales_agent' | 'qa_agent';
export type AgentStatus = 'active' | 'disabled' | 'testing';
export type AgentRunStatus = 'running' | 'completed' | 'failed' | 'cancelled';
export type AgentMessageRole = 'system' | 'user' | 'assistant' | 'tool';
export type LLMProvider = 'openai' | 'anthropic' | 'google';

export interface Agent {
  id: string;
  name: string;
  description: string | null;
  type: AgentType | null;
  status: AgentStatus;
  default_model_provider: LLMProvider | null;
  default_model_name: string | null;
  temperature: number;
  max_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface AgentSkill {
  id: string;
  agent_id: string;
  skill_name: string;
  created_at: string;
}

export interface AgentModel {
  id: string;
  agent_id: string;
  provider: LLMProvider;
  model_name: string;
  max_tokens: number | null;
  temperature: number | null;
  cost_input: number | null;
  cost_output: number | null;
  created_at: string;
}

export interface AgentRun {
  id: string;
  agent_id: string | null;
  ticket_id: string | null;
  conversation_id: string | null;
  status: AgentRunStatus;
  model_provider: string | null;
  model_name: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface AgentMessage {
  id: string;
  run_id: string;
  role: AgentMessageRole;
  content: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export type AgentWithRelations = Agent & {
  skills: AgentSkill[];
  models: AgentModel[];
};

export type RoutingLayer = 'rule' | 'llm' | 'fallback';

export interface RouterResult {
  agent_id: string | null;
  agent_type: string;
  agent_name: string;
  routing_layer: RoutingLayer;
  matched_rule: boolean;
  conversation_id: string | null;
  ticket_id: string | null;
}

export interface RouteMessagePayload {
  message: string;
  conversation_id?: string;
  ticket_id?: string;
}

export type AgentRunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type AgentMessageRole = 'system' | 'user' | 'assistant' | 'tool';

export interface AgentRun {
  id: string;
  agent_id: string;
  ticket_id: string | null;
  conversation_id: string | null;
  model_provider: string;
  model_name: string;
  status: AgentRunStatus;
  input_tokens: number;
  output_tokens: number;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
  created_at: string;
}

export interface AgentMessage {
  id: string;
  run_id: string;
  role: AgentMessageRole;
  content: string | null;
  metadata: {
    tool_name?: string;
    tool_input?: Record<string, unknown>;
    tool_result?: unknown;
    tool_use_id?: string;
    tool_calls?: string[];
    stop_reason?: string;
  } | null;
  created_at: string;
}

export interface AgentRunWithMessages extends AgentRun {
  messages: AgentMessage[];
}

export interface ExecuteAgentPayload {
  agent_id: string;
  message: string;
  ticket_id?: string;
  conversation_id?: string;
}

export interface ExecuteAgentResult {
  response: string;
  agent_run_id: string;
  agent_id: string;
  agent_name: string;
  model_provider: string;
  model_name: string;
  input_tokens: number;
  output_tokens: number;
}

export type LLMRequestStatus = 'pending' | 'success' | 'error' | 'timeout';

export interface LLMRequest {
  id: string;
  agent_id: string | null;
  model_id: string | null;
  provider: string | null;
  model_identifier: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  status: LLMRequestStatus;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  agent?: { id: string; name: string } | null;
  model?: { id: string; name: string; provider: string } | null;
}

export interface CreateLLMRequestPayload {
  agent_id?: string;
  model_id?: string;
  provider?: string;
  model_identifier?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdateLLMRequestSuccessPayload {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
}

export interface LLMRequestFilters {
  model_id?: string;
  agent_id?: string;
  provider?: string;
  status?: LLMRequestStatus;
  from?: string;
  to?: string;
}

export type LLMModelProvider = 'openai' | 'anthropic' | 'google' | 'mistral';

export interface LLMModel {
  id: string;
  name: string;
  provider: LLMModelProvider;
  model_identifier: string;
  description: string | null;
  input_cost_per_1k_tokens: number | null;
  output_cost_per_1k_tokens: number | null;
  max_tokens: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateLLMModelPayload {
  name: string;
  provider: LLMModelProvider;
  model_identifier: string;
  description?: string;
  input_cost_per_1k_tokens?: number;
  output_cost_per_1k_tokens?: number;
  max_tokens?: number;
}

export interface UpdateLLMModelPayload {
  name?: string;
  description?: string;
  input_cost_per_1k_tokens?: number;
  output_cost_per_1k_tokens?: number;
  max_tokens?: number;
  is_active?: boolean;
}

export type OperatorStatus = 'online' | 'away' | 'busy' | 'offline';

export interface OperatorPresence {
  id: string;
  user_id: string;
  status: OperatorStatus;
  last_seen: string;
  updated_at: string;
}
