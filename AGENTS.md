# Orientações para agentes de IA

Estas regras de organização, implementação, build e testes são obrigatórias para todo o repositório. A documentação do índice deve ser lida **sob demanda**, apenas quando necessária à tarefa. Não carregar todo o arquivo histórico nem todo o protótipo como contexto inicial.

## Regras obrigatórias

- O produto é um aplicativo Windows em Python 3.12+/PyQt6. Reutilizar a implementação real; React é somente referência histórica.
- Preservar a organização: `src/winlink/core/` para domínio e serviços de arquivos; `src/winlink/ui/` para apresentação e workers; `src/winlink/utils/` para infraestrutura; `tests/` para testes; `resources/` para recursos; `installer/`, `winlink.spec` e `scripts/` para distribuição.
- Documentação vigente fica em `docs/`; desenvolvimento da v0.1.0 fica em `docs/arquivo/v0.1.0/`. Não criar novos planos ou versões do protótipo na raiz. Corrigir links relativos quando mover documentos.
- Bugs, melhorias, critérios de aceite e andamento ficam exclusivamente nas [Issues do GitHub](https://github.com/steffmartin/win-link/issues). Consultar a issue pertinente e evitar duplicatas; não manter backlog paralelo em Markdown. Uma issue não autoriza implementar todas as demais.
- Preservar compatibilidade de configurações e histórico existentes, prévia, confirmação obrigatória, verificação de identidade antes da reversão, cancelamento cooperativo, backups e recuperação de falhas. Nunca substituir serviços reais por simulações do protótipo.
- Não operar sobre dados pessoais para testar. Usar diretórios temporários isolados; limpeza não pode seguir junctions/symlinks para seus destinos. Conferir caminhos absolutos antes de excluir ou mover árvores.
- Versionar fontes, lockfiles (`uv.lock` e o lockfile do protótipo), recursos e documentação relevante. Não commitar `.venv/`, `node_modules/`, caches, logs, relatórios correntes, `build/`, `dist/`, ferramentas baixadas ou binários distribuíveis. Novos relatórios vão para `build/`; evidências já arquivadas são históricas.

## Ambiente, testes e build obrigatórios

Executar a partir da raiz no Windows, usando o ambiente do projeto:

```powershell
uv sync --extra dev --extra build
.venv\Scripts\python.exe -m winlink.main
```

Para alterações no aplicativo, executar os quatro checks e corrigir falhas relacionadas antes de entregar:

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check src resources
.venv\Scripts\python.exe -m black --check src resources
.venv\Scripts\python.exe -m mypy src
```

Testes novos devem verificar comportamento e riscos reais. Para mudanças de UI, seguir também a seção de validação de `docs/UI.md`, incluindo janela reduzida e alta escala. Mudanças apenas documentais exigem conferir conteúdo, caminhos e links e executar `git diff --check`; não exigem rebuild ou repetição dos testes do aplicativo.

Build segue **PyInstaller pelo `winlink.spec` e instalador offline Inno Setup por `installer/winlink.iss`**, via `scripts/build.ps1`. Não trocar a stack de empacotamento nem remover o isolamento de descoberta de DLLs do spec (evita dependências externas do PATH). Para gerar/distribuir pacotes, ler `docs/DISTRIBUICAO.md` e executar:

```powershell
.\scripts\build.ps1 -Iscc 'C:\caminho\Inno Setup 6\ISCC.exe'
.venv\Scripts\python.exe scripts\validate_distribution.py 'C:\caminho\Inno Setup 6\ISCC.exe'
```

Distribuir a pasta portátil inteira, incluindo `_internal`, e instalador, com checksums como assets da release; nunca só o executável portátil. A instalação é por usuário, dados padrão ficam em `%APPDATA%\WinLink` e não há elevação automática por operação. Compatibilizar a versão entre metadados, instalador, nomes de pacotes e notas ao preparar uma nova release.

Windows limpo sem Python, Windows 10 e teste manual de sucesso de symlinks com privilégios foram dispensados para a v0.1.0; não anunciar esses cenários como homologados nem reabri-los como bloqueadores daquela release. Pacotes iniciais não são assinados. Não alterar tag/assets da versão publicada para incorporar mudanças futuras.

## Índice atual — ler somente o assunto necessário

| Quando precisar | Documento |
|---|---|
| Entender o produto, instalar dependências e localizar o código | [README](README.md) |
| Alterar aparência, textos, navegação, diálogos ou estados da interface | [Guia de UI](docs/UI.md) — referência suficiente sem ler o protótipo inteiro |
| Entender fluxos e orientações ao usuário | [Uso](docs/USO.md) |
| Retomar manutenção e limites conhecidos da entrega | [Continuidade](docs/CONTINUIDADE.md) |
| Empacotar, instalar/desinstalar, validar ou publicar | [Distribuição](docs/DISTRIBUICAO.md) |
| Entender o conteúdo entregue na versão | [Notas de versão](docs/NOTAS-DE-VERSAO.md) |
| Escolher trabalho ou verificar o estado de uma proposta | [Issues do GitHub](https://github.com/steffmartin/win-link/issues) |

## Índice histórico — consultar apenas para uma dúvida específica

O arquivo registra o passado; menções a trabalho pendente podem ter sido superadas. Código atual, documentação vigente e decisões posteriores do mantenedor orientam a continuidade.

| Assunto histórico | Referência |
|---|---|
| Visão geral e contexto do arquivamento | [Índice do arquivo](docs/arquivo/v0.1.0/README.md) |
| Fases e fechamento da entrega inicial | [Plano](docs/arquivo/v0.1.0/planejamento/PLANO.md) |
| Origem das propostas migradas para Issues | [Melhorias](docs/arquivo/v0.1.0/planejamento/MELHORIAS.md) |
| Especificação funcional da versão inicial | [Especificação](docs/arquivo/v0.1.0/produto/ESPECIFICACAO.md) |
| Contrato visual original e mapeamento da implementação | [Implementação da UI](docs/arquivo/v0.1.0/guias/IMPLEMENTACAO-UI.md) |
| Estrutura e premissas antigas de distribuição | [Estrutura](docs/arquivo/v0.1.0/arquitetura/ESTRUTURA.md), [distribuição histórica](docs/arquivo/v0.1.0/arquitetura/DISTRIBUICAO.md) |
| Evidências, capturas e limites das validações anteriores | [Fase 5](docs/arquivo/v0.1.0/validacao/FASE5.md), [redesign](docs/arquivo/v0.1.0/validacao/REDESIGN.md); JSON/XML adjacentes somente para investigar uma execução |
| Texto de uso e notas antes do fechamento | [Uso histórico](docs/arquivo/v0.1.0/guias/USO.md), [notas históricas](docs/arquivo/v0.1.0/produto/NOTAS-DE-VERSAO.md) |
| Dúvida visual não resolvida pelo guia atual ou capturas | [README do protótipo](docs/arquivo/v0.1.0/prototypes/ui/README.md), depois apenas o componente/estilo necessário em `src/` ou cenário em `tests/` dessa pasta |

Se a tarefa modificar o protótipo histórico explicitamente, seus checks são `npm.cmd --prefix docs/arquivo/v0.1.0/prototypes/ui test` e `npm.cmd --prefix docs/arquivo/v0.1.0/prototypes/ui run build`. Scripts `browser-*.js` precisam de runner Playwright e não são executados por `npm test`. Testes React não comprovam segurança das operações reais.
