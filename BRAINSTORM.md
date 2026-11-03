# Brainstorming e Dúvidas - WinLink

## Dúvidas para Esclarecimento

### 1. Stack Tecnológico
Qual stack tecnológico você prefere?

**Opções**:
- **Rust + Tauri** (Recomendado): Performance, segurança, binário pequeno
- **C# + WinUI 3**: Nativo Windows, desenvolvimento rápido, interface moderna oficial
- **Python + PyQt6**: Desenvolvimento muito rápido, ecossistema grande
- **Go + Wails**: Simples, single binary, similar ao Tauri

**Minha recomendação**: Rust + Tauri, pois oferece o melhor equilíbrio de performance, segurança e portabilidade, e você já tem experiência com análise de sistemas de baixo nível.

---

### 2. Escopo de Arquivos vs Diretórios

A especificação menciona suporte a junção de arquivos, mas o Windows tem limitações:

**Perguntas**:
- É essencial suportar hard links de arquivos, ou podemos focar apenas em diretórios inicialmente?
- Links simbólicos de arquivos são importantes, ou podemos focar em junctions de diretórios?

**Minha sugestão**: Fase 1 foca em diretórios (caso de uso principal). Se sobrar tempo, adicionamos suporte a arquivos em Fase 2.

---

### 3. Descoberta Automática de Junções

**Perguntas**:
- Escanear todo o sistema pode ser demorado. Devemos:
  - Escanear apenas diretórios específicos (ex: C:\Users, D:\Cache)?
  - Permitir que o usuário configure quais diretórios escanear?
  - Ter modo "escaneamento completo" opcional?

**Minha sugestão**: Escaneamento padrão em diretórios configuráveis (C:\Users, D:\Cache), com opção de escaneamento completo manual.

---

### 4. Classificação de "Criador"

A especificação define 4 categorias: App, Existente, SO, Usuário.

**Perguntas**:
- Como diferenciar "SO" de "Usuário"? Ambos podem ter criado manualmente.
- Devemos tentar detectar via logs do Windows, ou é suficiente classificar tudo que não foi criado pelo app como "Existente"?

**Minha sugestão**: Classificação simplificada:
- **App**: Criado pelo WinLink
- **Existente**: Já existia antes do WinLink (detectado na primeira execução)
- **Manual**: Criado após WinLink estar instalado (pode ser SO ou usuário)

---

### 5. Integração com Script Existente

**Perguntas**:
- O WinLink deve importar configurações do script `migrar_pastas.ps1`?
- Devemos manter compatibilidade para que ambos possam coexistir?
- Ou o WinLink deve substituir completamente o script?

**Minha sugestão**: Coexistência pacífica. WinLink detecta junções criadas pelo script como "Existente" e permite gerenciá-las.

---

### 6. Operações de Sincronização

A especificação menciona sincronização entre origem e destino.

**Perguntas**:
- É realmente necessário? O caso de uso principal é apenas mover pastas para outro disco.
- Se sim, qual estratégia padrão? Mais recente vence? Origem tem prioridade?
- Isso pode ser uma funcionalidade avançada para fase posterior?

**Minha sugestão**: Deixar para Fase 2. Fase 1 foca em criar/desfazer junções.

---

### 7. Backup Automático

A especificação menciona backup automático antes de operações destrutivas.

**Perguntas**:
- Onde armazenar backups? Pasta dedicada?
- Por quanto tempo manter backups?
- Limite de espaço para backups?

**Minha sugestão**: Backup apenas de metadados (lista de operações), não de arquivos completos (muito espaço). Para desfazer, oferecemos opção de mover arquivos de volta.

---

### 8. Elevação de Permissões

Algumas operações requerem administrador.

**Perguntas**:
- O app deve solicitar elevação apenas quando necessário, ou deve sempre rodar como admin?
- Devemos ter modo "leitura apenas" sem elevação?

**Minha sugestão**: App roda sem elevação por padrão. Solicita elevação apenas quando usuário tenta operação que requer admin.

---

## Funcionalidades Adicionais Sugeridas

### 1. Sugestão de Pastas para Migrar
**Descrição**: Analisar perfil do usuário e sugerir pastas que poderiam ser migradas (ex: pastas grandes em C:\Users).

**Benefício**: Descoberta guiada para usuários que não sabem quais pastas migrar.

**Complexidade**: Média

---

### 2. Análise de Espaço
**Descrição**: Mostrar quanto espaço seria economizado se determinadas pastas fossem migradas.

**Benefício**: Ajuda usuário a decidir quais pastas migrar.

**Complexidade**: Baixa

---

### 3. Perfis de Migração
**Descrição**: Perfis predefinidos (ex: "Desenvolvedor", "Gamer", "Geral") que sugerem conjuntos de pastas para migrar.

**Benefício**: Usuário menos técnico pode escolher perfil e aplicar.

**Complexidade**: Média

---

### 4. Histórico de Operações
**Descrição**: Log de todas as operações realizadas com opção de desfazer.

**Benefício**: Segurança e rastreabilidade.

**Complexidade**: Média

---

### 5. Validação de Integridade Periódica
**Descrição**: Verificar periodicamente se junções estão funcionais.

**Benefício**: Detectar problemas proativamente.

**Complexidade**: Média

---

### 6. Importação/Exportação de Configuração
**Descrição**: Exportar lista de junções para arquivo JSON e importar em outro computador.

**Benefício**: Backup e migração de configuração entre máquinas.

**Complexidade**: Baixa

---

### 7. Integração com OneDrive
**Descrição**: Reconhecer pastas OneDrive e ajustar comportamento (evitar conflitos de sincronização).

**Benefício**: Evita problemas com sincronização do OneDrive.

**Complexidade**: Alta

---

### 8. Visualização de Árvore
**Descrição**: Visualização em árvore das junções, mostrando hierarquia.

**Benefício**: Melhor entendimento de estrutura complexa.

**Complexidade**: Média

---

### 9. Suporte a Batch
**Descrição**: Criar múltiplas junções de uma vez (ex: selecionar 10 pastas e migrar todas).

**Benefício**: Eficiência para operações em massa.

**Complexidade**: Baixa

---

### 10. Linha de Comando (CLI)
**Descrição**: Versão CLI do app para automação e scripts.

**Benefício**: Integração com scripts existentes e automação.

**Complexidade**: Média

---

## Limitações Conhecidas

### 1. Hard Links Apenas no Mesmo Volume
Hard links só funcionam no mesmo volume físico. Isso limita o caso de uso para arquivos.

**Impacto**: Baixo - caso de uso principal é diretórios entre volumes.

---

### 2. Links Simbólicos Requerem Permissão
No Windows, criar links simbólicos pode requerer "Developer Mode" ou permissões especiais.

**Impacto**: Médio - pode limitar funcionalidade para usuários comuns.

**Mitigação**: Detectar disponibilidade e desabilitar funcionalidade se não disponível.

---

### 3. Aplicativos que Monitoram Sistema
Alguns aplicativos (antivírus, backup tools) podem reagir à criação de junções.

**Impacto**: Baixo - geralmente benigno, mas pode causar avisos.

**Mitigação**: Documentar e informar usuário.

---

### 4. OneDrive e Pastas Especiais
Pastas OneDrive e algumas pastas do sistema têm comportamento especial.

**Impacto**: Médio - pode causar problemas se não tratado corretamente.

**Mitigação**: Detectar pastas especiais e avisar usuário ou limitar operações.

---

## Decisões Pendentes

Por favor, responda às seguintes perguntas para que eu possa ajustar o plano:

1. **Stack tecnológico**: Qual você prefere? (Rust + Tauri, C# + WinUI 3, Python + PyQt6, Go + Wails, ou outro?)

2. **Escopo inicial**: Focar apenas em diretórios (Fase 1) ou incluir arquivos desde o início?

3. **Descoberta automática**: Escanear apenas diretórios configuráveis ou sistema completo?

4. **Classificação de criador**: Classificação simplificada (App/Existente/Manual) ou detalhada (App/Existente/SO/Usuário)?

5. **Sincronização**: Incluir na Fase 1 ou deixar para Fase 2?

6. **Backup**: Backup de metadados ou backup completo de arquivos?

7. **Elevação**: Solicitar sob demanda ou sempre rodar como admin?

8. **Funcionalidades adicionais**: Quais das sugeridas você gostaria de incluir? (Pode marcar múltiplas)

9. **Protótipo visual**: O design proposto está OK ou você quer alterações?

10. **Prioridade**: Qual funcionalidade é mais importante para você?

---

## Próximos Passos

Após suas respostas:
1. Ajustarei especificação e plano conforme suas escolhas
2. Atualizarei TECNOLOGIAS.md com a decisão final
3. Farei commit inicial do projeto
4. Iniciarei Fase 2 (Infraestrutura)
