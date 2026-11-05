import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const descobertas = [
  {
    pergunta: "Produto, setor, região ou vendedor indicam se um deal fecha?",
    resposta: "Não.",
    detalhe: "Todos ficam entre 60% e 65% de ganho. As diferenças são do tamanho do acaso.",
  },
  {
    pergunta: "Um modelo com o histórico de vendas preveria melhor?",
    resposta: "Não.",
    detalhe: "Testado com dados do passado, ele acertaria quase como cara ou coroa.",
  },
  {
    pergunta: "O que realmente indica o resultado?",
    resposta: "O tempo.",
    detalhe: "Quem perde, perde nas duas primeiras semanas. E nenhum deal fechou depois de 138 dias.",
  },
  {
    pergunta: "Como decidir a prioridade, então?",
    resposta: "Pelo valor, combinado com o tempo.",
    detalhe: "Um deal vale de US$ 55 a US$ 26.768, quase 500 vezes de diferença.",
  },
];

const problema = [
  {
    indicador: "Deals em negociação parados há mais de 138 dias",
    numero: "1.291 de 1.589 (81%)",
    significado: "Estão fora de qualquer padrão histórico de venda",
  },
  {
    indicador: "Valor travado nesses deals",
    numero: "US$ 3,2 milhões (64% do aberto)",
    significado: "Receita que provavelmente não virá",
  },
  {
    indicador: "Deals em negociação ainda vivos",
    numero: "298 (US$ 694 mil)",
    significado: "É onde o time deve concentrar o esforço",
  },
  {
    indicador: "Deals abertos sem a empresa cliente cadastrada",
    numero: "1.425 de 2.089 (68%)",
    significado: "O CRM está incompleto, e isso vale para todos os times",
  },
  {
    indicador: "Escritório Central",
    numero: "99% dos deals em negociação parados",
    significado: "Todos abertos num bloco de jul–ago/2017: o time segue vendendo; um lote inteiro ficou para trás",
  },
];

const recomendacoes = [
  {
    titulo: "Limpar o pipeline em até duas semanas.",
    detalhe: "Cada vendedor requalifica ou encerra seus deals parados há mais de 138 dias, começando pelo escritório Central.",
  },
  {
    titulo: "Colocar em uso a ferramenta de priorização.",
    detalhe: "Toda segunda-feira o vendedor vê seus deals vivos ordenados por valor e momento, com o motivo de cada posição. Os parados ficam numa fila separada.",
  },
  {
    titulo: "Tornar obrigatório o cadastro da empresa cliente no CRM.",
    detalhe: "Sem isso, não dá para analisar setor ou porte em dois terços do pipeline.",
  },
  {
    titulo: "Registrar as atividades de venda no CRM (reuniões, e-mails, propostas).",
    detalhe: "É o dado que falta para prever resultados com mais precisão.",
  },
  {
    titulo: "Revisar casos pontuais.",
    detalhe: "Possíveis lançamentos duplicados e 80 vendas fechadas acima de 120% do preço de lista.",
  },
];

export function ResumoDialog({ trigger }: { trigger: React.ReactNode }) {
  return (
    <Dialog>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[85vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-display text-3xl">Pipeline de Vendas — Resumo Executivo</DialogTitle>
          <DialogDescription>Análise de 8.800 oportunidades de 35 vendedores · retrato do CRM em 31/12/2017</DialogDescription>
        </DialogHeader>

        <div className="space-y-8 text-sm leading-relaxed">
          <section>
            <h3 className="font-display text-xl text-foreground">Em 30 segundos</h3>
            <p className="mt-2 text-muted-foreground">
              O time não perde vendas por escolher mal os deals. Perde tempo com deals que já morreram e continuam abertos no CRM.
            </p>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-muted-foreground">
              <li>
                <strong className="text-foreground">81% dos deals em negociação estão parados há mais tempo que qualquer venda já fechada</strong>{" "}
                (138 dias). Eles travam US$ 3,2 milhões, 64% dos US$ 5,0 milhões em aberto.
              </li>
              <li>
                <strong className="text-foreground">Produto, setor, região ou vendedor não indicam se um deal vai fechar.</strong>{" "}
                O que indica é o tempo, e o valor define a prioridade.
              </li>
              <li>
                <strong className="text-foreground">Recomendação:</strong> limpar o pipeline e concentrar o time nos 298 deals ainda vivos
                (US$ 694 mil), ordenados por valor e momento.
              </li>
            </ul>
          </section>

          <section>
            <h3 className="font-display text-xl text-foreground">O que descobrimos</h3>
            <p className="mt-2 text-muted-foreground">
              O time ganha 63% dos deals que fecha, e essa taxa quase não muda de um grupo para outro.
            </p>
            <div className="mt-3 overflow-hidden rounded-lg border border-border">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-border bg-muted">
                    <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Pergunta</th>
                    <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Resposta</th>
                  </tr>
                </thead>
                <tbody>
                  {descobertas.map((d) => (
                    <tr key={d.pergunta} className="border-b border-border last:border-0">
                      <td className="px-3 py-2.5 align-top text-muted-foreground">{d.pergunta}</td>
                      <td className="px-3 py-2.5 align-top">
                        <strong className="text-foreground">{d.resposta}</strong>{" "}
                        <span className="text-muted-foreground">{d.detalhe}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-muted-foreground">
              Um score do tipo "esse vendedor ou setor costuma ganhar" pareceria inteligente, mas estaria ordenando ruído.
            </p>
          </section>

          <section>
            <h3 className="font-display text-xl text-foreground">Onde está o problema</h3>
            <p className="mt-2 text-muted-foreground">
              O pipeline parece ter US$ 5,0 milhões em aberto, mas só uma pequena parte disso está viva. Qualquer previsão de receita feita sobre ele está inflada.
            </p>
            <div className="mt-3 overflow-hidden rounded-lg border border-border">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-border bg-muted">
                    <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Indicador</th>
                    <th className="px-3 py-2 text-xs font-medium text-muted-foreground">Número</th>
                    <th className="px-3 py-2 text-xs font-medium text-muted-foreground">O que significa</th>
                  </tr>
                </thead>
                <tbody>
                  {problema.map((p) => (
                    <tr key={p.indicador} className="border-b border-border last:border-0">
                      <td className="px-3 py-2.5 align-top text-muted-foreground">{p.indicador}</td>
                      <td className="px-3 py-2.5 align-top font-numeric font-semibold tabular-nums text-foreground">{p.numero}</td>
                      <td className="px-3 py-2.5 align-top text-muted-foreground">{p.significado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-muted-foreground">
              O caso do Central pede uma conversa com a gestão: o que aconteceu com esse lote de julho?
            </p>
          </section>

          <section>
            <h3 className="font-display text-xl text-foreground">O que recomendamos</h3>
            <p className="mt-2 text-muted-foreground">A primeira ação é de gestão, não de tecnologia: limpar o pipeline.</p>
            <ol className="mt-3 space-y-3">
              {recomendacoes.map((r, i) => (
                <li key={r.titulo} className="flex gap-3">
                  <span className="font-numeric text-lg font-semibold tabular-nums text-primary">{i + 1}</span>
                  <div>
                    <strong className="text-foreground">{r.titulo}</strong>{" "}
                    <span className="text-muted-foreground">{r.detalhe}</span>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className="rounded-lg border border-border bg-muted p-4">
            <h3 className="font-display text-xl text-foreground">Ressalvas</h3>
            <p className="mt-2 text-muted-foreground">
              Os números são um retrato do CRM em 31/12/2017. Os dados têm sinais de serem simulados: por exemplo, há tantos deals iniciados
              no sábado e no domingo quanto em dias úteis. Com dados reais e o registro de atividades, é provável que vendedor e cliente
              passem a ter algum peso, e o modelo deve ser recalibrado. A análise completa, com todos os testes estatísticos, está no
              notebook do projeto.
            </p>
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
