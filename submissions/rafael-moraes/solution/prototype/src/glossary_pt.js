// Camada de português: glossário PT → EN aplicado antes do classificador (treinado em inglês).
// Chaves sem acento e em minúsculas. Expressões com várias palavras são aplicadas primeiro.
// Construído a partir das palavras de maior peso de cada categoria do modelo.

const PT_PHRASES = {
  "caixa de correio": "mailbox", "caixa postal": "mailbox", "caixa de entrada": "mailbox",
  "pasta compartilhada": "shared folder", "pastas compartilhadas": "shared folders",
  "folha de ponto": "timecard", "cartao de ponto": "timecard", "banco de horas": "timecard hours",
  "folha de pagamento": "payroll", "licenca maternidade": "maternity leave", "licenca medica": "sick leave",
  "pedido de compra": "purchase po", "ordem de compra": "purchase po", "nota fiscal": "invoice receipt",
  "sala de reuniao": "meeting room", "salas de reuniao": "meeting rooms",
  "lista de distribuicao": "mailing list", "lista de email": "mailing list", "lista de e-mail": "mailing list",
  "direitos de administrador": "administrative rights admin", "acesso de administrador": "administrator access",
  "conta de administrador": "administrator account", "base de conhecimento": "knowledge base",
  "codigo de projeto": "project code", "codigo do projeto": "project code",
  "area restrita": "secured area", "nao consigo": "cannot", "nao funciona": "not working",
  "nao esta funcionando": "not working", "nao abre": "not opening", "nao liga": "not turning on",
  "fora do ar": "outage down", "esqueci a senha": "forgot password reset", "redefinir senha": "reset password",
  "trocar senha": "change password", "senha expirada": "password expired", "conta bloqueada": "account locked",
  "area de trabalho": "desktop", "disco rigido": "hard drive", "pen drive": "usb drive",
  "acesso remoto": "remote access vpn", "cota de email": "mailbox quota", "espaco em disco": "storage space",
  "importancia alta": "importance high", "prioridade alta": "importance high",
  "atualizacao do windows": "windows update upgrade", "fone de ouvido": "headphones headset",
  "tela azul": "blue screen", "sistema operacional": "os windows", "dados pessoais": "personal data",
  "recursos humanos": "hr", "base de dados": "database server", "banco de dados": "database server", "email de recuperacao": "reset password", "e-mail de recuperacao": "reset password", "novo colaborador": "new starter", "nova colaboradora": "new starter",
  "primeiro dia": "starter join", "saiu da empresa": "leaver left", "desligamento": "leaver leaving"
};

const PT_WORDS = {
  // Acesso
  acesso: "access", acessos: "access", acessar: "access", senha: "password", senhas: "password",
  usuario: "user", usuarios: "users", conta: "account", contas: "accounts", login: "log", logar: "log",
  bloqueado: "locked blocked", bloqueada: "locked blocked", bloquear: "block", desbloquear: "unlock",
  redefinir: "reset", resetar: "reset", licenca: "license", licencas: "licenses", cracha: "badge pass",
  cartao: "card", cartoes: "cards", expirou: "expired", expirada: "expired", expirado: "expired",
  sincronizacao: "sync synchronization", sincronizar: "sync", repositorio: "repository", visitante: "visitor",
  criar: "create", criacao: "creation", criem: "create", crie: "create", desativar: "deactivate", ativar: "activate",
  convidado: "guest", externo: "external", remover: "remove delete", removam: "remove delete",
  // Admin / software
  instalar: "install", instalacao: "installation", instalem: "install", instalado: "installed",
  atualizacao: "update", atualizar: "update", atualizem: "update", versao: "version",
  programa: "software program", aplicativo: "app application", app: "app", servidor: "server", servidores: "servers",
  calendario: "calendar", recuperacao: "reset password", recuperar: "reset password", reconhece: "login password", reconhecendo: "login password",
  reinstalar: "reinstall", reiniciar: "restart", reiniciando: "restarting", credenciais: "credentials", credencial: "credential",
  perfil: "profile", configuracoes: "settings", configuracao: "configuration", configurar: "configuration", configurem: "configuration", virus: "virus",
  administrador: "administrator admin", permissao: "permission rights", permissoes: "permissions rights",
  direitos: "rights", travando: "slow not responding", travado: "slow not responding", lento: "slow", lenta: "slow",
  // RH
  ferias: "holiday vacation leave", folga: "leave", ausencia: "absence", ponto: "timecard", horas: "hours",
  estagio: "internship", estagiario: "intern", estagiarios: "interns", transferencia: "transfer",
  formulario: "form", contratado: "contractor", terceirizado: "contractor", oficial: "officer",
  prédio: "floor", predio: "floor building", andar: "floor", torre: "tower", restrita: "secured", liberem: "granting allow",
  liberar: "allow granting", aprovacao: "approval", aprovar: "approve", aprovem: "approve", experiencia: "probation",
  // Hardware
  monitor: "monitor", monitores: "monitors", notebook: "laptop", notebooks: "laptop", laptop: "laptop",
  computador: "computer pc", teclado: "keyboard", mouse: "mouse", cabo: "cable", cabos: "cables",
  carregador: "charger", adaptador: "adapter", celular: "mobile phone", telefone: "phone", ramal: "extension phone",
  camera: "camera", cameras: "cameras", mochila: "backpack", memoria: "memory ram", impressora: "printer",
  tela: "screen display", piscando: "flickering", rede: "network", conexao: "connection", conectar: "connect",
  reuniao: "meeting", sala: "room", salas: "rooms", ligacao: "call", ligacoes: "calls", certificado: "certificate",
  documento: "document", documentos: "documents", substituicao: "replacement", troca: "replacement",
  quebrado: "broken damaged", quebrada: "broken damaged", treinamento: "training", apresentacao: "presentation",
  relatorio: "report", relatorios: "reports", patches: "patching", quadro: "board",
  // Projeto interno
  projeto: "project", projetos: "projects", codigo: "code", codigos: "codes", pipeline: "pipeline",
  oportunidade: "opportunity", oportunidades: "opportunities", previsao: "forecast", cliente: "client",
  modelo: "template", custos: "costs", tarefas: "tasks", alocar: "allocate", alocacao: "allocation",
  comercial: "commercial", portfolio: "portfolio programme", indenizacao: "indemnity",
  // Diversos
  mudanca: "change", mudar: "change", mudem: "change", alterar: "change amend", alteracao: "change amend", alteracoes: "changes amendments",
  aprovador: "approver", responsavel: "owner", dono: "owner", grupo: "group", grupos: "groups",
  adicionar: "add", adicionem: "add", adicione: "add", incluir: "add include", membro: "member", membros: "members",
  lista: "list", listas: "lists", contrato: "contract", chamado: "ticket", chamados: "tickets", incidente: "incident",
  pendente: "pending", fila: "queue", notificacao: "notification", notificacoes: "notifications", renomear: "rename",
  alerta: "alert", alertas: "alerts", equipe: "team", time: "team", gerente: "manager", fechado: "closed",
  // Compras
  compra: "purchase", compras: "purchases", comprar: "purchase", compramos: "purchased", comprado: "purchased",
  pedido: "order requisition", pedidos: "orders", item: "item", itens: "items", recebimento: "receipt",
  recebemos: "received", recebido: "received", dispositivo: "device", dispositivos: "devices",
  equipamento: "equipment", reposicao: "replenishment", repor: "replenishment", pelicula: "glass protector cover",
  capa: "cover", assinatura: "subscription", catalogo: "catalog", fatura: "invoice",
  // Armazenamento
  pasta: "folder", pastas: "folders", arquivo: "file", arquivos: "files", compartilhada: "shared", compartilhado: "shared",
  compartilhar: "share", armazenamento: "storage", espaco: "space", cheia: "full", cheio: "full", cota: "quota",
  aumentar: "increase", aumentem: "increase", arquivamento: "archiving archive", restaurar: "restore",
  excluido: "deleted", excluida: "deleted", apagado: "deleted", escrita: "write", leitura: "read",
  biblioteca: "library", limite: "limit", tamanho: "size", correio: "mail", email: "mail", emails: "mails",
  // Gerais
  urgente: "urgent", obrigado: "thank", obrigada: "thank", favor: "please", 
  novo: "new", nova: "new", sumiu: "disappeared", excluir: "delete", excluam: "delete", apagar: "delete",
  bloqueio: "block", anexo: "attached", anexa: "attached", semanal: "weekly", recusar: "decline", aceitar: "accept", aceitem: "accept", recusem: "decline",
  melhoria: "improvement", melhorias: "improvement", beneficios: "benefits"
};

// Palavras de ligação do português: removidas para não colidirem com termos do vocabulário em inglês.
const PT_STOP = new Set(("a o e de da do das dos em no na nos nas um uma uns umas para por com sem que se me te "
  + "eu ele ela nos eles elas meu minha meus minhas seu sua seus suas esse essa este esta isso isto la lá ja já "
  + "mais muito muita pois porque como quando onde ao aos à às ou mas tambem também ainda so só foi ser estar "
  + "esta está estou tem ter tenho temos preciso precisamos gostaria peço peco oi ola olá prezados pessoal bom dia "
  + "tarde noite atenciosamente vocês voces podem pode poderiam conforme problema problemas erro erros ajuda ajudem ajudar duvida "
  + "quer querem quero queria alguma alguem coisa algo aconteceu acontecendo parece tudo nada nenhum").split(" "));

const PT_HINTS = /\b(nao|não|voce|você|obrigad[oa]|favor|preciso|precisamos|quero|queria|gostaria|olá|ola|oi|bom dia|boa tarde|boa noite|prezad[oa]s?|estou|está|esta|tenho|minha|meu|senha|acesso|cancelar|problema|ajuda|parou|consigo|funciona|conta|empresa|colaborador[a]?|por favor)\b|[ãõçáéíóúâêô]/i;

function stripAccents(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, ""); }

function looksPortuguese(text) { return PT_HINTS.test(text); }

// Retorna o texto "traduzido" para o vocabulário do modelo e quais palavras foram reconhecidas.
function ptToModelText(text) {
  let s = " " + stripAccents(text.toLowerCase()).replace(/[^\p{L}\p{N}\- ]+/gu, " ") + " ";
  const hits = [];
  for (const [pt, en] of Object.entries(PT_PHRASES).sort((a, b) => b[0].length - a[0].length)) {
    const key = " " + pt + " ";
    if (s.includes(key)) { s = s.split(key).join(" " + en.replace(/ /g, "_") + " "); hits.push(pt); }
  }
  const out = [];
  for (const tok of s.trim().split(/\s+/)) {
    if (!tok) continue;
    if (tok.includes("_")) { out.push(tok.replace(/_/g, " ")); continue; }
    if (PT_STOP.has(tok)) continue;
    if (PT_WORDS[tok]) { out.push(PT_WORDS[tok]); hits.push(tok); continue; }
    out.push(tok); // nomes de sistemas e termos já em inglês (outlook, oracle, vpn, windows) seguem iguais
  }
  return { text: out.join(" "), hits };
}

if (typeof module !== "undefined") module.exports = { ptToModelText, looksPortuguese, PT_WORDS, PT_PHRASES };
