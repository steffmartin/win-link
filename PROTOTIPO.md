# Protótipo de Interface - WinLink

## Visão Geral do Design

A interface segue os princípios do **Fluent Design System** do Windows 11, com suporte a temas claro e escuro que seguem a configuração do sistema. Layout limpo, moderno e focado na usabilidade.

## Tela Principal

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ WinLink                                    ┌──────────────────┐ │
│                                          │ [🔍] Buscar      │ │
├──────────────────────────────────────────┴──────────────────┤ │
│ [🏠]  [➕]  [⚙️]                                             │ │
├─────────────────────────────────────────────────────────────┤ │
│ Filtros: [Todas ▼] [Ativas ▼] [Criador ▼]                   │ │
├─────────────────────────────────────────────────────────────┤ │
│ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ Origem                      │ Destino    │ Criador │ Ações│ │ │
│ ├─────────────────────────────┼────────────┼─────────┼──────┤ │ │
│ │ D:\Cache\.vscode            │ C:\Users\  │ App     │ [⚙️] │ │ │
│ │                             │ steff\.vs  │         │      │ │ │
│ ├─────────────────────────────┼────────────┼─────────┼──────┤ │ │
│ │ D:\Cache\.cargo             │ C:\Users\  │ App     │ [⚙️] │ │ │
│ │                             │ steff\.car │         │      │ │ │
│ ├─────────────────────────────┼────────────┼─────────┼──────┤ │ │
│ │ D:\Cache\jfinancas\auto     │ C:\Users\  │ Existente│ [⚙️] │ │ │
│ │                             │ steff\OneD │         │      │ │ │
│ │                             │ rive\...\  │         │      │ │ │
│ └─────────────────────────────────────────────────────────┘ │ │
├─────────────────────────────────────────────────────────────┤ │
│ Status: 3 junções encontradas                              │ │
└─────────────────────────────────────────────────────────────┘
```

### Componentes

#### Barra de Título
- Título "WinLink" à esquerda
- Botão de busca à direita
- Botões de minimizar, maximizar, fechar (nativos do Windows)

#### Barra de Ferramentas
- **🏠 Home**: Atualiza a lista e volta ao estado inicial
- **➕ Nova Junção**: Abre diálogo para criar nova junção
- **⚙️ Configurações**: Abre diálogo de configurações

#### Barra de Filtros
- Filtro por status: Todas, Ativas, Quebradas, Inacessíveis
- Filtro por criador: Todas, App, Existente, SO, Usuário
- Botão "Limpar Filtros"

#### Tabela de Junções
Colunas:
- **Origem**: Caminho completo onde os arquivos existem
- **Destino**: Caminho da junção
- **Criador**: Badge colorido (App=verde, Existente=amarelo, SO=azul, Usuário=cinza)
- **Tipo**: Ícone + texto (📁 Junction, 🔗 Symlink, 📄 HardLink)
- **Tamanho**: Tamanho total dos arquivos (ex: "2.3 GB")
- **Status**: Badge (✓ Ativo, ⚠ Quebrado, 🔒 Inacessível)
- **Ações**: Botão com menu dropdown (Desfazer, Sincronizar, Propriedades)

#### Barra de Status
- Número total de junções
- Número de junções ativas/quebradas
- Informações sobre última atualização

---

## Diálogo: Nova Junção

### Layout

```
┌────────────────────────────────────────────────────┐
│ Criar Nova Junção                     [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ Destino (pasta que será linkada):                  │
│ ┌──────────────────────────────────────────────┐  │
│ │ C:\Users\steff\.vscode               [...][📁]│  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ Origem (onde os arquivos ficarão):                │
│ ┌──────────────────────────────────────────────┐  │
│ │ D:\Cache\.vscode                    [...][📁]│  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ [ℹ️] Se o destino já existir, os arquivos serão   │
│      copiados para a origem antes de criar a      │
│      junção.                                      │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]              [Prévia]  [Criar Junção]  │
└────────────────────────────────────────────────────┘
```

### Estados

#### Estado Inicial
- Campos vazios ou com sugestões baseadas em pastas comuns
- Botão "Prévia" desabilitado

#### Estado Com Campos Preenchidos
- Validação em tempo real
- Botão "Prévia" habilitado
- Feedback visual se caminhos são inválidos

#### Diálogo de Prévia
```
┌────────────────────────────────────────────────────┐
│ Prévia da Operação                  [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ O que será feito:                                  │
│                                                    │
│ ✓ Criar diretório: D:\Cache\.vscode               │
│ ✓ Copiar arquivos de C:\Users\steff\.vscode       │
│   para D:\Cache\.vscode (2.3 GB)                  │
│ ✓ Remover C:\Users\steff\.vscode                  │
│ ✓ Criar junção: C:\Users\steff\.vscode →          │
│   D:\Cache\.vscode                                 │
│                                                    │
│ Espaço necessário: 2.3 GB                          │
│ Espaço disponível: 45.2 GB                        │
│                                                    │
│ ⚠️ Certifique-se de fechar o VS Code antes de     │
│    continuar.                                     │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                 [Confirmar e Criar]    │
└────────────────────────────────────────────────────┘
```

#### Diálogo de Prévia (com aviso de junções aninhadas)
```
┌────────────────────────────────────────────────────┐
│ Prévia da Operação                  [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ O que será feito:                                  │
│                                                    │
│ ✓ Criar diretório: D:\Cache\minha_pasta           │
│ ✓ Copiar arquivos de C:\Users\steff\minha_pasta   │
│   para D:\Cache\minha_pasta (500 MB)              │
│ ✓ Remover C:\Users\steff\minha_pasta              │
│ ✓ Criar junção: C:\Users\steff\minha_pasta →      │
│   D:\Cache\minha_pasta                            │
│                                                    │
│ Espaço necessário: 500 MB                          │
│ Espaço disponível: 45.2 GB                        │
│                                                    │
│ ⚠️ Aviso: A pasta de origem contém 2 junções:    │
│    • .cache → D:\Cache\.cache                      │
│    • .cargo → D:\Cache\.cargo                      │
│                                                    │
│    Windows redirecionará corretamente, mas isso   │
│    pode causar confusão. Considere usar as       │
│    junções originais diretamente.                 │
│                                                    │
│ ⚠️ Certifique-se de fechar o VS Code antes de     │
│    continuar.                                     │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                 [Confirmar e Criar]    │
└────────────────────────────────────────────────────┘
```

---

## Diálogo: Desfazer Junção

### Layout

```
┌────────────────────────────────────────────────────┐
│ Desfazer Junção                       [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ Junção selecionada:                                │
│ C:\Users\steff\.vscode → D:\Cache\.vscode         │
│                                                    │
│ Escolha o que fazer:                               │
│                                                    │
│ ○ Remover apenas a junção                          │
│   A junção será removida, deixando uma pasta       │
│   vazia no destino. Os arquivos permanecem na      │
│   origem.                                          │
│                                                    │
│ ● Mover arquivos de volta                          │
│   Os arquivos serão movidos da origem para o       │
│   destino, e a junção será removida.               │
│                                                    │
│ ○ Duplicar arquivos                                │
│   Os arquivos serão copiados da origem para o      │
│   destino. A junção será removida. A origem        │
│   permanece com os arquivos.                        │
│                                                    │
│ [ ] Manter origem como backup                      │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                    [Desfazer Junção]    │
└────────────────────────────────────────────────────┘
```

### Estados

#### Opção "Remover apenas"
- Mais rápido
- Arquivos permanecem na origem

#### Opção "Mover arquivos"
- Requer espaço no destino
- Útil se quer desfazer completamente

#### Opção "Duplicar arquivos"
- Requer espaço no destino
- Útil se quer manter backup na origem

---

## Diálogo: Progresso

### Layout

```
┌────────────────────────────────────────────────────┐
│ Criando Junção...                     [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ ████████████████████░░░░░░░░  65%                 │
│                                                    │
│ Copiando arquivos...                               │
│ 1.234 / 1.890 arquivos                             │
│                                                    │
│ Tempo estimado: 2 minutos                          │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                                         │
└────────────────────────────────────────────────────┘
```

### Estados

#### Em Progresso
- Barra de progresso animada
- Contador de arquivos
- Tempo estimado (se disponível)
- Botão "Cancelar" habilitado

#### Concluído
- Barra completa (100%)
- Mensagem de sucesso
- Botão "Fechar"

#### Erro
- Barra parada no ponto do erro
- Mensagem de erro detalhada
- Botão "Fechar" e "Tentar Novamente"

---

## Diálogo: Configurações

### Layout

```
┌────────────────────────────────────────────────────┐
│ Configurações                          [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ Geral                                              │
│ ───────────────────────────────────────────────── │
│ Tema: [🌙 Seguir sistema ▼]                        │
│ Idioma: [🇧🇷 Português ▼]                          │
│                                                    │
│ Diretórios para Escanear                           │
│ ───────────────────────────────────────────────── │
│ [✓] C:\Users\steff                         [+][-]   │
│ [✓] D:\Cache                               [+][-]   │
│ [ ] C:\ProgramData                         [+][-]   │
│                                                    │
│ Adicionar diretório personalizado:                │
│ ┌──────────────────────────────────────────────┐  │
│ │                                          [...][📁]│  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ Operações                                          │
│ ───────────────────────────────────────────────── │
│ [✓] Pedir confirmação antes de operações          │
│ [✓] Criar backup automático antes de desfazer      │
│ [✓] Mostrar notificações de conclusão              │
│ [✓] Avisar sobre junções aninhadas                 │
│     (quando criar junção para pasta que já         │
│      contém junções)                                │
│                                                    │
│ Logs                                               │
│ ───────────────────────────────────────────────── │
│ Nível: [Info ▼]                                   │
│ [📁] Abrir pasta de logs                          │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                          [Salvar]      │
└────────────────────────────────────────────────────┘
```

---

## Diálogo: Propriedades da Junção

### Layout

```
┌────────────────────────────────────────────────────┐
│ Propriedades                          [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ Informações Gerais                                 │
│ ───────────────────────────────────────────────── │
│ Tipo: Junção (Junction)                            │
│ Status: ✓ Ativo                                    │
│ Criador: App                                       │
│ Data de criação: 01/11/2026 14:30                  │
│                                                    │
│ Caminhos                                            │
│ ───────────────────────────────────────────────── │
│ Origem:                                            │
│ D:\Cache\.vscode                                   │
│ [📁] Abrir pasta                                   │
│                                                    │
│ Destino:                                           │
│ C:\Users\steff\.vscode                             │
│ [📁] Abrir pasta                                   │
│                                                    │
│ Estatísticas                                       │
│ ───────────────────────────────────────────────── │
│ Tamanho total: 2.3 GB                              │
│ Número de arquivos: 1.890                          │
│ Número de pastas: 45                               │
│                                                    │
│ Histórico de Operações                             │
│ ───────────────────────────────────────────────── │
│ 01/11/2026 14:30 - Criada via WinLink             │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Fechar]                     [Desfazer] [Editar]  │
└────────────────────────────────────────────────────┘
```

---

## Diálogo: Histórico de Operações

### Layout

```
┌────────────────────────────────────────────────────┐
│ Histórico de Operações                [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ Filtros:                                           │
│ Tipo: [Todas ▼]  Data: [Todos ▼]  [Limpar]        │
│                                                    │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Data       │ Tipo      │ Detalhes   │ Ações    │ │ │
│ ├────────────┼───────────┼────────────┼──────────┤ │ │
│ │ 01/11/2026 │ Criar    │ .vscode →  │ [⚙️]    │ │ │
│ │ 14:30      │ Junção   │ D:\Cache\  │          │ │ │
│ │            │           │ .vscode    │          │ │ │
│ ├────────────┼───────────┼────────────┼──────────┤ │ │
│ │ 01/11/2026 │ Remover   │ .vscode    │ [⚙️]    │ │ │
│ │ 15:45      │ Junção   │ (desfeito) │          │ │ │
│ │            │           │            │          │ │ │
│ ├────────────┼───────────┼────────────┼──────────┤ │ │
│ │ 02/11/2026 │ Copiar    │ jfinancas  │ [⚙️]    │ │ │
│ │ 10:20      │ Arquivos │ → Backup   │          │ │ │
│ │            │           │            │          │ │ │
│ └─────────────────────────────────────────────────┘ │
│                                                    │
│ Total: 45 operações  Últimos 30 dias               │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Fechar]           [Limpar Histórico]  [Exportar] │
└────────────────────────────────────────────────────┘
```

### Componentes

#### Filtros
- **Tipo**: Todas, Criar, Remover, Recriar, Copiar, Mover, Excluir, Duplicar
- **Data**: Todos, Hoje, Última semana, Último mês, Personalizado
- **Limpar**: Remove todos os filtros

#### Tabela de Operações
Colunas:
- **Data**: Data e hora da operação
- **Tipo**: Badge colorido (Criar=verde, Remover=vermelho, Copiar=azul, etc.)
- **Detalhes**: Descrição resumida da operação
- **Ações**: Botão com menu (Desfazer, Ver detalhes, Copiar caminho)

#### Ações da Barra
- **Limpar Histórico**: Remove todas as operações (com confirmação)
- **Exportar**: Exporta histórico para JSON/CSV

---

## Diálogo: Sincronizar

### Layout

```
┌────────────────────────────────────────────────────┐
│ Sincronizar Junção                      [X]          │
├────────────────────────────────────────────────────┤
│                                                    │
│ Comparando arquivos...                              │
│                                                    │
│ Diferenças encontradas:                            │
│                                                    │
│ [📄] settings.json                                 │
│      Modificado em: Origem (mais recente)          │
│      Ação: Copiar para destino                     │
│                                                    │
│ [📄] keybindings.json                              │
│      Modificado em: Destino (mais recente)         │
│      Ação: Copiar para origem                      │
│                                                    │
│ [📁] extensions                                    │
│      Existe apenas na origem                       │
│      Ação: Copiar para destino                     │
│                                                    │
│                                                    │
│ Estratégia de sincronização:                        │
│ ○ Mais recente vence                               │
│ ● Origem tem prioridade                            │
│ ○ Destino tem prioridade                           │
│ ○ Personalizar                                    │
│                                                    │
├────────────────────────────────────────────────────┤
│ [Cancelar]                       [Sincronizar]    │
└────────────────────────────────────────────────────┘
```

---

## Notificações (Toast)

### Sucesso
```
┌──────────────────────────────┐
│ ✓                      [×]   │
│ Junção criada com sucesso     │
│ C:\Users\steff\.vscode       │
└──────────────────────────────┘
```

### Erro
```
┌──────────────────────────────┐
│ ⚠                      [×]   │
│ Erro ao criar junção          │
│ Arquivos em uso pelo VS Code │
└──────────────────────────────┘
```

### Aviso
```
┌──────────────────────────────┐
│ ℹ                      [×]   │
│ 3 junções quebradas           │
│ Clique para ver detalhes      │
└──────────────────────────────┘
```

---

## Paleta de Cores (Windows 11)

### Tema Claro
- Background: `#FFFFFF`
- Surface: `#F3F3F3`
- Surface Variant: `#EDEDED`
- Primary: `#0067C0` (Windows Blue)
- Primary Container: `#D0E4FF`
- On Primary: `#FFFFFF`
- Text: `#1A1A1A`
- Text Secondary: `#5C5C5C`
- Border: `#E5E5E5`
- Success: `#107C10`
- Warning: `#9B8F06`
- Error: `#C42B1A`

### Tema Escuro
- Background: `#202020`
- Surface: `#2B2B2B`
- Surface Variant: `#333333`
- Primary: `#4CC2FF`
- Primary Container: `#004275`
- On Primary: `#000000`
- Text: `#FFFFFF`
- Text Secondary: `#D0D0D0`
- Border: `#404040`
- Success: `#6CCB6F`
- Warning: `#E2D868`
- Error: `#FF8A80`

---

## Tipografia

- Fonte: Segoe UI (fonte padrão do Windows)
- Tamanhos:
  - Título: 28px (Semibold)
  - Subtítulo: 20px (Semibold)
  - Body: 14px (Regular)
  - Caption: 12px (Regular)
  - Monospace: Consolas (para caminhos)

---

## Ícones

Usar ícones do **Segoe Fluent Icons** (padrão Windows 11):
- 🏠 Home
- ➕ Adicionar
- ⚙️ Configurações
- 🔍 Buscar
- 📁 Pasta
- 🔗 Link
- ✓ Sucesso
- ⚠ Aviso
- ❌ Erro
- ℹ Informação

---

## Responsividade

### Janela Mínima
- Largura: 800px
- Altura: 600px

### Janela Recomendada
- Largura: 1200px
- Altura: 800px

### Comportamento de Redimensionamento
- Tabela usa scroll horizontal se necessário
- Colunas se ajustam proporcionalmente
- Painéis laterais podem ser colapsados

---

## Acessibilidade

- Suporte a teclado (Tab, Enter, Esc)
- High contrast mode
- Screen reader friendly
- Texto escalável (DPI awareness)
- Foco visível em todos os elementos interativos

---

## Animações

- Transições suaves entre temas
- Fade-in para listas
- Slide-in para diálogos
- Progress bars animadas
- Hover effects em botões

---

## Melhorias Implementadas na Fase 3

### Atualizações no Protótipo (pós-implementação)

1. **Aviso de Junções Aninhadas**
   - Adicionado na seção de configurações: opção para avisar sobre junções aninhadas
   - Adicionado novo estado no diálogo de prévia para mostrar warning quando origem contém junções
   - Windows redireciona corretamente, mas o aviso ajuda a evitar confusão

2. **Diálogo de Histórico de Operações**
   - Novo diálogo para visualizar histórico completo de operações
   - Filtros por tipo e data
   - Opção de exportar histórico
   - Integração com funcionalidade de undo

3. **Correções de Terminologia**
   - Removidas menções específicas a "NTFS" (junctions funcionam em outros sistemas de arquivos)
   - Atualizado "Junção NTFS" para "Junção (Junction)"

4. **Scan Inverso (Futuro)**
   - Funcionalidade documentada em MELHORIAS.md
   - Permitirá descobrir quais junções apontam para um determinado destino
   - Não implementado na Fase 3, mas planejado para versões futuras

---

## Próximos Passos

Este protótipo define a direção visual e de UX. Antes de implementar, preciso validar:

1. **Stack tecnológico**: Rust + Tauri está OK ou prefere outra opção?
2. **Funcionalidades adicionais**: Há alguma funcionalidade que gostaria de adicionar?
3. **Modificações no design**: Algum aspecto do protópio que gostaria de alterar?
4. **Prioridades**: Qual funcionalidade é mais importante para você?
