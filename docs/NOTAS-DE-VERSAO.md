# WinLink 0.1.9 — 07/11/2026

Filtros atualizados para Meus Links e Histórico, com validação manual aprovada pelo mantenedor.

## Melhorias e correções

- Meus Links permite selecionar status, criadores, tipos e tags em dropdowns compactos com opções marcáveis; a altura do diálogo não cresce com a quantidade de valores. O filtro de tags inclui “(Vazio)” para links sem tags, combinável com outras tags. As opções escolhidas se combinam como os demais filtros; o controle “Aplicar tag como” foi removido. Os filtros continuam aplicados junto com busca e ordenação, salvos como listas e migrados das configurações legadas. Tags que não existem após uma descoberta completa deixam de ser filtros ativos (#65, #67).
- Os filtros do Histórico foram movidos para uma janela responsiva em até três colunas, liberando espaço para a tabela. Operação e resultado aceitam múltiplas seleções; período aceita uma opção: Todo período (padrão), Hoje, Última semana, Último mês ou Último ano. Ordenação pode ser escolhida por qualquer coluna, crescente ou decrescente; o padrão é Data / Hora decrescente. Aplicar confirma e Cancelar/fechar/Escape descartam. Limpar restaura os filtros e ordenação padrão no rascunho; exportar continua incluindo todo o histórico, sem considerar filtros (#68).
- As opções de filtro começam marcadas; marcar todas não restringe os resultados, enquanto desmarcar todas não retorna registros. Opções dentro de um grupo combinam por união; grupos diferentes combinam por interseção.
- O botão **Limpar** foi removido de Meus Links. **Limpar filtros** no diálogo remove os critérios de filtro sem apagar a busca nem alterar a ordenação.

## Validação

402 testes Python passaram; Ruff, Black e mypy aprovados. Os 22 testes de layout passaram com `QT_SCALE_FACTOR=2`. PyInstaller/Inno Setup 7 geraram `dist/WinLink-Portable-0.1.9.zip`, `dist/WinLink-Setup-0.1.9.exe` e `dist/SHA256SUMS.txt`; o smoke test portátil e a validação isolada de instalação/desinstalação em português e inglês passaram, preservando a junction de teste. O mantenedor aprovou a validação manual. Windows limpo sem Python não foi testado.

---

# WinLink 0.1.8 — 07/11/2026

Melhorias de apresentação e fluxo para histórico, tags, cálculo de armazenamento e criação de links.

## Melhorias

- Filtros do histórico em uma linha, alinhados, com ação distinta para apagar o histórico (#64).
- Tags múltiplas por link, edição em Propriedades e exibição em cartões/visão compacta; rótulos de tipos padronizados em toda a interface (#62).
- Preferência para desativar cálculos automáticos de armazenamento sem afetar o recálculo manual (#61).
- Seleção de Pasta/Arquivo antes do tipo de link; o tipo padrão também pré-seleciona a categoria correspondente (#44).
- A criação pode oferecer a inclusão do Ponto de Acesso na descoberta quando ele estiver fora das pastas monitoradas (#38).
- Propriedades mantém os caminhos completos selecionáveis em campos de até duas linhas; ícones dos menus de contexto ficam em coluna compacta junto aos rótulos.

## Validação e limites

390 testes Python passaram; Ruff, Black e mypy aprovados. Os testes de interface foram executados com `QT_SCALE_FACTOR=2`. O smoke test do pacote portátil confirmou inicialização, ícones e estado da descoberta. PyInstaller e Inno Setup 7 geraram o pacote portátil e o instalador v0.1.8; a validação automatizada de instalação/desinstalação não pôde iniciar o instalador temporário porque o Windows Application Control bloqueou sua execução. Essa etapa permanece não validada neste host.

Windows limpo sem Python, Windows 10 e sucesso de symlinks com privilégios apropriados continuam não homologados. Pacotes sem assinatura digital.

---

# WinLink 0.1.7 — 06/11/2026

Patch com correções dos bugs #58 e #29, conforme a triagem da #36.

## Correções

- A descoberta percorre destinos de junctions de diretório para encontrar junctions aninhadas, evitando ciclos e duplicidade e respeitando exclusões e cancelamento ([#58](https://github.com/steffmartin/win-link/issues/58)).
- Falhas de criação de symlink com WinError 1314 agora orientam sobre Modo de Desenvolvedor ou execução como administrador, sem elevação automática; as opções de symlink exibem indicador acessível de privilégio possível ([#29](https://github.com/steffmartin/win-link/issues/29)).
- O instalador adapta o tema claro/escuro do Windows e preserva as imagens personalizadas do assistente nos dois modos.

## Validação e limites

363 testes Python passaram; Ruff, Black e mypy aprovados. Os 16 testes de layout passaram com `QT_SCALE_FACTOR=2`. A validação de distribuição confirmou abertura do pacote portátil e instalado, instalação/desinstalação em português e inglês e preservação dos dados de teste usando Inno Setup 7.

O caso de #58 foi reproduzido em árvore temporária no Windows. Para #29, WinError 1314 foi simulado pelos caminhos de exceção e código de retorno; a criação real de symlink teve sucesso neste ambiente. Windows limpo sem Python, Windows 10 e sucesso de symlinks com privilégios apropriados continuam não homologados. Pacotes sem assinatura digital.

# WinLink 0.1.6 — 06/11/2026

Patch com correções de bugs e pequenas melhorias solicitado na triagem da #36.

## Correções

- Fechar Propriedades durante o cálculo de tamanho e contagem agora solicita cancelamento cooperativo e libera o diálogo, sem resultado parcial ou sinais tardios ([#54](https://github.com/steffmartin/win-link/issues/54)).
- Criar ou remover um link reflete a alteração na lista e no cache imediatamente, sem aguardar a varredura; resultados de varredura iniciados antes da operação são descartados ([#18](https://github.com/steffmartin/win-link/issues/18)).
- A janela restaura a geometria salva sem abrir fora da área visível, inclusive após fechar maximizada ([#63](https://github.com/steffmartin/win-link/issues/63)).
- Abrir dados ou ponto de acesso nas Propriedades trata falhas com mensagem em vez de encerrar o aplicativo ([#14](https://github.com/steffmartin/win-link/issues/14)).
- Setas dos campos de data do histórico usam o mesmo padrão vetorial dos demais campos ([#53](https://github.com/steffmartin/win-link/issues/53)).

## Melhorias

- Estado Inacessível usa um único ícone vetorial em lista, cartões e Propriedades; Inacessível exibe amarelo e Quebrado vermelho com tokens de tema ([#59](https://github.com/steffmartin/win-link/issues/59), [#60](https://github.com/steffmartin/win-link/issues/60)).
- Nova instância do aplicativo apenas ativa a janela já aberta ([#33](https://github.com/steffmartin/win-link/issues/33)).
- A lista lembra o último filtro e ordenação aplicados entre sessões ([#11](https://github.com/steffmartin/win-link/issues/11)).

## Validação e limites

357 testes Python passaram; Ruff, Black e mypy aprovados. Os 16 testes de layout também passaram com `QT_SCALE_FACTOR=2`.

Build por PyInstaller e instalador offline Inno Setup. A validação local de distribuição confirmou abertura do portátil e instalado, instalação/desinstalação em português e inglês com e sem histórico e preservação da junction de teste. O pacote portátil completo, instalador e checksums SHA-256 acompanham a release.

Windows limpo sem Python, Windows 10 e sucesso de symlinks com privilégios apropriados continuam não homologados; não fazem parte desta validação. Pacotes sem assinatura digital. O manual foi retirado deste patch após as tentativas online e offline; a #10 permanece aberta para decidir uma alternativa local.

# WinLink 0.1.5 — 05/11/2026

- Configurações permite salvar pastas excluídas da descoberta. A varredura pula cada subárvore excluída, mesmo quando uma raiz incluída está dentro dela. Os padrões são a pasta temporária e a pasta do Windows, quando disponíveis. As listas ficam lado a lado em janelas amplas e empilhadas nas menores. [#56](https://github.com/steffmartin/win-link/issues/56)
- Fechar durante a descoberta solicita cancelamento cooperativo, preserva os resultados parciais junto ao cache válido do mesmo escopo e encerra a janela quando a varredura para. Durante migração ou reversão, o bloqueio de fechamento continua ativo. [#34](https://github.com/steffmartin/win-link/issues/34)

# WinLink 0.1.4 — 05/11/2026

- Cabeçalho com ícones para Sobre e para o tema do sistema (#40 e #41).
- Busca com ação Limpar, colunas de caminhos com espaço distribuído e margem ao lado dos cartões (#42, #43 e #51).
- Ajuda contextual para os quatro tipos de link (#39).
- Preferência persistente em Configurações para abrir Meus Links em modo normal ou compacto (#50).
- Arte do instalador baseada na identidade visual do aplicativo (#55).

# WinLink 0.1.3 — 05/11/2026

- Configurações mantém a explicação da confirmação obrigatória na ajuda contextual ([#45](https://github.com/steffmartin/win-link/issues/45)).
- O botão Abrir pasta de logs acompanha o campo Nível de logs na mesma linha quando há espaço e passa para a linha seguinte em larguras menores ([#47](https://github.com/steffmartin/win-link/issues/47)).

# WinLink 0.1.2 — 05/11/2026

Patch de melhorias na apresentação dos fluxos existentes.

## Melhorias

- Nomenclatura Ponto de Acesso / Dados Físicos em criação, prévia, propriedades, histórico, reversão e manual. O Ponto de Acesso aparece primeiro no formulário, mantendo os parâmetros e a semântica dos serviços ([#13](https://github.com/steffmartin/win-link/issues/13)).
- Configurações acompanha a largura da janela, com rolagem em janela reduzida ([#24](https://github.com/steffmartin/win-link/issues/24)).
- Tipo padrão e quatro opções de Configurações têm explicações por ícones de informação, acessíveis por clique e teclado ([#25](https://github.com/steffmartin/win-link/issues/25)).
- Sobre usa ícone de interrogação no cabeçalho e inclui link acessível ao GitHub do projeto ([#26](https://github.com/steffmartin/win-link/issues/26)).
- Botão de tema alterna diretamente Escuro → Claro → Seguir sistema, com ícone do modo atual e indicação do próximo modo ([#27](https://github.com/steffmartin/win-link/issues/27)).
- Criação concluída mantém o resultado no progresso, sem diálogo de sucesso duplicado; limpa os campos e restaura o tipo padrão. Falhas/cancelamento mantêm o formulário; avisos de histórico e recuperação permanecem ([#28](https://github.com/steffmartin/win-link/issues/28)).
- Ordenação fica em Filtros e segue Aplicar/Cancelar. Limpar busca e filtros fica ao lado, preserva a ordenação e atualiza a descoberta ([#30](https://github.com/steffmartin/win-link/issues/30)).
- Instalador oferece português e inglês, selecionando licença traduzida ou original conforme idioma. Tradução portuguesa identificada e acompanhada do original, com copyright preservado ([#32](https://github.com/steffmartin/win-link/issues/32)).

Captura principal do README atualizada a partir do aplicativo real, usando apenas links e dados temporários isolados.

## Validação e limites

332 testes Python passaram; Ruff, Black e mypy aprovados. Os 19 testes de layout/interação afetados também passaram com QT_SCALE_FACTOR=2. Capturas reais em temas claro/escuro, janela 1280×800 e reduzida 760×400, também em alta escala; alternância e persistência do modo sistema verificadas.

Build por PyInstaller e instalador offline Inno Setup. Validação local do portátil e da instalação/desinstalação isolada em português e inglês, com e sem histórico, preservando junction e dados descartáveis. Portátil completo, instalador e SHA256SUMS.txt nos assets da release.

Configurações e histórico existentes são preservados; nenhuma nova operação de arquivos, sincronização, monitoramento ou elevação automática foi adicionada. Os seis bugs reservados para investigação continuam abertos na [#36](https://github.com/steffmartin/win-link/issues/36). A sugestão de adicionar pastas não escaneadas foi apenas registrada na [#38](https://github.com/steffmartin/win-link/issues/38).

Em 05/11/2026, o mantenedor confirmou manualmente que, após selecionar inglês ou português, a licença aparece no idioma correto. Essa confirmação complementa a conferência dos textos, o build e os testes automatizados de instalação/desinstalação.

Pacotes sem assinatura digital. Windows 10, máquina limpa sem Python e sucesso de symlink com privilégios elevados continuam não homologados. Nenhuma tag ou asset de versões anteriores foi alterado.

---

# WinLink 0.1.1 — 04/11/2026

Patch de correções locais identificado nos testes manuais da v0.1.0.

## Correções

- Prévia de diretórios distingue o local dos dados do caminho do link, explica a migração e anuncia a criação uma única vez ([#17](https://github.com/steffmartin/win-link/issues/17)).
- Propriedades abre uma única vez por duplo clique; Enter continua funcionando ([#19](https://github.com/steffmartin/win-link/issues/19)).
- Caminhos longos em Propriedades usam campos somente leitura com quebra de linha, rolagem e cópia integral, sem alargar a janela ([#20](https://github.com/steffmartin/win-link/issues/20)).
- Visão compacta tem linhas menores e não mostra o cabeçalho vertical vazio ([#21](https://github.com/steffmartin/win-link/issues/21)).
- Navegação evita o contorno nativo ao clicar e mantém foco de teclado; confirmação obrigatória tem aparência desabilitada; ações primárias têm feedback de hover/clique; informação usa ícones vetoriais transparentes ([#22](https://github.com/steffmartin/win-link/issues/22)).
- Procurar reutiliza o caminho preenchido, com fallback para a pasta existente mais próxima; cancelar preserva o campo ([#23](https://github.com/steffmartin/win-link/issues/23)).
- Padrões de descoberta incluem somente a pasta do usuário atual, removendo D:\Cache. Configurações personalizadas existentes são preservadas; Restaurar padrões exige Salvar ([#35](https://github.com/steffmartin/win-link/issues/35)).
- Timer e conexões de tema encerram junto com a janela, evitando callbacks em objetos Qt destruídos ([#37](https://github.com/steffmartin/win-link/issues/37)).

## Validação e limites

322 testes Python, Ruff, Black e mypy aprovados. Os 23 testes de layout e regressão do patch também passaram com QT_SCALE_FACTOR=2. Interface real inspecionada nos temas claro, escuro e sistema, em janela normal e reduzida, incluindo caminhos longos, navegação e controles obrigatórios.

Build por PyInstaller e Inno Setup; validação local de abertura portátil/instalada e instalação/desinstalação isolada com e sem histórico, preservando junction e dados descartáveis. Pacote portátil inclui a pasta WinLink inteira e _internal; instalador offline por usuário; checksums SHA-256 nos assets.

Windows limpo sem Python e Windows 10 permanecem não homologados. A validação deste patch não inclui sucesso de symlink com privilégios elevados. Pacotes sem assinatura digital. Os bugs que exigem investigação ou alterações mais amplas continuam abertos e ordenados para o segundo patch na [#36](https://github.com/steffmartin/win-link/issues/36); esta versão não os declara resolvidos.

---

# WinLink 0.1.0 — 04/11/2026

Release inicial do gerenciador de links para Windows, sob licença MIT.

- Descoberta, criação e reversão de junctions, symlinks de arquivo/diretório e hard links.
- Interface PyQt6 com navegação lateral, cartões e visão compacta, busca, filtros e propriedades.
- Prévia e confirmação, verificação de identidade antes da reversão, cancelamento cooperativo e opções de backup/restauração de diretórios.
- Histórico com exportação, filtros por operação/resultado/datas e indicação de criações já desfeitas.
- Temas claro, escuro e sistema; tipo de link padrão e preferências persistentes.
- Instalador offline por usuário e pacote portátil com runtime incluído. Pacotes sem assinatura digital.

## Validação e limites

308 testes Python passaram; Ruff, Black e mypy passaram. Os 74 testes unitários do protótipo histórico passaram e seu build foi concluído. A validação local de distribuição passou: abertura dos pacotes e instalação/desinstalação isolada com e sem histórico, preservando junction e dados de teste.

Em 04/11/2026, o mantenedor autorizou o lançamento e dispensou a validação manual de sucesso de symlinks de arquivo/diretório com privilégios apropriados. Windows limpo sem Python e Windows 10 também tiveram suas validações dispensadas. Esses cenários permanecem não homologados; a dispensa não representa um teste aprovado. No host, as tentativas anteriores de symlink sem privilégios retornaram WinError 1314 com falha segura.

Consulte [uso](USO.md), [distribuição](DISTRIBUICAO.md) e [continuidade](CONTINUIDADE.md).
