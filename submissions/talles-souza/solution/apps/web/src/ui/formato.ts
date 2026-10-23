/** Formatos de número e data em português, para o vendedor ler sem conta. */

const moeda = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});
const inteiro = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });

/** "US$ 4.821". */
export function formatarUs(valor: number): string {
  return moeda.format(valor).replace(/\s/g, ' ');
}

/** "4.540". */
export function formatarInteiro(valor: number): string {
  return inteiro.format(valor);
}

/** "2017-12-31" → "31/12/2017" (sem fuso: a data é do dataset, não do relógio). */
export function formatarData(iso: string): string {
  const [a, m, d] = iso.slice(0, 10).split('-');
  return a && m && d ? d + '/' + m + '/' + a : iso;
}

/** Soma dias a uma data ISO `AAAA-MM-DD`, em UTC. */
export function somarDias(iso: string, dias: number): string {
  const t = Date.parse(iso.slice(0, 10) + 'T00:00:00Z') + dias * 86_400_000;
  return new Date(t).toISOString().slice(0, 10);
}
