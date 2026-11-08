import { describe, expect, it } from 'vitest';
import { DEFAULT_URL_STATE, parseUrlState, serializeUrlState } from './urlState';

describe('urlState', () => {
  it('defaults to an empty query', () => {
    expect(serializeUrlState(DEFAULT_URL_STATE)).toBe('');
    expect(parseUrlState('')).toEqual(DEFAULT_URL_STATE);
  });
  it('round-trips non-default values', () => {
    const s = { ...DEFAULT_URL_STATE, view: 'all' as const, tab: 'review' as const, product: 'GTK 500', search: 'acme', page: 2 };
    expect(parseUrlState(serializeUrlState(s))).toEqual(s);
  });
  it('ignores invalid values', () => {
    expect(parseUrlState('?tab=xx&page=-3&sort=zz&size=7')).toEqual(DEFAULT_URL_STATE);
  });
});
