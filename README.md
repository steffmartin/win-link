# WinLink

Aplicativo Windows em Python/PyQt6 para descobrir, criar e desfazer junctions, links simbólicos de diretório/arquivo e hard links, com prévia, confirmação e preservação dos dados.

## Estado e próxima etapa

A implementação da fase 5 está entregue, com homologação externa pendente. O protótipo de redesign tem direção visual aprovada e cobertura das funcionalidades atuais. **A próxima etapa é implementá-lo no aplicativo real**, junto às melhorias aprovadas da etapa 6.6. O React é referência de interface e usa dados fictícios.

Comece pelo [guia de implementação](docs/IMPLEMENTACAO-UI.md) e pelo [plano](PLANO.md).

## Documentação essencial

| Documento | Finalidade |
|---|---|
| [Plano](PLANO.md) | Fases, próximo trabalho e critérios de conclusão |
| [Especificação](ESPECIFICACAO.md) | Funcionalidades atuais e regras de preservação |
| [Implementação da UI](docs/IMPLEMENTACAO-UI.md) | Design, cobertura e mapeamento React → PyQt6 |
| [Melhorias](MELHORIAS.md) | Novidades aprovadas e ideias fora do escopo |
| [Demo](prototypes/agente-externo-v1/README.md) | Como executar o protótipo final e seus testes |
| [Distribuição](docs/ARQUITETURA-DISTRIBUICAO.md) | Build, instalação e dados do aplicativo |
| [Validação da fase 5](docs/validacao/FASE5.md) | Evidências preservadas e homologação pendente |

## Desenvolvimento

Windows, Python 3.12+ e uv:

```powershell
uv sync --extra dev --extra build
.venv\Scripts\python.exe -m winlink.main
```

Alternativa para abrir o aplicativo: `iniciar-winlink.bat`.

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check src resources
.venv\Scripts\python.exe -m black --check src resources
.venv\Scripts\python.exe -m mypy src
```

A demo React roda em http://127.0.0.1:5174/; consulte seus comandos no README da demo. Não confundir o servidor web com o aplicativo real.

## Distribuição

Portátil: distribuir a pasta inteira `dist/WinLink`, incluindo `_internal`. Instalador: `dist/WinLink-Setup-0.1.0.exe`. Não distribuir builds anteriores à correção de coleta de DLLs descrita no relatório da fase 5. Homologação em Windows limpo/Windows 10 e permissões de symlinks permanece pendente.

Licença: pendente de definição.
