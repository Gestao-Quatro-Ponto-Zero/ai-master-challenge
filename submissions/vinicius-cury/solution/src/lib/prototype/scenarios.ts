// Pre-loaded demo scenarios for the walkthrough and quick testing

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  message: string;
  channel: string;
  expectedCategory: string;
  expectedSubject: string;
  expectedScenario: string;
}

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: "hardware-acelerar",
    name: "Hardware → Acelerar",
    description: "Notebook com problema de hardware. Classificado como urgente.",
    message:
      "Meu notebook Dell não liga desde ontem. Já tentei reiniciar mas a tela fica preta e o LED pisca.",
    channel: "Chat",
    expectedCategory: "Hardware",
    expectedSubject: "Hardware issue",
    expectedScenario: "acelerar",
  },
  {
    id: "cancelamento-redirecionar",
    name: "Cancelamento → Redirecionar",
    description:
      "Cliente quer cancelar assinatura. Melhor atendido por telefone.",
    message:
      "Quero cancelar minha assinatura do plano premium. Já tentei pelo site mas não encontro a opção.",
    channel: "Email",
    expectedCategory: "Access",
    expectedSubject: "Account access",
    expectedScenario: "redirecionar",
  },
  {
    id: "dados-quarentena",
    name: "Dados → Quarentena",
    description:
      "Dados desaparecendo do sistema. Requer investigação especial.",
    message:
      "Meus dados estão sumindo do sistema. Relatórios que eu salvei ontem desapareceram hoje de manhã. Isso já aconteceu 3 vezes esta semana.",
    channel: "Chat",
    expectedCategory: "Data",
    expectedSubject: "Data loss",
    expectedScenario: "quarentena",
  },
];
