const nf = (min: number, max: number) =>
  new Intl.NumberFormat("pt-BR", { minimumFractionDigits: min, maximumFractionDigits: max });

export const int = (v: number | null | undefined) => (v == null ? "—" : nf(0, 0).format(v));
export const dec = (v: number | null | undefined, d = 2) => (v == null ? "—" : nf(d, d).format(v));
export const pct = (v: number | null | undefined, d = 1) => (v == null ? "—" : `${nf(d, d).format(v * 100)}%`);
export const usd = (v: number | null | undefined) =>
  v == null ? "—" : `US$ ${nf(0, 0).format(v)}`;
export const usdK = (v: number | null | undefined) => {
  if (v == null) return "—";
  if (Math.abs(v) >= 1e6) return `US$ ${nf(1, 1).format(v / 1e6)} mi`;
  if (Math.abs(v) >= 1e3) return `US$ ${nf(0, 0).format(v / 1e3)} mil`;
  return usd(v);
};
export const pval = (p: number | null | undefined) =>
  p == null ? "—" : p < 0.001 ? "< 0,001" : nf(3, 3).format(p);

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
export const mes = (ym: string) => {
  const [y, m] = ym.split("-");
  return `${MESES[Number(m) - 1]}/${y.slice(2)}`;
};

/** Nome legível de cada variável da base ligada. */
export const NOMES: Record<string, string> = {
  perfil_industry: "Setor",
  perfil_country: "País",
  perfil_referral_source: "Como chegou",
  perfil_plan_tier: "Plano inicial",
  perfil_seats: "Usuários contratados (cadastro)",
  perfil_is_trial: "Em período de teste",
  perfil_coorte_signup: "Trimestre de cadastro",
  perfil_dias_desde_signup: "Dias desde o cadastro",
  receita_assinaturas: "Nº de assinaturas",
  receita_assinaturas_ativas: "Assinaturas ativas",
  receita_assinaturas_encerradas: "Assinaturas encerradas",
  receita_assinaturas_trial: "Assinaturas em teste",
  receita_mrr_ativo: "Receita mensal ativa",
  receita_mrr_perdido: "Receita mensal cancelada",
  receita_mrr_medio_assinatura: "Receita média por serviço",
  receita_seats_ativos: "Usuários contratados ativos",
  receita_pct_anual: "% cobrança anual",
  receita_pct_auto_renew: "% renovação automática",
  receita_upgrades: "Trocas para plano maior",
  receita_downgrades: "Trocas para plano menor",
  receita_arr_ativo: "Receita anual ativa",
  receita_pct_mrr_perdido: "% da receita cancelada",
  receita_pct_assin_basic: "% assinaturas Basic",
  receita_pct_assin_pro: "% assinaturas Pro",
  receita_pct_assin_enterprise: "% assinaturas Enterprise",
  uso_registros: "Registros de uso",
  uso_eventos: "Usos do produto",
  uso_duracao_h: "Horas de uso",
  uso_erros: "Erros",
  uso_registros_com_erro: "Usos com erro",
  uso_features_distintas: "Features distintas usadas",
  uso_registros_beta: "Usos de funções em teste",
  uso_taxa_erro: "Taxa de erro",
  uso_pct_registros_com_erro: "% registros com erro",
  uso_pct_beta: "% uso de funções em teste",
  uso_duracao_media_min: "Duração média (min)",
  uso_eventos_2023: "Eventos de uso 2023",
  uso_eventos_2024: "Eventos de uso 2024",
  uso_variacao_2024_vs_2023: "Variação de uso 24×23",
  uso_dias_desde_ultimo: "Dias desde o último uso",
  suporte_tickets: "Chamados",
  suporte_pct_urgente_alta: "% chamados urgentes",
  suporte_resolucao_media_h: "Resolução média (h)",
  suporte_resolucao_max_h: "Resolução máxima (h)",
  suporte_primeira_resposta_media_min: "Tempo até 1ª resposta (min)",
  suporte_escalonamentos: "Chamados escalados",
  suporte_satisfacao_media: "Satisfação média",
  suporte_pct_sem_nota: "% chamados sem nota",
  suporte_pct_escalonados: "% chamados escalados",
  churn_flag_conta: "Cancelou (marcação da conta)",
  churn_tem_evento: "Cancelou (lista de cancelamentos)",
  churn_eventos: "Nº de cancelamentos",
  plan_tier: "Plano da assinatura",
  seats: "Usuários contratados",
  mrr_amount: "Receita mensal do serviço",
  anual: "Cobrança anual",
  auto_renew_flag: "Renovação automática",
  upgrade_flag: "Troca para plano maior",
  downgrade_flag: "Troca para plano menor",
  taxa_erro: "Taxa de erro",
  pct_beta: "% uso de funções em teste",
  eventos_por_seat: "Usos por usuário contratado",
  conta_industry: "Setor",
  conta_referral_source: "Como chegou",
  conta_country: "País",
  conta_plan_tier: "Plano inicial da conta",
};
export const nome = (v: string) => NOMES[v] ?? v;
