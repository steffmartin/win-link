# Brainstorming e Decisões - WinLink

## Decisões Tomadas

### 1. Stack Tecnológico ✅
**Decisão**: Python + PyQt6

**Justificativa**: Desenvolvimento rápido, familiaridade com a linguagem, ecossistema maduro, PyQt6 oferece widgets modernos e suporte a temas nativos.

---

### 2. Escopo de Arquivos vs Diretórios ✅
**Decisão**: Diretórios e arquivos desde o início

**Justificativa**: Suporte completo a junctions de diretórios, hard links e symbolic links de arquivos. Embora hard links de arquivos tenham limitações (mesmo volume), symbolic links são mais flexíveis.

---

### 3. Descoberta Automática de Junções ✅
**Decisão**: Híbrida

**Justificativa**: Escaneamento rápido em diretórios configuráveis (C:\Users, D:\Cache) por padrão, com opção de escaneamento completo manual. Isso oferece bom equilíbrio entre performance e completude.

---

### 4. Funcionalidades Adicionais ✅
**Decisão**: Histórico de operações

**Justificativa**: Log de todas as operações com opção de desfazer, aumentando segurança e rastreabilidade. Isso será implementado como backup de metadados (não de arquivos completos, para economizar espaço).

---

## Dúvidas Pendentes (Para Refinamento Futuro)

### Classificação de "Criador"
A especificação define 4 categorias: App, Existente, SO, Usuário.

**Pergunta**:
- Como diferenciar "SO" de "Usuário"? Ambos podem ter criado manualmente.
- Devemos tentar detectar via logs do Windows, ou é suficiente classificar tudo que não foi criado pelo app como "Existente"?

**Sugestão**: Classificação simplificada:
- **App**: Criado pelo WinLink
- **Existente**: Já existia antes do WinLink (detectado na primeira execução)
- **Manual**: Criado após WinLink estar instalado (pode ser SO ou usuário)

---

### Integração com Script Existente
**Pergunta**:
- O WinLink deve importar configurações do script `migrar_pastas.ps1`?
- Devemos manter compatibilidade para que ambos possam coexistir?
- Ou o WinLink deve substituir completamente o script?

**Sugestão**: Coexistência pacífica. WinLink detecta junções criadas pelo script como "Existente" e permite gerenciá-las.

---

### Operações de Sincronização
A especificação menciona sincronização entre origem e destino.

**Pergunta**:
- É realmente necessário? O caso de uso principal é apenas mover pastas para outro disco.
- Se sim, qual estratégia padrão? Mais recente vence? Origem tem prioridade?
- Isso pode ser uma funcionalidade avançada para fase posterior?

**Sugestão**: Deixar para Fase 2. Fase 1 foca em criar/desfazer junções.

---

### Elevação de Permissões
Algumas operações requerem administrador.

**Pergunta**:
- O app deve solicitar elevação apenas quando necessário, ou deve sempre rodar como admin?
- Devemos ter modo "leitura apenas" sem elevação?

**Sugestão**: App roda sem elevação por padrão. Solicita elevação apenas quando usuário tenta operação que requer admin.

---

## Funcionalidades Adicionais NÃO Selecionadas (Para Fase 2)

As seguintes funcionalidades foram sugeridas mas não incluídas no MVP inicial. Podem ser consideradas para fases posteriores:

### 1. Sugestão de Pastas para Migrar
**Descrição**: Analisar perfil do usuário e sugerir pastas que poderiam ser migradas.
**Complexidade**: Média
**Status**: Fase 2

### 2. Análise de Espaço
**Descrição**: Mostrar quanto espaço seria economizado se determinadas pastas fossem migradas.
**Complexidade**: Baixa
**Status**: Fase 2

### 3. Perfis de Migração
**Descrição**: Perfis predefinidos (ex: "Desenvolvedor", "Gamer", "Geral") que sugerem conjuntos de pastas para migrar.
**Complexidade**: Média
**Status**: Fase 2

### 5. Validação de Integridade Periódica
**Descrição**: Verificar periodicamente se junções estão funcionais.
**Complexidade**: Média
**Status**: Fase 2

### 6. Importação/Exportação de Configuração
**Descrição**: Exportar lista de junções para arquivo JSON e importar em outro computador.
**Complexidade**: Baixa
**Status**: Fase 2

### 7. Integração com OneDrive
**Descrição**: Reconhecer pastas OneDrive e ajustar comportamento (evitar conflitos de sincronização).
**Complexidade**: Alta
**Status**: Fase 3 (avaliação de necessidade)

### 8. Visualização de Árvore
**Descrição**: Visualização em árvore das junções, mostrando hierarquia.
**Complexidade**: Média
**Status**: Fase 2

### 9. Suporte a Batch
**Descrição**: Criar múltiplas junções de uma vez (ex: selecionar 10 pastas e migrar todas).
**Complexidade**: Baixa
**Status**: Fase 2

### 10. Linha de Comando (CLI)
**Descrição**: Versão CLI do app para automação e scripts.
**Complexidade**: Média
**Status**: Fase 2 (se houver demanda)

---

## Limitações Conhecidas

### 1. Hard Links Apenas no Mesmo Volume
Hard links só funcionam no mesmo volume físico. Isso limita o caso de uso para arquivos.

**Impacto**: Baixo - caso de uso principal é diretórios entre volumes. Para arquivos, symbolic links podem ser usados entre volumes.

**Mitigação**: Documentar limitação e usar symbolic links quando necessário.

---

### 2. Links Simbólicos Requerem Permissão
No Windows, criar links simbólicos pode requerer "Developer Mode" ou permissões especiais.

**Impacto**: Médio - pode limitar funcionalidade para usuários comuns.

**Mitigação**: Detectar disponibilidade e desabilitar funcionalidade se não disponível. Oferecer instruções para habilitar.

---

### 3. Aplicativos que Monitoram Sistema
Alguns aplicativos (antivírus, backup tools) podem reagir à criação de junções.

**Impacto**: Baixo - geralmente benigno, mas pode causar avisos.

**Mitigação**: Documentar e informar usuário.

---

### 4. OneDrive e Pastas Especiais
Pastas OneDrive e algumas pastas do sistema têm comportamento especial.

**Impacto**: Médio - pode causar problemas se não tratado corretamente.

**Mitigação**: Detectar pastas especiais e avisar usuário ou limitar operações. Integração específica com OneDrive deixada para Fase 3.

---

## Resumo do Escopo MVP (Fase 1)

### Incluído
- ✅ Listagem de junções (escaneamento híbrido)
- ✅ Criação de junções (diretórios e arquivos)
- ✅ Desfazer junções (com opções de mover/duplicar)
- ✅ Histórico de operações (metadados)
- ✅ Interface Windows 11 (tema claro/escuro)
- ✅ Detecção de arquivos em uso
- ✅ Validações de segurança

### Deixado para Fase 2
- ⏳ Sincronização entre origem e destino
- ⏳ Sugestão de pastas para migrar
- ⏳ Análise de espaço
- ⏳ Batch de múltiplas junções
- ⏳ Visualização em árvore
- ⏳ Validação de integridade periódica
- ⏳ Importação/Exportação de configuração
- ⏳ CLI

### Deixado para Fase 3 (Avaliação)
- ⏳ Integração específica com OneDrive
- ⏳ Perfis de migração

---

## Próximos Passos

1. ✅ Commit inicial com documentação completa
2. Iniciar Fase 2: Infraestrutura do projeto
   - Configurar Poetry/uv para gerenciamento de dependências
   - Criar estrutura de diretórios
   - Configurar linter e formatter
   - Implementar sistema de logging
   - Implementar sistema de configuração
