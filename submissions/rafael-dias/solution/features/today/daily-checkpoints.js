import Icon from "../../components/ui/icon";
export default function DailyCheckpoints({ progress }) {
  if (!progress.total) return null;
  return (
    <section
      className="daily-checkpoints"
      id="daily-checkpoints"
      aria-label="Rodadas do dia"
    >
      <div className="checkpoint-heading">
        <div>
          <span className="eyebrow">SEU PROGRESSO</span>
          <h3>Rodadas do dia</h3>
        </div>
        <span>
          {progress.completed}/{progress.total} ações
        </span>
      </div>
      <ol>
        {progress.batches.map((b) => (
          <li
            key={b.index}
            className={
              b.done
                ? "complete"
                : b.index === progress.activeBatch
                  ? "current"
                  : "waiting"
            }
            aria-current={b.index === progress.activeBatch ? "step" : undefined}
          >
            <span className="checkpoint-icon">
              {b.done ? (
                <Icon name="check" size={14} />
              ) : b.index === progress.activeBatch ? (
                <span>{b.index + 1}</span>
              ) : (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  aria-hidden="true"
                >
                  <rect x="5" y="10" width="14" height="11" rx="3" />
                  <path d="M8 10V7a4 4 0 018 0v3" />
                </svg>
              )}
            </span>
            <div>
              <strong>Rodada {b.index + 1}</strong>
              <small>
                {b.done
                  ? "Concluída"
                  : b.index === progress.activeBatch
                    ? b.completed + "/" + b.total + " · em andamento"
                    : "Na sequência"}
              </small>
            </div>
          </li>
        ))}
      </ol>
      <p>
        Cinco prioridades por vez. Ao concluir, a próxima rodada entra no foco.
        Sua carteira continua acessível no pipeline.
      </p>
    </section>
  );
}
