# Continuidade do WinLink

Documento ativo de manutenção a partir da versão 0.1.0. Planos, protótipo e evidências anteriores estão no [arquivo histórico](arquivo/v0.1.0/README.md); seus checkpoints não são pendências atuais de lançamento.

## Base da entrega inicial

Em 04/11/2026, o mantenedor autorizou a release inicial e dispensou o teste manual de sucesso de symlinks com privilégios apropriados. Windows limpo sem Python e Windows 10 já haviam sido dispensados. A implementação e a interface atuais são a base para continuidade; não há uma nova rodada de aprovação de interface pendente para esta entrega.

Verificação de fechamento: 308 testes Python, Ruff, Black e mypy aprovados; 74 testes unitários do protótipo e build Vite aprovados. O build histórico emite avisos sobre a diretiva `use client` do lucide-react, sem impedir sua conclusão.

A validação de distribuição no fechamento passou: abertura portátil/instalada, instalação e desinstalação com/sem histórico, preservando junction e dados de teste. Os hashes do executável e instalador conferem com os pacotes preparados anteriormente; a reorganização não alterou o código do aplicativo.

## Bugs, melhorias e acompanhamento

As [Issues do GitHub do projeto](https://github.com/steffmartin/win-link/issues) são o registro único de novos bugs, melhorias e solicitações. Não manter backlog ou lista paralela de issues em documentos do repositório. As ideias anteriores permanecem no [arquivo histórico](arquivo/v0.1.0/planejamento/MELHORIAS.md) como referência; não representam tarefas aprovadas.

Ao abrir uma issue de bug, registrar versão do WinLink, versão/build do Windows, tipo de link, permissões, passos mínimos, resultado esperado e observado. Incluir mensagem de erro e trechos de log com caminhos e informações pessoais removidos. Usar dados descartáveis para reproduzir operações de arquivos.

Para melhorias, descrever o problema, comportamento proposto e critério de aceite. Usar labels e estado da própria issue para triagem; vincular commits/PRs e indicar a versão da correção nas notas de versão.

## Limites da release inicial

Nenhum novo bug funcional foi identificado nesta revisão. O sucesso de symlinks com privilégios apropriados, Windows limpo sem Python e Windows 10 não foram homologados por dispensa do mantenedor. Os pacotes não possuem assinatura digital. Esses limites descrevem a entrega inicial; se houver trabalho para tratá-los, o acompanhamento será em Issues do GitHub.

## Rotina de manutenção

1. Instalar as dependências e executar o aplicativo conforme o README.
2. Preservar compatibilidade de configuração e histórico; manter prévia, confirmação, verificação de identidade e recuperação de dados.
3. Executar pytest, Ruff, Black e mypy pelos comandos do README. Para mudanças visuais, conferir temas, teclado, janela reduzida e alta escala.
4. Gerar e validar os pacotes conforme [distribuição](DISTRIBUICAO.md), atualizar as issues correspondentes e as notas da versão.
5. Versionar fontes, lockfiles e documentação; manter logs, relatórios gerados, caches, `build/` e `dist/` fora do Git. Publicar os pacotes como assets da release.
