/**
 * PROVISÓRIO — será substituído pela política escolhida na próxima etapa do projeto.
 *
 * Os limites dos blocos seguem a curva medida no histórico: até 40 dias fecharam perto de 50%;
 * de 41 a 60 dias cai a cada 10 dias; acima de 60 dias quase nenhum fechou. A faixa mede se o
 * negócio anda, não se ele é bom. Três coisas separadas: o score é a qualidade (a idade medida + as
 * respostas do vendedor); a ordem da tela é o grupo, depois o que há a ganhar; o preço é quanto
 * está em jogo.
 * Acima do limite, a ação é encaminhar para nutrição (o negócio sai da fila ativa).
 *
 * A chance de cada negócio NÃO está aqui: o domínio a calcula pelo replay (`chance`), a partir
 * do deals.json. Os textos da tela também ficam aqui, para trocar sem mexer no componente;
 * `{…}` são valores que o domínio preenche.
 */
import type { PoliticaPriorizacao } from './index';

export const politicaProvisoria: PoliticaPriorizacao = {
  id: 'politica-provisoria-v2',
  nome: 'Política provisória',
  versao: '0.2.0',
  provisoria: true,
  aviso:
    'Política provisória: os limites vêm da curva medida no histórico e ainda podem ser recalibrados.',
  faixas: [
    {
      bloco: 'siga_no_ritmo',
      ateDias: 40,
      rotulo: 'até 40 dias',
      porque: 'Até 40 dias, a chance de fechar medida no histórico ainda é a mais alta.',
    },
    {
      bloco: 'foque_agora',
      ateDias: 60,
      rotulo: '41 a 60 dias',
      porque:
        'De 41 a 60 dias, a chance medida no histórico cai a cada 10 dias: é agora que o negócio decide.',
    },
    {
      bloco: 'nutricao',
      ateDias: null,
      rotulo: 'acima de 60 dias',
      porque:
        'Acima de 60 dias, quase nenhum negócio do histórico fechou; nenhum fechou depois do teto do dataset.',
    },
  ],
  semData: {
    rotulo: 'Aborde primeiro',
    porque: 'Sem data de início não há idade: ainda não houve a primeira conversa.',
  },
  chance: {
    corteDias: 92,
    faixas: [
      { ateDias: 10 },
      { ateDias: 20 },
      { ateDias: 30 },
      { ateDias: 40 },
      { ateDias: 50 },
      { ateDias: 60 },
      { ateDias: 90 },
      { ateDias: null },
    ],
  },
  leitura:
    'O score diz se o negócio é bom: a idade dele contra o histórico e as suas respostas. A ordem da tela diz por onde começar. O preço diz quanto está em jogo.',
  ordenacao: {
    rotulo: 'Ordem da tela',
    porque:
      'A ordem da tela é primeiro o grupo; dentro dele, o que há a ganhar: a chance de fechar medida no histórico × o preço de tabela do produto (sem data de início, só o preço). O score não muda a ordem.',
  },
  textos: {
    pagina: {
      titulo: 'Onde focar hoje',
      subtitulo: 'Seus {n} negócios abertos, do que mais precisa de você para o que menos precisa.',
      quem: 'Quem é você?',
      escolha: 'Escolha o seu nome',
      semNegocios: 'Você não tem negócios abertos agora.',
    },
    indicador: {
      semNumero: '—',
      aviso:
        'O score diz se o negócio é bom: a idade dele contra o histórico e as suas respostas. O preço fica fora do score: ele diz quanto está em jogo.',
    },
    receita: {
      porNegocio: 'Deve render cerca de US$ {esperado} em 3 meses (estimativa pela chance).',
      zero: 'Pela chance, quase nada deve render.',
      semData: 'Sem data de início: não dá pra estimar.',
      preco: 'Preço de tabela: US$ {valor}',
      total:
        'Dos seus negócios abertos hoje, devem sair cerca de US$ {total} nos próximos 3 meses.',
      totalQuaseNada: 'Pela chance, quase nada deve sair dos seus negócios abertos hoje.',
      aviso:
        'Estimativa pelo histórico: chance de fechar × preço de tabela. Não conta negócios novos que vão entrar. Não é promessa.',
      semDataNaConta: '{n} negócios sem data não entram na conta',
      semDataNaContaUm: '1 negócio sem data não entra na conta',
      campo: 'Sua comissão (%)',
      comissao: 'Sua comissão estimada nesses negócios: cerca de US$ {valor}',
      comissaoQuaseNada: 'Sua comissão estimada nesses negócios: quase nada, pela chance.',
    },
    nutricao: {
      mostrar: 'Mostrar os {n}',
      recolher: 'Recolher',
      botao: 'Encaminhar os {n}',
      pergunta: 'Encaminhar {n} negócios para nutrição?',
      confirmar: 'Sim, encaminhar',
      cancelar: 'Cancelar',
      encaminhado: 'Encaminhado em {data}.',
      contestar: 'Contestar',
    },
    painel: {
      titulo: 'Acompanhar a equipe',
      subtitulo:
        'Onde o time está perdendo dinheiro, contado na lista de cada vendedor. Só para ler: quem age em cada negócio é o vendedor.',
      receita: {
        titulo: 'Receita esperada do time',
        rotulo: 'nos próximos 3 meses, sem contar negócios novos',
        mede: 'Soma da chance × preço de tabela dos negócios abertos com data de início. Não é promessa.',
      },
      foqueSemConversa: {
        titulo: 'Foque agora sem próxima conversa marcada',
        rotulo: 'vai esfriar se ninguém agir',
        mede: 'Negócios que a tela do vendedor mostra em Foque agora sem "Sim" para "Tem próxima conversa marcada, com data?", e o preço deles somado.',
      },
      parado: {
        titulo: 'Pipeline parado',
        rotulo: 'inflando o pipeline',
        mede: 'Abertos há mais de {limite} dias (Nutrição), e o preço deles somado. Nessa idade quase nenhum negócio do histórico fechou.',
      },
      semInicio: {
        titulo: 'Leads sem primeira conversa',
        rotulo: 'nunca abordados',
        mede: 'Abertos sem data de início, e o preço deles somado.',
      },
      tabela: {
        titulo: 'Por vendedor',
        mede: 'Os mesmos números na lista de cada vendedor, de quem tem mais em Foque agora sem próxima conversa para quem tem menos.',
        vendedor: 'Vendedor',
        receita: 'Receita esperada',
        foqueSemConversa: 'Foque sem próxima conversa',
        parado: 'Parado',
        semInicio: 'Sem primeira conversa',
        respostas: 'Respostas registradas',
      },
      local: 'Respostas gravadas neste navegador: {x} de {n}',
      banco: 'Respostas gravadas: {x} de {n}',
    },
    score: {
      numero: 'Score {score}',
      rotulo: 'se o negócio é bom: a idade e as suas respostas',
      emJogo: '{produto} · US$ {preco} em jogo',
      idade:
        'Aberto há {dias} dias: {taxa}% dos negócios com essa idade fecharam (a melhor faixa fecha {max}%).',
      semData:
        'Ainda sem primeira conversa: sem idade, o score parte de {base} e muda só com as suas respostas.',
      semScore: 'Responda as perguntas para pontuar.',
      resposta: '{rotulo}: {pontos}',
      posicao: 'Na sua lista: {k}º de {n} (o grupo, depois o que há a ganhar).',
      chance: 'Chance de fechar em 3 meses: {chance}%',
      chanceSemData: 'Chance de fechar em 3 meses: sem dado (ainda sem primeira conversa).',
      conta: 'De onde vem a chance',
      verPorque: 'ver por quê',
      parcela: '{pontos} · {fator}: {valor}',
      parcelaZero: '{fator}: 0 · {motivo}',
      zero: {
        pontua: 'igual à média do histórico',
        sem_dado: 'sem dado no cadastro, não tira ponto',
        n_pequeno: 'poucos negócios no histórico com esse valor',
        fora_do_score: 'não muda a chance no histórico',
      },
    },
    motivos: [
      {
        ateDias: 40,
        texto: 'Aberto há {dias} dias. {taxa}% dos negócios com essa idade fecharam.',
      },
      {
        ateDias: 60,
        texto:
          'Aberto há {dias} dias. Nessa idade, só {taxa}% fecharam. Daqui pra frente a chance cai rápido.',
      },
      { ateDias: 90, texto: 'Aberto há {dias} dias. Nessa idade, só {taxa}% fecharam.' },
      {
        ateDias: null,
        texto: 'Aberto há {dias} dias. Nenhum negócio com mais de 90 dias fechou neste histórico.',
      },
    ],
    motivoSemData: 'Ainda sem primeira conversa. US$ {preco} em jogo: comece por este.',
    grupos: {
      foque_agora: {
        titulo: 'Foque agora',
        subtitulo: 'Ainda podem fechar, mas a chance está caindo.',
        acao: 'A chance está caindo: marque a próxima conversa esta semana.',
        vazio: 'Nenhum negócio seu está entre {de} e {ate} dias hoje.',
      },
      siga_no_ritmo: {
        titulo: 'Siga no ritmo',
        subtitulo: 'Abertos há pouco tempo. A chance ainda é alta.',
        acao: 'Marque a próxima conversa com data.',
        vazio: 'Nenhum negócio seu está entre {de} e {ate} dias hoje.',
      },
      nutricao: {
        titulo: 'Nutrição',
        subtitulo: 'Abertos há mais de {limite} dias. Quase nenhum fechou com essa idade.',
        acao: 'Encaminhar para nutrição',
        vazio: 'Nenhum negócio seu está com mais de {limite} dias hoje.',
      },
      sem_inicio: {
        titulo: 'Aborde primeiro',
        subtitulo: 'Ainda sem a primeira conversa. O de maior valor em jogo vem primeiro.',
        acao: 'Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver.',
        vazio: 'Nenhum negócio seu está sem data de início.',
      },
    },
    perguntas: { titulo: 'O que só você sabe (muda o score e a ação)', sim: 'Sim', nao: 'Não' },
    avisos: {
      nutricao:
        'Nenhum negócio deste histórico fechou depois de {maxDias} dias. Pode ser um limite dos próprios dados.',
      modoLocal: 'Sem conexão com o servidor. A lista foi calculada aqui no seu navegador.',
      referencia: 'Dados até {referencia}. As idades são contadas até essa data.',
    },
    respostas: {
      banco: 'suas respostas ficam guardadas para a equipe.',
      local: 'suas respostas ficam só neste navegador.',
    },
    comoFunciona: {
      score:
        'O score diz se o negócio é bom, de 0 a 100. Parte da idade: a chance de fechar dos negócios com a mesma idade, comparada com a melhor idade (a melhor vale 100). Depois, as suas respostas: cada "Sim" soma {sim} e cada "Não" tira {nao} (esses pesos são uma escolha nossa: o histórico não tem essas respostas). Sem data de início, o score só aparece depois da primeira resposta e parte de {base}. O preço não entra no score: ele diz quanto está em jogo. A ordem da tela é outra coisa: primeiro o grupo (Foque agora, Siga no ritmo, Aborde primeiro, Nutrição), depois o que há a ganhar (a chance × o preço de tabela; sem data de início, só o preço).',
      calculo:
        'De onde vem a chance: o sistema testou {n} fatores no histórico. Cada valor ganha ou perde pontos pelo quanto fechou a mais ou a menos que a média; a soma dos pontos vira a chance de fechar em 3 meses.',
      testado:
        'Só entra na chance o fator que melhorou a previsão em negócios que o cálculo não tinha visto (abertos em {corte}, fechados até {referencia}). Entrou: {escolhidos}. Os outros valem 0 ponto.',
      acerto:
        'Acerto da chance: em {score} de cada 100 pares (um negócio que fechou e um que não fechou), a chance maior ficou com o que fechou. Só com a idade: {idade}.',
      motivos: {
        entrou: 'entrou na chance',
        nao_melhorou: 'não melhorou a previsão',
        n_pequeno: 'poucos negócios para medir',
      },
      fonte:
        'De onde vem o método: lead scoring por perfil e interesse (RD Station) e pontos pela taxa de fechamento de cada atributo (HubSpot).',
      respostasBanco: 'Respostas e decisões ficam guardadas para a equipe.',
      respostasLocal: 'Respostas e decisões ficam só neste navegador.',
    },
  },
};
