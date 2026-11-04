# Implementação do protótipo no WinLink

Este é o guia vigente para portar o protótipo React para o aplicativo Python/PyQt6. A direção visual foi aprovada pelo usuário; a cobertura da interface existente e as melhorias propostas foram incorporadas à demo. O redesign ainda não foi implementado no aplicativo real.

## Referências e ponto de retomada

- [Demo e comandos](../../prototypes/ui/README.md): fonte visual executável e editável.
- [Plano, etapa 6.6](../planejamento/PLANO.md): ordem de trabalho e critérios de entrega.
- [Regras do produto](../produto/ESPECIFICACAO.md): comportamento que deve ser preservado.
- [Melhorias aprovadas e ideias fora do escopo](../planejamento/MELHORIAS.md).
- [Distribuição](../arquitetura/DISTRIBUICAO.md) e [evidências/pendências da fase 5](../validacao/FASE5.md).

Retomar pela etapa 6.6; não refazer estudos nem buscar versões anteriores do protótipo. O protótipo e a demo ficam em `prototypes/ui`, sem nomes de agente ou número de versão no caminho. Consulte a [estrutura do projeto](../arquitetura/ESTRUTURA.md) antes de acrescentar arquivos.

## Fonte de verdade

O React especifica aparência, navegação e estados. As regras de arquivo, identidade de links, preservação, cópia, backup e rollback devem continuar nos serviços Python. Não portar timers, fixtures, validadores simplificados ou controles de simulação como operações de produção. Quando houver divergência, manter a proteção real e ajustar a apresentação.

O aplicativo atual usa três tipos de domínio: JUNCTION, SYMLINK e HARDLINK. Os quatro cartões do protótipo distinguem symlinks de arquivo/diretório na interface; não criar um quarto mecanismo no domínio.

## Cobertura que deve permanecer acessível

| Lacuna identificada | Representação agora disponível |
|---|---|
| Criador e filtro | App, Existente e Manual nos cards, propriedades e diálogo de filtros |
| Status Inacessível | Exemplos de diretório e arquivo, filtro, estatísticas indisponíveis e bloqueio de remoção sem identidade |
| Tamanho e ordenação | Tamanho ilustrativo por card; ordenar por origem/destino/criador/tipo/tamanho/status, crescente/decrescente |
| Atualização e cache inicial | Atualizar/F5, Início limpa busca/filtros e atualiza; simular abertura com cache mantém a lista durante atualização |
| Abrir caminhos | Abrir origem/destino demonstra Explorer e aviso de caminho indisponível, sem abrir arquivos reais |
| Propriedades completas | Criador, data/hora, tamanho, arquivos/pastas, calculando/indisponível e recalcular |
| Capacidade na prévia | Necessário/disponível fictícios, cálculo pendente e confirmação bloqueada quando insuficiente para migração |
| Links aninhados e processos | Cenários da prévia mostram caminhos, processos/PIDs e orientação de fechamento manual; liberação simulada de processos |
| Reversão com estados | Progresso, cancelamento, falha de cópia/espaço/alteração externa/limpeza e retorno; restauração parcial informa destino restaurado e origem preservada, sem sugerir repetir |
| Links de arquivo | Só remoção do nome; falha de permissão e identidade alterada preservam estado; origem indisponível bloqueia remoção |
| Histórico por operação | Operação separada de tipo de link; opções de criação, desfazer, remover, mover e copiar; exemplos carregáveis sem alterar links |
| Períodos e totais | Hoje/última semana/último mês, intervalo personalizado e total filtrado/geral |
| Falhas do histórico | Cenários de erro ao limpar/exportar mantêm registros e orientam tentar novamente; sucesso continua exportando JSON |
| Tema automático | Seguir sistema salvo e reagindo a mudanças de preferência do sistema/navegador |
| Descoberta configurável | Adicionar via seletor fictício, remover cada diretório, editar lista e exigir pelo menos um caminho absoluto |
| Logs | Abrir pasta de logs demonstrativo com sucesso/aviso de pasta inexistente |
| Confirmação obrigatória | Informação explícita nas preferências, marcada e desabilitada |
| Sobre e atalhos | Sobre com versão/descrição/atalhos; Ctrl+N, Ctrl+vírgula, Ctrl+H, Ctrl+F, F5 e Ctrl+Q demonstrativo |


## Melhorias novas aprovadas

Implementar na etapa 6.6: tipo de link padrão persistente, restaurar padrões/descartar rascunho, filtro do histórico por resultado e datas manuais, distinção de symlinks arquivo/diretório nos filtros, troca rápida de tema, detalhes/estado explícito de criação desfeita e reversão pelas propriedades. Estas capacidades não devem ser anunciadas como já implementadas no PyQt6. [Backlog detalhado](../planejamento/MELHORIAS.md).

## Aparência e componentes

## Tokens visuais

Fonte: sans do sistema (Segoe UI no Windows), corpo 14–16 px, títulos 20–24 px em peso 700; caminhos em monospace. Escala de espaçamento: 4, 8, 12, 16, 24 e 32 px. Raios: 6–12 px; bordas 1 px. Sidebar 256 px em desktop, 192 px intermediário e 145 px em janela reduzida. Conteúdo flexível com rolagem independente; histórico admite rolagem horizontal da tabela. Janelas reduzidas conferidas: 760 × 400 px e 1280 × 500 px.

Claro: fundo #ffffff, superfícies #f9fafb/#f3f4f6, texto #111827, bordas #d1d5db. Escuro: fundo/sidebar #111827, superfícies #1f2937/#374151, texto #f3f4f6, bordas #4b5563. Ação primária #2563eb; foco #3b82f6; sucesso verde, aviso âmbar e falha vermelho, acompanhados de texto/ícone. Tons secundários seguem a escala gray do Tailwind 3. Preferência por movimento reduzido é respeitada.

## Comportamento dos componentes

Botões: normal, hover, foco com anel de 2 px e offset 3 px, disabled com opacidade. Durante criação/cancelamento, navegação de operações bloqueada. Campos: label, borda, foco e mensagens de validação; nenhum sobrescrito automático. Caminhos completos nas propriedades/confirmações; truncamento com título somente na lista.

Diálogos: nome acessível, role dialog, aria-modal, foco inicial, Tab/Shift+Tab contidos, Escape fecha e restaura foco quando o controle ainda existe. Fundo da aplicação inerte. Conteúdo com rolagem até 90% da altura. Estratégias de reversão usam radios nativos visíveis.

Estados: lista normal/compacta/vazia/filtrada, atualização com cache preservado e tentativa novamente; criação simples/migração/validação; progresso, cancelando/preservando, cancelado, falha, sucesso, sucesso com backup e sucesso com falha do registro. Histórico combina tipo/resultado/período inclusivo; exporta todos os registros, independentemente dos filtros. Limpar exige confirmação e mantém os links.

## Textos e limites

Usar “Local dos dados” e “Caminho do novo link”. Hard links são nomes equivalentes dos mesmos dados; remover um nome preserva os demais. Symlinks podem exigir Modo de Desenvolvedor ou permissões apropriadas. Cancelamento é apresentado como resultado próprio. Falha no histórico não significa falha da criação e orienta não repetir a operação. Backup preservado informa caminho fictício para conferência.

Preferências persistem somente no localStorage deste navegador. Dados da sessão (links/histórico/caminhos) reiniciam ao recarregar. Salvar aplica tema/tipo padrão/backup; descoberta, notificações, avisos e logs são valores demonstrativos para a futura implementação. Integração com o menu do Explorer, inicialização com Windows e monitoramento automático estão fora do escopo. Nenhum seletor lê o disco; somente a exportação JSON gera um download solicitado pelo usuário.

## Mapeamento PyQt6

Layout geral → QMainWindow + layouts / QListWidget para navegação / QStackedWidget para páginas. Lista e histórico → modelos Qt com QTableView ou cards em QScrollArea; filtros → QSortFilterProxyModel. Formulário → QLineEdit/QComboBox/QFileDialog (arquivos existentes e novos nomes com modos distintos). Confirmações → QDialog modal com foco/tab order; progresso → QProgressBar e worker com sinais, sem bloquear a UI. Preferências → SettingsDialog e configuração existente, preservando validações reais. Tema → tokens/QPalette/QSS, cobrindo sidebar e diálogos. Reusar os serviços do aplicativo; não transportar temporizadores nem regras simplificadas da demo para operações reais.


## Integração com o código real

| Responsabilidade | Arquivos/serviços a reutilizar |
|---|---|
| Shell, navegação, ações, atalhos, descoberta | `src/winlink/ui/main_window.py` |
| Dados, filtros, ordenação | `ui/junction_model.py`, `ui/junction_filter.py` |
| Criação e confirmação | `ui/dialogs/create_junction_dialog.py`, `preview_dialog.py` |
| Progresso e trabalho fora da thread gráfica | `ui/dialogs/progress_dialog.py`, `ui/operation_worker.py` |
| Propriedades e estatísticas | `ui/dialogs/properties_dialog.py` |
| Histórico, exportação e reversão | `ui/dialogs/history_dialog.py`, `undo_dialog.py`, `core/history.py` |
| Tema, configurações e persistência | `ui/theme.py`, `ui/dialogs/settings_dialog.py`, `core/config.py` |
| Operações/validação de arquivos | `core/operations.py`, `file_ops.py`, `validators.py`, `process_manager.py` |
| Scanner/cache | `core/scanner.py`, `core/cache.py` |

Caminhos abreviados da tabela são relativos a `src/winlink`. Manter histórico/configurações anteriores compatíveis. Não substituir operações reais por lógica React. Explorer, seletores e logs devem usar as integrações nativas existentes; nenhuma dessas ações abre arquivos reais na demo.

## Regras de interação e recuperação

- Filtros da lista usam rascunho: Aplicar confirma; Cancelar/X/Escape/clique fora descartam. Inputs com labels acima e botões formatados nos dois temas.
- Preservar o espaçamento de 24 px entre cenário da atualização e lista na demo. Produção não deve mostrar controles de cenário.
- Cada página tem rolagem própria sem comprimir filhos; último controle deve ser alcançável. Diálogos têm rolagem independente até 90% da altura.
- Tema Seguir sistema reage ao esquema do host; troca manual substitui o modo automático na sessão até novo salvamento. No aplicativo usar QPalette/QSS e a configuração real.
- Cancelamento tem estado intermediário de preservação; não exibir como erro genérico. Confirmação de operação destrutiva permanece obrigatória.
- Não permitir remover um nome de arquivo se a identidade não puder ser verificada. Não tratar origem inacessível como tamanho zero.
- Prévia bloqueia confirmação durante cálculo, falta de espaço ou processos ainda bloqueando; informar espaço necessário/disponível e avisos de aninhamento.
- Desfazer distingue falha com link/originais preservados e restauração já feita com origem mantida após falha na limpeza. Informar os locais e evitar orientar repetição perigosa.
- Backup preservado e falha somente no histórico são resultados distintos de falha da operação principal.
- Histórico diferencia tipo de operação e tipo de link. Exportação usa todos os registros, independentemente dos filtros. Limpar exige confirmação e mantém os links.
- Notificações, avisos de aninhamento e logs são preferências demonstrativas no React; integrar seu comportamento real na implementação.

## Validação e entrega

Última validação registrada da demo: 74 testes de regras passaram, build passou e scripts de navegador verificaram os quatro tipos, criação/reversão/backup, falhas/recuperação, filtros, diretórios, tema automático, logs, atalhos e Sobre. Scripts estão em `prototypes/ui/tests`; funções `browser-*.js` recebem uma página Playwright e precisam desse runner. Não são executadas por `npm test`.

Rolagem conferida em 760×400 e 1280×500; cores nos dois temas; lista revisada visualmente. Isso não equivale a auditoria com leitor de tela ou homologação Windows.

Para a implementação, executar testes Python, verificações de estilo/tipos e cenários reais isolados de criação/reversão. Testar diretórios/arquivos, quatro tipos, conflitos, inacessíveis, mudanças externas, cancelamento, backup, erros de histórico e migração de configurações. Revalidar teclado, foco, caminhos longos, alta escala e acesso aos últimos controles. Homologação externa da fase 5 continua pendente.

## Organização documental

Estudos, versões recebidas do agente, comparações antigas, checkpoints intermediários, prints da interface anterior e o ZIP de envio foram removidos após consolidação. Código final da demo, testes e este guia substituem esses materiais; não recriar um pacote de handoff externo para a implementação local.
