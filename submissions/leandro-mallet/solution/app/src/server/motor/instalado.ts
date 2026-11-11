import "server-only";
// O motor do score que a rotina diária usa: a lógica da #3 (src/lib/score/) ligada ao banco por motor-score.ts.
// Para desligar o cálculo sem tirar o cron, troque por null: a rotina registra "sem_motor" e tenta de novo no dia seguinte.
import type { MotorScore } from "./contrato";
import { motorScore } from "./motor-score";

export const motorInstalado: MotorScore | null = motorScore;
