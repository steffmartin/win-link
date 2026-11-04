# WinLink

Aplicativo Windows em Python/PyQt6 para descobrir, criar e desfazer junctions, links simbólicos de diretório/arquivo e hard links, com prévia, confirmação e preservação dos dados.

## Estado e próxima etapa

O design aprovado foi implementado no aplicativo Python/PyQt6, com navegação lateral, cartões/visão compacta, criação, propriedades, histórico e configurações. As melhorias da etapa 6.6 estão implementadas. O React continua sendo apenas referência visual.

**Homologação de permissões pendente:** falta validar manualmente o sucesso real de symlinks de arquivo/diretório com privilégios apropriados. Windows limpo sem Python e Windows 10 não serão testados, por decisão do mantenedor; esses ambientes continuam sem homologação. Consulte a [validação atual](docs/validacao/REDESIGN.md), o [guia de uso](docs/guias/USO.md) e as [notas de versão](docs/produto/NOTAS-DE-VERSAO.md).

Comece pelo [guia de implementação](docs/guias/IMPLEMENTACAO-UI.md) e pelo [plano](docs/planejamento/PLANO.md).

## Documentação essencial

| Documento | Finalidade |
|---|---|
| [Plano](docs/planejamento/PLANO.md) | Fases, próximo trabalho e critérios de conclusão |
| [Especificação](docs/produto/ESPECIFICACAO.md) | Funcionalidades atuais e regras de preservação |
| [Implementação da UI](docs/guias/IMPLEMENTACAO-UI.md) | Design, cobertura e mapeamento React → PyQt6 |
| [Melhorias](docs/planejamento/MELHORIAS.md) | Novidades aprovadas e ideias fora do escopo |
| [Demo](prototypes/ui/README.md) | Como executar o protótipo final e seus testes |
| [Distribuição](docs/arquitetura/DISTRIBUICAO.md) | Build, instalação e dados do aplicativo |
| [Validação da fase 5](docs/validacao/FASE5.md) | Evidências preservadas e homologação pendente |

## Estrutura

Aplicativo em `src/winlink`, testes em `tests`, protótipo/demo em `prototypes/ui` e documentação por assunto em `docs`. Veja a [estrutura completa e convenções](docs/arquitetura/ESTRUTURA.md).

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

Após gerar o build, distribuir a pasta portátil inteira `dist/WinLink`, incluindo `_internal`. Instalador: `dist/WinLink-Setup-0.1.0.exe`. Não distribuir builds anteriores à correção de coleta de DLLs descrita no relatório da fase 5. Homologação em Windows limpo/Windows 10 e permissões de symlinks permanece pendente.

Licença [MIT](LICENSE), escolhida pelo mantenedor.
