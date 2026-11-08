# Continuidade do WinLink

Documento ativo de manutenção. A v1.0.0 é a versão publicada mais recente, descrita nas [notas de versão](NOTAS-DE-VERSAO.md); a triagem e a fila de trabalho ficam na [issue #36](https://github.com/steffmartin/win-link/issues/36).

## Base da entrega inicial

Em 04/11/2026, o mantenedor autorizou a release inicial e dispensou o teste manual de sucesso de symlinks com privilégios apropriados. Windows limpo sem Python e Windows 10 já haviam sido dispensados. A implementação e a interface atuais são a base para continuidade; não há uma nova rodada de aprovação de interface pendente para esta entrega.

## Verificação da v0.1.7

363 testes Python passaram; Ruff, Black e mypy aprovados, assim como 16 testes de layout em escala 2. A validação de distribuição confirmou os pacotes portátil e instalado, os fluxos de instalação/desinstalação em português e inglês e a preservação dos dados de teste. A v0.1.7 corrige a descoberta de junctions aninhadas em destinos de outras junctions (#58) e orienta corretamente falhas de privilégio ao criar symlinks (#29). Windows limpo sem Python, Windows 10 e sucesso de symlinks com privilégios apropriados permanecem não homologados.

## Entrega da v0.1.8

390 testes Python passaram; Ruff, Black e mypy aprovados. O pacote portátil passou no smoke test e o instalador foi compilado pelo Inno Setup 7. A validação automatizada de instalação/desinstalação não pôde iniciar o instalador temporário devido ao bloqueio do Windows Application Control; não considerar essa etapa homologada. A release inicial v1.0.0 foi publicada com `WinLink-Portable-0.1.8.zip`, `WinLink-Setup-0.1.8.exe` e `SHA256SUMS.txt`.

## Descoberta e cache

A descoberta usa as listas de inclusão e exclusão da configuração. A varredura pula as subárvores excluídas antes de abrir seus diretórios. Cache e resultados precisam corresponder à política de exclusões vigente. Ao fechar durante a descoberta, a thread recebe um pedido de interrupção e a janela fecha após sua conclusão. O cache parcial preserva entradas anteriores do mesmo escopo e é seguido por uma nova varredura na abertura.

## Bugs, melhorias e acompanhamento

As [Issues do GitHub do projeto](https://github.com/steffmartin/win-link/issues) são o registro único de novos bugs, melhorias e solicitações. Não manter backlog ou lista paralela de issues em documentos do repositório.

Agentes devem seguir [AGENTS.md](../AGENTS.md) e consultar o [guia de UI](UI.md) ao evoluir a interface.

Ao abrir uma issue de bug, registrar versão do WinLink, versão/build do Windows, tipo de link, permissões, passos mínimos, resultado esperado e observado. Incluir mensagem de erro e trechos de log com caminhos e informações pessoais removidos. Usar dados descartáveis para reproduzir operações de arquivos.

Para melhorias, descrever o problema, comportamento proposto e critério de aceite. Usar labels e estado da própria issue para triagem; vincular commits/PRs e indicar a versão da correção nas notas de versão.

## Limites da release inicial

O sucesso de symlinks com privilégios apropriados, Windows limpo sem Python e Windows 10 não foram homologados por dispensa do mantenedor. Os pacotes não possuem assinatura digital. Esses limites descrevem a entrega inicial; se houver trabalho para tratá-los, o acompanhamento será em Issues do GitHub.

## Rotina de manutenção

1. Instalar as dependências e executar o aplicativo conforme o README.
2. Preservar compatibilidade de configuração e histórico; manter prévia, confirmação, verificação de identidade e recuperação de dados.
3. Executar pytest, Ruff, Black e mypy pelos comandos do README. Para mudanças visuais, conferir temas, teclado, janela reduzida e alta escala.
4. Gerar e validar os pacotes conforme [distribuição](DISTRIBUICAO.md), atualizar as issues correspondentes e as notas da versão.
5. Versionar fontes, lockfiles e documentação; manter logs, relatórios gerados, caches, `build/` e `dist/` fora do Git. Publicar os pacotes como assets da release.
