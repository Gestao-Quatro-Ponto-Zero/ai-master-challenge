/**
 * Método de qualificação em uso: BANT. T (tempo) e B (orçamento) vêm do dado: a idade contra a
 * curva do histórico e o preço de tabela como contexto. A (o vendedor fala com quem decide), N
 * (o comprador confirmou que o produto resolve o problema dele) e o compromisso (próxima conversa
 * com data) só o vendedor confirma, pelas três perguntas opcionais. Cada resposta soma ou tira do
 * score (pesos em `score/qualidade.config.ts`, heurística declarada) e a resposta "não" troca a
 * ação do negócio pela frase da pergunta; nenhuma resposta muda o bloco nem a ordem da tela.
 * Trocar o método = trocar este config.
 */
import type { MetodoQualificacao } from './index';

export const metodoProvisorio: MetodoQualificacao = {
  id: 'metodo-bant-v1',
  nome: 'BANT',
  versao: '1.1.0',
  provisorio: false,
  aviso: null,
  criterios: [
    {
      id: 'T',
      nome: 'Tempo',
      origem: 'dado',
      descricao: 'A idade do negócio contra a curva do histórico.',
      perguntaId: null,
    },
    {
      id: 'B',
      nome: 'Orçamento',
      origem: 'dado',
      descricao: 'O preço de tabela do produto, como contexto do que está em jogo.',
      perguntaId: null,
    },
    {
      id: 'A',
      nome: 'Quem decide',
      origem: 'vendedor',
      descricao: 'O vendedor fala direto com quem decide a compra.',
      perguntaId: 'decisor',
    },
    {
      id: 'N',
      nome: 'Necessidade',
      origem: 'vendedor',
      descricao: 'O comprador confirmou que o problema dele é um que o produto resolve.',
      perguntaId: 'dor',
    },
    {
      id: 'compromisso',
      nome: 'Compromisso',
      origem: 'vendedor',
      descricao: 'Próxima conversa marcada, com data.',
      perguntaId: 'proximo_passo',
    },
  ],
  perguntas: [
    {
      id: 'decisor',
      rotulo: 'Quem decide',
      pergunta: 'Você está falando com quem decide a compra?',
      aplicaEm: ['foque_agora', 'siga_no_ritmo', 'sem_inicio'],
      acaoSeNao: 'Descubra quem decide a compra e marque uma conversa com essa pessoa.',
      noScore: { sim: 'Decisor confirmado', nao: 'Sem decisor' },
      criterio: 'A',
      referencias: ['BANT'],
      porque: 'Authority (BANT): falar com quem decide a compra, não só saber quem é.',
    },
    {
      id: 'dor',
      rotulo: 'Problema do cliente',
      pergunta: 'O cliente confirmou que o problema dele é um que o produto resolve?',
      aplicaEm: ['foque_agora', 'siga_no_ritmo', 'sem_inicio'],
      acaoSeNao:
        'Pergunte qual problema o cliente quer resolver e confirme com ele que o produto resolve. Sem isso, nada do que você falar vai importar.',
      noScore: {
        sim: 'Problema confirmado pelo cliente',
        nao: 'Problema não confirmado pelo cliente',
      },
      criterio: 'N',
      referencias: ['BANT'],
      porque: 'Need (BANT): o comprador confirma que o produto resolve o problema dele.',
    },
    {
      id: 'proximo_passo',
      rotulo: 'Próxima conversa',
      pergunta: 'Tem próxima conversa marcada, com data?',
      aplicaEm: ['foque_agora', 'siga_no_ritmo', 'sem_inicio'],
      acaoSeNao: 'Proponha uma data agora. Sem data marcada, a chance continua caindo.',
      noScore: { sim: 'Próxima conversa com data', nao: 'Sem próxima conversa marcada' },
      criterio: 'compromisso',
      referencias: ['BANT'],
      porque: 'Compromisso: o próximo passo tem data.',
    },
  ],
  fontes: ['BANT', 'Alex Hormozi, “$100M Leads”', 'Alex Hormozi, “Selling with Logic”'],
};
