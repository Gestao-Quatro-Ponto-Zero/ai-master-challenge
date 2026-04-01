export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return 'R$ 0'
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
}
