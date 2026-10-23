import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ProvedorApp } from '../app/contexto';
import { avaliacao, base, clienteFalso, deal, dependencias, fila, item } from '../testes/fixtures';
import { SegundaFeira } from './SegundaFeira';

afterEach(cleanup);

function montar(f: ReturnType<typeof fila>) {
  const deps = dependencias(clienteFalso({ fila: async () => ({ ok: true, valor: f }) }));
  render(
    <ProvedorApp deps={deps}>
      <SegundaFeira base={base} />
    </ProvedorApp>,
  );
  return deps;
}

const completa = () =>
  fila({
    foque_agora: [item('foque_agora', {}, { id: 'FOQUE001' })],
    siga_no_ritmo: [item('siga_no_ritmo', {}, { id: 'SIGA0001', idadeDias: 10 })],
    nutricao: [item('nutricao', {}, { id: 'NUTRI001', idadeDias: 90 })],
    sem_inicio: [
      item(
        'sem_inicio',
        {},
        { id: 'NOVO0001', idadeDias: null, dataEngajamento: null, estagio: 'Prospecting' },
      ),
    ],
  });

describe('Onde focar hoje', () => {
  it('mostra os grupos na ordem, com contador, indicador, motivo, valor e ação, tudo dos textos da política', async () => {
    montar(completa());

    const foque = await screen.findByTestId('bloco-foque-agora');
    const siga = screen.getByTestId('bloco-siga-no-ritmo');
    const nutricao = screen.getByTestId('bloco-nutricao');
    const novo = screen.getByTestId('grupo-ainda-nao-comecou');
    const segue = (a: Element, b: Element) =>
      a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING;
    // do que mais precisa do vendedor para o que menos precisa: a Nutrição fica por último
    expect(segue(foque, siga)).toBeTruthy();
    expect(segue(siga, novo)).toBeTruthy();
    expect(segue(novo, nutricao)).toBeTruthy();

    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Onde focar hoje');
    expect(document.body.textContent).toContain(
      'Seus 4 negócios abertos, do que mais precisa de você para o que menos precisa.',
    );

    expect(screen.getByTestId('contador-foque-agora').textContent).toBe('1');
    expect(screen.getByTestId('contador-siga-no-ritmo').textContent).toBe('1');
    expect(screen.getByTestId('contador-nutricao').textContent).toBe('1');
    expect(screen.getByTestId('contador-ainda-nao-comecou').textContent).toBe('1');

    expect(foque.textContent).toContain('Ainda podem fechar, mas a chance está caindo.');
    const linha = within(foque).getByTestId('fila-item');
    // o cartão: 3 linhas e nada mais (score, ação, produto · preço em jogo · ver por quê)
    expect([...linha.children].map((c) => c.textContent)).toEqual([
      'Score 80',
      'A chance está caindo: marque a próxima conversa esta semana.',
      'GTX Pro · US$ 4.821 em jogo · ver por quê',
    ]);
    expect(within(linha).getByTestId('fila-item-porque').getAttribute('href')).toContain(
      'FOQUE001',
    );
    // o porquê do score, a posição, a chance, os fatores e a receita do negócio ficam no detalhe
    for (const fora of [
      '+3 · Idade',
      'Chance de fechar',
      'Na sua lista',
      'Aberto há',
      'Deve render',
      'Preço de tabela',
    ])
      expect(linha.textContent).not.toContain(fora);
    // o topo soma a receita esperada e diz quantos ficam fora da conta
    expect(screen.getByTestId('receita-total').textContent).toBe(
      'Dos seus negócios abertos hoje, devem sair cerca de US$ 4.339 nos próximos 3 meses.',
    );
    expect(screen.getByTestId('receita-aviso').textContent).toContain('Não é promessa.');
    expect(screen.getByTestId('receita-sem-data').textContent).toBe(
      '1 negócio sem data não entra na conta',
    );
    expect(document.body.textContent).not.toMatch(/em 10\b|em cada 10/);

    // "Aborde primeiro": o mesmo cartão de 3 linhas, com a ação de qualificar
    const semInicio = within(novo).getByTestId('fila-item');
    expect([...semInicio.children].map((c) => c.textContent)).toEqual([
      'Score —',
      'Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver.',
      'GTX Pro · US$ 4.821 em jogo · ver por quê',
    ]);
    expect(nutricao.textContent).toContain(
      'Nenhum negócio deste histórico fechou depois de 138 dias.',
    );
    // a Nutrição começa recolhida: só a contagem; o vendedor abre para ver
    expect(within(nutricao).queryAllByTestId('fila-item')).toHaveLength(0);
    expect(within(nutricao).getByTestId('nutricao-alternar').textContent).toBe('Mostrar os 1');
    fireEvent.click(within(nutricao).getByTestId('nutricao-alternar'));
    expect(within(nutricao).getByTestId('fila-item-acao').textContent).toBe(
      'Encaminhar para nutrição',
    );
    expect(screen.getAllByTestId('fila-item')).toHaveLength(4);
    expect(document.body.textContent).toContain(
      'O score diz se o negócio é bom: a idade dele contra o histórico e as suas respostas. O preço fica fora do score: ele diz quanto está em jogo.',
    );
  });

  it('comissão: o campo começa vazio, sem percentual sugerido; preenchido mostra a estimativa e fica guardado', async () => {
    const deps = montar(completa());
    const campo = (await screen.findByTestId('comissao')) as HTMLInputElement;
    expect(campo.value).toBe('');
    expect(screen.getByLabelText('Sua comissão (%)')).toBe(campo);
    expect(screen.queryByTestId('comissao-total')).toBeNull();
    fireEvent.change(campo, { target: { value: '10' } });
    // 10% de US$ 4.338,9 (a receita esperada da lista)
    expect(screen.getByTestId('comissao-total').textContent).toBe(
      'Sua comissão estimada nesses negócios: cerca de US$ 434',
    );
    expect(deps.comissao.ler()).toBe(10);
    fireEvent.change(campo, { target: { value: '' } });
    expect(screen.queryByTestId('comissao-total')).toBeNull();
    expect(deps.comissao.ler()).toBeNull();
  });

  it('não usa jargão nem palavra de descarte na tela', async () => {
    montar(completa());
    await screen.findByTestId('bloco-foque-agora');
    expect(document.body.textContent).not.toMatch(
      /\b(deal|deals|lead|pipeline|follow-up|morto|encerrar)\b/i,
    );
  });

  it('grupo vazio usa a frase da política, com os limites dela', async () => {
    montar(
      fila({
        siga_no_ritmo: [
          item('siga_no_ritmo', {}, { id: 'NOVO0001', idadeDias: null, dataEngajamento: null }),
        ],
      }),
    );
    const foque = await screen.findByTestId('bloco-foque-agora');
    expect(screen.getByTestId('contador-foque-agora').textContent).toBe('0');
    expect(foque.textContent).toContain('Nenhum negócio seu está entre 41 e 60 dias hoje.');
    expect(within(foque).queryAllByTestId('fila-item')).toHaveLength(0);
    expect(screen.getByTestId('bloco-nutricao').textContent).toContain(
      'Nenhum negócio seu está com mais de 60 dias hoje.',
    );
  });

  it('"Encaminhar para nutrição" guarda a decisão com a data e a lista mostra que foi encaminhado', async () => {
    let f = completa();
    const deps = dependencias(
      clienteFalso({
        fila: async (pedido) => {
          const r = pedido.respostas.find((x) => x.dealId === 'NUTRI001');
          if (r?.decisao) {
            f = fila({
              ...f.blocos,
              nutricao: [
                item('nutricao', { decisao: r.decisao }, { id: 'NUTRI001', idadeDias: 90 }),
              ],
            });
          }
          return { ok: true, valor: f };
        },
      }),
    );
    render(
      <ProvedorApp deps={deps}>
        <SegundaFeira base={base} />
      </ProvedorApp>,
    );
    const nutricao = await screen.findByTestId('bloco-nutricao');
    fireEvent.click(within(nutricao).getByTestId('nutricao-alternar'));
    fireEvent.click(within(nutricao).getByTestId('fila-item-acao'));
    await waitFor(() =>
      expect(
        within(screen.getByTestId('bloco-nutricao')).getByTestId('fila-item-acao').textContent,
      ).toContain('Encaminhado em 22/10/2026.'),
    );
    // o encaminhado continua visível no grupo, com "Contestar" (vai para o detalhe)
    const contestar = within(screen.getByTestId('bloco-nutricao')).getByTestId(
      'fila-item-contestar',
    );
    expect(contestar.textContent).toBe('Contestar');
    expect(contestar.getAttribute('href')).toBe('#/deal/NUTRI001');
    expect(deps.repositorio.ler('NUTRI001')?.decisao).toMatchObject({
      acao: 'encaminhar_para_nutricao',
      aceita: true,
      motivo: null,
    });
  });

  it('"Encaminhar os N" pede confirmação; só "Sim, encaminhar" grava, um registro por negócio com a mesma data', async () => {
    const ids = ['NUTRI001', 'NUTRI002', 'NUTRI003'];
    let f = fila({
      nutricao: ids.map((id) => item('nutricao', {}, { id, idadeDias: 90 })),
    });
    const deps = dependencias(
      clienteFalso({
        fila: async (pedido) => {
          f = fila({
            nutricao: ids.map((id) => {
              const d = pedido.respostas.find((x) => x.dealId === id)?.decisao ?? null;
              return item('nutricao', { decisao: d }, { id, idadeDias: 90 });
            }),
          });
          return { ok: true, valor: f };
        },
      }),
    );
    render(
      <ProvedorApp deps={deps}>
        <SegundaFeira base={base} />
      </ProvedorApp>,
    );
    const nutricao = await screen.findByTestId('bloco-nutricao');
    fireEvent.click(within(nutricao).getByTestId('nutricao-lote'));
    expect(screen.getByTestId('nutricao-lote-pergunta').textContent).toBe(
      'Encaminhar 3 negócios para nutrição?',
    );
    // cancelar não grava nada
    fireEvent.click(screen.getByTestId('nutricao-lote-cancelar'));
    expect(ids.map((id) => deps.repositorio.ler(id))).toEqual([null, null, null]);
    expect(screen.getByTestId('nutricao-lote').textContent).toBe('Encaminhar os 3');

    fireEvent.click(screen.getByTestId('nutricao-lote'));
    fireEvent.click(screen.getByTestId('nutricao-lote-confirmar'));
    const decisoes = ids.map((id) => deps.repositorio.ler(id)?.decisao);
    expect(new Set(decisoes.map((d) => d?.em))).toEqual(new Set(['2026-10-22T12:00:00.000Z']));
    expect(decisoes.every((d) => d?.acao === 'encaminhar_para_nutricao' && d.aceita)).toBe(true);
    // depois do lote, ninguém mais pendente: o botão some; os encaminhados continuam no grupo
    await waitFor(() => expect(screen.queryByTestId('nutricao-lote')).toBeNull());
    expect(screen.getByTestId('contador-nutricao').textContent).toBe('3');
  });

  it('Foque vazio com Siga promovido: o Foque mostra os negócios do Siga e o Siga não aparece', async () => {
    montar(
      fila(
        {
          foque_agora: [
            item('siga_no_ritmo', {}, { id: 'SIGA0001', idadeDias: 10 }),
            item('siga_no_ritmo', {}, { id: 'SIGA0002', idadeDias: 20 }),
          ],
        },
        2,
      ),
    );
    const foque = await screen.findByTestId('bloco-foque-agora');
    expect(screen.getByTestId('contador-foque-agora').textContent).toBe('2');
    expect(within(foque).getAllByTestId('fila-item')).toHaveLength(2);
    expect(foque.textContent).toContain('Foque agora');
    expect(screen.queryByTestId('bloco-siga-no-ritmo')).toBeNull();
  });

  it('sem escolha guardada, a tela pergunta "Quem é você?" com o time agrupado; a escolha fica guardada', async () => {
    const deps = dependencias(clienteFalso(), null);
    render(
      <ProvedorApp deps={deps}>
        <SegundaFeira base={base} />
      </ProvedorApp>,
    );
    expect((await screen.findByTestId('quem-e-voce')).textContent).toContain('Quem é você?');
    const seletor = screen.getByTestId('seletor-perfil');
    expect(seletor.getAttribute('data-valor')).toBe('');
    expect(seletor.getAttribute('aria-haspopup')).toBe('listbox');
    expect(screen.queryByTestId('fila-item')).toBeNull();
    expect(document.body.textContent).toContain('não é login');
    // a lista abre pelo teclado, agrupada por escritório e manager, com as contagens de cada grupo
    fireEvent.keyDown(seletor, { key: 'ArrowDown' });
    const lista = screen.getByRole('listbox');
    expect(
      within(lista)
        .getAllByRole('group')
        .map((g) => g.getAttribute('aria-label')),
    ).toEqual(['West · Marcos Gestor']);
    const bruno = within(lista).getByRole('option', { name: /Bruno Campo/ });
    expect(bruno.textContent).toContain('Foque agora: 2');
    expect(bruno.textContent).toContain('Siga no ritmo: 0');
    expect(
      [...bruno.querySelectorAll('[data-grupo]')].map((c) => c.getAttribute('data-grupo')),
    ).toEqual(['foque_agora', 'siga_no_ritmo', 'sem_inicio', 'nutricao']);
    fireEvent.keyDown(lista, { key: 'ArrowDown' });
    expect(lista.getAttribute('aria-activedescendant')).toBe(bruno.id);
    fireEvent.keyDown(lista, { key: 'Enter' });
    expect(screen.queryByRole('listbox')).toBeNull();
    expect(seletor.getAttribute('data-valor')).toBe('Bruno Campo');
    expect(deps.perfil.ler()).toEqual({ tipo: 'vendedor', nome: 'Bruno Campo' });
    await screen.findByTestId('bloco-foque-agora');
  });

  it('vendedor sem negócio aberto: a frase própria e zero em todos os números', async () => {
    montar(fila({}));
    expect((await screen.findByTestId('sem-negocios')).textContent).toBe(
      'Você não tem negócios abertos agora.',
    );
    for (const slug of ['foque-agora', 'siga-no-ritmo', 'nutricao', 'ainda-nao-comecou']) {
      expect(screen.getByTestId('contador-' + slug).textContent).toBe('0');
    }
    expect(screen.getByTestId('receita-total').textContent).toBe(
      'Pela chance, quase nada deve sair dos seus negócios abertos hoje.',
    );
  });

  it('total arredondado abaixo de US$ 1: o topo diz "quase nada", o aviso e os sem data continuam; a comissão segue a mesma regra', async () => {
    const velho = deal({ id: 'NUTRI001', idadeDias: 120 });
    montar(
      fila({
        nutricao: [item('nutricao', { avaliacao: avaliacao(velho, { esperado: 0.4 }) }, velho)],
        sem_inicio: [
          item('sem_inicio', {}, { id: 'NOVO0001', idadeDias: null, dataEngajamento: null }),
          item('sem_inicio', {}, { id: 'NOVO0002', idadeDias: null, dataEngajamento: null }),
        ],
      }),
    );
    expect((await screen.findByTestId('receita-total')).textContent).toBe(
      'Pela chance, quase nada deve sair dos seus negócios abertos hoje.',
    );
    expect(screen.getByTestId('receita-aviso').textContent).toContain('Não é promessa.');
    expect(screen.getByTestId('receita-sem-data').textContent).toBe(
      '2 negócios sem data não entram na conta',
    );
    fireEvent.change(screen.getByTestId('comissao'), { target: { value: '10' } });
    expect(screen.getByTestId('comissao-total').textContent).toBe(
      'Sua comissão estimada nesses negócios: quase nada, pela chance.',
    );
  });

  it('comissão abaixo de US$ 1 com total acima: só a comissão diz "quase nada"', async () => {
    const d = deal({ id: 'SIGA0001', idadeDias: 10 });
    montar(
      fila({
        siga_no_ritmo: [item('siga_no_ritmo', { avaliacao: avaliacao(d, { esperado: 4 }) }, d)],
      }),
    );
    expect((await screen.findByTestId('receita-total')).textContent).toBe(
      'Dos seus negócios abertos hoje, devem sair cerca de US$ 4 nos próximos 3 meses.',
    );
    fireEvent.change(screen.getByTestId('comissao'), { target: { value: '10' } });
    expect(screen.getByTestId('comissao-total').textContent).toBe(
      'Sua comissão estimada nesses negócios: quase nada, pela chance.',
    );
  });
});
