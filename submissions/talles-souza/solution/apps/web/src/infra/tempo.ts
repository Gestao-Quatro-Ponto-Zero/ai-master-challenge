/** Relógio, espera e sorteio injetáveis: os testes controlam o tempo e o jitter. */

/** Milissegundos desde a época, como `Date.now`. */
export type Relogio = () => number;

/** Espera `ms` milissegundos. */
export type Dormir = (ms: number) => Promise<void>;

/** Número em [0, 1), como `Math.random`. */
export type Aleatorio = () => number;

/** Agenda e cancela um disparo (o timeout por requisição usa isto). */
export interface Temporizador {
  definir(fn: () => void, ms: number): unknown;
  limpar(id: unknown): void;
}

export const relogioDoSistema: Relogio = () => Date.now();

export const dormirDeVerdade: Dormir = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

export const aleatorioDoSistema: Aleatorio = () => Math.random();

export const temporizadorDoSistema: Temporizador = {
  definir: (fn, ms) => setTimeout(fn, ms),
  limpar: (id) => clearTimeout(id as ReturnType<typeof setTimeout>),
};
