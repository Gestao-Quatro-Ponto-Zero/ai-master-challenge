import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import App from '../App';
import { MockDealsApi } from '../api/mock/MockDealsApi';
import type { ListDealsQuery } from '../api/types';

const memory = () => {
  const m = new Map<string, string>();
  return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) };
};
const setup = (url = '/', showProbability = false) => {
  window.history.replaceState(null, '', url);
  const api = new MockDealsApi({ latencyMs: 0, storage: memory(), showProbability });
  render(<App api={api} />);
  return { api, user: userEvent.setup() };
};

describe('SellerPage', () => {
  it('shows "Meu dia" first with the user', async () => {
    setup();
    expect(await screen.findByText('Vicki Laflamme')).toBeInTheDocument();
    expect(await screen.findByRole('region', { name: 'Deals de hoje' })).toBeInTheDocument();
  });

  it('switches to the pipeline and shows KPIs and rows', async () => {
    const { user } = setup();
    await user.click(await screen.findByRole('tab', { name: /Todo o pipeline/ }));
    expect(await screen.findByText('Em foco esta semana')).toBeInTheDocument();
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(1));
    expect(window.location.search).toContain('view=all');
  });

  it('restores state from the URL', async () => {
    setup('/?view=all&tab=review');
    const tab = await screen.findByRole('tab', { name: /A revisar/ });
    expect(tab).toHaveAttribute('aria-selected', 'true');
  });

  it('shows an error banner when the API fails and retries', async () => {
    window.history.replaceState(null, '', '/');
    const api = new MockDealsApi({ latencyMs: 0, storage: memory() });
    let fail = true;
    const orig = api.listTodayDeals.bind(api);
    api.listTodayDeals = async (qy) => { if (fail) throw new Error('boom'); return orig(qy); };
    const user = userEvent.setup();
    render(<App api={api} />);
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    fail = false;
    await user.click(screen.getByRole('button', { name: /Tentar de novo/ }));
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument());
  });

  it('detalhe separa índice, preço, valor esperado, confiança e completude, e explica os fatores', async () => {
    const { user } = setup('/?view=all&tab=focus');
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(0));
    await user.click(document.querySelectorAll('.dealrow')[0] as HTMLElement);
    const ind = await screen.findByLabelText('Indicadores do deal');
    expect(within(ind).getByText('Índice de prioridade')).toBeInTheDocument();
    expect(within(ind).getByText(/Não é uma probabilidade/)).toBeInTheDocument();
    expect(within(ind).getByText('Preço do deal')).toBeInTheDocument();
    expect(within(ind).getByText('Valor esperado')).toBeInTheDocument();
    expect(within(ind).getByText(/próximos 30 dias/)).toBeInTheDocument();
    expect(within(ind).queryByText('Probabilidade de fechar')).not.toBeInTheDocument();
    expect(await screen.findByRole('table', { name: 'Fatores que explicam a prioridade' })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: 'Referência' })).toBeInTheDocument();
    expect(screen.getByText('Confiança da previsão')).toBeInTheDocument();
    expect(screen.getByText('Completude dos dados')).toBeInTheDocument();
  });

  it('mostra a Chance ao lado do valor esperado quando a API a envia', async () => {
    const { user } = setup('/?view=all&tab=focus', true);
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(0));
    const row = document.querySelectorAll('.dealrow')[0] as HTMLElement;
    expect(within(row).getByText(/Esperado US\$/)).toBeInTheDocument();
    expect(within(row).getByText(/Chance \d+(,\d)?%/)).toBeInTheDocument();
    await user.click(row);
    const ind = await screen.findByLabelText('Indicadores do deal');
    expect(within(ind).getByText('Chance de fechar')).toBeInTheDocument();
  });

  it('hides probability by default (F7)', async () => {
    const { user } = setup('/?view=all');
    await screen.findByText('Em foco esta semana');
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(0));
    await user.click(document.querySelectorAll('.dealrow')[0] as HTMLElement);
    expect(screen.queryByText(/Probabilidade de ganho/i)).not.toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/Chance \d/);
  });

  it('opens the "how it works" modal and closes with Esc', async () => {
    const { user } = setup();
    await user.click(await screen.findByRole('button', { name: /Como a prioridade é calculada/ }));
    const dlg = await screen.findByRole('dialog');
    expect(within(dlg).getByRole('button', { name: 'Fechar' })).toBeInTheDocument();
    expect(within(dlg).getByText(/próximos 30 dias/, { selector: 'strong' })).toBeInTheDocument();
    expect(within(dlg).getByText(/Decidir agora/)).toBeInTheDocument();
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('filters by search text and clears', async () => {
    const { user } = setup('/?view=all');
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(3));
    await user.type(screen.getByRole('searchbox'), 'zzzz-nada');
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBe(0));
    expect(window.location.search).toContain('q=zzzz-nada');
    await user.click(screen.getAllByRole('button', { name: /Limpar filtros/ })[0]);
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(3));
  });

  it('bulk-closes selected review deals after confirmation, then undoes', async () => {
    const { user } = setup('/?view=all&tab=review');
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(0));
    const before = document.querySelectorAll('.dealrow').length;
    await user.click(screen.getAllByRole('checkbox')[1]);
    await user.click(screen.getByRole('button', { name: /Encerrar como perdidos/ }));
    await user.click(screen.getByRole('button', { name: 'Confirmar' }));
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBe(before - 1));
    await user.click(await screen.findByRole('button', { name: 'Desfazer' }));
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBe(before));
  });

  it('records feedback with a reason and shows history', async () => {
    const { user } = setup('/?view=all');
    await waitFor(() => expect(document.querySelectorAll('.dealrow').length).toBeGreaterThan(0));
    await user.click(await screen.findByRole('button', { name: /Discordo da prioridade/ }));
    await user.click(screen.getByRole('button', { name: /Enviar sem motivo/ }));
    expect(await screen.findByRole('list', { name: 'Histórico de feedback' })).toBeInTheDocument();
  });

  it('cada troca de aba, filtro, ordem e página pede uma nova lista à API com a query certa', async () => {
    window.history.replaceState(null, '', '/?view=all');
    const api = new MockDealsApi({ latencyMs: 0, storage: memory() });
    const queries: ListDealsQuery[] = [];
    const orig = api.listDeals.bind(api);
    api.listDeals = async (qy) => { queries.push(qy); return orig(qy); };
    const user = userEvent.setup();
    render(<App api={api} />);
    await waitFor(() => expect(queries.length).toBeGreaterThan(0));
    const last = () => queries[queries.length - 1];
    expect(last()).toMatchObject({ tab: 'focus', level: 'all', sort: null, page: 1 });

    await user.click(await screen.findByRole('tab', { name: /A revisar/ }));
    await waitFor(() => expect(last().tab).toBe('review'));

    await user.selectOptions(document.getElementById('sort') as HTMLSelectElement, 'expected_value');
    await waitFor(() => expect(last()).toMatchObject({ tab: 'review', sort: 'expected_value' }));

    await user.click(await screen.findByRole('tab', { name: /Foco/ }));
    await user.selectOptions(document.getElementById('prod') as HTMLSelectElement, 'GTX Pro');
    await waitFor(() => expect(last()).toMatchObject({ tab: 'focus', product: 'GTX Pro', page: 1 }));
  });
});

