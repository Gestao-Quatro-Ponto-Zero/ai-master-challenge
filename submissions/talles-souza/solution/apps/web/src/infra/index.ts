/**
 * Infraestrutura da web: o cliente da API (timeout, retry com jitter, disjuntor), o modo local
 * (o domínio no navegador) e a persistência das respostas no `localStorage`.
 */
export type { ClienteLeadScorer, Operacao } from './cliente';
export { IDEMPOTENTE, OPERACOES } from './cliente';
export {
  criarClienteHttp,
  lerRetryAfter,
  TIMEOUT_PADRAO_MS,
  type ClienteHttp,
  type OpcoesClienteHttp,
} from './clienteHttp';
export { criarClienteLocal, type ClienteLocal, type OpcoesClienteLocal } from './clienteLocal';
export { criarClienteResiliente, type ClienteResiliente, type Modo } from './clienteResiliente';
export {
  criarDisjuntor,
  DISJUNTOR_PADRAO,
  type Disjuntor,
  type EstadoDisjuntor,
  type OpcoesDisjuntor,
} from './disjuntor';
export { comoErroCliente, ErroCliente, type TipoErroCliente } from './erros';
export {
  CHAVE_COMISSAO,
  CHAVE_PERFIL,
  comissaoValida,
  criarRepositorioNavegador,
  lerComissao,
  lerPerfil,
  PREFIXO_RESPOSTAS,
  salvarComissao,
  salvarPerfil,
  storageDisponivel,
} from './repositorio';
export {
  comRetry,
  esperaComJitter,
  RETRY_PADRAO,
  type ContextoRetry,
  type OpcoesRetry,
} from './retry';
export * from './tempo';
export {
  criarRegistrosHttp,
  SEM_REGISTROS_REMOTOS,
  type OpcoesRegistros,
  type RegistrosRemotos,
} from './registrosHttp';
