# Arquitetura de Distribuição e Instalação - WinLink

## Visão Geral

Este documento descreve como o WinLink será compilado, distribuído, instalado e desinstalado.

## 1. Compilação e Empacotamento

### Ferramenta: PyInstaller

**Por que PyInstaller?**
- Maduro e amplamente usado
- Empacota Python runtime e todas as dependências
- Cria executável standalone (.exe)
- Suporte multi-plataforma (necessário apenas Windows aqui)
- Bem documentado

**Como funciona:**
1. PyInstaller analisa o código Python
2. Coleta todas as dependências (PyQt6, pywin32, pydantic, etc.)
3. Empacota o Python interpreter
4. Cria um executável que auto-extrai os recursos

**Resultado esperado:**
- Executável: `winlink.exe` (~80-150 MB)
- Pasta de recursos (opcional): contém DLLs, assets, etc.
- Tamanho total: ~100-200 MB (PyQt6 é a maior parte)

**Estrutura após PyInstaller:**
```
dist/
└── winlink/
    ├── winlink.exe           # Executável principal
    ├── PyQt6/                # DLLs do Qt
    ├── pywin32/              # DLLs do pywin32
    └── ...                   # Outras dependências
```

### Alternativas Consideradas

| Ferramenta | Vantagens | Desvantagens | Decisão |
|------------|-----------|--------------|---------|
| PyInstaller | Maduro, documentado | Executável grande | ✅ Escolhido |
| cx_Freeze | Similar ao PyInstaller | Menos popular | Alternativa |
| Nuitka | Compila para C nativo | Complexo, setup difícil | Futuro (se necessário) |
| Briefcase | Simplifica processo | Menos controle | Alternativa |

---

## 2. Instalação

### Ferramenta: Inno Setup

**Por que Inno Setup?**
- Gratuito e open-source
- Especializado em instaladores Windows
- Gera instalador profissional com wizard
- Suporta desinstalador automático
- Compatível com Windows 7+

**Alternativa: NSIS**
- Similar ao Inno Setup
- Script mais complexo
- Inno Setup é mais simples para este caso

### Processo de Instalação

**O que o instalador faz:**
1. Exibe wizard de instalação
2. Solicita diretório de instalação (padrão: `C:\Program Files\WinLink`)
3. Copia arquivos do PyInstaller
4. Cria atalho no Desktop (opcional)
5. Cria atalho no Menu Iniciar
6. Opcionalmente adiciona ao PATH
7. Registra aplicativo no "Adicionar/Remover Programas"

**O que NÃO faz:**
- ❌ Não instala Python (já vem no executável)
- ❌ Não baixa dependências (já empacotadas)
- ❌ Não requer conexão com internet

**Requisitos do sistema:**
- Windows 10 (versão 1903 ou superior) ou Windows 11
- ~200 MB de espaço em disco
- Sem necessidade de Python ou outras dependências

### Estrutura após Instalação

```
C:\Program Files\WinLink\
├── winlink.exe
├── PyQt6/
├── pywin32/
└── ...

C:\Users\<usuario>\AppData\Roaming\WinLink\
├── config.json          # Criado na primeira execução
├── history.json          # Criado na primeira execução
├── winlink.log          # Criado na primeira execução
└── cache\               # Criado quando necessário
```

---

## 3. Armazenamento de Dados

### Localização: %APPDATA%\WinLink

**Por que %APPDATA%?**
- Padrão do Windows para dados de aplicativo
- Funciona com permissões de usuário padrão
- Não requer elevação para leitura/escrita
- Preservado entre reinstalações do aplicativo
- Seguro (acessível apenas pelo usuário)

**Caminho completo:**
```
C:\Users\<usuario>\AppData\Roaming\WinLink\
```

### Estrutura de Arquivos

```
%APPDATA%\WinLink\
├── config.json          # Configurações do usuário
│   ├── theme_mode: "auto"
│   ├── scan_directories: [...]
│   ├── window_width: 1200
│   └── ...
├── history.json         # Histórico de operações
│   [
│     {
│       "timestamp": "2026-11-02T21:35:00",
│       "operation": "create_junction",
│       "source": "D:\\Cache\\.vscode",
│       "target": "C:\\Users\\steff\\.vscode",
│       "status": "success"
│     },
│     ...
│   ]
├── winlink.log          # Logs do aplicativo
└── cache\               # Cache opcional (se necessário)
```

### Por que JSON e não Banco de Dados?

**Vantagens do JSON:**
- ✅ Simplicidade - não requer dependências adicionais
- ✅ Portabilidade - fácil de exportar/importar
- ✅ Leitura humana - usuário pode editar se necessário
- ✅ Suficiente para MVP - histórico de operações é simples
- ✅ Sem overhead - não precisa de processo de banco de dados

**Quando considerar SQLite:**
- Se implementarmos sincronização complexa entre origem/destino
- Se tivermos milhares de junções e precisarmos de queries complexas
- Se precisarmos de transações ACID
- Para Fase 1, JSON é suficiente

**Decisão**: JSON para MVP. SQLite pode ser adicionado em Fase 2 se necessário.

### Por que não Registro do Windows?

**Desvantagens do Registro:**
- ❌ Difícil de fazer backup/migração
- ❌ Não é legível/editável por humanos
- ❌ Pode causar problemas de permissões
- ❌ Padrão antigo (moderno: %APPDATA%)
- ❌ Difícil de debugar

**Vantagens do Registro:**
- ✅ Rápido para leitura/escrita
- ✅ Padrão para configurações do sistema

**Decisão**: Registro NÃO é usado. Dados em %APPDATA%\WinLink é o padrão moderno (UWP, Electron apps, etc.).

---

## 4. Desinstalação

### Desinstalador Gerado pelo Inno Setup

**O que REMOVE:**
- ✅ Executável do aplicativo (`C:\Program Files\WinLink\`)
- ✅ Atalhos (Desktop, Menu Iniciar)
- ✅ Entrada no "Adicionar/Remover Programas"
- ✅ **Configurações** (`%APPDATA%\WinLink\config.json`) - sempre remove
- ✅ **Logs** (`%APPDATA%\WinLink\winlink.log`) - sempre remove
- ❓ **Histórico** (`%APPDATA%\WinLink\history.json`) - perguntar ao usuário (manter ou apagar)

**O que NÃO REMOVE:**
- ❌ **Junções NTFS** - elas pertencem ao sistema de arquivos, não ao app
- ❌ **Arquivos nas pastas linkadas** - dados do usuário
- ❌ **Pastas de origem** - dados do usuário

### Justificativa

**Por que não remover junções?**
- As junções são configurações do sistema do usuário
- O app apenas as gerencia
- Desinstalar o app não deve destruir configurações do usuário
- Similar a como desinstalar um gerenciador de arquivos não apaga seus arquivos

**Por que perguntar sobre configurações/logs?**
- Alguns usuários querem manter histórico
- Outros querem limpar tudo
- Deixar a decisão com o usuário

### Tela de Desinstalação

```
┌────────────────────────────────────────────────────┐
│ Desinstalador do WinLink                  [X]     │
├────────────────────────────────────────────────────┤
│                                                    │
│ O desinstalador removerá os arquivos do programa. │
│                                                    │
│ Os seguintes dados do usuário serão removidos:     │
│                                                    │
│ [✓] Configurações (config.json)                   │
│ [✓] Logs (winlink.log)                             │
│                                                    │
│ Deseja manter o histórico de operações?           │
│                                                    │
│ ○ Manter histórico (history.json)                  │
│ ● Apagar histórico (history.json)                  │
│                                                    │
│ [ ] As junções NTFS NÃO serão removidas.           │
│    Elas pertencem ao sistema de arquivos e        │
│    continuam funcionando mesmo após desinstalação. │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                    [Desinstalar]       │
└────────────────────────────────────────────────────┘
```

---

## 5. Atualizações

### Estratégia de Atualização

**Fase 1 (MVP):**
- Sem atualização automática
- Usuário baixa nova versão e reinstala
- Configurações preservadas (em %APPDATA%)

**Fase 2 (Futuro):**
- Possível implementação de atualização automática
- Usar lib como `PyUpdater` ou implementar próprio
- Verificar atualização ao iniciar
- Download silencioso em background
- Instalação ao fechar o app

---

## 6. Assinatura de Código

### Opcional para Fase 1

**O que é:**
- Assinatura digital do executável
- Certificado da autoridade certificadora
- Windows SmartScreen confia mais em executáveis assinados

**Vantagens:**
- ✅ Reduz avisos do SmartScreen
- ✅ Aumenta confiança do usuário
- ✅ Previne warnings de "publisher desconhecido"

**Desvantagens:**
- ❌ Custo (~$100-500/ano)
- ❌ Processo de verificação
- ❌ Não é obrigatório

**Decisão**: Não assinar para Fase 1. Pode ser adicionado em Fase 2 se necessário.

---

## 7. Resumo

| Aspecto | Decisão | Justificativa |
|---------|---------|---------------|
| Compilação | PyInstaller | Maduro, empacota Python + dependências |
| Instalador | Inno Setup | Simples, profissional, gratuito |
| Dados | JSON em %APPDATA% | Simples, portátil, padrão moderno |
| Banco de dados | Não (JSON suficiente) | MVP não precisa de complexidade |
| Registro | Não usar | Antigo, difícil de backup |
| Desinstalador | Sim (Inno Setup) | Profissional |
| Remover configs/logs | Sim (sempre) | Limpeza completa |
| Remover histórico | Perguntar usuário | Usuário decide manter/apagar |
| Remover junções | NÃO | Pertencem ao usuário, não ao app |
| Assinatura de código | Não (Fase 1) | Custo, não obrigatório |
| Atualização automática | Não (Fase 1) | MVP, usuário reinstala |

---

## 8. Perguntas Frequentes

**Q: O usuário precisa ter Python instalado?**
A: Não. PyInstaller empacota o Python runtime dentro do executável.

**Q: O instalador baixa dependências da internet?**
A: Não. Todas as dependências já estão empacotadas no executável.

**Q: O tamanho do instalador será grande?**
A: Sim, ~100-200 MB. PyQt6 é a maior parte. Isso é normal para apps Qt.

**Q: As junções serão removidas ao desinstalar?**
A: Não. As junções pertencem ao sistema de arquivos do usuário, não ao app.

**Q: Posso migrar minhas configurações para outro computador?**
A: Sim. Basta copiar a pasta `%APPDATA%\WinLink\` para o novo computador.

**Q: O app funciona sem internet?**
A: Sim. Não há dependências de internet para funcionamento.

**Q: O app requer permissões de administrador?**
A: Para operações de leitura, não. Para criar/remover junções, sim (solicita elevação).

**Q: O histórico de operações é removido ao desinstalar?**
A: O desinstalador pergunta ao usuário. Pode escolher manter ou apagar o histórico. Configurações e logs são sempre removidos.
