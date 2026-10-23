import type { PedidoItem } from '@lead-scorer/dominio/priorizacao';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ProvedorApp } from '../app/contexto';
import { base, clienteFalso, dependencias, item } from '../testes/fixtures';
import { anunciarMudanca, TelaDeal } from './TelaDeal';

afterEach(cleanup);

const ACAO_DECISOR = 'Descubra quem decide a compra e marque uma conversa com essa pessoa.';

/** O falso responde como o domínio: "não" em `decisor` troca a ação pela frase da pergunta. */
async function itemFalso(pedido: PedidoItem) {
  const r = pedido.respostas?.respostas ?? [];
  const decisorNao = r.some((x) => x.perguntaId === 'decisor' && x.valor === 'nao');
  const valor = item(
    'siga_no_ritmo',
    decisorNao
      ? { proximaAcao: { tipo: 'manter_ritmo', texto: ACAO_DECISOR, perguntaId: 'decisor' } }
      : {},
    {
      idadeDias: 12,
    },
  );
  return { ok: true as const, valor };
}

function montar() {
  const deps = dependencias(clienteFalso({ item: itemFalso }));
  render(
    <ProvedorApp deps={deps}>
      <TelaDeal base={base} id="AAAA0001" />
    </ProvedorApp>,
  );
  return deps;
}

describe('Tela do negócio', () => {
  it('mostra o score, o que está em jogo, o porquê do score, o valor e o grupo', async () => {
    montar();
    expect((await screen.findByTestId('deal-bloco')).textContent).toBe('Siga no ritmo');
    expect(screen.getByTestId('deal-indicador').textContent).toBe(
      'Score 80se o negócio é bom: a idade e as suas respostas',
    );
    expect(screen.getByTestId('deal-em-jogo').textContent).toBe('GTX Pro · US$ 4.821 em jogo');
    // o "ver por quê": a idade, as respostas e, por último, a posição na lista
    const porque = screen.getByTestId('deal-porque-score');
    expect(within(porque).getByRole('heading').textContent).toBe('Por que Score 80');
    expect([...porque.querySelectorAll('li')].map((l) => l.textContent)).toEqual([
      'Aberto há 12 dias: 30% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).',
      'Na sua lista: 3º de 11 (o grupo, depois o que há a ganhar).',
    ]);
    expect(screen.getByTestId('deal-posicao').textContent).toBe(
      'Na sua lista: 3º de 11 (o grupo, depois o que há a ganhar).',
    );
    // a chance absoluta e a conta por fator, com os zeros e o motivo
    expect(screen.getByTestId('deal-chance-absoluta').textContent).toBe(
      'Chance de fechar em 3 meses: 30%',
    );
    expect(screen.getByTestId('deal-conta').textContent).toContain(
      '+3 · Idade: 45 dias (41 a 50 dias)',
    );
    expect(screen.getByTestId('deal-conta').textContent).toContain(
      'Setor: 0 · não muda a chance no histórico',
    );
    expect(document.body.textContent).not.toMatch(/em 10\b|em cada 10/);
    expect(screen.getByTestId('deal-receita').textContent).toBe(
      'Deve render cerca de US$ 1.446 em 3 meses (estimativa pela chance).',
    );
    // o preço de tabela só aparece no detalhe, rotulado
    expect(screen.getByTestId('deal-preco').textContent).toBe('Preço de tabela: US$ 4.821');
    expect(
      screen.getByRole('heading', {
        level: 2,
        name: 'O que só você sabe (muda o score e a ação)',
      }),
    ).toBeTruthy();
  });

  it('responder "não" troca a ação pela frase da pergunta e guarda a resposta com a data', async () => {
    const deps = montar();
    await screen.findByTestId('deal-bloco');
    fireEvent.click(screen.getByTestId('pergunta-decisor-nao'));
    await waitFor(() => expect(screen.getByTestId('deal-acao').textContent).toBe(ACAO_DECISOR));
    expect(screen.getByTestId('pergunta-decisor-acao').textContent).toBe(ACAO_DECISOR);
    expect(screen.getByTestId('deal-anuncio').textContent).toBe('A ação agora é: ' + ACAO_DECISOR);
    expect(screen.getByTestId('pergunta-decisor-nao').getAttribute('aria-pressed')).toBe('true');
    expect(deps.repositorio.ler('AAAA0001')?.respostas).toEqual([
      { perguntaId: 'decisor', valor: 'nao', respondidoEm: '2026-10-22T12:00:00.000Z' },
    ]);
  });

  it('responder nunca muda o grupo: a tela não anuncia mudança de grupo', async () => {
    montar();
    await screen.findByTestId('deal-bloco');
    fireEvent.click(screen.getByTestId('pergunta-dor-sim'));
    await waitFor(() =>
      expect(screen.getByTestId('deal-anuncio').textContent).toContain('Resposta registrada.'),
    );
    expect(screen.getByTestId('deal-bloco').textContent).toBe('Siga no ritmo');
    expect(document.body.textContent).not.toContain('Pela sua resposta, foi para');
  });

  it('contestar sem motivo não salva; com motivo salva', async () => {
    const deps = montar();
    fireEvent.click(await screen.findByTestId('acao-contestar'));
    fireEvent.click(screen.getByTestId('acao-enviar-contestacao'));
    expect((await screen.findByRole('alert')).textContent).not.toBe('');
    expect(deps.repositorio.ler('AAAA0001')).toBeNull();

    fireEvent.change(screen.getByTestId('acao-motivo'), {
      target: { value: 'O cliente pediu para esperar o orçamento.' },
    });
    fireEvent.click(screen.getByTestId('acao-enviar-contestacao'));
    await waitFor(() => expect(deps.repositorio.ler('AAAA0001')?.decisao?.aceita).toBe(false));
    expect(deps.repositorio.ler('AAAA0001')?.decisao?.motivo).toBe(
      'O cliente pediu para esperar o orçamento.',
    );
    expect(screen.getByTestId('acao-decisao').textContent).toContain('Você contestou');
  });

  it('aceitar guarda a decisão sem motivo', async () => {
    const deps = montar();
    fireEvent.click(await screen.findByTestId('acao-aceitar'));
    await waitFor(() =>
      expect(deps.repositorio.ler('AAAA0001')?.decisao).toMatchObject({
        aceita: true,
        motivo: null,
      }),
    );
  });

  it('empresa vazia aparece como contexto neutro', async () => {
    const deps = dependencias(
      clienteFalso({
        item: async () => ({
          ok: true,
          valor: item('siga_no_ritmo', {}, { conta: null, funcionarios: null }),
        }),
      }),
    );
    render(
      <ProvedorApp deps={deps}>
        <TelaDeal base={base} id="AAAA0001" />
      </ProvedorApp>,
    );
    await screen.findByTestId('deal-bloco');
    expect(document.body.textContent).toContain('sem dado de conta');
  });
});

describe('anunciarMudanca', () => {
  it('diz quanto o score mudou e a ação; sem mudança no score, só a ação', () => {
    const antes = item('foque_agora');
    const depois = { ...antes, indicador: { ...antes.indicador, score: 90 } };
    expect(anunciarMudanca(antes, depois)).toBe(
      'O score foi de 80 para 90. A ação continua: ' + antes.proximaAcao.texto,
    );
    const outraAcao = {
      ...depois,
      proximaAcao: { ...antes.proximaAcao, texto: 'Proponha uma data agora.' },
    };
    expect(anunciarMudanca(antes, outraAcao)).toBe(
      'O score foi de 80 para 90. A ação agora é: Proponha uma data agora.',
    );
    expect(anunciarMudanca(antes, antes)).toBe(
      'Resposta registrada. A ação continua: ' + antes.proximaAcao.texto,
    );
    const semScore = { ...antes, indicador: { ...antes.indicador, score: null } };
    expect(anunciarMudanca(semScore, antes)).toMatch(/^O score foi de — para 80\. /);
  });
});
