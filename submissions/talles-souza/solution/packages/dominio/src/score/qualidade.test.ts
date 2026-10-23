import { describe, expect, it } from 'vitest';
import { configQualidadePadrao } from './qualidade.config';
import { parteDoDado, pontuarQualidade, qualidadeDoDado } from './qualidade';

const cfg = configQualidadePadrao;

describe('parteDoDado (a idade: a chance da faixa ÷ a melhor faixa)', () => {
  it('a melhor faixa vale 100; as outras, proporcionais; arredonda', () => {
    // as chances do motor em 31/12/2017 (conversão razão)
    expect(parteDoDado(0.516, 0.516)).toBe(100);
    expect(parteDoDado(0.467, 0.516)).toBe(91);
    expect(parteDoDado(0.313, 0.516)).toBe(61);
    expect(parteDoDado(0.21, 0.516)).toBe(41);
    expect(parteDoDado(0.077, 0.516)).toBe(15);
    expect(parteDoDado(0.006, 0.516)).toBe(1);
  });

  it('sem nenhuma faixa que fecha (máxima 0) = 0; nunca passa de 100', () => {
    expect(parteDoDado(0, 0)).toBe(0);
    expect(parteDoDado(0.9, 0.5)).toBe(100);
  });

  it('qualidadeDoDado pega a máxima da lista e guarda o que fechou de fato', () => {
    expect(qualidadeDoDado(0.25, [0.5, 0.25, 0.1], { taxa: 0.3, faixas: [0.52, 0.3] })).toEqual({
      chance: 0.25,
      maxima: 0.5,
      parte: 50,
      fecharam: { taxa: 0.3, maxima: 0.52 },
    });
    expect(qualidadeDoDado(0.25, [0.5]).fecharam).toBeNull();
  });
});

describe('pontuarQualidade (a idade + as respostas do vendedor)', () => {
  it('sem resposta, o score é a parte do dado', () => {
    expect(pontuarQualidade(61, [], cfg)).toEqual({
      score: 61,
      base: 61,
      temIdade: true,
      ajustes: [],
    });
  });

  it('"Sim" soma 10 e "Não" tira 15, pelo config', () => {
    expect(cfg).toMatchObject({ porSim: 10, porNao: -15, semDataBase: 50 });
    expect(pontuarQualidade(41, [{ perguntaId: 'decisor', valor: 'sim' }], cfg).score).toBe(51);
    expect(pontuarQualidade(41, [{ perguntaId: 'decisor', valor: 'nao' }], cfg).score).toBe(26);
    const tres = pontuarQualidade(
      61,
      [
        { perguntaId: 'decisor', valor: 'sim' },
        { perguntaId: 'dor', valor: 'sim' },
        { perguntaId: 'proximo_passo', valor: 'nao' },
      ],
      cfg,
    );
    expect(tres.score).toBe(66);
    expect(tres.ajustes.map((a) => a.pontos)).toEqual([10, 10, -15]);
  });

  it('limite 0–100', () => {
    const sim = { perguntaId: 'x', valor: 'sim' } as const;
    const nao = { perguntaId: 'x', valor: 'nao' } as const;
    expect(pontuarQualidade(100, [sim, sim, sim], cfg).score).toBe(100);
    expect(pontuarQualidade(1, [nao], cfg).score).toBe(0);
    expect(pontuarQualidade(15, [nao, nao, nao], cfg).score).toBe(0);
  });

  it('sem data: sem resposta = sem score; com resposta, parte de 50', () => {
    expect(pontuarQualidade(null, [], cfg)).toEqual({
      score: null,
      base: null,
      temIdade: false,
      ajustes: [],
    });
    expect(pontuarQualidade(null, [{ perguntaId: 'dor', valor: 'sim' }], cfg)).toMatchObject({
      score: 60,
      base: 50,
      temIdade: false,
    });
    expect(pontuarQualidade(null, [{ perguntaId: 'dor', valor: 'nao' }], cfg).score).toBe(35);
  });
});
