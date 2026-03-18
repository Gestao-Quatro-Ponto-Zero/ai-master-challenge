import type { EmailAdapterPayload, NormalizedPayload } from '../../types';
import { normalizeEmailPayload } from '../normalizers/messageNormalizer';

export function adaptEmailMessage(raw: EmailAdapterPayload): NormalizedPayload {
  if (!raw.from_email) throw new Error('email adapter: from_email is required');
  if (!raw.body) throw new Error('email adapter: body is required');

  return normalizeEmailPayload(raw);
}
