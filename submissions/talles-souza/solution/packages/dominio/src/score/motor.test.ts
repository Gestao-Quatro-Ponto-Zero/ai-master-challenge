import { describe, expect, it } from 'vitest';
import type { Deal } from '../pipeline';
import {
  calcularAuc,
  configMotorPadrao,
  fatoresNoCorte,
  medirMotor,
  type ConfigMotor,
  type FatorDoMotor,
} from './index';

const REFERENCIA = '2017-12-31';
// cortes do replay com a config padrão: treino em R − 184 d, validação em R − 92 d
const C1 = '2017-06-30';
const C2 = '2017-09-30';
const FAIXAS = [
  { ateDias: 10 },
  { ateDias: 20 },
  { ateDias: 30 },
  { ateDias: 40 },
  { ateDias: 50 },
  { ateDias: 60 },
  { ateDias: 90 },
  { ateDias: null },
];
const DIA = 86_400_000;

function somarDias(iso: string, dias: number): string {
  return new Date(Date.parse(iso + 'T00:00:00Z') + dias * DIA).toISOString().slice(0, 10);
}

function deal(parcial: Partial<Deal>): Deal {
  return {
    id: 'AAAA0001',
    vendedor: 'Ana',
    manager: 'Mara',
    regiao: 'West',
    produto: 'GTX Pro',
    serie: 'GTX',
    precoTabela: 4821,
    conta: 'Acme',
    setor: 'retail',
    funcionarios: 4540,
    receitaConta: 700,
    empresaMae: null,
    estagio: 'Engaging',
    dataEngajamento: '2017-11-21',
    dataFechamento: null,
    valorFechamento: null,
    aberto: true,
    idadeDias: null,
    duracaoDias: null,
    lacunas: [],
    ...parcial,
  };
}

interface Caso {
  idade: number;
  ganhou: boolean;
  extra?: Partial<Deal>;
}

/**
 * Um negócio aberto no corte com a idade dada: ganha 30 dias depois do corte ou perde 60 dias
 * depois (os dois antes do fim do recorte de 92 dias).
 */
function noCorte(corte: string, id: string, caso: Caso): Deal {
  return deal({
    id,
    dataEngajamento: somarDias(corte, -caso.idade),
    estagio: caso.ganhou ? 'Won' : 'Lost',
    dataFechamento: somarDias(corte, caso.ganhou ? 30 : 60),
    aberto: false,
    ...caso.extra,
  });
}

/** Os dois recortes com a mesma regra, mais 2 abertos na referência. */
function historico(regra: (i: number) => Caso, n = 400): Deal[] {
  const deals: Deal[] = [];
  for (let i = 0; i < n; i++) {
    deals.push(noCorte(C1, 'T' + String(i).padStart(4, '0'), regra(i)));
    deals.push(noCorte(C2, 'V' + String(i).padStart(4, '0'), regra(i)));
  }
  deals.push(
    deal({ id: 'ABERTO01', dataEngajamento: somarDias(REFERENCIA, -15), idadeDias: 15 }),
    deal({ id: 'ABERTO02', dataEngajamento: somarDias(REFERENCIA, -80), idadeDias: 80 }),
  );
  return deals;
}

// até 89 dias: quem é da validação começou depois do corte do treino (os recortes não se misturam)
const idadeDe = (i: number) => 5 + ((i * 7) % 85);
// a idade decide (até 40 dias ganha), com 1 em 10 trocado para não ser perfeito
const regraDaIdade = (i: number): Caso => ({
  idade: idadeDe(i),
  ganhou: idadeDe(i) <= 40 !== (i % 10 === 0),
  extra: {
    produto: i % 2 === 0 ? 'GTX Pro' : 'MG Special',
    vendedor: i % 3 === 0 ? 'Ana' : 'Bia',
  },
});

function fator(motor: { fatores: FatorDoMotor[] }, id: FatorDoMotor['id']): FatorDoMotor {
  const f = motor.fatores.find((x) => x.id === id);
  if (!f) throw new Error('sem fator ' + id);
  return f;
}

describe('calcularAuc', () => {
  it('1 quando todo ganho fica acima, 0 quando fica abaixo, 0,5 no empate', () => {
    expect(calcularAuc([3, 2, 1, 0], [true, true, false, false])).toBe(1);
    expect(calcularAuc([0, 1, 2, 3], [true, true, false, false])).toBe(0);
    expect(calcularAuc([1, 1, 1, 1], [true, false, true, false])).toBe(0.5);
    expect(calcularAuc([2, 1, 1, 0], [true, true, false, false])).toBe(0.875);
  });

  it('null sem ganho ou sem perda', () => {
    expect(calcularAuc([1, 2], [true, true])).toBeNull();
    expect(calcularAuc([1, 2], [false, false])).toBeNull();
  });
});

describe('medirMotor: replay, pontos e seleção', () => {
  const deals = historico(regraDaIdade);
  const { motor } = medirMotor(deals, REFERENCIA, FAIXAS, configMotorPadrao);

  it('cortes do replay: treino em R − 184 d até R − 92 d; validação em R − 92 d até R', () => {
    expect(motor.treino).toMatchObject({ corte: C1, ate: C2, n: 400 });
    expect(motor.validacao).toMatchObject({ corte: C2, ate: REFERENCIA, n: 400 });
    expect(motor.taxaBase).toBe(motor.validacao.ganhos / 400);
  });

  it('pontos = round(10 × ln(taxa suavizada ÷ taxa geral)), com 20 negócios na taxa geral', () => {
    const idade = fator(motor, 'idade');
    const p = motor.treino.ganhos / motor.treino.n;
    for (const c of idade.categoriasTreino) {
      const esperado =
        c.n < configMotorPadrao.nMinimo
          ? 0
          : Math.round(10 * Math.log((c.ganhos + 20 * p) / (c.n + 20) / p));
      expect(c.pontos).toBe(esperado);
    }
  });

  it('categoria com n < 30 vale 0 e diz por quê', () => {
    const pequenas = fator(motor, 'idade').categoriasTreino.filter((c) => c.n < 30);
    expect(pequenas.length).toBeGreaterThan(0);
    for (const c of pequenas) expect(c).toMatchObject({ pontos: 0, motivo: 'n_pequeno' });
  });

  it('a seleção gulosa põe a idade e deixa de fora o que é ruído', () => {
    expect(motor.escolhidos).toEqual(['idade']);
    expect(fator(motor, 'idade')).toMatchObject({ entrou: true, passo: 1, motivo: 'entrou' });
    expect(motor.aucScore).toBe(motor.aucIdade);
    const produto = fator(motor, 'produto');
    expect(produto.entrou).toBe(false);
    expect(produto.motivo).toBe('nao_melhorou');
    expect(produto.ganhoAuc as number).toBeLessThan(configMotorPadrao.ganhoMinimoAuc);
    expect(produto.categorias.every((c) => c.pontos === 0 && c.motivo === 'fora_do_score')).toBe(
      true,
    );
    // o estágio no corte é sempre "em andamento" (Prospecting não entra no replay)
    expect(fator(motor, 'estagio').motivo).toBe('n_pequeno');
  });

  it('um segundo fator entra quando sobe o AUC na validação', () => {
    // na mesma idade, o MG Special ganha mais que o GTX Pro
    const regra = (i: number): Caso => {
      const idade = idadeDe(i);
      const mg = i % 2 === 1;
      return {
        idade,
        ganhou: idade <= (mg ? 70 : 30),
        extra: { produto: mg ? 'MG Special' : 'GTX Pro' },
      };
    };
    const { motor: m } = medirMotor(historico(regra), REFERENCIA, FAIXAS, configMotorPadrao);
    expect(m.escolhidos).toContain('produto');
    expect(fator(m, 'produto').ganhoAuc as number).toBeGreaterThanOrEqual(
      configMotorPadrao.ganhoMinimoAuc,
    );
    expect(m.aucScore as number).toBeGreaterThan(m.aucIdade as number);
  });

  it('"sem dado" nunca ganha nem perde, nem dá pontos às outras categorias', () => {
    // sem conta nunca ganha; com conta, ter ou não empresa-mãe não muda nada
    const regra = (i: number): Caso => {
      const idade = idadeDe(i);
      const semConta = i % 4 === 0;
      return {
        idade,
        ganhou: !semConta && idade <= 40,
        extra: semConta
          ? { conta: null, setor: null, funcionarios: null, receitaConta: null }
          : { empresaMae: i % 4 === 1 ? 'Mãe' : null },
      };
    };
    const { motor: m } = medirMotor(historico(regra), REFERENCIA, FAIXAS, configMotorPadrao);
    const mae = fator(m, 'empresa_mae');
    expect(mae.entrou).toBe(false);
    expect(mae.aucValidacao).toBeCloseTo(0.5, 1);
    // medidas contra a taxa geral, as conhecidas ganhariam ~+3 só por ter conta (o vazamento)
    const conhecidas = mae.categoriasTreino.filter((c) => c.chave !== 'sem_dado');
    for (const c of conhecidas) expect(Math.abs(c.pontos)).toBeLessThanOrEqual(1);
    expect(conhecidas.every((c) => c.pontos > 0)).toBe(false);
    expect(mae.categoriasTreino.find((c) => c.chave === 'sem_dado')).toMatchObject({
      pontos: 0,
      motivo: 'sem_dado',
    });
  });
});

describe('sem vazamento: o fator no corte só usa o que se sabia no corte', () => {
  const antesDe = (iso: string | null, corte: string) =>
    iso !== null && Date.parse(iso + 'T00:00:00Z') <= Date.parse(corte + 'T00:00:00Z');

  /** Apaga o futuro: some quem começou depois do corte e quem fechou depois volta a estar aberto. */
  function censurar(deals: readonly Deal[], corte: string): Deal[] {
    return deals
      .filter((d) => antesDe(d.dataEngajamento, corte))
      .map((d) =>
        d.dataFechamento !== null && !antesDe(d.dataFechamento, corte)
          ? {
              ...d,
              estagio: 'Engaging' as const,
              dataFechamento: null,
              valorFechamento: null,
              aberto: true,
              duracaoDias: null,
              idadeDias: null,
            }
          : d,
      );
  }

  it('apagar tudo depois do corte não muda nenhum fator de nenhum negócio aberto nele', () => {
    // contas com histórico antes e depois dos cortes, vendedores com ciclos diferentes
    const deals = historico((i) => ({
      idade: idadeDe(i),
      ganhou: i % 3 !== 0,
      extra: { conta: i % 5 === 0 ? null : 'Conta ' + (i % 7), vendedor: 'V' + (i % 4) },
    }));
    for (const corte of [C1, C2]) {
      const completo = fatoresNoCorte(deals, corte, FAIXAS, configMotorPadrao);
      const censurado = fatoresNoCorte(censurar(deals, corte), corte, FAIXAS, configMotorPadrao);
      expect(completo.size).toBe(400);
      expect(censurado).toEqual(completo);
    }
  });

  it('a censura muda o que o futuro sabe: um fator que lesse o estágio de hoje seria pego', () => {
    const deals = historico(regraDaIdade);
    const abertosNoCorte = new Set(fatoresNoCorte(deals, C2, FAIXAS, configMotorPadrao).keys());
    const estagios = (lista: readonly Deal[]) =>
      lista.filter((d) => abertosNoCorte.has(d.id)).map((d) => d.estagio);
    expect(estagios(censurar(deals, C2)).every((e) => e === 'Engaging')).toBe(true);
    expect(estagios(deals)).toContain('Won');
  });
});

describe('score do negócio', () => {
  const deals = historico(regraDaIdade);
  const config: ConfigMotor = { ...configMotorPadrao, conversao: 'log_odds' };
  const a = medirMotor(deals, REFERENCIA, FAIXAS, config);
  const b = medirMotor(deals, REFERENCIA, FAIXAS, config);
  const novo = deals.find((d) => d.id === 'ABERTO01') as Deal;
  const velho = deals.find((d) => d.id === 'ABERTO02') as Deal;

  it('reproduzível: as mesmas entradas dão o mesmo motor e o mesmo score', () => {
    expect(b.motor).toEqual(a.motor);
    expect(b.pontuar(novo)).toEqual(a.pontuar(novo));
  });

  it('score = round(100 × chance); chance pela log-odds da taxa base + pontos ÷ 10', () => {
    for (const d of [novo, velho]) {
      const s = a.pontuar(d);
      if (!s) throw new Error('sem score');
      const p = a.motor.taxaBase;
      const chance = 1 / (1 + Math.exp(-(Math.log(p / (1 - p)) + s.pontos / 10)));
      expect(s.chance).toBeCloseTo(chance, 12);
      expect(s.score).toBe(Math.round(100 * chance));
      expect(s.pontos).toBe(s.parcelas.reduce((soma, x) => soma + x.pontos, 0));
    }
    expect(a.pontuar(novo)?.score as number).toBeGreaterThan(a.pontuar(velho)?.score as number);
  });

  it('na conversão pela razão, chance = taxa base × e^(pontos ÷ 10), com teto 1', () => {
    const r = medirMotor(deals, REFERENCIA, FAIXAS, { ...config, conversao: 'razao' });
    const s = r.pontuar(novo);
    if (!s) throw new Error('sem score');
    expect(s.chance).toBeCloseTo(Math.min(1, r.motor.taxaBase * Math.exp(s.pontos / 10)), 12);
    expect(s.pontos).toBe(a.pontuar(novo)?.pontos);
  });

  it('a decomposição traz todos os fatores; os de fora valem 0 e dizem por quê', () => {
    const s = a.pontuar(novo);
    if (!s) throw new Error('sem score');
    expect(s.parcelas).toHaveLength(a.motor.fatores.length);
    expect(s.parcelas[0]).toMatchObject({
      fator: 'idade',
      valor: '15 dias',
      faixa: '11 a 20 dias',
    });
    expect(s.principal?.fator).toBe('idade');
    expect(s.parcelas.find((p) => p.fator === 'produto')).toMatchObject({
      pontos: 0,
      motivo: 'fora_do_score',
    });
  });

  it('sem data de início (Prospecting) fica sem score', () => {
    const prospeccao = deal({ id: 'PROSP001', estagio: 'Prospecting', dataEngajamento: null });
    expect(a.pontuar(prospeccao)).toBeNull();
    const comSemData = medirMotor(deals, REFERENCIA, FAIXAS, { ...config, pontuarSemData: true });
    expect(comSemData.pontuar(prospeccao)?.parcelas.find((p) => p.fator === 'idade')).toMatchObject(
      { pontos: 0, motivo: 'sem_dado' },
    );
  });
});
