import { describe, expect, it } from 'vitest';
import { money, daysText, initialsOf, percent } from './format';
import { bandStyle } from './theme';

describe('format', () => {
  it('formats money', () => expect(money(5482)).toMatch(/US\$\s?5\.482/));
  it('formats chance', () => { expect(percent(0.7)).toBe('70%'); expect(percent(0.061)).toBe('6,1%'); expect(percent(0.1)).toBe('10%'); });
  it('formats days', () => { expect(daysText(1)).toBe('1 dia'); expect(daysText(7)).toBe('7 dias'); });
  it('initials', () => expect(initialsOf('Vicki Laflamme')).toBe('VL'));
  it('prospecting band is labelled', () => expect(bandStyle('prospecting', '#1D4E89').label).toBe('Prospecção'));
});
