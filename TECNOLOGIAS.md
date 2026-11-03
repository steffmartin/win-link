# Tecnologias - WinLink

## Stack Tecnológico Proposto

### Linguagem e Framework

#### Opção Recomendada: Rust + Tauri

**Linguagem**: Rust
**Framework UI**: Tauri + Windows-native APIs ou WebView2

**Justificativa**:
- **Performance**: Rust oferece performance nativa e gerenciamento de memória seguro
- **Segurança**: Sistema de tipos forte previne bugs de memória e race conditions
- **Tamanho**: Binários pequenos sem dependências pesadas
- **Tauri**: Framework moderno para apps desktop que usa WebView do sistema (mais leve que Electron)
- **Windows API**: Rust tem excelente suporte a Windows API via crates como `windows-rs`
- **Cross-platform**: Código pode ser reutilizado para Linux/macOS se necessário no futuro
- **Concorrência**: Modelo async de Rust facilita operações em segundo plano

**Crates relevantes**:
- `windows-rs`: Windows API bindings
- `tauri`: Framework desktop
- `tokio`: Runtime async
- `serde`: Serialização (JSON)
- `anyhow`: Tratamento de erros
- `tracing`: Logging estruturado
- `thiserror`: Erros customizados

**Desvantagens**:
- Curva de aprendizado para Rust
- Tempo de desenvolvimento pode ser maior inicialmente

---

#### Opção Alternativa 1: C# + WPF/WinUI 3

**Linguagem**: C#
**Framework UI**: WinUI 3 (Windows App SDK)

**Justificativa**:
- **Nativo Windows**: WinUI 3 é a UI moderna oficial da Microsoft para Windows 11
- **Familiaridade**: Se você já conhece C#, desenvolvimento é mais rápido
- **Visual Studio**: Excelente suporte de ferramentas
- **Windows API**: Acesso nativo sem bindings
- **Design**: Controles modernos prontos para Windows 11
- **Comunidade**: Grande comunidade e documentação

**Desvantagens**:
- Dependência do .NET runtime
- Binários maiores que Rust
- Limitado a Windows (menos portável)

---

#### Opção Escolhida: Python + PyQt6

**Linguagem**: Python
**Framework UI**: PyQt6

**Justificativa**:
- **Desenvolvimento rápido**: Python permite prototipagem rápida
- **Qt**: Framework UI maduro e poderoso
- **Familiaridade**: Linguagem conhecida
- **Bibliotecas**: Grande ecossistema de bibliotecas
- **Distribuição**: PyInstaller/cx_Freeze para executáveis standalone

**Desvantagens**:
- Performance menor que Rust/C# (aceitável para este caso de uso)
- Distribuição mais complexa (Python runtime incluído no executável)
- Look and feel pode não ser 100% nativo Windows 11 (mas pode ser customizado)

---

#### Opção Alternativa 3: Go + Fyne ou Wails

**Linguagem**: Go
**Framework UI**: Fyne (cross-platform) ou Wails (WebView)

**Justificativa**:
- **Simplicidade**: Go é simples e fácil de aprender
- **Concorrência**: Goroutines facilitam operações em segundo plano
- **Binários**: Single binary sem runtime
- **Wails**: Similar ao Tauri, mas com Go

**Desvantagens**:
- UI cross-platform pode não ser 100% nativa Windows 11
- Ecossistema de Windows API menor que Rust/C#
- Menos otimizado para Windows específico

---

### Decisão Final

**Python + PyQt6** foi escolhido para este projeto porque:
1. Desenvolvimento rápido e iteração ágil
2. Familiaridade com a linguagem
3. Ecossistema maduro de bibliotecas para Windows
4. PyQt6 oferece widgets modernos e suporte a temas nativos
5. Facilidade de criação de executáveis com PyInstaller/cx_Freeze
6. Adequado para aplicação desktop com foco em funcionalidade sobre performance extrema

---

## Bibliotecas Específicas por Categoria

### Manipulação de Sistema de Arquivos
- `pathlib`: API moderna para caminhos
- `os`, `shutil`: APIs padrão para operações de arquivo
- `pywin32` (win32api, win32file, win32con): Windows API para junções NTFS
- `ctypes`: Para chamadas de sistema de baixo nível se necessário

### Interface Gráfica
- `PyQt6`: Bindings Qt6 - Framework principal
- `PyQt6-Qt6`: Runtime Qt6
- `PyQt6-WebEngine`: Se precisar de WebView (opcional)
- `pyqt-fluent-widgets`: Widgets estilo Fluent Design (opcional, para look Windows 11)

### Logging
- `logging`: Biblioteca padrão
- `loguru`: Alternativa mais moderna e simples (opcional)

### Serialização/Configuração
- `json`: Biblioteca padrão
- `toml`: Suporte TOML (via `toml` package)
- `pydantic`: Validação de dados e configurações
- `pydantic-settings`: Gerenciamento de configurações

### Testes
- `pytest`: Framework popular
- `pytest-qt`: Para testes de GUI PyQt
- `pytest-cov`: Cobertura de código
- `unittest.mock`: Para mocking

### Operações em Segundo Plano
- `QThread` e `QThreadPool` (PyQt6): Para operações assíncronas na UI
- `concurrent.futures`: Para threading em geral

### Build e Distribuição
- `PyInstaller`: Para criar executável standalone
- `cx_Freeze`: Alternativa para freeze
- `Nuitka`: Compilador Python para executáveis nativos (opcional)

---

## Build e Distribuição
- `PyInstaller`: Para criar executável standalone
- `cx_Freeze`: Alternativa para freeze
- `Nuitka`: Compilador Python para executáveis nativos (opcional)
- Inclui Python runtime no executável
- Executável único ou com dependências

---

## Ferramentas de Desenvolvimento

### Comuns
- **Git**: Controle de versão
- **VS Code**: Editor (com extensões Python)
- **GitHub/GitLab**: Hospedagem

### Python Específico
- **Poetry** ou **uv**: Gerenciamento de dependências e ambientes virtuais
- **black**: Formatter de código
- **pylint** ou **ruff**: Linter
- **mypy**: Type checking (opcional)
- **pyright**: Type checker alternativo (VS Code integration)

### PyQt6 Específico
- **Qt Designer**: Editor visual de UI (incluído com PyQt6-tools)
- **pyuic6**: Converter arquivos .ui para Python
