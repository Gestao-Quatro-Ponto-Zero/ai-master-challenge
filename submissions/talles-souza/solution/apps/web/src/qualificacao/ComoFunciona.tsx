/**
 * Como a nota funciona: o score é a qualidade do negócio (a idade medida + as respostas do
 * vendedor, com os pesos declarados como heurística); a ordem da tela usa o que há a ganhar e o
 * preço fica fora do score. Abaixo, de onde vem a chance (o motor de pontos e a tabela que ele gerou: cada fator, se entrou, o
 * acerto sozinho, os pontos por valor e quantos negócios), o acerto da chance ao lado do acerto
 * só da idade, a curva por idade, os grupos e seus limites, as perguntas do método e os limites
 * dos dados.
 */
import { emPorcento, textoDoScore, textosDoMotor } from '@lead-scorer/dominio/priorizacao';
import type { ChanceHistorica, MotorDePontos } from '@lead-scorer/dominio/score';
import { useEffect, useState } from 'react';
import { useApp, type Base } from '../app/contexto';
import { formatarData, formatarInteiro } from '../ui/formato';

/** AUC → "de cada 100 pares" (0,83 → 83). */
const cem = (x: number | null) => (x === null ? '–' : String(Math.round(x * 100)));
const comSinal = (x: number) => (x > 0 ? '+' + x : x < 0 ? '−' + Math.abs(x) : '0');

export function ComoFunciona({ base }: { base: Base }) {
  const { deps, respostasCompartilhadas } = useApp();
  const { politica, metodo, resumo, textos } = base;
  const { janela } = resumo;
  const [chance, setChance] = useState<ChanceHistorica | null>(null);
  const [motor, setMotor] = useState<MotorDePontos | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    Promise.all([deps.cliente.chance(), deps.cliente.motor()])
      .then(([c, m]) => {
        if (!vivo) return;
        setChance(c);
        setMotor(m);
      })
      .catch((e: unknown) => {
        if (vivo) setErro(e instanceof Error ? e.message : String(e));
      });
    return () => {
      vivo = false;
    };
  }, [deps]);

  const tc = politica.textos.comoFunciona;
  const tm = motor ? textosDoMotor(politica, motor) : null;
  return (
    <>
      <section className="topo">
        <div className="container cabeca">
          <p className="eyebrow">Como a nota funciona</p>
          <h1 className="titulo">
            O score diz se o negócio é bom{' '}
            <em>pela idade dele e pelas suas respostas. A ordem da tela é outra coisa.</em>
          </h1>
          <p className="sub">{politica.textos.indicador.aviso}</p>
        </div>
      </section>
      <div className="container principal" data-testid="como-funciona">
        <section className="secao">
          <h2>
            Como <em>calculamos</em>{' '}
            {politica.provisoria ? <span className="selo">Provisório</span> : null}
          </h2>
          {erro ? <p className="erro">Não deu para carregar as medições: {erro}</p> : null}
          <p className="texto" data-testid="como-funciona-score">
            {textoDoScore(politica)}
          </p>
          {motor && tm ? (
            <>
              <p className="texto">{tm.calculo}</p>
              <p className="texto">{tm.testado}</p>
              <p className="texto" data-testid="como-funciona-acerto">
                {tm.acerto}
              </p>
              <div className="rolagem">
                <table className="tabela" data-testid="tabela-motor">
                  <caption className="aviso">
                    Pontos de cada valor = 10 × ln(quanto fechou ÷ a média), medidos nos negócios
                    abertos em {formatarData(motor.validacao.corte)} (
                    {formatarInteiro(motor.validacao.n)}, {formatarInteiro(motor.validacao.ganhos)}{' '}
                    fecharam até {formatarData(motor.validacao.ate)}). Acerto sozinho: em quantos de
                    cada 100 pares o fator, sozinho, dá a nota maior a quem fechou (50 = sorteio).
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Fator</th>
                      <th scope="col">Na nota?</th>
                      <th scope="col">Acerto sozinho</th>
                      <th scope="col">Pontos por valor (negócios)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {motor.fatores.map((f) => (
                      <tr key={f.id} data-fator={f.id}>
                        <th scope="row">{f.rotulo}</th>
                        <td className="tabela__texto">{tm.motivos[f.motivo]}</td>
                        <td>{cem(f.aucValidacao)}</td>
                        <td className="tabela__texto">
                          {f.categorias
                            .map(
                              (c) =>
                                c.rotulo +
                                ': ' +
                                comSinal(c.pontos) +
                                ' (' +
                                formatarInteiro(c.n) +
                                ')',
                            )
                            .join(' · ')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
          {chance ? (
            <div className="rolagem">
              <table className="tabela" data-testid="tabela-chance">
                <caption className="aviso">
                  Negócios abertos em {formatarData(chance.corte)} e quantos fecharam até{' '}
                  {formatarData(chance.referencia)}.
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Idade</th>
                    <th scope="col">Negócios</th>
                    <th scope="col">Fecharam</th>
                    <th scope="col">Chance</th>
                  </tr>
                </thead>
                <tbody>
                  {chance.faixas.map((f) => (
                    <tr key={f.rotulo}>
                      <th scope="row">{f.rotulo}</th>
                      <td>{formatarInteiro(f.n)}</td>
                      <td>{formatarInteiro(f.ganhos)}</td>
                      <td>{f.taxa === null ? '–' : emPorcento(f.taxa) + '%'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>

        <section className="secao">
          <h2>
            Os grupos e <em>os limites</em>
          </h2>
          <ul className="lista">
            {politica.faixas.map((f) => (
              <li key={f.bloco + f.rotulo} className={'item item--simples bloco--' + f.bloco}>
                <p className="item__titulo">
                  {textos.grupos[f.bloco].titulo}: {f.rotulo}
                </p>
                <p className="item__porque">{f.porque}</p>
              </li>
            ))}
            <li className="item item--simples bloco--sem_inicio">
              <p className="item__titulo">{textos.grupos.sem_inicio.titulo}</p>
              <p className="item__porque">{politica.semData.porque}</p>
            </li>
          </ul>
          <p className="texto">
            Dentro de cada grupo, o que deve render mais aparece primeiro.{' '}
            {politica.ordenacao.porque} O preço e a receita esperada não mudam o score nem o grupo.
          </p>
          {politica.aviso ? <p className="aviso">{politica.aviso}</p> : null}
        </section>

        <section className="secao">
          <h2>
            As perguntas <em>(opcionais)</em>
          </h2>
          <p className="texto">
            Método {metodo.nome}. Cada pergunta é sim ou não. Responder “não” troca a ação pela
            frase da pergunta; deixar em branco não tira ponto.
          </p>
          <ul className="lista">
            {metodo.criterios.map((c) => {
              const p = c.perguntaId
                ? metodo.perguntas.find((x) => x.id === c.perguntaId)
                : undefined;
              return (
                <li key={c.id} className="item item--simples">
                  <p className="item__titulo">
                    {c.nome}: {c.descricao}
                  </p>
                  <p className="item__porque">
                    {c.origem === 'dado'
                      ? 'Vem dos dados.'
                      : 'Só o vendedor confirma: “' + (p?.pergunta ?? '') + '”'}
                  </p>
                  {p?.acaoSeNao ? <p className="item__nota">Se “não”: {p.acaoSeNao}</p> : null}
                </li>
              );
            })}
          </ul>
          <p className="texto">{tc.fonte}</p>
          {metodo.fontes.length > 0 ? (
            <p className="aviso">Fontes: {metodo.fontes.join(' · ')}.</p>
          ) : null}
        </section>

        <section className="secao">
          <h2>
            Limites <em>dos dados</em>
          </h2>
          <dl className="numeros">
            <div>
              <dt>Metade dos negócios ganhos fechou em até</dt>
              <dd>{janela.p50Dias} dias</dd>
            </div>
            <div>
              <dt>95% fecharam em até</dt>
              <dd>{janela.p95Dias} dias</dd>
            </div>
            <div>
              <dt>O mais demorado levou</dt>
              <dd>{janela.maxDias} dias</dd>
            </div>
          </dl>
          <ul className="texto">
            <li>{textos.avisos.referencia} Não é a data de hoje.</li>
            <li>{textos.avisos.nutricao}</li>
            <li>
              {formatarInteiro(resumo.total)} negócios no histórico,{' '}
              {formatarInteiro(resumo.abertos)} abertos.
            </li>
            <li data-testid="como-funciona-qualidade">
              Qualidade do dado: {formatarInteiro(resumo.lacunas.sem_conta)} negócios sem empresa
              cadastrada (é falta no cadastro, não tira ponto) e{' '}
              {formatarInteiro(resumo.lacunas.sem_engage_date)} sem data de início (ficam em “
              {textos.grupos.sem_inicio.titulo}”).
            </li>
            <li>Escolher o seu nome não é login: só diz de quem é a lista.</li>
            <li data-testid="como-funciona-respostas">
              {respostasCompartilhadas
                ? politica.textos.comoFunciona.respostasBanco
                : politica.textos.comoFunciona.respostasLocal}
            </li>
          </ul>
        </section>
      </div>
    </>
  );
}
