/**
 * Fluxos ponta a ponta com o dado real, como o vendedor usa: "Quem é você?", a segunda-feira
 * dele com a receita esperada no topo, o deal do topo, um "Sim" que sobe o score e um "Não" que o
 * desce e muda a ação, a decisão
 * dele sobre a ação; a Nutrição recolhida e o "Encaminhar os N"; o vendedor sem nenhum negócio
 * aberto; o painel da equipe pelos filtros; e a fila que continua quando a API cai (modo local
 * com o mesmo domínio). O servidor do E2E sobe sem banco (ver playwright.config.ts).
 */
import { expect, test, type Page } from '@playwright/test';

/** Vendedor da região West com deals nos três blocos (medido no teste de integração da API). */
const VENDEDOR = 'Zane Levy';
/** Vendedor do time sem nenhum negócio no histórico (sales_teams.csv). */
const SEM_NEGOCIO = 'Carl Lin';
/** Vendedor da Central: só Nutrição e "Aborde primeiro", receita esperada US$ 0. */
const CENTRAL = 'Darcel Schlecht';
/** Vendedor com o Foque vazio e 2 negócios vivos no Siga: os 2 sobem para o Foque. */
const PROMOVIDA = 'Elease Gluck';

/** Junta os erros de console e de página; `ignorar` filtra os esperados (rede derrubada de propósito). */
function vigiarConsole(page: Page, ignorar?: RegExp): string[] {
  const erros: string[] = [];
  page.on('console', (m) => {
    if (m.type() === 'error' && !(ignorar && ignorar.test(m.text()))) erros.push(m.text());
  });
  page.on('pageerror', (e) => erros.push(e.message));
  return erros;
}

async function escolherQuemSou(page: Page, vendedor: string): Promise<void> {
  await page.goto('/');
  await expect(page.getByTestId('quem-e-voce')).toContainText('Quem é você?');
  await page.getByTestId('seletor-perfil').click();
  await page.locator('[role="option"][data-valor="' + vendedor + '"]').click();
  await expect(page.getByTestId('seletor-perfil')).toHaveAttribute('data-valor', vendedor);
}

async function abrirSegundaDe(page: Page, vendedor: string): Promise<void> {
  await escolherQuemSou(page, vendedor);
  await expect(page.getByTestId('fila-item').first()).toBeVisible();
}

/**
 * Abre a Nutrição e todos os "Mostrar mais", e lê o score de cada cartão, por grupo. O score é a
 * qualidade (a idade medida + as respostas), não a posição: cada cartão diz "Score {n}" de 0 a 100
 * ou "Score —" (sem data e sem resposta); toda a Nutrição fica em 15 ou menos; o Siga no ritmo
 * fica igual ou acima do Foque agora; e nenhum "X em 10" na tela.
 */
async function conferirScores(page: Page): Promise<Record<string, (number | null)[]>> {
  await page.getByTestId('nutricao-alternar').click();
  await expect(page.getByTestId('lista-nutricao')).toBeVisible();
  const mais = page.getByRole('button', { name: /^Mostrar mais/ });
  for (let i = 0; i < 60 && (await mais.count()) > 0; i++) await mais.first().click();
  await expect(mais).toHaveCount(0);
  const ler = async (grupo: string) =>
    (await page.getByTestId(grupo).getByTestId('fila-item-indicador').allTextContents()).map(
      (t) => {
        expect(t).toMatch(/^Score (\d{1,3}|—)$/);
        return t === 'Score —' ? null : Number(t.replace('Score ', ''));
      },
    );
  const porGrupo: Record<string, (number | null)[]> = {};
  for (const g of [
    'bloco-foque-agora',
    'bloco-siga-no-ritmo',
    'grupo-ainda-nao-comecou',
    'bloco-nutricao',
  ])
    porGrupo[g] = (await page.getByTestId(g).count()) > 0 ? await ler(g) : [];
  const numeros = (g: string) => (porGrupo[g] ?? []).filter((x): x is number => x !== null);
  expect(numeros('bloco-nutricao').length).toBeGreaterThan(10);
  expect(Math.max(...numeros('bloco-nutricao'))).toBeLessThanOrEqual(15);
  if (numeros('bloco-foque-agora').length && numeros('bloco-siga-no-ritmo').length)
    expect(Math.min(...numeros('bloco-siga-no-ritmo'))).toBeGreaterThanOrEqual(
      Math.max(...numeros('bloco-foque-agora')),
    );
  expect(await page.locator('body').textContent()).not.toMatch(/em 10\b|em cada 10/);
  return porGrupo;
}

test('segunda-feira do vendedor → deal do topo → "Sim" sobe o score → "Não" desce e muda a ação → a decisão fica guardada', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, VENDEDOR);

  for (const id of ['bloco-foque-agora', 'bloco-siga-no-ritmo', 'bloco-nutricao']) {
    await expect(page.getByTestId(id)).toBeVisible();
  }
  const topo = page.getByTestId('bloco-foque-agora').getByTestId('fila-item').first();
  // o cartão: 3 linhas (score, ação, produto · preço em jogo · ver por quê) e nada mais
  await expect(topo.locator(':scope > *')).toHaveCount(3);
  await expect(topo.getByTestId('fila-item-indicador')).toHaveText(/^Score \d{1,3}$/);
  const scoreNoCartao = Number(
    ((await topo.getByTestId('fila-item-indicador').textContent()) ?? '').replace('Score ', ''),
  );
  await expect(topo.getByTestId('fila-item-acao')).toHaveText(
    'A chance está caindo: marque a próxima conversa esta semana.',
  );
  await expect(topo.getByTestId('fila-item-produto')).toHaveText(
    /^.+ · US\$ [\d.]+ em jogo · ver por quê$/,
  );
  const id = await topo.getAttribute('data-deal-id');
  expect(id).toBeTruthy();

  // "ver por quê" abre o detalhe: o porquê do score, a posição, a chance e os fatores ficam lá
  await topo.getByTestId('fila-item-porque').click();
  await expect(page).toHaveURL(new RegExp('#/deal/' + id));
  await expect(page.getByTestId('deal-bloco')).toBeVisible();
  await expect(page.getByTestId('deal-porque')).not.toBeEmpty();
  await expect(page.getByTestId('deal-preco')).toContainText('Preço de tabela: US$');
  await expect(page.getByTestId('deal-indicador')).toContainText('Score ' + scoreNoCartao);
  await expect(page.getByTestId('deal-em-jogo')).toHaveText(/^.+ · US\$ [\d.]+ em jogo$/);
  // o porquê do score: a idade contra a melhor faixa e, por último, a posição na lista
  const porque = page.getByTestId('deal-porque-score');
  await expect(porque).toContainText(
    /Aberto há \d+ dias: \d+% dos negócios com essa idade fecharam \(a melhor faixa fecha \d+%\)\./,
  );
  await expect(page.getByTestId('deal-posicao')).toHaveText(
    /^Na sua lista: \d+º de \d+ \(o grupo, depois o que há a ganhar\)\.$/,
  );
  // a chance absoluta e a conta por fator, com os zeros e o motivo
  await expect(page.getByTestId('deal-chance-absoluta')).toHaveText(
    /^Chance de fechar em 3 meses: \d+%$/,
  );
  await expect(page.getByTestId('deal-conta')).toContainText('Idade:');
  await expect(page.getByTestId('deal-conta')).toContainText('não muda a chance no histórico');

  const acao = page.getByTestId('deal-acao');
  const antes = (await acao.textContent()) ?? '';
  const grupo = (await page.getByTestId('deal-bloco').textContent()) ?? '';
  const numero = page.getByTestId('deal-indicador').locator('.indicador__numero');
  const depois = Math.max(0, scoreNoCartao + 10 - 15);
  // "Sim" sobe o score (+10) e aparece no porquê; a ação continua
  await page.getByTestId('pergunta-decisor-sim').click();
  await expect(numero).toHaveText('Score ' + (scoreNoCartao + 10));
  await expect(porque).toContainText('Decisor confirmado: +10');
  await expect(acao).toHaveText(antes);
  // "Não" desce o score (−15) e troca a ação pela frase da pergunta
  await page.getByTestId('pergunta-proximo_passo-nao').click();
  await expect(numero).toHaveText('Score ' + depois);
  await expect(porque).toContainText('Sem próxima conversa marcada: −15');
  await expect(acao).not.toHaveText(antes);
  await expect(acao).toHaveText(
    'Proponha uma data agora. Sem data marcada, a chance continua caindo.',
  );
  // a resposta muda o score e a ação, nunca o grupo
  await expect(page.getByTestId('deal-bloco')).toHaveText(grupo);

  // contestar exige motivo; com motivo, a decisão do vendedor fica registrada
  await page.getByTestId('acao-contestar').click();
  await page.getByTestId('acao-enviar-contestacao').click();
  await expect(page.getByTestId('acao-decisao')).toHaveCount(0);
  await page.getByTestId('acao-motivo').fill('O cliente pediu para falar só em janeiro.');
  await page.getByTestId('acao-enviar-contestacao').click();
  await expect(page.getByTestId('acao-decisao')).toContainText('janeiro');

  // a resposta e a decisão sobrevivem ao recarregar
  await page.reload();
  await expect(page.getByTestId('deal-acao')).toContainText('Proponha uma data');
  await expect(page.getByTestId('acao-decisao')).toContainText('janeiro');
  await expect(numero).toHaveText('Score ' + depois);
  // na lista, o cartão mostra o score novo; a ordem da tela não mudou (ainda o primeiro do Foque)
  await page.goto('/');
  const primeiro = page.getByTestId('bloco-foque-agora').getByTestId('fila-item').first();
  await expect(primeiro).toHaveAttribute('data-deal-id', id ?? '');
  await expect(primeiro.getByTestId('fila-item-indicador')).toHaveText('Score ' + depois);
  expect(erros).toEqual([]);
});

test('receita esperada no topo da lista, com o aviso e a comissão opcional', async ({ page }) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, VENDEDOR);
  const total = page.getByTestId('receita-total');
  await expect(total).toContainText('Dos seus negócios abertos hoje, devem sair cerca de US$');
  await expect(total).toContainText('nos próximos 3 meses.');
  await expect(page.getByTestId('receita-aviso')).toContainText('Não é promessa.');
  // o campo de comissão começa vazio, sem percentual sugerido
  await expect(page.getByTestId('comissao')).toHaveValue('');
  await expect(page.getByTestId('comissao-total')).toHaveCount(0);
  await page.getByTestId('comissao').fill('10');
  await expect(page.getByTestId('comissao-total')).toContainText(
    'Sua comissão estimada nesses negócios: cerca de US$',
  );
  // a escolha de quem é e a comissão ficam neste navegador
  await page.reload();
  await expect(page.getByTestId('seletor-perfil')).toHaveAttribute('data-valor', VENDEDOR);
  await expect(page.getByTestId('comissao')).toHaveValue('10');
  // vendedor de West: o score é a qualidade; o Siga fica acima do Foque e a Nutrição em 15 ou menos
  const zane = await conferirScores(page);
  expect(zane['bloco-foque-agora']?.length).toBeGreaterThan(0);
  expect(zane['bloco-siga-no-ritmo']?.length).toBeGreaterThan(0);
  expect(erros).toEqual([]);
});

test('Nutrição recolhida → "Encaminhar os N" com confirmação → encaminhados visíveis, com "Contestar"', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, VENDEDOR);
  const nutricao = page.getByTestId('bloco-nutricao');
  // recolhida: só a contagem
  await expect(nutricao.getByTestId('fila-item')).toHaveCount(0);
  const n = Number((await page.getByTestId('contador-nutricao').textContent())?.trim());
  expect(n).toBeGreaterThan(1);

  await nutricao.getByTestId('nutricao-lote').click();
  await expect(page.getByTestId('nutricao-lote-pergunta')).toHaveText(
    'Encaminhar ' + n + ' negócios para nutrição?',
  );
  await page.getByTestId('nutricao-lote-cancelar').click();
  await expect(nutricao.getByTestId('nutricao-lote')).toHaveText('Encaminhar os ' + n);

  await nutricao.getByTestId('nutricao-lote').click();
  await page.getByTestId('nutricao-lote-confirmar').click();
  await expect(nutricao.getByTestId('nutricao-lote')).toHaveCount(0);

  // continuam no grupo, marcados e com "Contestar"
  await page.reload();
  await expect(page.getByTestId('contador-nutricao')).toHaveText(String(n));
  await page.getByTestId('bloco-nutricao').getByTestId('nutricao-alternar').click();
  const primeiro = page.getByTestId('bloco-nutricao').getByTestId('fila-item').first();
  await expect(primeiro.getByTestId('fila-item-acao')).toContainText('Encaminhado em');
  await expect(primeiro.getByTestId('fila-item-contestar')).toHaveText('Contestar');
  expect(erros).toEqual([]);
});

test('vendedor sem negócio aberto: a frase própria e zero em todos os números', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await escolherQuemSou(page, SEM_NEGOCIO);
  await expect(page.getByTestId('sem-negocios')).toHaveText('Você não tem negócios abertos agora.');
  for (const slug of ['foque-agora', 'siga-no-ritmo', 'nutricao', 'ainda-nao-comecou']) {
    await expect(page.getByTestId('contador-' + slug)).toHaveText('0');
  }
  await expect(page.getByTestId('receita-total')).toHaveText(
    'Pela chance, quase nada deve sair dos seus negócios abertos hoje.',
  );
  await expect(page.getByTestId('fila-item')).toHaveCount(0);
  expect(erros).toEqual([]);
});

test('vendedor da Central: só negócios antigos, receita pequena no topo, com o aviso e os sem data fora da conta', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, CENTRAL);
  // a ordem dos grupos: do que mais precisa do vendedor para o que menos precisa
  const grupos = await page
    .locator('[data-testid^="bloco-"], [data-testid="grupo-ainda-nao-comecou"]')
    .evaluateAll((els) => els.map((e) => e.getAttribute('data-testid')));
  expect(grupos).toEqual([
    'bloco-foque-agora',
    'bloco-siga-no-ritmo',
    'grupo-ainda-nao-comecou',
    'bloco-nutricao',
  ]);
  // só Nutrição (acima de 60 dias): a nota ainda dá uma chance pequena, não zero
  await expect(page.getByTestId('receita-total')).toHaveText(
    'Dos seus negócios abertos hoje, devem sair cerca de US$ 1.736 nos próximos 3 meses.',
  );
  await expect(page.getByTestId('receita-aviso')).toContainText('Não é promessa.');
  await expect(page.getByTestId('receita-sem-data')).toContainText(
    'negócios sem data não entram na conta',
  );
  await page.getByTestId('comissao').fill('10');
  await expect(page.getByTestId('comissao-total')).toHaveText(
    'Sua comissão estimada nesses negócios: cerca de US$ 174',
  );
  // o seletor mostra, na cor de cada grupo, quantos abertos cada vendedor tem em cada um
  await page.getByTestId('seletor-perfil').click();
  const opcao = page.locator('[role="option"][data-valor="' + CENTRAL + '"]');
  await expect(opcao).toContainText('Foque agora: 0');
  await expect(opcao).toContainText('Aborde primeiro: 111');
  await expect(opcao).toContainText('Nutrição: 83');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('listbox')).toHaveCount(0);
  // sem Foque e sem Siga, o primeiro grupo com negócio é o Aborde primeiro, antes da Nutrição
  await expect(page.getByTestId('grupo-ainda-nao-comecou')).toContainText('Aborde primeiro');
  await expect(page.getByTestId('contador-ainda-nao-comecou')).toHaveText('111');
  const semData = page.getByTestId('grupo-ainda-nao-comecou').getByTestId('fila-item').first();
  await expect(semData.getByTestId('fila-item-acao')).toHaveText(
    'Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver.',
  );
  // sem data e sem resposta: "Score —" e, no detalhe, o pedido para responder
  await expect(semData.getByTestId('fila-item-indicador')).toHaveText('Score —');
  await semData.getByTestId('fila-item-porque').click();
  await expect(page.getByTestId('deal-porque-score')).toContainText(
    'Responda as perguntas para pontuar.',
  );
  await page.goBack();
  await expect(page.getByTestId('fila-item').first()).toBeVisible();
  const central = await conferirScores(page);
  expect(central['grupo-ainda-nao-comecou']?.every((x) => x === null)).toBe(true);
  expect(erros).toEqual([]);
});

test('Foque vazio com 2 negócios vivos no Siga: o Foque mostra os 2 e o Siga some (Elease Gluck)', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, PROMOVIDA);
  await expect(page.getByTestId('contador-foque-agora')).toHaveText('2');
  const foque = page.getByTestId('bloco-foque-agora');
  await expect(foque.getByTestId('fila-item')).toHaveCount(2);
  await expect(page.getByTestId('bloco-siga-no-ritmo')).toHaveCount(0);
  // cada cartão com o score (a idade deles é de Siga: 90 ou mais) e 3 linhas
  const scores = (await foque.getByTestId('fila-item-indicador').allTextContents()).map((t) =>
    Number(t.replace('Score ', '')),
  );
  expect(scores.every((x) => x >= 90 && x <= 100)).toBe(true);
  for (const cartao of await foque.getByTestId('fila-item').all())
    await expect(cartao.locator(':scope > *')).toHaveCount(3);
  // o seletor conta o que a tela mostra
  await page.getByTestId('seletor-perfil').click();
  await expect(page.locator('[role="option"][data-valor="' + PROMOVIDA + '"]')).toContainText(
    'Foque agora: 2',
  );
  await page.keyboard.press('Escape');
  expect(erros).toEqual([]);
});

test('painel da equipe: 4 métricas e a tabela dos 35 vendedores, só leitura; o filtro por região muda os números', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await page.goto('/#/manager');
  for (const id of ['receita', 'foque-sem-conversa', 'parado', 'sem-inicio'])
    await expect(page.getByTestId('metrica-' + id)).toBeVisible();
  await expect(page.locator('.metrica')).toHaveCount(4);
  // sem filtro: o time inteiro
  await expect(page.getByTestId('painel-receita')).toHaveText('US$ 69.395');
  await expect(page.getByTestId('painel-foque-sem-conversa')).toHaveText('33');
  await expect(page.getByTestId('painel-foque-sem-conversa-valor')).toHaveText(
    'US$ 67.896 em jogo',
  );
  await expect(page.getByTestId('painel-parado')).toHaveText('1.532');
  await expect(page.getByTestId('painel-parado-valor')).toHaveText('US$ 3.779.334 em jogo');
  await expect(page.getByTestId('painel-sem-inicio')).toHaveText('500');
  await expect(page.getByTestId('painel-sem-inicio-valor')).toHaveText('US$ 1.073.986 em jogo');
  await expect(page.getByTestId('metrica-foque-sem-conversa')).toContainText(
    'vai esfriar se ninguém agir',
  );
  // a tabela: os 35 vendedores, inclusive os sem negócio, do que mais tem Foque sem próxima
  // conversa para o que menos tem
  const linhas = page.getByTestId('painel-vendedores').locator('tbody tr');
  await expect(linhas).toHaveCount(35);
  const foqueNaTabela = (await linhas.locator('td:nth-of-type(2)').allTextContents()).map((t) =>
    Number(t.split(' · ')[0]),
  );
  expect(foqueNaTabela).toEqual([...foqueNaTabela].sort((a, b) => b - a));
  await expect(page.getByTestId('filtro-vendedor').locator('option')).toHaveCount(36);
  // a curva por idade foi para "Como a nota funciona"
  await expect(page.getByTestId('painel-curva')).toHaveCount(0);

  // o E2E sobe sem banco: o painel e o rodapé dizem que as respostas ficam neste navegador
  await expect(page.getByTestId('painel-respostas')).toContainText(
    'Respostas gravadas neste navegador:',
  );
  await expect(page.getByTestId('rodape-respostas')).toContainText(
    'suas respostas ficam só neste navegador.',
  );
  await page.getByTestId('filtro-regiao').selectOption('Central');
  await expect(page.getByTestId('painel-foque-sem-conversa')).toHaveText('0');
  await expect(page.getByTestId('painel-sem-inicio')).toHaveText('500');
  await page.getByTestId('filtro-regiao').selectOption('West');
  await expect(page.getByTestId('painel-receita')).toHaveText('US$ 38.435');
  await expect(page.getByTestId('painel-foque-sem-conversa')).toHaveText('17');
  await expect(page.getByTestId('painel-foque-sem-conversa-valor')).toHaveText(
    'US$ 36.502 em jogo',
  );
  await expect(page.getByTestId('painel-parado')).toHaveText('716');
  await expect(page.getByTestId('painel-sem-inicio')).toHaveText('0');
  await expect(linhas).toHaveCount(12);
  await expect(page.getByRole('button', { name: /aprovar|encaminhar/i })).toHaveCount(0);
  expect(erros).toEqual([]);
});

test('API derrubada → banner de modo local e a segunda-feira continua', async ({ page }) => {
  // rede derrubada de propósito: o navegador registra as requisições abortadas
  const erros = vigiarConsole(page, /Failed to load resource|ERR_FAILED/);
  await page.route('**/api/**', (r) => r.abort());
  await page.route('**/health', (r) => r.abort());
  await abrirSegundaDe(page, VENDEDOR);
  await expect(page.getByTestId('banner-modo-local')).toBeVisible();
  await expect(
    page.getByTestId('bloco-foque-agora').getByTestId('fila-item').first(),
  ).toBeVisible();
  await expect(page.getByTestId('receita-total')).toContainText('US$');
  await expect(page.getByTestId('rodape-respostas')).toContainText(
    'suas respostas ficam só neste navegador.',
  );
  expect(erros).toEqual([]);
});

test('como funciona e lead novo, com o dado real', async ({ page }) => {
  const erros = vigiarConsole(page);
  await page.goto('/#/como-funciona');
  await expect(page.getByTestId('como-funciona')).toBeVisible();
  await expect(page.getByTestId('tabela-chance')).toBeVisible();
  await expect(page.getByTestId('tabela-chance')).toContainText('7%');
  // a qualidade do dado mora aqui, não no painel da equipe
  await expect(page.getByTestId('como-funciona-qualidade')).toContainText('1.425');
  await expect(page.getByTestId('como-funciona-score')).toContainText(
    'O score diz se o negócio é bom, de 0 a 100.',
  );
  await expect(page.getByTestId('como-funciona-score')).toContainText(
    'cada "Sim" soma 10 e cada "Não" tira 15 (esses pesos são uma escolha nossa',
  );
  await expect(page.getByTestId('como-funciona-score')).toContainText('O preço não entra no score');
  await expect(page.getByTestId('como-funciona')).not.toContainText(/em 10\b|em cada 10/);
  // a tabela que o motor gerou: cada fator, se entrou, o acerto sozinho e os pontos por valor
  const motor = page.getByTestId('tabela-motor');
  await expect(motor).toBeVisible();
  await expect(motor.locator('tbody tr')).toHaveCount(19);
  await expect(motor.locator('tr[data-fator="idade"]')).toContainText('entrou na chance');
  await expect(motor.locator('tr[data-fator="setor"]')).toContainText('não melhorou a previsão');
  await expect(page.getByTestId('como-funciona-acerto')).toContainText('Só com a idade:');

  await page.goto('/#/novo-lead');
  const form = page.getByTestId('novo-lead-form');
  await form.locator('#lead-vendedor').selectOption(VENDEDOR);
  await form.locator('#lead-produto').selectOption({ index: 1 });
  await form.getByRole('button').click();
  await expect(page.getByTestId('novo-lead-status')).not.toBeEmpty();
  expect(erros).toEqual([]);
});

test('datas no formato brasileiro em toda a interface; nenhuma "2017-12-31" à vista', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, VENDEDOR);
  await expect(page.getByTestId('rodape-referencia')).toHaveText(
    'Dados até 31/12/2017. As idades são contadas até essa data.',
  );
  const deal = await page.getByTestId('fila-item').first().getAttribute('data-deal-id');
  for (const rota of ['/', '/#/deal/' + deal, '/#/manager', '/#/novo-lead', '/#/como-funciona']) {
    await page.goto(rota);
    await page.waitForLoadState('networkidle');
    const texto = await page.evaluate(() => document.body.innerText);
    expect(texto, 'data em ISO em ' + rota).not.toContain('2017-12-31');
    expect(texto, 'data em ISO em ' + rota).not.toMatch(/\b\d{4}-\d{2}-\d{2}\b/);
  }
  expect(erros).toEqual([]);
});

test('390 px sem rolagem horizontal e sem marca de terceiros em nenhuma tela @celular', async ({
  page,
}) => {
  const erros = vigiarConsole(page);
  await abrirSegundaDe(page, VENDEDOR);
  const deal = await page.getByTestId('fila-item').first().getAttribute('data-deal-id');
  for (const rota of ['/', '/#/deal/' + deal, '/#/manager', '/#/novo-lead', '/#/como-funciona']) {
    await page.goto(rota);
    await page.waitForLoadState('networkidle');
    const { largura, rolagem, texto } = await page.evaluate(() => ({
      largura: window.innerWidth,
      rolagem: document.documentElement.scrollWidth,
      texto: document.body.innerText,
    }));
    expect(rolagem, 'rolagem horizontal em ' + rota).toBeLessThanOrEqual(largura);
    expect(texto, 'marca de terceiros em ' + rota).not.toMatch(/\bG4\b/);
  }
  expect(erros).toEqual([]);
});
