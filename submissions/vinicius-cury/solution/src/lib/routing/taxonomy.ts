// D2 categories (8) → D1 subjects (16)
export const D2_TO_D1: Record<string, string[]> = {
  Software: [
    "Software issue",
    "Product recommendation",
    "Peripheral compatibility",
  ],
  Hardware: [
    "Hardware issue",
    "Product recommendation",
    "Peripheral compatibility",
  ],
  Network: ["Network problem", "Installation support"],
  Data: ["Data loss", "Account access"],
  Access: ["Account access", "Password reset"],
  Application: [
    "Software issue",
    "Installation support",
    "Product recommendation",
  ],
  Integration: ["Third-party integration", "Network problem"],
  Storage: ["Data loss", "Storage issue", "Backup recovery"],
};

// All D1 subjects (unique)
export const D1_SUBJECTS = [
  "Account access",
  "Backup recovery",
  "Data loss",
  "Hardware issue",
  "Installation support",
  "Network problem",
  "Password reset",
  "Peripheral compatibility",
  "Product recommendation",
  "Software issue",
  "Storage issue",
  "Third-party integration",
] as const;

// All D2 categories
export const D2_CATEGORIES = [
  "Software",
  "Hardware",
  "Network",
  "Data",
  "Access",
  "Application",
  "Integration",
  "Storage",
] as const;

// Scenario descriptions in pt-BR
export const SCENARIO_LABELS: Record<
  string,
  { label: string; action: string; color: string }
> = {
  acelerar: {
    label: "Acelerar",
    action: "Mais tempo → menos satisfação. Rotear para agentes rápidos.",
    color: "red",
  },
  desacelerar: {
    label: "Desacelerar",
    action:
      "Mais tempo → mais satisfação. Rotear para especialistas.",
    color: "blue",
  },
  redirecionar: {
    label: "Redirecionar",
    action: "Canal inadequado. Sugerir canal com melhor CSAT.",
    color: "yellow",
  },
  quarentena: {
    label: "Quarentena",
    action: "CSAT ruim sem alternativa. Investigar causa raiz.",
    color: "gray",
  },
  manter: {
    label: "Manter",
    action: "Canal funciona bem. Não alterar.",
    color: "green",
  },
  liberar: {
    label: "Liberar",
    action: "Tempo não importa. Deprioritizar, liberar recursos.",
    color: "emerald",
  },
};
