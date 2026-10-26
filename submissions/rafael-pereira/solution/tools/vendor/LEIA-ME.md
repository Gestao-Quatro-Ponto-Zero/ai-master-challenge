# tools/vendor

- `axe.min.js`: **axe-core 4.9.1**, Deque Systems, licença **MPL-2.0** (https://www.mozilla.org/MPL/2.0/). Arquivo sem modificação, copiado do pacote publicado do axe-core. Usado só por `tools/check_views.py`, injetado na página com `page.add_script_tag(path=...)`. Não faz parte da interface publicada e não é carregado por `app/index.html`.
- Motivo de estar aqui: a máquina não tem Node nem npm, então o `@axe-core/playwright` não está disponível. A versão Python do Playwright injeta o mesmo `axe.min.js` e chama `axe.run()`.
