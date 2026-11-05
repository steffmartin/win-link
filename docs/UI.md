# Guia de continuidade da interface

Referência vigente para evoluir o aplicativo PyQt6 sem ler todo o protótipo React. A implementação atual e seus testes são a fonte executável; este guia resume a direção visual e os comportamentos que devem ser preservados. Propostas nas Issues não são funcionalidades já entregues.

![Tela principal](imagens/tela-principal.png)

## Estrutura visual e componentes

Cabeçalho com marca, Sobre e escolha de tema; navegação lateral com Meus Links, Criar Novo, Histórico e Configurações; páginas em área central com rolagem própria; status de descoberta no rodapé. Reutilizar os componentes existentes antes de criar novos padrões.

| Responsabilidade | Código relativo a `src/winlink/` |
|---|---|
| Shell, ações, atalhos, navegação e descoberta | `ui/main_window.py` |
| Páginas e componentes responsivos compartilhados | `ui/pages.py`, `ui/components.py` |
| Lista virtualizada/cartões, dados e filtros | `ui/link_cards.py`, `ui/junction_model.py`, `ui/junction_filter.py` |
| Ícones vetoriais, tokens, paleta e estilos | `ui/icons.py`, `ui/theme.py`; recursos em `resources/ui/` na raiz |
| Criação, prévia, propriedades e reversão | `ui/dialogs/create_junction_dialog.py`, `preview_dialog.py`, `properties_dialog.py`, `undo_dialog.py` |
| Progresso e execução fora da thread gráfica | `ui/dialogs/progress_dialog.py`, `ui/operation_worker.py` |
| Histórico e configurações | `ui/dialogs/history_dialog.py`, `ui/history_actions.py`, `ui/dialogs/settings_dialog.py`, `core/config.py`, `core/history.py` |

Domínio e acesso ao disco permanecem em `core/operations.py`, `file_ops.py`, `validators.py`, `process_manager.py`, `scanner.py` e `cache.py`. Workers comunicam resultados por sinais Qt; não bloquear a thread gráfica. Os mecanismos do domínio são JUNCTION, SYMLINK e HARDLINK; a apresentação distingue symlink de arquivo/diretório.

## Aparência

- Fonte do sistema, preferindo Segoe UI no Windows. Referência visual: corpo 14–16 px, títulos 20–24 px em negrito e caminhos em monospace. Respeitar métricas e escala do Qt; não fixar alturas que cortem texto.
- Espaçamentos de referência: 4, 8, 12, 16, 24 e 32 px; margens centrais de 24 px; bordas finas e cantos de 6–12 px. Usar layouts flexíveis e componentes compartilhados.
- Sidebar atual: 256 px em desktop e 192 px abaixo de 1100 px de largura. Reutilizar o comportamento responsivo implementado; não impor largura mínima que force a janela a exceder a tela.
- Criação usa quatro cartões em grade 2×2 na largura adequada; adaptar colunas e ações ao espaço disponível. Configurações acompanham a largura disponível, com textos explicativos curtos e controles alinhados. Histórico pode rolar sua tabela horizontalmente quando necessário.
- Ícones vetoriais consistentes com `ui/icons.py`, acompanhados de rótulo ou descrição acessível. Não substituir por emojis nem criar outro sistema visual.

Usar `ThemeColors`, `ThemeManager` e os estilos existentes como fonte de cores, sem espalhar novas cores fixas nos widgets:

| Token | Claro | Escuro |
|---|---|---|
| Fundo | `#FFFFFF` | `#111827` |
| Superfície | `#f9fafb` | `#1f2937` |
| Superfície alternativa | `#f3f4f6` | `#374151` |
| Primária | `#2563eb` | `#2563eb` |
| Texto | `#111827` | `#FFFFFF` |
| Texto secundário | `#5C5C5C` | `#D0D0D0` |
| Borda | `#d1d5db` | `#4b5563` |
| Sucesso / aviso / erro | `#107C10` / `#9B8F06` / `#C42B1A` | `#6CCB6F` / `#E2D868` / `#FF8A80` |

Estados normal, hover, foco, seleção e desabilitado precisam continuar legíveis nos dois temas. Cor não pode ser o único indicador de resultado. Seguir sistema deve reagir ao tema do Windows; a troca rápida deve respeitar a preferência persistida e a opção automática.

## Fluxos e estados que devem permanecer

| Área | Contrato de interação |
|---|---|
| Lista | Cartões e visão compacta; busca nos dois caminhos; filtros combinados de criador, status e tipo; ordenação crescente/decrescente; distinguir lista vazia de ausência de resultados. |
| Descoberta | Atualizar/F5 repete scan; **Limpar** fica ao lado de **Filtros**, limpa busca/filtros e atualiza; mantém a ordenação. Cache pode ser mostrado durante atualização; falha parcial não apaga dados válidos. Indicar quando a lista pode estar desatualizada. |
| Filtros | Filtros e ordenação editam rascunho; Aplicar confirma; Cancelar/X/Escape/clique fora descartam. Preferência de filtro inicial é proposta em Issue, ainda não um contrato implementado. |
| Criação | Labels explícitos, seleção adequada de arquivos/pastas, validações reais e tipo padrão persistente. Prévia mostra os caminhos completos e o efeito de migração antes de confirmar. |
| Prévia | Informar espaço necessário/disponível, conflitos, aninhamento e processos bloqueadores. Não confirmar enquanto cálculo obrigatório estiver pendente, houver espaço insuficiente ou bloqueios impeditivos. |
| Progresso | Executar em worker; distinguir executando, cancelando/preservando, cancelado, falha, sucesso e sucesso com aviso. Cancelamento é cooperativo: aguardar a preservação antes de liberar nova operação. |
| Propriedades | Caminhos completos, criador, data, estatísticas, indisponível/calculando e recalcular. Abrir pasta usa integração nativa; Reverter usa o mesmo fluxo protegido das demais entradas. |
| Reversão | Revalidar identidade; diretórios oferecem remover link, mover de volta ou duplicar, com opção de backup. Arquivos removem somente o nome verificado. Não interpretar inacessível como vazio ou tamanho zero. |
| Histórico | Distinguir operação e tipo de link; combinar resultado e datas inclusivas; marcar criação já desfeita; exportar todos os registros independentemente dos filtros. Limpar exige confirmação e não modifica links. |
| Configurações | Salvar persiste; Restaurar padrões prepara rascunho; Descartar recarrega o salvo. Os modos normal e compacto ajustam a densidade da página durante a sessão e preservam o rascunho. Manter compatibilidade com preferências antigas e não apagar histórico/log personalizados ao restaurar preferências. |

Durante operações, preservar os bloqueios existentes contra ações conflitantes. Distinguir falha principal de falha apenas ao registrar histórico: uma criação bem-sucedida com erro no registro não deve incentivar repetição. Se a restauração já ocorreu e a limpeza falhou, informar os caminhos restaurado e preservado e orientar conferência, sem sugerir repetir a reversão.

## Linguagem e acessibilidade

Usar português claro e ações com verbos. Usar **Ponto de Acesso** para o caminho do link e **Dados Físicos** para o local dos dados. A criação apresenta Ponto de Acesso primeiro e Dados Físicos depois, sem alterar os parâmetros dos serviços. Exemplo: Dados Físicos em `D:\Dados\Projetos`, Ponto de Acesso em `C:\Links\Projetos`. Na migração, explicar separadamente onde os dados estão antes e onde ficarão depois. Hard links são nomes equivalentes dos mesmos dados, não uma cópia nem um atalho comum.

Mostrar ambos os caminhos completos nas propriedades, prévia e confirmação. Truncar apenas na lista, mantendo acesso ao valor completo. Mostrar caminhos de backup e recuperação; explicar necessidade de permissões sem prometer elevação automática.

Preservar Tab/Shift+Tab, foco visível, labels associados aos campos, nomes acessíveis e Escape nos diálogos. Ao fechar, devolver foco ao controle de origem quando existir. Usar semântica e controles Qt, sem reproduzir atributos ARIA de HTML. Diálogos precisam permitir alcançar o último controle por rolagem e manter botões de confirmação acessíveis.

Atalhos existentes: Ctrl+N criar, Ctrl+H histórico, Ctrl+, configurações, Ctrl+F buscar, F5 atualizar e Ctrl+Q sair. Não registrar atalhos duplicados ao reconstruir páginas ou trocar tema.

## Validação de alterações de UI

1. Executar os quatro checks definidos em [AGENTS.md](../AGENTS.md). Acrescentar regressão de comportamento/layout quando a alteração justificar, especialmente para clipping, foco e recuperação.
2. Conferir as páginas e diálogos afetados nos temas claro/escuro/sistema, janela 1280×800 e janela reduzida 760×400, respeitando a área disponível do monitor.
3. Para mudanças de layout, executar `QT_SCALE_FACTOR=2` em processo novo. Em PowerShell, definir `$env:QT_SCALE_FACTOR = '2'` e executar `.venv\Scripts\python.exe -m pytest -q tests/test_ui_layout.py`; ao concluir, restaurar o valor anterior da variável.
4. Conferir teclado, caminhos longos, ausência de resultados, erros e avisos pertinentes; rolagem deve alcançar os últimos controles sem comprimir ou cortar os filhos. Reutilizar `tests/test_ui_layout.py`, `test_ui_main_window.py`, `test_ui_theme.py` e testes de workers/falhas conforme o caso.
5. Capturar o aplicativo real com `.venv\Scripts\python.exe scripts/capture_ui.py` quando precisar de evidência visual. Saída padrão em `build/ui-review`, ignorada pelo Git; não sobrescrever o arquivo histórico. Atualizar a imagem do README somente se a mudança tornar a captura vigente obsoleta.

Referências visuais adicionais: [capturas arquivadas](arquivo/v0.1.0/validacao/REDESIGN.md). Só se uma dúvida específica continuar sem resposta, consultar o componente necessário do [protótipo](arquivo/v0.1.0/prototypes/ui/README.md). Não transportar fixtures, temporizadores ou integrações fictícias do React para produção.
