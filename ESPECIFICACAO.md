# Especificação vigente — WinLink

## Produto e stack

Aplicativo Windows em Python 3.12+/PyQt6, com pywin32, psutil, pydantic e configurações JSON. O React/Vite/Tailwind é somente o protótipo de referência do redesign. Dependências e ferramentas vigentes: `pyproject.toml` e `prototypes/agente-externo-v1/package.json`. Não migrar para stacks alternativas discutidas em estudos antigos.

Origem/local dos dados é onde o conteúdo reside. Destino/caminho do link é o nome de acesso que aponta para ele. Hard links são nomes equivalentes dos mesmos dados, sem origem privilegiada; exigem o mesmo volume. Symlinks dependem do Modo de Desenvolvedor ou permissões apropriadas do Windows.

## Escopo implementado no aplicativo atual

| Requisito | Comportamento vigente |
|---|---|
| RF-01/02 Descoberta | Varredura dos diretórios configurados, cache inicial e atualização nova em background; não promete descobrir todo o disco sem configurar as raízes |
| RF-03 Lista | Origem/destino, criador App/Existente/Manual, tipo, tamanho quando disponível, status Ativo/Quebrado/Inacessível; busca, filtros e ordenação |
| RF-04/05 Criação | Junction de diretório, symlink de diretório/arquivo e hard link; pasta de dados pode ser criada para diretórios; arquivos exigem origem existente e novo nome livre |
| RF-06 Validação/prévia | Caminhos, identidade, conflitos, espaço, processos e avisos de aninhamento; confirmação obrigatória antes de executar |
| RF-07 Desfazer | Remover somente o link, mover de volta, duplicar e manter origem como backup; links de arquivo removem somente o nome selecionado |
| RF-09 Integridade | Verificada na descoberta e antes de desfazer, incluindo referência do histórico; sem monitoramento periódico entregue |
| RF-10 Arquivos | Criação/descoberta/propriedades de hard links e symlinks de arquivo; não representar junctions como mecanismo de arquivo |
| RF-11 Processos | Detecção e aviso para fechar manualmente; sem encerramento automático na interface entregue |

Propriedades mostram criador, data, caminhos, estatísticas assíncronas e histórico relacionado; abrem origem/destino no Explorer. Histórico registra operações, filtra, exporta JSON, limpa com confirmação e permite desfazer criação específica após revalidar integridade. Preferências persistem tema auto/claro/escuro, diretórios, backup, notificações, avisos e logs. Confirmação destrutiva permanece obrigatória. Atalhos e Sobre fazem parte da aplicação.

## Preservação, concorrência e recuperação

- Não substituir um link existente nem sobrescrever conflitos automaticamente.
- Ao migrar uma pasta anterior, copiar/preservar conteúdo, conferir identidade/alterações, manter backup e só então publicar o link.
- Uma operação mutável por vez. Usar worker/QThread e sinais; não bloquear a thread gráfica.
- Cancelamento cooperativo deve preservar originais e limpar temporários quando possível, informando os locais preservados se falhar.
- Não remover nome de arquivo sem verificar identidade; origem indisponível não autoriza ignorar essa proteção.
- Reversão deve diferenciar originais preservados, arquivos já restaurados e falha de limpeza. Não sugerir repetir operação concluída parcialmente.
- Falha apenas ao gravar histórico não significa falha da criação; impedir repetição inadvertida.
- Verificações contra alterações externas não equivalem a snapshot transacional; não prometer garantia absoluta contra toda corrida de filesystem.
- Testes reais usam diretórios temporários isolados, nunca pastas pessoais como dados descartáveis.

## Requisitos de interface e desempenho

Dois temas mais modo automático, teclado/foco, labels, mensagens em português, caminhos legíveis, alta escala e rolagem integral. Operações/estatísticas/scan em background. Cache atômico vinculado às raízes, seguido de varredura atualizada. Diminuir trabalho inicial; tamanhos de árvores sob demanda. Preservar compatibilidade de configurações e histórico entre versões.

## Próxima entrega e limites

O redesign mantém esse escopo e incorpora as novidades autorizadas em [MELHORIAS.md](MELHORIAS.md). Aparência, cobertura e mapeamento estão no [guia de implementação](docs/IMPLEMENTACAO-UI.md). RF-08 (editar/reconstruir/sincronizar), importação, templates, monitoramento periódico, terminação de processos e elevação automática são propostas históricas fora da entrega atual, não funcionalidades omitidas por acidente do redesign.

Windows 11 foi usado na validação local; Windows limpo, Windows 10 e sucesso real de symlinks com permissões apropriadas ainda precisam de homologação. Ver [evidências](docs/validacao/FASE5.md). Não anunciar lançamento aprovado antes de fechá-las.
