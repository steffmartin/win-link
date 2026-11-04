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
