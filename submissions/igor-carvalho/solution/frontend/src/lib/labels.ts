/** Traduz valores que vêm do dataset (em inglês) para o texto mostrado ao vendedor. */
export function stageLabel(stage: string): string {
  if (stage === 'Engaging') return 'Em engajamento';
  if (stage === 'Prospecting') return 'Prospecção';
  return stage;
}

export function isProspecting(stage: string): boolean {
  return stage === 'Prospecting';
}
