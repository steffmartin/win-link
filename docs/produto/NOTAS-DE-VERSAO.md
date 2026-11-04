# WinLink 0.1.0 — candidato local, 04/11/2026

O redesign aprovado está no aplicativo Python/PyQt6: cabeçalho, navegação lateral, lista virtualizada de cartões, visão compacta, criação com quatro tipos visuais, propriedades, histórico e configurações. Os serviços de arquivos existentes continuam responsáveis pelas operações reais.

Novidades: tipo padrão persistente com compatibilidade de configuração, restaurar padrões sem salvar automaticamente, descartar rascunho, filtros do histórico por resultado/datas, detalhes e criação desfeita, filtros de symlink arquivo/diretório, tema rápido com modo automático e reversão pelas propriedades. Atalhos, rolagem e foco foram adaptados ao novo shell.

Proteções: cache preservado em atualização incompleta, confirmação obrigatória, identidade revalidada antes de reverter, identidade persistida em registros novos, cancelamento cooperativo, backups e mensagens distintas para falhas e restauração já realizada. Configuração e histórico anteriores continuam legíveis.

Licença MIT, escolhida pelo mantenedor. A versão continua 0.1.0; nenhum release remoto foi publicado. Builds locais não são assinados. Instalação e portátil serão distribuíveis após fechar a homologação em Windows limpo sem Python, Windows 10 e sucesso de symlinks com permissões apropriadas. Consulte [validação](../validacao/REDESIGN.md).
