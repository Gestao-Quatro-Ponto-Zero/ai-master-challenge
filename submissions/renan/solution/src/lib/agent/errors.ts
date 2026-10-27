import Anthropic from "@anthropic-ai/sdk";

/** Traduz erros do SDK em mensagens para o usuário, do mais específico ao mais geral. */
export function describeApiError(error: unknown): { status: number; message: string } {
  if (error instanceof Anthropic.AuthenticationError) {
    return { status: 401, message: "A chave da API foi recusada. Confira a chave em Configurações." };
  }
  if (error instanceof Anthropic.PermissionDeniedError) {
    return { status: 403, message: "Esta chave não tem permissão para o modelo escolhido. Troque o modelo em Configurações." };
  }
  if (error instanceof Anthropic.NotFoundError) {
    return { status: 404, message: "O modelo escolhido não está disponível para esta chave." };
  }
  if (error instanceof Anthropic.RateLimitError) {
    return { status: 429, message: "Limite de uso da API atingido. Aguarde um pouco e tente de novo." };
  }
  if (error instanceof Anthropic.BadRequestError) {
    return { status: 400, message: "A API recusou o pedido. Tente reformular a pergunta." };
  }
  if (error instanceof Anthropic.APIConnectionError) {
    return { status: 502, message: "Não foi possível falar com a API da Anthropic. Verifique a conexão." };
  }
  if (error instanceof Anthropic.APIError) {
    return { status: 502, message: "A API da Anthropic respondeu com erro. Tente de novo em instantes." };
  }
  return { status: 500, message: "Erro inesperado no agente." };
}
