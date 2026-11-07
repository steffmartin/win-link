# Guia de uso do WinLink

## Instalar e abrir

Baixe o instalador offline ou o ZIP portátil na [release indicada no README](../README.md#baixar-e-começar). Extraia toda a pasta `WinLink` do ZIP, incluindo `_internal`. Não precisa de Python instalado para executar o pacote; a validação em outro Windows sem Python foi dispensada pelo mantenedor. O aplicativo é por usuário e não solicita elevação automática. Código sob licença MIT; pacote sem assinatura digital.

## Encontrar links

Em **Configurações**, escolha pelo menos uma pasta absoluta para descoberta e salve. **Meus Links** abre na apresentação salva em **Configurações**. O modo normal exibe cartões e o compacto exibe uma tabela. O seletor da lista permite alternar temporariamente. A busca procura nos dois caminhos. **Filtros** abre um dropdown compacto para cada grupo: status, criador, tipo e tag, distinguindo symlinks de arquivo/diretório. Abra um dropdown para marcar ou desmarcar opções; todas começam marcadas. Em Tags, **(Vazio)** seleciona links sem tags e pode ser combinado com nomes de tags. Seleções dentro de um grupo combinam-se por união (qualquer valor marcado) e grupos diferentes por interseção. Aplicar confirma o rascunho; Cancelar, X ou Escape descartam. A ordenação fica no mesmo diálogo e inclui caminhos, criador, tipo, tamanho e status; também segue Aplicar/Cancelar. Tamanho indisponível não significa pasta vazia. Clique duas vezes ou use Enter para propriedades; o menu de contexto também permite desfazer.

O cache acelera a abertura e uma varredura nova atualiza a lista. **Atualizar/F5** repete a descoberta. Para remover os critérios de filtro, use **Limpar filtros** na janela **Filtros**; a busca é independente e permanece como digitada. Se a atualização falhar, confira o aviso e os diretórios, depois tente novamente. Uma lista preservada pode estar desatualizada; cada reversão verifica novamente o link.

Se você fechar o WinLink durante a descoberta, ele solicita o cancelamento e fecha assim que a varredura parar. Os links já encontrados complementam o cache anterior da mesma seleção de pastas. A próxima abertura inicia uma nova varredura.

### Pastas incluídas e excluídas

Em **Configurações**, adicione as raízes em **Pastas incluídas** e use **Pastas excluídas** para pular diretórios inteiros. Por exemplo, incluir `C:/` e excluir `C:/tmp` percorre as demais subpastas de `C:/`. Uma exclusão prevalece mesmo se a pasta ou uma de suas subpastas também estiver na lista de inclusão. Um link cujo próprio caminho esteja excluído também é omitido.

Configurações antigas sem uma lista de exclusões recebem os padrões, a pasta temporária e a pasta do Windows quando disponíveis. Revise ou remova essas entradas conforme precisar. **Restaurar Padrões** repõe a lista padrão no rascunho, **Descartar alterações** recupera a lista salva e **Salvar Alterações** aplica a seleção à descoberta. Uma lista vazia salva é preservada.

## Criar

Em **Criar Novo**, escolha Junction, Symlink (Dir), Symlink (File) ou Hardlink. O ícone no canto de cada cartão abre a ajuda sobre aquele tipo. **1. Ponto de Acesso** é o caminho do link; **2. Dados Físicos** é onde os dados ficam. Por exemplo: Ponto de Acesso em `C:\Links\Projetos`, Dados Físicos em `D:\Dados\Projetos`. Hard links são nomes equivalentes do mesmo arquivo, sem um nome principal; substituir o arquivo por outro pode romper essa relação. A preferência de tipo padrão vale para um formulário vazio.

Diretórios podem usar um novo local dos dados. Se o caminho do link já contiver uma pasta normal, a prévia explica a migração. Arquivos exigem dados existentes e um novo nome livre; hard links exigem o mesmo volume. Symlinks podem exigir Modo de Desenvolvedor ou privilégios apropriados. Nenhuma opção faz elevação automática.

Revise caminhos completos, espaço, processos e avisos na **Prévia**. A confirmação é obrigatória. Feche manualmente processos informados e recalcule a prévia. Operações são executadas em background. **Cancelar** solicita interrupção cooperativa; aguarde a preservação dos dados antes de fechar. Após sucesso, o progresso apresenta a conclusão sem outro diálogo de sucesso, e os campos são limpos, com o tipo padrão restaurado. Falha ou cancelamento mantém os campos para conferência.

## Propriedades e reversão

Propriedades mostra caminhos, criador, data, estatísticas e histórico relacionado. **Recalcular** atualiza as estatísticas; **Abrir pasta** usa o Explorer. **Reverter** abre o mesmo fluxo protegido do menu e histórico.

Para diretórios, escolha remover só o link (deixa pasta vazia), mover de volta ou duplicar. **Manter Dados Físicos como backup** preserva o local dos dados. Arquivos removem somente o nome selecionado após verificar a identidade; os demais nomes e dados permanecem. Um caminho inacessível não dispensa a verificação de identidade.

Em falhas, leia os caminhos preservados antes de agir. Se os arquivos já foram restaurados e a limpeza falhou, **não repita a reversão**: confira a pasta restaurada e os Dados Físicos preservados. Sucesso com backup informa o caminho a conferir. Falha apenas no histórico não desfaz a operação: confira o link antes de repetir. Nunca apague um backup sem verificar os dados.

## Histórico e preferências

No Histórico, **Filtros** abre uma janela de três colunas. Operação e resultado aceitam múltiplas seleções; período é único: **Todo período** (padrão), Hoje, Última semana, Último mês ou Último ano. Cada intervalo substitui o anterior; períodos maiores já incluem os menores. **Ordenar por** oferece todas as colunas da tabela (Data / Hora, Ação Realizada, Ponto de Acesso, Status e Recuperação); **Ordem** define crescente ou decrescente. O padrão é Data / Hora decrescente. Aplicar confirma; Cancelar, X ou Escape descartam. **Limpar** restaura os filtros e ordenação padrão e também exige Aplicar. Nas ações de cada registro, **Detalhes** mostra caminhos, erro e metadados. Criações já desfeitas são indicadas e não podem ser revertidas novamente pelo histórico. Registros novos guardam identidade; registros antigos continuam legíveis e usam a verificação de integridade existente. **Exportar** inclui todos os registros, independentemente dos filtros. **Limpar Histórico** exige confirmação e não altera links.

O botão de tema no cabeçalho alterna Escuro → Claro → Seguir sistema → Escuro. O ícone indica o modo atual e o tooltip informa o próximo modo. Automático acompanha mudanças do host. Nas configurações, **Restaurar padrões** prepara os campos e só persiste com **Salvar**. **Descartar alterações** recarrega os valores salvos. Caminhos personalizados do histórico/log não são apagados pela restauração de preferências. Os ícones de informação ao lado das opções explicam seus efeitos; clique ou use Tab e Espaço/Enter para consultar. Notificações, backup, avisos e nível de log usam os serviços reais. **Abrir pasta de logs** ajuda a investigar falhas.

Atalhos: Ctrl+N criar; Ctrl+H histórico; Ctrl+, configurações; Ctrl+F buscar; F5 atualizar; Ctrl+Q sair. Tab/Shift+Tab percorrem controles; Escape fecha confirmações ou solicita cancelamento seguro no progresso. Telas e diálogos têm rolagem para alcançar os últimos controles em janelas pequenas.

## Desinstalar e limites

O desinstalador remove configuração/cache/log padrão e pergunta se deve manter o histórico. Em modo silencioso mantém o histórico, salvo `/DELETEHISTORY`. Não apaga dados migrados, destinos de junctions nem arquivos de histórico/log personalizados.

Windows 10 e máquina limpa sem Python não foram homologados; esses testes foram dispensados pelo mantenedor. Neste host a criação de symlinks retornou erro 1314; o teste comprova a falha segura, não o sucesso com privilégios. O teste manual de sucesso com privilégios foi dispensado pelo mantenedor em 04/11/2026 para a release inicial. Os limites conhecidos da versão estão em [Continuidade](CONTINUIDADE.md).
