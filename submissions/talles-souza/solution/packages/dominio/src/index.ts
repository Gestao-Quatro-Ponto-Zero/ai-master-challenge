/**
 * Domínio do Lead Scorer. Cada contexto é um slice com contrato público no próprio index.ts;
 * este arquivo só reexporta, para quem prefere um ponto de entrada único.
 */
export * from './compartilhado';
export * from './pipeline';
export * from './organizacao';
export * from './qualificacao';
export * from './score';
export * from './priorizacao';
export * from './aplicacao';
