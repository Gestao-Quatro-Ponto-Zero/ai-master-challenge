import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const walk = (dir: string): string[] =>
  readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });

describe('architecture (F1: sem hooks)', () => {
  const files = walk(join(__dirname)).filter((f) => /\.tsx?$/.test(f) && !/\.test\.tsx?$/.test(f) && !f.includes('/test/'));
  it('no React hooks in source', () => {
    const hook = /\buse(State|Effect|Memo|Callback|Ref|Reducer|Context|LayoutEffect)\s*\(/;
    expect(files.filter((f) => hook.test(readFileSync(f, 'utf8')))).toEqual([]);
  });
  it('no function components with hooks: only classes render UI', () => {
    const tsx = files.filter((f) => f.endsWith('.tsx'));
    expect(tsx.filter((f) => !/extends\s+React\.(Pure)?Component/.test(readFileSync(f, 'utf8')) && !f.endsWith('main.tsx'))).toEqual([]);
  });
});

describe('architecture (sem regra de negócio no front)', () => {
  const src = walk(join(__dirname)).filter((f) => /\.tsx?$/.test(f) && !/\.test\.tsx?$/.test(f));
  const outsideMock = src.filter((f) => !f.includes('/api/mock/'));
  const strip = (t: string) => t.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');

  it('limiares do modelo (138, 104, 41, 80, 40) só existem em src/api/mock', () => {
    const literal = /(?<![\w.#-])(138|104|41|80|40)(?![\w.%-])/;
    const hits = outsideMock.filter((f) => literal.test(strip(readFileSync(f, 'utf8')).replace(/(['"`]).*?\1/g, '""')));
    expect(hits).toEqual([]);
  });
  it('componentes e lib não importam o mock', () => {
    const bad = src.filter((f) => /\/(components|lib|pages)\//.test(f) && /from\s+['"][^'"]*api\/mock/.test(readFileSync(f, 'utf8')));
    expect(bad).toEqual([]);
  });
  it('só createApi e a camada de api conhecem o mock', () => {
    const bad = src.filter((f) => !f.includes('/api/') && /from\s+['"][^'"]*\/mock\//.test(readFileSync(f, 'utf8')));
    expect(bad).toEqual([]);
  });
});

