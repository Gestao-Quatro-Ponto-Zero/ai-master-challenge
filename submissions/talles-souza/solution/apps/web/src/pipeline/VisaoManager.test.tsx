import type { LinhaDoPainel, MetricasDoPainel, Painel } from '@lead-scorer/dominio/priorizacao';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ProvedorApp } from '../app/contexto';
import { base, clienteFalso, dependencias } from '../testes/fixtures';
import { VisaoManager } from './VisaoManager';

afterEach(cleanup);

function metricas(total: number, foque: number): MetricasDoPainel {
  return {
    total,
    receita: 46487.4,
    foqueSemConversa: {
      n: foque,
      valor: foque * 1096,
      foque: foque + 1,
      sim: 1,
      nao: 0,
      semResposta: foque,
    },
    parado: { n: total - 3, valor: 3779334 },
    semInicio: { n: 1, valor: 1073986 },
    respostas: { n: 0, base: 3, pct: 0 },
  };
}

const linha = (vendedor: string, foque: number): LinhaDoPainel => ({
  vendedor,
  manager: 'Marcos Gestor',
  regiao: 'West',
  ...metricas(foque === 0 ? 3 : 10, foque),
});

function painel(total: number): Painel {
  return {
    ...metricas(total, 2),
    limiteParadoDias: 60,
    vendedores: [linha('Ana Vendas', 2), linha('Bruno Sem Negócio', 0)],
  };
}

describe('Acompanhar a equipe', () => {
  it('mostra as 4 métricas, cada uma com o rótulo e a frase do que mede, e a tabela por vendedor, só para ler', async () => {
    const pedidos: unknown[] = [];
    const deps = dependencias(
      clienteFalso({
        painel: async (pedido) => {
          pedidos.push(pedido.filtro);
          return { ok: true, valor: painel(pedido.filtro.regiao ? 10 : 2089) };
        },
      }),
    );
    render(
      <ProvedorApp deps={deps}>
        <VisaoManager base={base} />
      </ProvedorApp>,
    );
    await screen.findByTestId('metrica-receita');
    for (const id of ['receita', 'foque-sem-conversa', 'parado', 'sem-inicio'])
      expect(screen.getByTestId('metrica-' + id)).toBeTruthy();
    expect(document.querySelectorAll('.metrica')).toHaveLength(4);
    expect(screen.getByTestId('painel-receita').textContent).toBe('US$ 46.487');
    expect(screen.getByTestId('metrica-receita').textContent).toContain(
      'nos próximos 3 meses, sem contar negócios novos',
    );
    expect(screen.getByTestId('painel-foque-sem-conversa').textContent).toBe('2');
    expect(screen.getByTestId('painel-foque-sem-conversa-valor').textContent).toBe(
      'US$ 2.192 em jogo',
    );
    expect(screen.getByTestId('metrica-foque-sem-conversa').textContent).toContain(
      'vai esfriar se ninguém agir',
    );
    expect(screen.getByTestId('painel-parado').textContent).toBe('2.086');
    expect(screen.getByTestId('painel-parado-valor').textContent).toBe('US$ 3.779.334 em jogo');
    expect(screen.getByTestId('metrica-parado').textContent).toContain('inflando o pipeline');
    expect(screen.getByTestId('metrica-parado').textContent).toContain(
      'Abertos há mais de 60 dias (Nutrição)',
    );
    expect(screen.getByTestId('painel-sem-inicio').textContent).toBe('1');
    expect(screen.getByTestId('metrica-sem-inicio').textContent).toContain('nunca abordados');
    // a curva e a qualidade do dado ficam em "Como a nota funciona"
    expect(screen.queryByTestId('metrica-curva')).toBeNull();
    expect(screen.queryByTestId('metrica-qualidade')).toBeNull();

    // a tabela por vendedor, na ordem que o domínio manda, com zero quando for o caso
    const linhas = [...screen.getByTestId('painel-vendedores').querySelectorAll('tbody tr')];
    expect(linhas.map((l) => l.getAttribute('data-vendedor'))).toEqual([
      'Ana Vendas',
      'Bruno Sem Negócio',
    ]);
    expect(linhas[0]?.textContent).toContain('2 · US$ 2.192');
    expect(linhas[1]?.textContent).toContain('0 · US$ 0');
    expect(linhas[0]?.textContent).toContain('0 de 3');

    // sem banco compartilhado, o painel diz de onde vêm as respostas
    expect(screen.getByTestId('painel-respostas').textContent).toBe(
      'Respostas gravadas neste navegador: 0 de 3',
    );
    // só leitura: nenhum botão
    expect(screen.queryAllByRole('button')).toHaveLength(0);

    fireEvent.change(screen.getByTestId('filtro-regiao'), { target: { value: 'West' } });
    await waitFor(() => expect(screen.getByTestId('painel-parado').textContent).toBe('7'));
    expect(pedidos).toEqual([{}, { regiao: 'West' }]);
  });

  it('com o banco compartilhado, as respostas do servidor entram no navegador e o painel diz "Respostas gravadas"', async () => {
    const doServidor = {
      formato: 1 as const,
      dealId: 'AAAA0001',
      metodoId: base.metodo.id,
      respostas: [
        { perguntaId: 'dor', valor: 'sim' as const, respondidoEm: '2026-10-22T10:00:00.000Z' },
      ],
      decisao: null,
    };
    const enviados: unknown[] = [];
    const deps = {
      ...dependencias(
        clienteFalso({
          painel: async (pedido) => {
            enviados.push(pedido.respostas.length);
            return { ok: true as const, valor: painel(2089) };
          },
        }),
      ),
      registros: {
        baixar: async () => ({ armazenamento: 'banco' as const, registros: [doServidor] }),
        responder: async () => true,
        decidir: async () => true,
        decidirLote: async () => true,
      },
    };
    render(
      <ProvedorApp deps={deps}>
        <VisaoManager base={base} />
      </ProvedorApp>,
    );
    await waitFor(() => expect(deps.repositorio.ler('AAAA0001')?.respostas).toHaveLength(1));
    await waitFor(() => expect(enviados.at(-1)).toBe(1));
    await waitFor(() =>
      expect(screen.getByTestId('painel-respostas').textContent).toBe('Respostas gravadas: 0 de 3'),
    );
    expect(document.body.textContent).not.toContain('neste navegador');
  });
});
