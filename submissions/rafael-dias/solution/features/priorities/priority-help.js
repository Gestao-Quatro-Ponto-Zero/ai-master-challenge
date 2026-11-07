export default function PriorityHelp({ data }) {
  return (
    <div className="help-page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">PARA USAR NO DIA A DIA</div>
          <h1>
            Entenda suas prioridades<span className="gold">.</span>
          </h1>
          <p>
            O que a nota diz, o que ela não diz e como avançar uma oportunidade.
          </p>
        </div>
      </div>
      <section className="help-intro panel">
        <span className="help-example-score">
          85<small>/100</small>
        </span>
        <div>
          <h2>Uma nota alta significa: vale olhar primeiro.</h2>
          <p>
            Ela ajuda a escolher a próxima conversa. Quem confirma se existe uma
            boa venda é você, conversando com o cliente.
          </p>
        </div>
      </section>
      <div className="help-grid">
        <section className="panel help-card">
          <span className="help-number">01</span>
          <h2>Por que uma oportunidade aparece primeiro?</h2>
          <p>O sistema considera três coisas que já existem no CRM:</p>
          <ul>
            <li>
              <strong>Andamento:</strong> a negociação já começou ou ainda está
              em prospecção?
            </li>
            <li>
              <strong>Potencial:</strong> qual é o preço de referência do
              produto? Isso não é uma previsão de receita.
            </li>
            <li>
              <strong>Tempo:</strong> há quanto tempo ela estava em negociação,
              comparado ao histórico daquele produto?
            </li>
          </ul>
          <p>
            Retornos que você agendou e ficaram vencidos passam à frente. Contas
            sem identificação têm uma fila própria para completar cadastro.
          </p>
          <details>
            <summary>Como os pontos são distribuídos?</summary>
            <p>
              Andamento: até 40 pontos. Preço do produto: até 30, limitando o
              peso dos produtos mais caros. Tempo: até 30. A soma vai de 0 a
              100. Sem data, o componente de tempo fica sem pontos. Falta de
              nome da conta não reduz a nota.
            </p>
            <p>
              Até um ciclo típico: 30 pontos de tempo; até dois: 20; acima de
              dois: 10 e revisão sugerida. A referência é a duração central dos
              negócios já encerrados daquele produto; com pouco histórico,
              usamos a referência geral.
            </p>
          </details>
        </section>
        <section className="panel help-card">
          <span className="help-number">02</span>
          <h2>Quando o cliente vira um SQL?</h2>
          <p>
            SQL é uma <strong>oportunidade qualificada para venda</strong>. Para
            confirmar, registre as respostas do cliente:
          </p>
          <ul>
            <li>
              <strong>Necessidade:</strong> o que ele precisa resolver?
            </li>
            <li>
              <strong>Decisor:</strong> quem aprova a compra e como?
            </li>
            <li>
              <strong>Prazo:</strong> quando pretende decidir?
            </li>
          </ul>
          <div className="help-takeaway">
            Nota alta não transforma o cliente em SQL. As respostas confirmadas
            é que permitem avançar.
          </div>
          <p>
            Depois de confirmar, prepare e apresente uma proposta alinhada ao
            que o cliente precisa.
          </p>
        </section>
        <section className="panel help-card">
          <span className="help-number">03</span>
          <h2>O que a saúde da negociação mostra?</h2>
          <p>
            Mostra evidências atuais da compra, separadas do potencial
            histórico.
          </p>
          <ul>
            <li>
              <strong>40 pontos:</strong> necessidade, decisor e prazo
              confirmados.
            </li>
            <li>
              <strong>25 pontos:</strong> participação recente do comprador.
              Tentativas não são respostas.
            </li>
            <li>
              <strong>25 pontos:</strong> próximo passo aceito pelo cliente e
              data válida.
            </li>
            <li>
              <strong>10 pontos:</strong> condições financeiras compatíveis
              informadas na proposta.
            </li>
          </ul>
          <p>
            Sem informação suficiente, aparece “Em validação”. Não deduzimos
            respostas nos registros antigos. Conversas perdem força após 7 dias;
            qualificação e condições precisam ser reconfirmadas após 30 dias. Um
            risco pode aparecer mesmo com nota alta.
          </p>
          <div className="help-takeaway">
            Regras iniciais de piloto, não chance de fechar. Retorno vencido
            entra na frente das rodadas; pausas e compromissos futuros são
            respeitados.
          </div>
        </section>
        <section className="panel help-card">
          <span className="help-number">04</span>
          <h2>O que entra no seu plano do dia?</h2>
          <p>
            Na primeira abertura do dia, o sistema prepara até 20 tarefas da sua
            carteira em quatro rodadas de cinco: retornos de hoje ou vencidos,
            oportunidades prioritárias e cadastros quando necessário.
          </p>
          <p>
            Conclua a rodada atual para iniciar a próxima. Os checkpoints
            permanecem; retornos vencidos e avanços atuais podem entrar no foco
            fora da rodada. Salvar a ação pedida conclui a tarefa; anotar algo
            ou só reagendar uma conversa não conta como contato realizado.
          </p>
          <p>
            O indicador lateral mostra o total do dia e as rodadas concluídas.
            Se houver menos de 20 disponíveis, o plano se adapta. No dia
            seguinte, o sistema prepara outro plano com o que estiver
            disponível.
          </p>
        </section>
      </div>
      <section className="panel help-faq">
        <h2>Sobre esta versão</h2>
        <div className="faq-grid">
          <details>
            <summary>Por que aparece a data de 2017?</summary>
            <p>
              Os dados fornecidos pelo desafio são históricos. A base tem{" "}
              {data.summary.total.toLocaleString("pt-BR")} oportunidades, sendo{" "}
              {data.summary.open.toLocaleString("pt-BR")} abertas. A nota usa
              esse contexto de 2017; seus contatos e tarefas são registrados com
              a data atual. Esse tempo antigo não prova falta de contato
              recente.
            </p>
          </details>
          <details>
            <summary>
              Por que alguns clientes estão sem telefone ou informações?
            </summary>
            <p>
              O arquivo original não traz telefone, e-mail ou nome do comprador.
              Essas informações precisam ser cadastradas a partir de uma fonte
              verificada. Nunca preenchemos intenção de compra ou dados de
              contato por suposição.
            </p>
          </details>
          <details>
            <summary>Onde meus registros ficam salvos?</summary>
            <p>
              Neste navegador. Eles continuam depois de recarregar, mas ainda
              não aparecem em outro computador. Selecionar um vendedor muda a
              carteira, sem fazer login. Você pode exportar atividades em
              Resultados.
            </p>
          </details>
          <details>
            <summary>O sistema liga ou manda mensagem sozinho?</summary>
            <p>
              Não. Ao cadastrar um telefone ou e-mail, os atalhos abrem os
              aplicativos do seu computador. A conversa e o registro do
              resultado continuam sob seu controle.
            </p>
          </details>
        </div>
      </section>
    </div>
  );
}
