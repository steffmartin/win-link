# Melhorias de UI - Fase 5 (Polimento)

**Data**: 2026-11-02
**Status**: Pendente de implementação

## Melhorias Identificadas

### 1. Ícone do Aplicativo ⚠️

**Problema Atual:**
- O aplicativo exibe ícones default do Python na barra de tarefas e barra de título
- Não há ícones nos botões da toolbar e menus
- Contraria o protótipo (PROTOTIPO.md) que especifica ícones modernos (Segoe Fluent Icons)

**Solução:**
- Criar arquivo de ícone `.ico` para o aplicativo
- Integrar ícone na aplicação PyQt6:
  - Barra de título
  - Barra de tarefas
  - Task Manager
- Adicionar ícones aos botões da toolbar usando recursos do PyQt6
- Adicionar ícones aos menus

**Implementação:**
```python
# Em main_window.py
from PyQt6.QtGui import QIcon

# Definir ícone da janela
self.setWindowIcon(QIcon("path/to/icon.ico"))

# Adicionar ícones aos botões da toolbar
home_action = QAction(QIcon("path/to/home.png"), "Home", self)
```

**Recursos Necessários:**
- Arquivo de ícone `.ico` (pode ser criado com ferramentas como GIMP, Inkscape, ou online)
- Ícones individuais para cada ação (Home, Novo, Configurações, etc.)
- Alternativa: usar Unicode emojis como solução temporária ou ícones do sistema

**Prioridade:** Alta

---

### 2. Redimensionamento Automático de Colunas ⚠️

**Problema Atual:**
- As colunas da tabela não se redimensionam automaticamente após o escaneamento
- Usuário precisa ajustar manualmente

**Solução:**
- Redimensionar colunas automaticamente quando o escaneamento termina
- **Importante:** Não redimensionar colunas que o usuário ajustou manualmente
- **Exceção:** Se o usuário der 2 cliques no cabeçalho da coluna, isso deve "limpar" o ajuste manual e permitir redimensionamento automático futuro

**Implementação:**
```python
# Em main_window.py
class MainWindow(QMainWindow):
    def __init__(self):
        # ... código existente ...
        self._user_resized_columns = set()  # Rastrear colunas ajustadas pelo usuário

    def on_scan_finished(self, result):
        """Handle scan completion"""
        self.junction_model.set_junctions(result.junctions)

        # Redimensionar colunas automaticamente
        for col in range(self.junction_model.columnCount()):
            if col not in self._user_resized_columns:
                self.table_view.resizeColumnToContents(col)

        self.status_bar.showMessage(
            f"Escaneamento concluído: {len(result.junctions)} junções encontradas"
        )

    # Conectar sinal de resize do header
    self.table_view.horizontalHeader().sectionResized.connect(self.on_column_resized)

    def on_column_resized(self, logical_index, old_size, new_size):
        """Rastrear quando usuário redimensiona coluna manualmente"""
        self._user_resized_columns.add(logical_index)

    # Detectar duplo clique no header
    self.table_view.horizontalHeader().sectionDoubleClicked.connect(self.on_header_double_clicked)

    def on_header_double_clicked(self, logical_index):
        """Limpar marca de ajuste manual ao dar duplo clique"""
        if logical_index in self._user_resized_columns:
            self._user_resized_columns.remove(logical_index)
```

**Prioridade:** Média

---

### 3. Ordenação por Clique na Coluna ⚠️

**Problema Atual:**
- Não é possível ordenar a lista clicando nas colunas
- O usuário não pode ordenar A-Z ou Z-A facilmente

**Solução:**
- Permitir ordenação clicando no cabeçalho da coluna
- Alternar entre A-Z e Z-A ao clicar novamente
- Indicador visual de ordenação (seta no cabeçalho)

**Implementação:**
```python
# Em main_window.py
from PyQt6.QtCore import Qt

def init_ui(self):
    # ... código existente ...

    # Habilitar ordenação
    self.table_view.setSortingEnabled(True)

    # Configurar comportamento de ordenação
    self.table_view.setAlternatingRowColors(True)

    # O proxy model já suporta ordenação via lessThan()
    # Mas precisamos garantir que o header seja clicável
    self.table_view.horizontalHeader().setSectionsClickable(True)
    self.table_view.horizontalHeader().setSortIndicatorShown(True)
```

**Nota:** O `JunctionFilterProxyModel` já tem o método `lessThan` implementado, então a ordenação deve funcionar com apenas habilitar `setSortingEnabled(True)`.

**Prioridade:** Alta

---

## Outras Melhorias Sugeridas (Baseadas no Protótipo)

### 4. Tooltips Detalhados

**Descrição:** Adicionar tooltips mais detalhados em botões e elementos da interface.

**Implementação:**
```python
home_action.setStatusTip("Atualizar lista e voltar ao estado inicial")
home_action.setToolTip("Atualiza a lista de junções e limpa todos os filtros")
```

**Prioridade:** Baixa

---

### 5. Atalhos de Teclado

**Descrição:** Implementar atalhos de teclado para ações comuns.

**Implementação:**
```python
# Ctrl+N: Nova Junção (já implementado)
# F5: Atualizar (já implementado)
# Ctrl+Q: Sair (já implementado)
# Ctrl+F: Focar na busca
# Ctrl+,: Configurações
# Ctrl+H: Histórico
```

**Prioridade:** Média

---

### 6. Animações e Transições

**Descrição:** Adicionar animações sutis para melhorar a experiência do usuário.

**Implementação:**
- Fade-in ao abrir diálogos
- Smooth transition ao mudar tema
- Animação na barra de progresso

**Prioridade:** Baixa

---

## Ordem de Implementação Sugerida

1. **Cache de Junções Descobertas** (Alta prioridade)
2. **Ícone do Aplicativo** (Alta prioridade)
3. **Ordenação por Clique** (Alta prioridade)
4. **Redimensionamento de Colunas** (Média prioridade)
5. **Atalhos de Teclado** (Média prioridade)
6. **Tooltips Detalhados** (Baixa prioridade)
7. **Animações e Transições** (Baixa prioridade)

---

## 7. Cache de Junções Descobertas ⚠️

**Problema Atual:**
- O scanner roda a cada inicialização (~20 segundos)
- Não há cache dos resultados do scan
- Usuário precisa esperar toda vez que abre o app

**Solução:**
- Criar cache de junções em JSON em `%APPDATA%\WinLink\cache.json`
- Salvar resultados do scan com timestamp
- Carregar do cache ao iniciar (instantâneo)
- Scan em background e atualizar quando terminar
- Indicador visual mostrando dados do cache vs. atualizados

**Implementação:**
```python
# Em cache.py (novo módulo)
class JunctionCache:
    def __init__(self):
        self.cache_file = Path.home() / "AppData" / "Roaming" / "WinLink" / "cache.json"

    def load(self) -> list[Junction]:
        """Carregar junções do cache"""
        if self.cache_file.exists():
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                return [Junction(**j) for j in data.get("junctions", [])]
        return []

    def save(self, junctions: list[Junction]):
        """Salvar junções no cache"""
        data = {
            "junctions": [j.model_dump() for j in junctions],
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def is_expired(self, max_age_hours: int = 24) -> bool:
        """Verificar se cache expirou"""
        if not self.cache_file.exists():
            return True
        # Implementar verificação de timestamp
        return True
```

**Integração com MainWindow:**
```python
def start_scan(self):
    """Start scanning for junctions"""
    # Carregar do cache primeiro
    cached_junctions = self.cache.load()
    if cached_junctions:
        self.junction_model.set_junctions(cached_junctions)
        self.status_bar.showMessage("Carregando dados do cache...")

    # Scan em background
    self.scan_worker = ScanWorker(directories)
    self.scan_worker.finished.connect(self.on_scan_finished)
    self.scan_worker.start()
```

**Prioridade:** Alta (performance)

---

## Notas

- Para ícones, considerar usar recursos do sistema (Segoe Fluent Icons) ou criar ícones SVG customizados
- O redimensionamento de colunas precisa ser testado cuidadosamente para não incomodar o usuário
- A ordenação deve funcionar corretamente com todos os tipos de dados (texto, números, datas)
