# Melhorias Futuras - WinLink

## Prioridade Alta

### 1. Scan Inverso (Reverse Scan)
**Descrição**: Permitir escanear para descobrir quais junções apontam para um determinado destino.

**Caso de uso**: Usuário quer saber todas as junções que apontam para `D:\Cache` para entender a dependência.

**Implementação sugerida**:
- Criar função `scan_reverse(destination: Path)` que escaneia diretórios comuns e encontre junções cujo `source` seja o destino especificado
- Adicionar opção na UI para "Encontrar junções que apontam para..."
- Possível otimização: criar um índice de junções para consultas rápidas

**Complexidade**: Média

---

## Prioridade Média

### 2. Cache de Scan
**Descrição**: Manter cache dos resultados de scan para evitar escaneamentos repetidos.

**Caso de uso**: Usuário abre o app frequentemente e não quer esperar o scan a cada vez.

**Implementação sugerida**:
- Salvar último resultado de scan em JSON
- Detectar mudanças (fs watchers) para invalidar cache
- Opção para forçar scan completo

**Complexidade**: Média

---

### 3. Exportar/Importar Configuração de Junções
**Descrição**: Permitir exportar lista de junções para backup ou migrar para outra máquina.

**Caso de uso**: Usuário quer manter backup das junções configuradas ou migrar para novo computador.

**Implementação sugerida**:
- Exportar para JSON/CSV
- Importar com validação
- Suporte para seleção parcial

**Complexidade**: Baixa

---

## Prioridade Baixa

### 4. Integração com OneDrive
**Descrição**: Detectar e gerenciar junções envolvendo pastas OneDrive.

**Caso de uso**: Usuário usa OneDrive e quer evitar conflitos.

**Implementação sugerida**:
- Detectar pastas OneDrive
- Alertar sobre conflitos potenciais
- Modo de compatibilidade

**Complexidade**: Alta

---

### 5. Compressão de Destinos
**Descrição**: Comprimir destinos para economizar espaço.

**Caso de uso**: Junções para diretórios raramente usados podem ser compactados.

**Implementação sugerida**:
- Opção para compactar origem
- Descompactação sob demanda
- Integração com Windows Compact

**Complexidade**: Alta

---

## Observações

- Todas as melhorias devem manter a regra de não modificar junções sem confirmação explícita
- Testes devem usar pastas de teste dedicadas
- Priorizar usabilidade e segurança
