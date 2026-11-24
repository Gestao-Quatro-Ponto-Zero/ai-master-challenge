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
  perfil_industry: "Indústria",
  perfil_country: "País",
  perfil_referral_source: "Canal de aquisição",
  perfil_plan_tier: "Plano inicial",
  perfil_seats: "Assentos (cadastro)",
  perfil_is_trial: "Em trial",
  perfil_coorte_signup: "Trimestre de cadastro",
  perfil_dias_desde_signup: "Dias desde o cadastro",
  receita_assinaturas: "Nº de assinaturas",
  receita_assinaturas_ativas: "Assinaturas ativas",
  receita_assinaturas_encerradas: "Assinaturas encerradas",
  receita_assinaturas_trial: "Assinaturas trial",
  receita_mrr_ativo: "MRR ativo",
  receita_mrr_perdido: "MRR perdido",
  receita_mrr_medio_assinatura: "MRR médio por assinatura",
  receita_seats_ativos: "Assentos ativos",
  receita_pct_anual: "% cobrança anual",
  receita_pct_auto_renew: "% renovação automática",
  receita_upgrades: "Upgrades",
  receita_downgrades: "Downgrades",
  receita_arr_ativo: "ARR ativo",
  receita_pct_mrr_perdido: "% do MRR perdido",
  receita_pct_assin_basic: "% assinaturas Basic",
  receita_pct_assin_pro: "% assinaturas Pro",
  receita_pct_assin_enterprise: "% assinaturas Enterprise",
  uso_registros: "Registros de uso",
  uso_eventos: "Eventos de uso",
  uso_duracao_h: "Horas de uso",
  uso_erros: "Erros",
  uso_registros_com_erro: "Registros com erro",
  uso_features_distintas: "Features distintas usadas",
  uso_registros_beta: "Registros em beta",
  uso_taxa_erro: "Taxa de erro",
  uso_pct_registros_com_erro: "% registros com erro",
  uso_pct_beta: "% uso em beta",
  uso_duracao_media_min: "Duração média (min)",
  uso_eventos_2023: "Eventos de uso 2023",
  uso_eventos_2024: "Eventos de uso 2024",
  uso_variacao_2024_vs_2023: "Variação de uso 24×23",
  uso_dias_desde_ultimo: "Dias desde o último uso",
  suporte_tickets: "Tickets",
  suporte_pct_urgente_alta: "% tickets urgentes/altos",
  suporte_resolucao_media_h: "Resolução média (h)",
  suporte_resolucao_max_h: "Resolução máxima (h)",
  suporte_primeira_resposta_media_min: "1ª resposta média (min)",
  suporte_escalonamentos: "Escalonamentos",
  suporte_satisfacao_media: "Satisfação média",
  suporte_pct_sem_nota: "% tickets sem nota",
  suporte_pct_escalonados: "% escalonados",
  churn_flag_conta: "Churn (flag da conta)",
  churn_tem_evento: "Churn (tem evento)",
  churn_eventos: "Nº eventos de churn",
  plan_tier: "Plano da assinatura",
  seats: "Assentos",
  mrr_amount: "MRR da assinatura",
  anual: "Cobrança anual",
  auto_renew_flag: "Renovação automática",
  upgrade_flag: "Upgrade",
  downgrade_flag: "Downgrade",
  taxa_erro: "Taxa de erro",
  pct_beta: "% uso em beta",
  eventos_por_seat: "Eventos por assento",
  conta_industry: "Indústria",
  conta_referral_source: "Canal de aquisição",
  conta_country: "País",
  conta_plan_tier: "Plano inicial da conta",
};
export const nome = (v: string) => NOMES[v] ?? v;
