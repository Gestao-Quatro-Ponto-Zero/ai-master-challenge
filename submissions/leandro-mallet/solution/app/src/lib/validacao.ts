// Frase simples para um erro de campo na API. A tela já valida antes; isto cobre quem chama a rota direto.
// Nunca devolve o valor digitado, só o nome do campo e a regra.
import { z } from "zod";

/** Texto obrigatório: tira os espaços das pontas ANTES de conferir, para "só espaços" contar como vazio. */
export const textoObrigatorio = (maximo: number) => z.string().trim().min(1).max(maximo);
/** Texto opcional, também sem os espaços das pontas ("só espaços" vira vazio). */
export const textoOpcional = (maximo: number) => z.string().trim().max(maximo).nullish();

/** Marca um campo como faltando dentro de um superRefine (vira "Preencha …" na resposta). */
export function exigir(ctx: z.RefinementCtx, campo: string, valor: string | null | undefined) {
  if (!valor) ctx.addIssue({ code: "custom", path: [campo], message: "obrigatório" });
}

/** Mesmas regras do banco (core_contatos). */
export const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
export const TELEFONE = /^[0-9 +().-]{6,25}$/;

export const FRASE_GENERICA = "Não entendi o pedido. Recarregue a página e tente de novo.";

/** O que a rota precisa saber de um erro de validação (um subconjunto do "issue" do zod). */
export interface ErroDeCampo {
  code: string;
  path: PropertyKey[];
  message?: string;
  origin?: string;
  format?: string;
  maximum?: number | bigint;
  minimum?: number | bigint;
}

// Nome do campo como a pessoa lê na tela, com o artigo.
const ROTULOS: Record<string, string> = {
  nome: "o nome",
  cargo: "o cargo",
  email: "o e-mail",
  telefone: "o telefone",
  texto: "o comentário",
  comentario: "o comentário",
  nota: "a observação",
  produto: "o produto",
  conta: "a empresa",
  vendedor: "o vendedor",
  estagio: "o estágio",
  para: "o estágio",
  valor: "o valor",
  motivo: "o motivo da perda",
  acao: "a ação",
  resultado: "a marcação (feita ou pulada)",
  tipoAtividade: "o tipo de atividade",
  tagId: "a tag",
  cor: "a cor da tag",
  tipo: "a ação em lote",
  ids: "os leads",
  dealId: "o lead",
  setor: "o setor",
  funcionarios: "o número de funcionários",
  receitaMilhoes: "a receita",
  anoFundacao: "o ano de fundação",
  sede: "a sede",
  empresaMae: "a empresa-mãe",
  usuarioId: "o perfil",
};

const maiuscula = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

function valorEm(corpo: unknown, caminho: PropertyKey[]): unknown {
  let v = corpo;
  for (const p of caminho) {
    if (v === null || typeof v !== "object") return undefined;
    v = (v as Record<PropertyKey, unknown>)[p];
  }
  return v;
}

/**
 * Traduz o primeiro erro de validação em frase específica ("E-mail inválido…", "Preencha o nome.").
 * Campo desconhecido ou corpo que não é um objeto: frase genérica.
 */
export function fraseDeValidacao(erros: ErroDeCampo[], corpo: unknown): { frase: string; campo: string | null } {
  const e = erros[0];
  const campo = e && typeof e.path[0] === "string" ? e.path[0] : null;
  const rotulo = campo ? ROTULOS[campo] : undefined;
  if (!e || !campo || !rotulo || corpo === null || typeof corpo !== "object") return { frase: FRASE_GENERICA, campo: null };

  const valor = valorEm(corpo, e.path);
  const vazio = valor === undefined || valor === null || (typeof valor === "string" && valor.trim() === "");
  const frase = ((): string => {
    if (campo === "ids" && e.code === "too_big") return `Selecione até ${String(e.maximum)} leads por vez; refine o filtro.`;
    if (campo === "ids") return "Selecione pelo menos um lead.";
    if (vazio) return `Preencha ${rotulo}.`;
    if (campo === "email" && (e.code === "invalid_format" || e.code === "custom")) return "E-mail inválido. Confira o endereço (exemplo: nome@empresa.com).";
    if (campo === "telefone" && (e.code === "invalid_format" || e.code === "custom")) return "Telefone inválido. Use de 6 a 25 caracteres: números, espaço, +, parênteses, ponto ou traço.";
    if (e.code === "too_big" && e.origin === "string") return `${maiuscula(rotulo)} pode ter no máximo ${String(e.maximum)} caracteres.`;
    if (e.code === "too_small" && e.origin === "string") return `Preencha ${rotulo}.`;
    if (e.code === "too_big") return `${maiuscula(rotulo)} não pode passar de ${Number(e.maximum).toLocaleString("pt-BR")}.`;
    if (e.code === "too_small") return `${maiuscula(rotulo)} não pode ser menor que ${Number(e.minimum).toLocaleString("pt-BR")}.`;
    if (e.code === "invalid_value") return `Escolha uma opção válida para ${rotulo}.`;
    return `Confira ${rotulo}: o valor não é aceito.`;
  })();
  return { frase, campo };
}
