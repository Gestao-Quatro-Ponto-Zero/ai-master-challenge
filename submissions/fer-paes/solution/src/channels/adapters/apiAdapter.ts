import type { ApiAdapterPayload, NormalizedPayload } from '../../types';
import { normalizeApiPayload } from '../normalizers/messageNormalizer';

export function adaptApiMessage(raw: ApiAdapterPayload): NormalizedPayload {
  if (!raw.external_id) throw new Error('api adapter: external_id is required');
  if (!raw.message?.content) throw new Error('api adapter: message.content is required');

  return normalizeApiPayload(raw);
}
