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
