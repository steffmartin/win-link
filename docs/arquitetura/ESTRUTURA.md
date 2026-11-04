# Estrutura e convenções do projeto

## Organização vigente

```text
win-link/
├── README.md                     # entrada do projeto e comandos básicos
├── pyproject.toml / uv.lock       # dependências e ferramentas do aplicativo
├── winlink.spec                   # build PyInstaller (relativo à raiz)
├── iniciar-winlink.bat            # inicializador de desenvolvimento
├── src/winlink/                   # aplicativo real Python/PyQt6
│   ├── core/                     # domínio, arquivos, scanner, cache e configuração
│   ├── ui/                       # janela, modelos, tema, workers e diálogos
│   └── utils/                    # infraestrutura compartilhada do aplicativo
├── tests/                        # testes Python do aplicativo
├── prototypes/ui/                # protótipo React vigente e sua demo
│   ├── README.md                 # executar, testar e compilar a demo
│   ├── package.json / package-lock.json
│   ├── index.html                # entrada Vite
│   ├── src/                      # telas, estilos e regras fictícias
│   └── tests/                    # regras e cenários de navegador da demo
├── docs/
│   ├── arquitetura/              # estrutura e distribuição
│   ├── produto/                  # especificação do comportamento
│   ├── planejamento/             # fases e melhorias aprovadas/futuras
│   ├── guias/                    # implementação do protótipo no PyQt6
│   └── validacao/                # evidências finais e limites de homologação
├── resources/                    # ícones e fontes de recursos do aplicativo
├── installer/                    # fonte do instalador Inno Setup
└── scripts/                      # build e validação de distribuição
```

## Separação de responsabilidades

`src/winlink` e `tests` mantêm a organização padrão de pacote Python; a reorganização não altera imports nem o entrypoint `winlink.main`. A demo e o protótipo são o mesmo projeto em `prototypes/ui`, evitando duplicar versões. Nenhum pacote Node é dependência do aplicativo real ou do instalador.

O design e os estados da demo são referências de implementação. Os serviços Python continuam responsáveis por filesystem, identidade dos links, preservação de dados e recuperação. Regras simplificadas, fixtures e temporizadores do React não entram no domínio real.

[Guia de implementação](../guias/IMPLEMENTACAO-UI.md), [especificação](../produto/ESPECIFICACAO.md), [plano](../planejamento/PLANO.md) e [melhorias](../planejamento/MELHORIAS.md) são as referências de trabalho. Estudos intermediários, checkpoints duplicados e capturas de versões anteriores não devem ser recriados como documentação vigente.

## Como executar

Executar comandos Python, build e distribuição a partir da raiz do repositório. A partir da raiz também é possível usar:

```powershell
npm.cmd --prefix prototypes/ui ci
npm.cmd --prefix prototypes/ui run dev
npm.cmd --prefix prototypes/ui test
npm.cmd --prefix prototypes/ui run build
```

A demo continua em http://127.0.0.1:5174/. Comandos locais da demo estão no [README próprio](../../prototypes/ui/README.md). Scripts `browser-*.js` continuam sendo funções para um runner Playwright que fornece uma página; não dependem do caminho antigo da pasta.

## Arquivos gerados e limpeza

Não versionar `.venv`, `node_modules`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.coverage`, `.playwright-mcp`, caches Vite, logs ou diretórios `build`/`dist`. `.gitignore` vale para essas pastas também dentro do protótipo. Os arquivos `uv.lock`, `package-lock.json`, `winlink.spec`, fontes do instalador e ícones são versionados.

`build/` contém trabalho intermediário de empacotamento/validação; `dist/` contém artefatos distribuíveis gerados e pode ser recriado. O build da demo fica em `prototypes/ui/dist`. Após validar uma alteração de estrutura, remover builds descartáveis e caches, preservando os ambientes de dependências necessários para trabalhar. Não limpar `%APPDATA%/WinLink` nem instalações fora do repositório como parte dessa manutenção.

Evidências finais em `docs/validacao` são registros históricos versionados, não caches. Os hashes/paths neles descritos referem-se à execução original; limpar os binários locais não os transforma em builds atuais. Para redistribuir, gerar e validar novamente conforme [distribuição](DISTRIBUICAO.md).

Diretórios de teste do produto podem conter junctions. Qualquer limpeza deve conferir os caminhos dentro do workspace e remover apenas os links, sem seguir os destinos. Nunca usar uma limpeza genérica que apague `.venv`, dependências ou dados pessoais.

## Convenções de manutenção

- Atualizar links Markdown relativos sempre que mover um guia.
- Manter README da raiz como índice, sem copiar especificação ou relatórios inteiros.
- Acrescentar guias em `docs/guias`, decisões de organização em `docs/arquitetura` e backlog em `docs/planejamento`.
- Usar nomes estáveis de função, sem identificar um agente ou uma versão transitória na pasta da demo.
- Manter scripts relativos à raiz calculada a partir do arquivo, sem caminhos absolutos da máquina do desenvolvedor.
