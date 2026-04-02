# Como submeter sua solução

A submissão é feita **exclusivamente via Pull Request**. Isso faz parte do teste — se você vai implementar IA em áreas inteiras, precisa saber trabalhar com git.

## Passo a passo

1. **Fork** este repositório
2. Clone o fork: `git clone https://github.com/SEU-USUARIO/ai-master-challenge.git`
3. Crie uma branch: `git checkout -b submission/seu-nome`
4. Crie sua pasta: `mkdir -p submissions/seu-nome`
5. Adicione sua solução e process log dentro da pasta
6. Commit e push: `git push origin submission/seu-nome`
7. Abra um **Pull Request** para `main` com título: `[Submission] Seu Nome — Challenge XXX`

## Estrutura da pasta

```
submissions/seu-nome/
├── README.md            ← Use o template de templates/submission-template.md
├── solution/            ← Sua solução (análise, código, protótipo)
│   ├── ...
│   └── ...
├── process-log/         ← Evidências de uso de IA
│   ├── screenshots/
│   ├── chat-exports/
│   └── ...
└── docs/                ← Documentação adicional (se houver)
```

## Checklist antes de abrir o PR

- [ ] Escolhi um challenge e li o README completo
- [ ] Minha solução está na pasta `submissions/meu-nome/`
- [ ] Incluí o process log com evidências de uso de IA
- [ ] O README da minha submissão segue o [template](./templates/submission-template.md)
- [ ] Se construí código, incluí instruções de setup
- [ ] Não modifiquei nenhum arquivo fora da minha pasta

## Regras do PR

- Só modifique arquivos dentro de `submissions/seu-nome/` — PRs que alteram outros arquivos serão rejeitados
- Um PR por pessoa. Se quiser atualizar, faça push na mesma branch
- O título do PR deve seguir o formato: `[Submission] Nome — Challenge XXX`

## Nunca usou git?

Se você está aprendendo agora, use IA para te ajudar. Sério — pedir pro Claude ou ChatGPT te guiar pelo processo de fork, branch e PR é exatamente o tipo de coisa que um AI Master faz. Isso já é parte do teste.

---

## Dúvidas?

Abra uma [issue](../../issues) neste repositório.
