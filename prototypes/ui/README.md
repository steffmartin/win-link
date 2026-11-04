# Protótipo vigente do WinLink

Referência visual/navegável para a próxima implementação em Python/PyQt6. Direção visual aprovada, cobertura da interface existente acrescida e novidades mantidas por autorização do usuário. A pasta `prototypes/ui` contém a versão vigente revisada localmente e também serve a demo navegável.

**Guia e checkpoint único de implementação:** [guia de implementação](../../docs/guias/IMPLEMENTACAO-UI.md). Backlog: [PLANO.md, etapa 6.6](../../docs/planejamento/PLANO.md).

## Executar

Nesta pasta:

```powershell
npm.cmd ci
npm.cmd run dev
```

Demo em http://127.0.0.1:5174/. Se já houver servidor nessa porta, reutilizá-lo.

```powershell
npm.cmd test
npm.cmd run build
```

Os testes `*.test.js` são executados pelo Node. Os scripts `browser-*.js` exportam uma expressão de função que recebe uma página Playwright; precisam ser executados por esse runner, não pelo comando `npm test`.

## Arquivos essenciais

- `src/App.jsx`: telas, diálogos, fluxos e estados da demo.
- `src/styles.css`: tokens/classes e layout/rolagem.
- `src/model.js`, `history.js`, `controls.js`, `coverage.js`: regras simplificadas de simulação.
- `tests/`: regras e cenários de regressão da demo.
- `package.json`, `package-lock.json` e configuração Vite/Tailwind: ambiente reproduzível.

Tudo usa dados fictícios. Somente exportar histórico gera um download solicitado. Preferências locais persistem no navegador; links/histórico da sessão reiniciam ao recarregar. Não copiar fixtures/timers/controles de cenário para o aplicativo real. Os serviços Python continuam sendo a fonte de verdade para filesystem e segurança.
