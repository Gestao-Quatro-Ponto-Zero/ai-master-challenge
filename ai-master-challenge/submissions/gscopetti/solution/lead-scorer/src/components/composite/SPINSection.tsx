import { Card, Button } from '@/components/ui';

export interface SPINScript {
  situation: string;
  problem: string;
  implication: string;
  need_payoff: string;
}

export interface SPINSectionProps {
  script: SPINScript;
  accountName?: string;
}

export function SPINSection({
  script,
  accountName = 'Cliente',
}: SPINSectionProps) {
  const handleCopy = () => {
    const text = `${accountName}\n\n[S] SITUAÇÃO\n${script.situation}\n\n[P] PROBLEMA\n${script.problem}\n\n[I] IMPLICAÇÃO\n${script.implication}\n\n[N] NECESSIDADE-PAYOFF\n${script.need_payoff}`;
    navigator.clipboard.writeText(text);
    alert('✅ Script copiado!');
  };

  return (
    <div className="space-y-6">
      {/* Situação */}
      <Card variant="default" padding="lg" className="border-l-4 border-l-blue-500 shadow-sm">
        <h3 className="font-bold text-blue-600 mb-4 flex items-center gap-2 text-sm uppercase tracking-widest">
          SITUAÇÃO
        </h3>
        <p className="text-hubspot-dark leading-relaxed font-medium">
          {script.situation}
        </p>
      </Card>

      {/* Problema */}
      <Card variant="default" padding="lg" className="border-l-4 border-l-yellow-500 shadow-sm bg-hubspot-gray-100/30">
        <h3 className="font-bold text-yellow-600 mb-4 flex items-center gap-2 text-sm uppercase tracking-widest">
          PROBLEMA
        </h3>
        <p className="text-hubspot-dark leading-relaxed font-medium">
          {script.problem}
        </p>
      </Card>

      {/* Implicação */}
      <Card variant="default" padding="lg" className="border-l-4 border-l-hubspot-orange shadow-sm">
        <h3 className="font-bold text-hubspot-orange mb-4 flex items-center gap-2 text-sm uppercase tracking-widest">
          IMPLICAÇÃO
        </h3>
        <p className="text-hubspot-dark leading-relaxed font-medium">
          {script.implication}
        </p>
      </Card>

      {/* Necessidade-Payoff */}
      <Card variant="default" padding="lg" className="border-l-4 border-l-green-500 shadow-sm bg-hubspot-gray-100/30">
        <h3 className="font-bold text-green-600 mb-4 flex items-center gap-2 text-sm uppercase tracking-widest">
          NECESSIDADE-PAYOFF
        </h3>
        <p className="text-hubspot-dark leading-relaxed font-medium">
          {script.need_payoff}
        </p>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2">
        <Button
          variant="primary"
          size="md"
          fullWidth
          onClick={handleCopy}
        >
          📋 Copiar Script
        </Button>
        <Button
          variant="secondary"
          size="md"
          fullWidth
          onClick={() => window.print()}
        >
          🖨️ Imprimir
        </Button>
      </div>
    </div>
  );
}
