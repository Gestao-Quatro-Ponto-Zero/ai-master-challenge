"use client";

import { useRef, useState } from "react";
import { spinQuestions } from "../../lib/presentation.mjs";
export default function SpinGuide({ deal }) {
  const questions = spinQuestions(deal);
  const [active, setActive] = useState(0),
    tabRefs = useRef([]),
    current = questions[active];
  return (
    <section className="spin-guide">
      <div className="spin-header">
        <span className="eyebrow">CONVERSA GUIADA · SPIN</span>
        <small>
          Use como apoio. Ouça a resposta e siga o que fizer sentido.
        </small>
      </div>
      <div className="spin-context">
        <strong>Contexto para você</strong>
        <p>{questions[0].context}</p>
      </div>
      <div className="spin-tabs" role="tablist" aria-label="Perguntas SPIN">
        {questions.map((q, i) => (
          <button
            key={q.key}
            ref={(el) => {
              tabRefs.current[i] = el;
            }}
            id={`spin-tab-${q.key}`}
            role="tab"
            aria-selected={active === i}
            aria-controls="spin-active-question"
            tabIndex={active === i ? 0 : -1}
            onClick={() => setActive(i)}
            onKeyDown={(e) => {
              let next;
              if (e.key === "ArrowRight") next = (i + 1) % 4;
              if (e.key === "ArrowLeft") next = (i + 3) % 4;
              if (e.key === "Home") next = 0;
              if (e.key === "End") next = 3;
              if (next !== undefined) {
                e.preventDefault();
                setActive(next);
                tabRefs.current[next]?.focus();
              }
            }}
          >
            <strong>{q.key}</strong>
            <span>{q.label}</span>
          </button>
        ))}
      </div>
      <article
        className={`spin-question spin-${current.key}`}
        id="spin-active-question"
        role="tabpanel"
        aria-labelledby={`spin-tab-${current.key}`}
      >
        <p>“{current.question}”</p>
        <small>{current.investigate}</small>
      </article>
    </section>
  );
}
