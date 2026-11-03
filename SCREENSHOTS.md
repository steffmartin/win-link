# Instruções para Captura de Screenshots

## Objetivo
Capturar screenshots de todas as janelas/menus do WinLink para comparação com o protótipo (PROTOTIPO.md).

## Passos

### 1. Criar pasta para screenshots
A pasta `screenshots/` já foi criada na raiz do projeto.

### 2. Abrir o aplicativo
Dê 2 cliques em `iniciar-winlink.bat` ou execute:
```bash
cd D:\Projects\win-link
.venv\Scripts\python.exe -m winlink.main
```

### 3. Capturar as seguintes janelas (nesta ordem):

#### a) Janela Principal
- **Nome do arquivo**: `01_main_window.png`
- **Quando capturar**: Após o escaneamento completar (quando aparecer "32 junções encontradas" na barra de status)
- **O que mostrar**: Janela principal completa com toolbar, tabela, e barra de status

#### b) Diálogo Criar Junção
- **Nome do arquivo**: `02_create_junction_dialog.png`
- **Como abrir**: Clique no botão "Nova Junção" na toolbar
- **O que mostrar**: Diálogo completo com campos de origem e destino

#### c) Diálogo Prévia
- **Nome do arquivo**: `03_preview_dialog.png`
- **Como abrir**: No diálogo Criar Junção, preencha os campos e clique em "Prévia"
- **O que mostrar**: Diálogo de prévia com detalhes da operação
- **Nota**: Use pastas de teste (ex: D:\WinLink-Test e D:\WinLink-Test\origem)

#### d) Diálogo Configurações
- **Nome do arquivo**: `04_settings_dialog.png`
- **Como abrir**: Clique no botão "Configurações" na toolbar
- **O que mostrar**: Diálogo completo com todas as seções (Geral, Diretórios, Operações, Logs)

#### e) Diálogo Histórico
- **Nome do arquivo**: `05_history_dialog.png`
- **Como abrir**: Clique no botão "Histórico" na toolbar
- **O que mostrar**: Diálogo com tabela de histórico e filtros

#### f) Diálogo Propriedades
- **Nome do arquivo**: `06_properties_dialog.png`
- **Como abrir**: Clique com botão direito em uma junção na tabela e selecione "Propriedades"
- **O que mostrar**: Diálogo com informações da junção selecionada

#### g) Diálogo Desfazer (se possível)
- **Nome do arquivo**: `07_undo_dialog.png`
- **Como abrir**: Clique com botão direito em uma junção criada pelo App (se houver) e selecione "Desfazer"
- **O que mostrar**: Diálogo com opções de estratégia de desfazer
- **Nota**: Se não houver junções criadas pelo App, esta captura pode ser pulada

#### h) Context Menu
- **Nome do arquivo**: `08_context_menu.png`
- **Como abrir**: Clique com botão direito em uma junção na tabela
- **O que mostrar**: Menu de contexto com opções (Propriedades, Desfazer se aplicável)

#### i) Menu Arquivo
- **Nome do arquivo**: `09_menu_file.png`
- **Como abrir**: Clique em "Arquivo" na barra de menu
- **O que mostrar**: Menu dropdown com opções (Nova Junção, Atualizar, Sair)

#### j) Menu Exibir
- **Nome do arquivo**: `10_menu_view.png`
- **Como abrir**: Clique em "Exibir" na barra de menu
- **O que mostrar**: Menu dropdown com opção Histórico

#### k) Menu Editar
- **Nome do arquivo**: `11_menu_edit.png`
- **Como abrir**: Clique em "Editar" na barra de menu
- **O que mostrar**: Menu dropdown com opção Configurações

#### l) Menu Ajuda
- **Nome do arquivo**: `12_menu_help.png`
- **Como abrir**: Clique em "Ajuda" na barra de menu
- **O que mostrar**: Menu dropdown com opção Sobre

### 4. Como capturar
- Use a ferramenta de captura do Windows (Win + Shift + S)
- Salve cada captura na pasta `D:\Projects\win-link\screenshots\`
- Use os nomes de arquivo especificados acima

### 5. Após capturar
Commit as screenshots para o git:
```bash
git add screenshots/
git commit -m "Add UI screenshots for prototype comparison"
```

## Comparação com Protótipo

Após capturar as screenshots, crie um documento de comparação em `COMPARACAO-PROTO TIPO.md` com:
- Screenshot de cada janela
- Referência ao protótipo correspondente em PROTOTIPO.md
- Lista de diferenças encontradas
- Lista de melhorias necessárias (já documentado em MELHORIAS-UI.md)
