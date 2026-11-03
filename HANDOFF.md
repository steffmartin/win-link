# Handoff - WinLink Fase 3

**Data**: 2026-11-02
**Fase Concluída**: Fase 2 - Infraestrutura e Base do Projeto
**Próxima Fase**: Fase 3 - Camada de Domínio (Lógica de Negócio)
**Agente**: Devin

---

## Resumo do Projeto

**WinLink** é um aplicativo Windows para gerenciamento de junções NTFS (NTFS Junctions) e links simbólicos. Permite criar, listar, gerenciar e desfazer links de diretórios e arquivos no sistema de arquivos NTFS com interface moderna compatível com Windows 11.

**Stack Tecnológico**: Python 3.12 + PyQt6

**Repositório**: https://github.com/steffmartin/win-link (privado)

---

## O Que Foi Feito (Fases 1-2)

### Fase 1: Planejamento e Especificação ✅

**Documentos criados:**
- `ESPECIFICACAO.md` - Requisitos funcionais e não-funcionais detalhados
- `PLANO.md` - 6 fases de desenvolvimento com etapas detalhadas
- `TECNOLOGIAS.md` - Stack Python + PyQt6 com bibliotecas específicas
- `PROTOTIPO.md` - Wireframes ASCII de todas as telas
- `BRAINSTORM.md` - Decisões tomadas e funcionalidades deixadas para Fase 2
- `README.md` - Visão geral do projeto
- `docs/ARQUITETURA-DISTRIBUICAO.md` - Detalhes de compilação, instalação, desinstalação

**Decisões aprovadas pelo usuário:**
- Stack: Python + PyQt6
- Escopo: Diretórios e arquivos desde o início
- Descoberta: Híbrida (configuráveis + opção completa)
- Funcionalidade extra: Histórico de operações
- Distribuição: PyInstaller + Inno Setup
- Desinstalador: Remove configs/logs sempre, pergunta sobre histórico, NÃO remove junções

### Fase 2: Infraestrutura e Base do Projeto ✅

**Estrutura criada:**
```
winlink/
├── src/
│   └── winlink/
│       ├── __init__.py
│       ├── main.py                    # Entry point
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py              # AppSettings com pydantic
│       ├── ui/
│       │   ├── __init__.py
│       │   └── main_window.py         # MainWindow PyQt6 básica
│       └── utils/
│           ├── __init__.py
│           └── logger.py              # Sistema de logging
├── tests/
│   ├── test_config.py                 # 4 testes passando
│   └── test_logger.py                # 3 testes passando
├── docs/
│   └── ARQUITETURA-DISTRIBUICAO.md
├── pyproject.toml                     # Configuração uv
├── .ruff.toml                        # Configuração ruff
└── .gitignore                        # Atualizado para Python/uv
```

**Dependências instaladas:**
- PyQt6 6.12.0
- pywin32 312
- pydantic 2.14.2
- pydantic-settings 2.16.2
- pytest 9.2.0
- pytest-qt 4.5.0
- ruff 0.17.3
- black 26.10.1
- mypy 2.4.1

**Gerenciador de dependências**: uv 0.13.6

**Virtual environment**: `.venv/` (criado pelo uv)

**Validação:**
- ✅ 7 testes unitários passando
- ✅ Aplicação inicia sem erros
- ✅ Janela PyQt6 exibida corretamente
- ✅ Linting com ruff sem erros
- ✅ Formatação com black OK

---

## Próxima Fase: Fase 3 - Camada de Domínio

**Objetivo**: Implementar a lógica de manipulação de junções NTFS, sem interface gráfica.

### Etapas da Fase 3 (PLANO.md)

- [ ] 3.1 Modelo de dados (dataclasses/pydantic)
  - Classe Junction para representar junções
  - Enum JunctionType (JUNCTION, SYMLINK, HARDLINK)
  - Enum JunctionStatus (ACTIVE, BROKEN, INACCESSIBLE)
  - Enum Creator (APP, EXISTING, MANUAL)
  - Modelos de configuração com pydantic

- [ ] 3.2 Scanner de junções
  - Função para escanear diretórios recursivamente
  - Detecção de reparse points via pywin32
  - Identificação de tipo de link (junction vs symlink)
  - Resolução de destino do link
  - Classificação de criador (comparando com histórico)
  - Escaneamento híbrido (rápido vs completo)

- [ ] 3.3 Operações de junção (Windows API via pywin32)
  - Criar junção NTFS (CreateSymbolicLink / DeviceIoControl)
  - Criar link simbólico de diretório
  - Criar link simbólico de arquivo
  - Criar hard link de arquivo
  - Remover junção/link
  - Verificar integridade do link

- [ ] 3.4 Operações de arquivo
  - Cópia com preservação de atributos (shutil.copy2 com metadados extendidos)
  - Movimentação de arquivos
  - Duplicação de arquivos
  - Detecção de arquivos em uso (try/except + pywin32)
  - Cálculo de tamanho e espaço necessário (os.walk + os.path.getsize)

- [ ] 3.5 Gerenciamento de processos
  - Lista de processos conhecidos que bloqueiam arquivos (psutil)
  - Função para encerrar processos (psutil)
  - Detecção de arquivos bloqueados

- [ ] 3.6 Histórico de operações
  - Sistema de log de operações em JSON
  - Estrutura de registro de operação
  - Persistência do histórico
  - Função para desfazer operação (baseada no histórico)

- [ ] 3.7 Validações
  - Validação de caminhos (pathlib)
  - Validação de permissões (os.access)
  - Validação de espaço em disco (shutil.disk_usage)
  - Validação de pré-condições (já é junção, destino existe, etc.)

### Critérios de Conclusão da Fase 3
- Todas as operações de junção funcionam via CLI/tests
- Scanner detecta junções corretamente
- Operações de arquivo são seguras e preservam metadados
- Validações previnem operações perigosas
- Histórico de operações funciona
- Testes unitários cobrem todas as funções (pytest)

---

## Comandos Úteis

### Ativar ambiente virtual
```bash
# O ambiente já está configurado com uv
# Scripts estão em .venv/Scripts/
# Use uv run para executar comandos no ambiente
```

### Executar comandos no ambiente
```bash
/c/Users/steff/.local/bin/uv.exe run <comando>
```

### Exemplos:
```bash
# Executar app
/c/Users/steff/.local/bin/uv.exe run python -m winlink.main

# Executar testes
/c/Users/steff/.local/bin/uv.exe run pytest

# Executar ruff
/c/Users/steff/.local/bin/uv.exe run ruff check src/

# Executar black
/c/Users/steff/.local/bin/uv.exe run black src/
```

### Instalar nova dependência
```bash
/c/Users/steff/.local/bin/uv.exe add <pacote>
```

### Instalar dependência de dev
```bash
/c/Users/steff/.local/bin/uv.exe add --dev <pacote>
```

---

## Configuração Importante

### uv.lock
**NÃO commitar uv.lock** - já está no .gitignore. Cada ambiente gera seu próprio lock file.

### Python
Versão: 3.12.10 (mantida do sistema, não reinstalada)

### Permissões Git
Configurado em `.devin/config.json` para permitir `Exec(git)` sem solicitação.

---

## Documentos de Referência

### Especificação
- `ESPECIFICACAO.md` - Requisitos funcionais e não-funcionais
- `PLANO.md` - Fases de desenvolvimento (veja Fase 3 em detalhes)
- `PROTOTIPO.md` - Wireframes da interface (para Fase 4)

### Arquitetura
- `docs/ARQUITETURA-DISTRIBUICAO.md` - Compilação, instalação, desinstalação
- `TECNOLOGIAS.md` - Stack tecnológico e bibliotecas

### Decisões
- `BRAINSTORM.md` - Decisões tomadas e funcionalidades futuras

---

## Dados de Validação

Para testar o scanner de junções, use estas pastas conhecidas:

- Junções em `D:\Cache` apontando para `C:\Users\steff`
- Junção específica: `C:\Users\steff\OneDrive\Documentos\Finanças\Backup jFinanças\auto`

Essas devem aparecer como criadas "por fora do app" (status: EXISTENT).

**IMPORTANTE**: Durante o desenvolvimento, nenhum arquivo ou junção real deve ser modificada. Toda junção testada deve ser em uma pasta de teste criada para isso (ex: `D:\WinLink-Test`).

---

## Restrições do Projeto

### Diretório craft-jfincancas
- Nenhum arquivo fora de `D:\Projects\win-link` pode ser alterado sem autorização
- craft.json, transcript.json, feed.json e capture/README.md pertencem a outra tentativa
- Não executar alvos só para verificar inventário

### Backup OneDrive
- Preservar arquivos do OneDrive
- Nunca apagar, sobrescrever ou mesclar pasta local sobre eles
- Consulte REAPLICAR-PATCH.md do projeto craft-jfincancas se necessário

---

## Script de Referência

O script `D:\Cache\migrar_pastas.ps1` é a referência para o comportamento das junções:

- Usa robocopy para copiar arquivos com preservação de atributos
- Cria junção NTFS com `New-Item -ItemType Junction`
- Verifica se já é junção antes de criar
- Para processos que bloqueiam arquivos (VS Code, Docker Desktop, etc.)

---

## Notas para Fase 3

### Dependências adicionais que podem ser necessárias
- `psutil` - para gerenciamento de processos (já pode ser útil para 3.5)
- Verificar se pywin32 tem tudo necessário para Windows API de junções

### Windows API para junções
Pesquisar:
- `CreateSymbolicLink` (CreateSymbolicLinkW)
- `DeviceIoControl` com `FSCTL_SET_REPARSE_POINT`
- `FSCTL_GET_REPARSE_POINT` para detectar junções
- `FILE_FLAG_REPARSE_POINT` em atributos

### Testes unitários
- Criar testes para cada função do domínio
- Usar pytest
- Para testes que tocam o sistema de arquivos, usar diretórios temporários
- NÃO testar com junções reais do usuário

### Estrutura sugerida para Fase 3
```
src/winlink/core/
├── __init__.py
├── config.py              # Já existe
├── models.py              # NOVO: modelos de dados (Junction, enums)
├── scanner.py              # NOVO: scanner de junções
├── operations.py          # NOVO: operações de junção
├── file_ops.py            # NOVO: operações de arquivo
├── process_manager.py     # NOVO: gerenciamento de processos
└── history.py             # NOVO: histórico de operações
```

---

## Status do Git

Branch: `main`
Último commit: `416767e` - Remover uv.lock do controle de versão
Status: Limpo (nada pendente)

---

## Próximos Passos

1. Começar pela etapa 3.1 (Modelo de dados)
2. Criar `src/winlink/core/models.py` com classes e enums
3. Escrever testes para os modelos
4. Prosseguir para 3.2 (Scanner)
5. Continuar sequencialmente até 3.7

---

## Contato

Se houver dúvidas sobre decisões anteriores, consulte:
- `BRAINSTORM.md` - Decisões tomadas
- `docs/ARQUITETURA-DISTRIBUICAO.md` - Decisões de distribuição
- `ESPECIFICACAO.md` - Requisitos originais

---

**Arquivamento**: Esta seção foi arquivada após conclusão da Fase 2. Próximo agente deve iniciar pela Fase 3 usando este handoff como referência.
