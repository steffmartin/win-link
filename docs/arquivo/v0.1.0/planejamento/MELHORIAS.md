# Melhorias — escopo aprovado e evolução

## Implementadas na etapa 6.6

O usuário autorizou manter estas novidades no protótipo e implementá-las nas próximas fases do aplicativo. Entregues no PyQt6; evidências em [REDESIGN.md](../validacao/REDESIGN.md):

1. Preferência persistente de tipo de link padrão, compatível com configuração antiga.
2. Restaurar padrões e descartar alterações nas configurações; restaurar não salva automaticamente.
3. Filtro do histórico por resultado e intervalo manual de datas, além de operação/períodos existentes.
4. Distinção de symlink de arquivo/diretório na apresentação e nos filtros.
5. Alternância rápida de tema no cabeçalho, mantendo modo Seguir sistema.
6. Detalhes e indicação explícita de criação já desfeita, sem permitir repetir reversão.
7. Acesso à reversão pelas propriedades, preservando confirmações e verificação de identidade.

Detalhamento visual/técnico: [guia de implementação](../guias/IMPLEMENTACAO-UI.md). Critérios e ordem: [plano](PLANO.md).

## Fora do escopo atual — ideias a avaliar

Estas propostas foram preservadas dos estudos históricos para não perder decisões, mas **não são funcionalidades entregues nem tarefas aprovadas para a etapa 6.6**:

- Scan inverso: encontrar links que apontam para determinado local de dados.
- Importar/exportar configuração de links (distinto da exportação do histórico), importar scripts e adicionar link conhecido manualmente.
- Alterar destino, reconstruir links e sincronizar árvores com política de conflitos a definir.
- Monitoramento automático/periódico e invalidação de cache por eventos.
- Encerrar processos automaticamente e elevação automática por operação.
- Sugestões/análise de espaço, templates e perfis de migração.
- Visualização em árvore, operações em lote e CLI de automação.
- Integração com OneDrive/pastas especiais e compressão de destinos.
- Menu do Explorer, iniciar com Windows, tradução para inglês e atualizações automáticas.

Cache de descoberta, histórico JSON e suporte a arquivos já existem; não tratá-los como novidades pendentes. As versões antigas usavam “Fase 2/3” também como gerações do produto; não reutilizar essa numeração para priorizar o plano atual.
