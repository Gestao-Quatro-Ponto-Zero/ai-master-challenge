# Process log

Pacote de evidências do desenvolvimento assistido por IA:

- `chat-export.md`: histórico cronológico desta sessão;
- `evidence-manifest.md`: inventário e hashes de integridade;
- `evidence/videos/`: gravações de tela;
- `evidence/images/`: capturas e diagramas;
- `evidence/links/linksdechats.txt`: conversas externas compartilhadas;
- `screenshots/`: capturas adicionais, quando existirem;
- `narrative/`: relatos complementares, quando existirem.

Os vídeos são evidências binárias e não foram modificados. O manifesto permite verificar sua integridade após cópia, commit ou upload.

## Dificuldades registradas

Durante o processo, o Claude apresentou repetidamente `API Error: Connection closed mid-response`, com aviso de que a resposta poderia estar incompleta. O incidente, impacto, hipóteses e mitigações estão documentados na seção 9 de `chat-export.md`.
