import type { ChatAdapterPayload, NormalizedPayload } from '../../types';
import { normalizeChatPayload } from '../normalizers/messageNormalizer';

export function adaptChatMessage(raw: ChatAdapterPayload): NormalizedPayload {
  if (!raw.session_id) throw new Error('chat adapter: session_id is required');
  if (!raw.message) throw new Error('chat adapter: message is required');

  return normalizeChatPayload(raw);
}
