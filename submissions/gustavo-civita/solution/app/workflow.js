"use strict";

/*
 * Fluxo de cada negociação: o que o vendedor registrou e o que vem depois.
 *
 * Nada aqui é estado guardado à parte: a situação de uma negociação é sempre
 * recalculada a partir da lista de eventos registrados (ligou, enviou,
 * respondeu...). Assim "desfazer" é só apagar o último evento.
 */

const Workflow = (() => {
  const LOG_KEY = "leadscorer.eventos.v3";
  const CLOCK_KEY = "leadscorer.diasAvancados";

  /* Regras de retorno, confirmadas pelo Gustavo (process-log, decisões 10 e 27).
     A base não registra tentativas de contato, então não há dado para calibrá-las. */
  const RULES = { religarEmDias: 2, esperarRespostaDias: 3, maximoTentativas: 3 };

  const EVENTS = {
    nao_atendeu: "Ligou, não atendeu",
    retornar: "Falou e combinou retorno",
    enviou: "Enviou mensagem",
    respondeu: "Cliente respondeu",
    ganhou: "Fechou",
    perdeu: "Sem interesse",
    encerrou: "Encerrou no CRM",
  };

  function read(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key));
      return value ?? fallback;
    } catch {
      return fallback;
    }
  }

  function write(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* Sem armazenamento (aba anônima) a tela segue funcionando, só não lembra. */
    }
  }

  /* Relógio: "hoje" real, mais os dias avançados no modo demonstração. */
  const daysAhead = () => read(CLOCK_KEY, 0);
  const now = () => new Date(Date.now() + daysAhead() * 86400000);
  const dayOf = (date) => {
    const d = new Date(date);
    return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  };
  /* Soma dias de calendário (não blocos de 24 h), para não errar na virada do horário de verão. */
  const addDays = (date, days) => {
    const d = new Date(dayOf(date));
    d.setDate(d.getDate() + days);
    return d;
  };
  const validDate = (value) => value != null && !Number.isNaN(new Date(value).getTime());
  const CLOSING = ["ganhou", "perdeu", "encerrou"];
  const isToday = (date) => dayOf(date) === dayOf(now());
  const isDue = (date) => dayOf(date) <= dayOf(now());

  const events = () => {
    const stored = read(LOG_KEY, []);
    return Array.isArray(stored) ? stored.filter((event) => event && event.id && Object.hasOwn(EVENTS, event.tipo) && validDate(event.quando)) : [];
  };

  function add(deal, tipo, extra = {}) {
    const log = events();
    log.push({
      quando: now().toISOString(),
      tipo,
      id: deal.id,
      lista: deal.lista,
      vendedor: deal.vendedor,
      manager: deal.manager,
      regiao: deal.regiao,
      produto: deal.produto,
      preco: deal.preco,
      idadeDias: deal.idade,
      conta: deal.conta,
      setor: deal.setor,
      ...extra,
    });
    write(LOG_KEY, log);
  }

  function undoLast(dealId) {
    const log = events();
    for (let i = log.length - 1; i >= 0; i -= 1) {
      if (log[i].id === dealId) {
        log.splice(i, 1);
        break;
      }
    }
    write(LOG_KEY, log);
  }

  function byDeal() {
    const grouped = {};
    for (const event of events()) (grouped[event.id] = grouped[event.id] || []).push(event);
    return grouped;
  }

  /*
   * Situação atual de uma negociação.
   *   fase: "fila"       ainda não trabalhada, está na lista de origem
   *         "retorno"    voltou para hoje (data combinada, nova tentativa, cliente respondeu)
   *         "aguardando" mensagem enviada, esperando o cliente
   *         "agendada"   tem data futura para voltar
   *         "esgotada"   sem resposta por telefone e por mensagem: encerrar
   *         "concluida"  fechou, perdeu ou foi encerrada
   *   modo: o que fazer quando chegar a vez ("ligar", "mensagem" ou "encerrar")
   */
  function statusOf(deal, history = []) {
    const base = { foco: "ligar", abordar: "mensagem", reativar: "mensagem", encerrar: "encerrar" }[deal.lista];
    const status = { fase: "fila", modo: base, tarefa: null, volta: null, tentativas: 0, ligacoes: 0, confirmar: false, resultado: null, historico: history };

    for (const event of history) {
      if (status.fase === "concluida") break; // nada reabre uma negociação concluída, só desfazer
      if (event.tipo === "nao_atendeu") {
        status.ligacoes += 1;
        status.fase = "agendada";
        if (status.ligacoes >= RULES.maximoTentativas) {
          // O telefone não funcionou: antes de desistir, uma mensagem para confirmar o interesse.
          status.modo = "mensagem";
          status.confirmar = true;
          status.tentativas = RULES.maximoTentativas - 1; // é a última tentativa
          status.volta = new Date(event.quando);
          status.tarefa = `${status.ligacoes} ligações sem resposta: enviar mensagem para confirmar o interesse`;
        } else {
          status.modo = "ligar";
          status.volta = addDays(event.quando, RULES.religarEmDias);
          status.tarefa = `Ligar de novo (${status.ligacoes + 1}ª tentativa)`;
        }
      } else if (event.tipo === "retornar") {
        status.tentativas = 0;
        status.ligacoes = 0;
        status.confirmar = false;
        status.fase = "agendada";
        status.modo = "ligar";
        // sem data válida (registro corrompido), o retorno vale para o próprio dia do registro
        status.volta = new Date(validDate(event.retornoEm) ? event.retornoEm : event.quando);
        status.tarefa = "Retornar como combinado";
      } else if (event.tipo === "enviou") {
        status.tentativas += 1;
        status.fase = "aguardando";
        status.modo = "mensagem";
        status.volta = addDays(event.quando, RULES.esperarRespostaDias);
        status.tarefa = status.tentativas >= RULES.maximoTentativas
          ? "Sem resposta: encerrar" // era a última tentativa
          : `Sem resposta: enviar ${status.tentativas + 1}ª mensagem`;
      } else if (event.tipo === "respondeu") {
        status.tentativas = 0;
        status.ligacoes = 0;
        status.confirmar = false;
        status.fase = "agendada";
        status.modo = "ligar";
        status.volta = new Date(event.quando);
        status.tarefa = "Cliente respondeu: ligar";
      } else if (CLOSING.includes(event.tipo)) {
        status.fase = "concluida";
        status.resultado = EVENTS[event.tipo];
        status.volta = null;
      } // qualquer outro tipo é ignorado
    }

    const waitingOrScheduled = status.fase === "agendada" || status.fase === "aguardando";
    if (waitingOrScheduled && status.tentativas >= RULES.maximoTentativas && (status.fase === "agendada" || isDue(status.volta))) {
      status.fase = "esgotada";
      status.modo = "encerrar";
      status.tarefa = status.confirmar
        ? "Sem resposta por telefone e por mensagem: encerrar"
        : `${status.tentativas} mensagens sem resposta: encerrar`;
    } else if (waitingOrScheduled && isDue(status.volta)) {
      status.fase = "retorno";
    }
    return status;
  }

  return {
    RULES, EVENTS, events, add, undoLast, byDeal, statusOf, now, addDays, isToday,
    daysAhead,
    advanceDay: () => write(CLOCK_KEY, daysAhead() + 1),
    resetClock: () => write(CLOCK_KEY, 0),
    clear: () => write(LOG_KEY, []),
    read, write,
  };
})();
