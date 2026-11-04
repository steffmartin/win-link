# Validação do redesign — 04/11/2026

Estado: implementação local entregue; homologação obrigatória externa pendente. Este relatório complementa a evidência histórica da fase 5, sem reclassificá-la como lançamento aprovado.

## Checkpoint de 15 minutos — 17:49 (America/Sao_Paulo)

Base inicial: Git limpo em `c2f4ee0`, 278 testes Python e 74 testes da demo passando, build Vite aprovado. Nenhuma alteração prévia foi sobrescrita. Leitura da documentação e inspeção da demo vigente antes de portar o shell e os fluxos reais.

Implementado: shell/páginas PyQt6, cartões e visão compacta, quatro seleções de tipo, temas, configurações compatíveis, filtros com rascunho, histórico ampliado e reversão pelas propriedades. Nenhuma fixture, seletor simulado ou timer de operação do React foi transportado. A licença MIT foi escolhida explicitamente pelo mantenedor durante esta execução.

Verificação local: suíte ampliada para 296 testes Python aprovados na execução do checkpoint; a execução final ampliou a suíte para **299 testes aprovados**, sem ignorados, incluindo configurações antigas, restauração/descartar, filtros de symlink, datas inclusivas, atalhos reais, bloqueio de reentrada, rolagem, cache em falha e identidade da junction substituída. A suíte existente cobre junctions/hard links reais, Unicode/caminhos longos, conflitos, alterações externas, cancelamento, falhas de restauração e histórico. Todos os dados mutáveis dos testes ficam em diretórios temporários isolados.

Demo: 74 testes Node e build aprovados; cenários de navegador `browser-coverage.js`, `browser-final.js` e `browser-priority2.js` aprovados (propriedades, temas automático/manual, filtros, histórico, falhas, recuperação e cache). A demo continua referência visual/comportamental, não evidência de segurança do filesystem.

Capturas do aplicativo real geradas com `scripts/capture_ui.py`, em claro/escuro, 1280×800 e 760×400. Uma execução separada com `QT_SCALE_FACTOR=2` conferiu escala 200% e rolagem até os últimos botões. Os snapshots vêm de junction/hard link reais em pasta temporária. Capturas selecionadas em `capturas/`; demais saídas de revisão ficam em `build/`, não versionadas. Isso não equivale a auditoria com leitor de tela.

## Ambiente e bloqueios reais

`redesign-environment.json` registra Windows 11 build 26300, Windows Sandbox ausente e novas tentativas reais de symlink de arquivo/diretório: ambos negados com WinError 1314, preservando os dados originais. Não foram alterados privilégios ou configurações do Windows.

Permanecem pendentes: instalar/executar em Windows limpo sem Python; testar Windows 10 mínimo; criar/descobrir/reverter symlinks com permissões apropriadas. O host tem Python instalado e não fornece esses ambientes. A consulta de VMs Hyper-V também foi negada por falta de permissão; não foi possível usar uma VM existente. A execução empacotada com PATH isolado está registrada separadamente e não os substitui.

## Reproduzir

Use os comandos do README para pytest, Ruff, Black e mypy. Capture com `.venv\Scripts\python.exe scripts/capture_ui.py`; para alta escala, execute em novo processo com `QT_SCALE_FACTOR=2`. A suíte React e os scripts de navegador estão no README do protótipo. Build/instalação isolada seguem [distribuição](../arquitetura/DISTRIBUICAO.md).

## Distribuição atual

Portátil e instalador de produção regenerados com PyInstaller 6.22.3 e Inno Setup 6.7.4 (compilador oficial com assinatura válida). Licença MIT incluída no pacote e no instalador. Validação isolada registra execução portátil/instalada com PATH restrito ao Windows, sem PYTHONPATH/PYTHONHOME; instalação/desinstalação com AppId e dados próprios, preservação/apagamento do histórico e junction/dados de teste preservados. Resultado em `redesign-distribution.json`; hashes e tamanhos em `redesign-artifacts.json`. Binários e ferramentas ficam fora do Git.

A execução adicional do script de navegador `browser-priority1.js` foi interrompida sem conclusão durante a automação; não está contabilizada como aprovada. Os testes de regras (74), os outros três scripts de navegador citados e os testes reais Python são evidências independentes. Não houve alteração no código da demo.

Validação final do build de código `8b8ab19`: 299 testes Python aprovados (XML versionado), Ruff/Black/mypy aprovados, portátil e instalação isolada aprovados novamente após a última alteração. Não foram incluídos caches, dependências, ferramentas ou binários nos commits. O pacote portátil exige a pasta inteira; `redesign-artifacts.json` registra a presença da licença e o SHA-256 do executável e instalador.

## Decisão posterior do mantenedor — 04/11/2026

Os testes em Windows limpo sem Python e Windows 10 foram explicitamente dispensados pelo mantenedor. Permanecem não executados e não são tratados como aprovados; deixam de bloquear esta entrega por decisão de escopo. A pendência restante de permissões é a validação manual de symlink de diretório e de arquivo com o aplicativo elevado (ou Modo de Desenvolvedor). Os resultados WinError 1314 acima continuam sendo a evidência histórica das tentativas sem privilégio.

## Revisão visual após comparação com o protótipo — 04/11/2026

As capturas anteriores não comprovavam fidelidade suficiente: faltavam ícones, a criação não trazia a prévia estrutural, e ações de histórico/configurações estavam em posições e tamanhos diferentes. A revisão corrige a apresentação sem alterar serviços de arquivos, confirmações, identidade ou preservação de dados.

- Cabeçalho com marca e alternância de tema por ícone/menu; navegação e cartões com símbolos vetoriais que acompanham o tema.
- Lista com título/atualização/início e controles de busca/filtro/visualização alinhados, cartões com ícone de arquivo/pasta, status e acesso às propriedades.
- Criação com quatro opções em grade 2×2, descrições, campos com seletores de largura adequada, botão Avançar e prévia estrutural em duas colunas no desktop, empilhadas em janela reduzida. A ilustração usa somente os caminhos digitados; validação/operação continuam reais.
- Histórico com exportação/limpeza no topo, filtros agrupados, resultado em badges e detalhes/desfazer por registro. Alternativas por seleção continuam disponíveis para teclado.
- Configurações em coluna limitada a 672 px, campos com labels, ações de restaurar/descartar/salvar próximas do conteúdo. Propriedades, prévia, reversão, progresso, filtros, detalhes e Sobre têm cabeçalhos, ícones, espaçamentos e ações consistentes.
- Indicadores de radios/checkboxes e setas de seleção agora são explícitos nos dois temas. SVGs de interface entram no empacotamento, sem dependência de rede ou Node.

**Validação atual:** 308 testes Python aprovados, Ruff/Black/mypy aprovados. Os nove testes de layout também passaram em processo separado com `QT_SCALE_FACTOR=2`. Eles verificam dimensões reais, ausência de rolagem horizontal externa, tamanho legível das opções, presença de ícones, reposicionamento do cabeçalho, ações por registro e acesso ao botão Salvar. No monitor em escala 200%, o caso desktop é limitado à área lógica disponível pelo Windows; o cenário reduzido permanece exatamente 760×400. A primeira tentativa de pedir 1280×800 nessa escala encontrou o limite físico do monitor; o teste foi corrigido para respeitar essa área, sem ignorar o cenário.

`scripts/capture_ui.py` foi ampliado para capturar as quatro telas e propriedades/prévia/reversão/progresso nos dois temas, além de filtros e Sobre. As capturas reduzidas agora validam 760×400 por assert, evitando tratar como sucesso uma janela que o layout forçou a ficar maior. Saídas de revisão/alta escala ficam em `build/layout-review` e `build/layout-review-highscale`; as capturas vigentes selecionadas substituem as anteriores em `capturas/`.

Código desta revisão: `eec1dee`. Distribuição e hashes atuais são atualizados nos mesmos relatórios JSON da entrega, preservando a decisão de dispensa de Windows limpo/Windows 10 e a pendência manual de symlinks com privilégios.

A suíte de layout também cobre a seleção exclusiva ao clicar repetidamente no tipo atual e a permanência do estado vazio ao alternar a visualização. Verificação final: 308 testes Python e nove testes de layout em escala 200% aprovados.

Validação do pacote final desta revisão: portátil e instalado abriram com os ícones de navegação/criação presentes; o smoke test também gerou capturas do executável congelado. Instalação e desinstalação com/sem histórico passaram em diretório e AppId isolados, preservando junction e dados de teste. O instalador de produção foi regenerado com todos os SVGs e QtSvg incluídos; hashes atuais em `redesign-artifacts.json`. Não houve alteração em dados/configurações da instalação do usuário.
