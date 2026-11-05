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
