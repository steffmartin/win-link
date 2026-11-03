# Plano de Desenvolvimento - WinLink

## Visão Geral

Este documento define as fases e etapas do desenvolvimento do WinLink, do planejamento inicial ao lançamento. O projeto está organizado em 5 fases principais, cada uma com entregas específicas e critérios de conclusão.

## Fase 1: Planejamento e Especificação ✅

**Objetivo**: Definir claramente o escopo, requisitos e tecnologias do projeto.

### Etapas Concluídas
- [x] 1.1 Leitura e análise do script `migrar_pastas.ps1`
- [x] 1.2 Definição de requisitos funcionais e não-funcionais
- [x] 1.3 Especificação do sistema (ESPECIFICACAO.md)
- [x] 1.4 Documentação inicial (README.md)
- [x] 1.5 Seleção de tecnologias (TECNOLOGIAS.md)
- [x] 1.6 Protótipo de interface (PROTOTIPO.md)
- [x] 1.7 Plano de desenvolvimento (este documento)

### Critérios de Conclusão
- Documentação de requisitos clara e completa
- Stack tecnológico definido
- Protótipo visual aprovado pelo usuário
- Repo inicializado com git

---

## Fase 2: Infraestrutura e Base do Projeto ✅

**Objetivo**: Configurar o ambiente de desenvolvimento e a estrutura base do projeto Python + PyQt6.

**Status**: CONCLUÍDA (2026-11-02)

### Etapas Concluídas
- [x] 2.1 Configuração do projeto
  - Criar estrutura de diretórios (src/, tests/, docs/)
  - Configurar uv para gerenciamento de dependências
  - Configurar pyproject.toml
  - Configurar linter (ruff) e formatter (black)
  - Configurar mypy para type checking

- [x] 2.2 Dependências principais
  - Instalar PyQt6 6.12.0
  - Instalar pywin32 312
  - Instalar pydantic 2.14.2
  - Instalar pytest 9.2.0

- [x] 2.3 Implementação de logging
  - Sistema de logging com `logging`
  - Configuração de níveis de log
  - Logging para arquivo e console
  - 3 testes unitários passando

- [x] 2.4 Sistema de configuração
  - Arquivo de configuração com pydantic
  - Persistência de preferências do usuário
  - Validação de configuração
  - Localização: %APPDATA%/WinLink/config.json
  - 4 testes unitários passando

- [x] 2.5 Testes unitários base
  - Framework pytest configurado
  - Estrutura de testes definida
  - 7 testes unitários passando
  - pytest-qt configurado

### Critérios de Conclusão ✅
- Ambiente virtual configurado
- Dependências instaladas
- Sistema de logging funcional
- Configuração pode ser lida e escrita
- Testes podem ser executados
- Janela PyQt6 básica abre sem erros

---

## Fase 3: Camada de Domínio (Lógica de Negócio) ✅

**Objetivo**: Implementar a lógica de manipulação de junções, sem interface gráfica.

**Status**: CONCLUÍDA

**Data**: 2026-11-02

### Etapas
- [x] 3.1 Modelo de dados (dataclasses/pydantic)
  - Classe Junction para representar junções
  - Enum JunctionType (JUNCTION, SYMLINK, HARDLINK)
  - Enum JunctionStatus (ACTIVE, BROKEN, INACCESSIBLE)
  - Enum Creator (APP, EXISTING, MANUAL)
  - Modelos de configuração com pydantic

- [x] 3.2 Scanner de junções
  - Função para escanear diretórios recursivamente
  - Detecção de reparse points via pywin32
  - Identificação de tipo de link (junction vs symlink)
  - Resolução de destino do link
  - Classificação de criador (comparando com histórico)
  - Escaneamento híbrido (rápido vs completo)

- [x] 3.3 Operações de junção (Windows API via pywin32)
  - Criar junção (CreateSymbolicLink / DeviceIoControl)
  - Criar link simbólico de diretório
  - Criar link simbólico de arquivo
  - Criar hard link de arquivo
  - Remover junção/link
  - Verificar integridade do link

- [x] 3.4 Operações de arquivo
  - Cópia com preservação de atributos (shutil.copy2 com metadados extendidos)
  - Movimentação de arquivos
  - Duplicação de arquivos
  - Detecção de arquivos em uso (try/except + pywin32)
  - Cálculo de tamanho e espaço necessário (os.walk + os.path.getsize)

- [x] 3.5 Gerenciamento de processos
  - Lista de processos conhecidos que bloqueiam arquivos (psutil)
  - Função para encerrar processos (psutil)
  - Detecção de arquivos bloqueados

- [x] 3.6 Histórico de operações
  - Sistema de log de operações em JSON
  - Estrutura de registro de operação
  - Persistência do histórico
  - Função para desfazer operação (baseada no histórico)

- [x] 3.7 Validações
  - Validação de caminhos (pathlib)
  - Validação de permissões (os.access)
  - Validação de espaço em disco (shutil.disk_usage)
  - Validação de pré-condições (já é junção, destino existe, etc.)

### Critérios de Conclusão
- Todas as operações de junção funcionam via CLI/tests
- Scanner detecta junções corretamente
- Operações de arquivo são seguras e preservam metadados
- Validações previnem operações perigosas
- Histórico de operações funciona
- Testes unitários cobrem todas as funções (pytest)

---

## Fase 4: Interface Gráfica (PyQt6)

**Objetivo**: Implementar a interface gráfica moderna compatível com Windows 11 usando PyQt6.

### Etapas
- [ ] 4.1 Janela principal (QMainWindow)
  - Layout básico da aplicação (QVBoxLayout, QHBoxLayout)
  - Barra de menu (QMenuBar)
  - Barra de status (QStatusBar)
  - Suporte a redimensionamento
  - Ícone da aplicação

- [ ] 4.2 Tema Windows 11
  - Detecção de tema do sistema (claro/escuro) via Windows Registry
  - Aplicação de QPalette (QStyleFactory)
  - Paleta de cores customizada (Fusion style + custom palette)
  - Estilo CSS (QSS) para widgets
  - Fonte Segoe UI

- [ ] 4.3 Lista de junções (QTableView)
  - QAbstractTableModel para dados
  - Colunas: Origem, Destino, Criador, Tipo, Tamanho, Status, Ações
  - Ordenação (QSortFilterProxyModel)
  - Filtros
  - Busca (QLineEdit com filtragem)
  - Lazy loading para grandes listas
  - Context menu (botão direito)

- [ ] 4.4 Detalhes da junção
  - Painel de detalhes (QDockWidget ou QGroupBox)
  - Visualização de propriedades
  - Botões de ação (Desfazer, etc.)

- [ ] 4.5 Diálogo de criação (QDialog)
  - QLineEdit para caminhos com botões de browse (QFileDialog)
  - Preview de operação (QTextEdit read-only)
  - Confirmação (QMessageBox)
  - Validação em tempo real

- [ ] 4.6 Diálogo de desfazer (QDialog)
  - QRadioButton para estratégias (remover, mover, duplicar)
  - Preview de operação
  - Confirmação

- [ ] 4.7 Diálogo de progresso (QProgressDialog)
  - Barra de progresso (QProgressBar)
  - Mensagens de status (QLabel)
  - Botão de cancelar
  - Indicação de tempo estimado

- [ ] 4.8 Notificações
  - QMessageBox para diálogos
  - QSystemTrayIcon para notifications (opcional)
  - Toast notifications customizados (QFrame temporário)

- [ ] 4.9 Configurações (QDialog)
  - Formulário de configurações
  - Lista de diretórios para escanear (QListWidget)
  - Salvar/carregar configuração

### Critérios de Conclusão
- Interface estável e responsiva
- Tema claro/escuro funciona corretamente
- Todas as ações da UI têm implementação
- Interface segue guidelines do Windows 11 (estilo Fusion + custom)
- Acessibilidade básica implementada (atalhos de teclado)

---

## Fase 5: Integração e Refinamento

**Objetivo**: Integrar camada de domínio com interface PyQt6, polir funcionalidades e preparar para lançamento.

### Etapas
- [ ] 5.1 Integração UI ↔ Domínio
  - Conectar botões a operações do domínio
  - Atualizar lista após operações (signals/slots)
  - Gerenciar operações assíncronas (QThread)
  - Tratamento de erros na UI (try/except com QMessageBox)

- [ ] 5.2 Operações em segundo plano (QThread)
  - Worker threads para operações pesadas (cópia, movimentação)
  - QThreadPool para gerenciar threads
  - Signals para progresso (QProgressBar)
  - Cancelamento de operações
  - Não-bloqueio da UI

- [ ] 5.3 Persistência
  - Salvar configurações (pydantic + JSON) em %APPDATA%\WinLink\config.json
  - Salvar histórico de operações (JSON) em %APPDATA%\WinLink\history.json
  - Salvar logs em %APPDATA%\WinLink\winlink.log
  - Salvar preferências de usuário
  - Carregar estado anterior ao iniciar
  - Não usar banco de dados (SQLite) - JSON é suficiente para MVP

- [ ] 5.4 Histórico de operações
  - UI para visualizar histórico
  - Opção de desfazer operação específica
  - Filtragem de histórico por data/tipo
  - Exportação de histórico

- [ ] 5.5 Validação em produção
  - Testes com junções reais em pasta de teste (D:\WinLink-Test)
  - Testes com pastas conhecidas do usuário (D:\Cache, C:\Users\steff)
  - Testes de stress (muitas junções)
  - Testes de casos de borda (caminhos longos, caracteres especiais)

- [ ] 5.6 Polimento
  - Tratamento de erros robusto
  - Mensagens de erro amigáveis (QMessageBox)
  - Atalhos de teclado (QShortcut)
  - Tooltips e ajuda contextual (QToolTip)
  - Otimizações de performance (lazy loading, caching)

- [ ] 5.7 Build e distribuição (PyInstaller + Inno Setup)
  - Configurar spec file do PyInstaller
  - Criar executável standalone (inclui Python runtime e dependências)
  - Testar executável em máquina limpa (sem Python instalado)
  - Criar instalador com Inno Setup
    - Adicionar atalhos (Desktop, Menu Iniciar)
    - Configurar desinstalador
    - Desinstalador remove configs e logs (sempre)
    - Desinstalador pergunta sobre histórico (manter ou apagar)
    - Desinstalador NÃO remove junções NTFS (elas pertencem ao usuário)
  - Validar tamanho final do instalador (~100-200 MB)

### Critérios de Conclusão
- Aplicativo funciona de ponta a ponta
- Operações em segundo plano funcionam sem travar UI
- Histórico de operações funcional
- Validação com dados reais bem-sucedida
- Build de distribuição funcional
- Performance aceitável (< 3s para listagem, UI responsiva)

---

## Fase 6: Documentação Final e Lançamento

**Objetivo**: Completar documentação e preparar para uso.

### Etapas
- [ ] 6.1 Documentação de usuário
  - Guia de instalação
  - Guia de uso
  - FAQ
  - Troubleshooting

- [ ] 6.2 Documentação técnica
  - Arquitetura do sistema
  - Guia de contribuição
  - API docs (se aplicável)

- [ ] 6.3 Release notes
  - Lista de funcionalidades
  - Conhecidos issues
  - Requisitos de sistema

- [ ] 6.4 Commit inicial final
  - Commit de documentação completa
  - Tag de versão inicial

### Critérios de Conclusão
- Documentação completa e clara
- Usuário consegue instalar e usar sem ajuda
- Commit inicial com plano completo

---

## Ordem de Execução

1. **Fase 1** ✅ (Em progresso - este documento)
2. **Fase 2** - Infraestrutura
3. **Fase 3** - Camada de domínio (prioridade alta)
4. **Fase 4** - Interface gráfica (pode ser paralela com início da Fase 3)
5. **Fase 5** - Integração
6. **Fase 6** - Documentação final

## Prazos Estimados

- Fase 1: 1 dia (planejamento)
- Fase 2: 1-2 dias
- Fase 3: 3-5 dias
- Fase 4: 3-5 dias
- Fase 5: 2-3 dias
- Fase 6: 1 dia

**Total estimado**: 11-17 dias

## Riscos e Mitigações

### Risco 1: Permissões de Administrador
**Descrição**: Algumas operações de junção requerem elevação.
**Mitigação**: Detectar privilégios e solicitar elevação quando necessário; designar operações que funcionam sem elevação.

### Risco 2: Compatibilidade com Windows
**Descrição**: Links simbólicos podem requerer configuração especial.
**Mitigação**: Documentar requisitos; detectar disponibilidade de recursos; fornecer modo de compatibilidade.

### Risco 3: Interface Complexa
**Descrição**: Interface pode ficar complexa com muitas funcionalidades.
**Mitigação**: Focar em MVP inicial; usar wizard para operações complexas; iterar com feedback do usuário.

### Risco 4: Operações Destrutivas
**Descrição**: Erros podem causar perda de dados.
**Mitigação**: Validações rigorosas; backups automáticos; reversão em caso de erro; testes extensivos.

## Próximos Passos

Após aprovação deste plano:
1. Criar arquivo TECNOLOGIAS.md com stack tecnológico
2. Criar arquivo PROTOTIPO.md com wireframes da interface
3. Brainstorm com usuário sobre requisitos não esclarecidos
4. Iniciar Fase 2 (Infraestrutura)
