import { describe, expect, it } from 'vitest';
import { createApi } from './createApi';
import { HttpDealsApi } from './HttpDealsApi';
import { MockDealsApi } from './mock/MockDealsApi';

describe('createApi', () => {
  it('npm run dev usa a API real; os outros modos usam o mock', () => {
    expect(createApi({ MODE: 'development' })).toBeInstanceOf(HttpDealsApi);
    expect(createApi({ MODE: 'production' })).toBeInstanceOf(MockDealsApi);
    expect(createApi({ MODE: 'test' })).toBeInstanceOf(MockDealsApi);
  });
  it('VITE_API_MODE manda sobre o padrão', () => {
    expect(createApi({ MODE: 'development', VITE_API_MODE: 'mock' })).toBeInstanceOf(MockDealsApi);
    expect(createApi({ MODE: 'production', VITE_API_MODE: 'http' })).toBeInstanceOf(HttpDealsApi);
  });
});
