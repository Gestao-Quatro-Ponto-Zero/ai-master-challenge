/** Erro lançado quando a API responde com status fora de 2xx (formato de erro padrão do contrato). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;

  constructor(status: number, code: string, message: string, requestId: string | null = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message;
  return 'Algo deu errado. Tente de novo.';
}
