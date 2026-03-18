import type {
  NormalizedPayload,
  ChatAdapterPayload,
  EmailAdapterPayload,
  ApiAdapterPayload,
} from '../../types';

export function normalizeChatPayload(raw: ChatAdapterPayload): NormalizedPayload {
  return {
    channel: 'chat',
    external_id: raw.session_id,
    customer: {
      name: raw.name ?? null,
      email: raw.email ?? null,
      phone: raw.phone ?? null,
    },
    message: {
      content: raw.message,
      type: 'text',
      attachments: [],
    },
  };
}

export function normalizeEmailPayload(raw: EmailAdapterPayload): NormalizedPayload {
  return {
    channel: 'email',
    external_id: raw.from_email,
    customer: {
      name: raw.from_name ?? null,
      email: raw.from_email,
      phone: null,
    },
    message: {
      content: raw.body,
      type: 'text',
      attachments: (raw.attachments ?? []).map((a) => ({
        file_url: a.file_url,
        file_type: a.file_type,
        file_size: a.file_size,
      })),
    },
    subject: raw.subject ?? null,
  };
}

export function normalizeApiPayload(raw: ApiAdapterPayload): NormalizedPayload {
  return {
    channel: 'api',
    external_id: raw.external_id,
    customer: {
      name: raw.customer.name ?? null,
      email: raw.customer.email ?? null,
      phone: raw.customer.phone ?? null,
    },
    message: {
      content: raw.message.content,
      type: raw.message.type ?? 'text',
      attachments: raw.message.attachments ?? [],
    },
    subject: raw.subject ?? null,
    priority: raw.priority,
  };
}
