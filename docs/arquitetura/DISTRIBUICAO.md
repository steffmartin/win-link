# Distribuição e dados — WinLink

## Implementação vigente

Aplicativo Python/PyQt6 empacotado por PyInstaller (`winlink.spec`) e instalador offline Inno Setup (`installer/winlink.iss`). Build: `scripts/build.ps1`. Não usar a estimativa de tamanho ou stacks alternativas dos estudos antigos como requisito.

- Instalador por usuário, sem elevação obrigatória, em `%LOCALAPPDATA%\Programs\WinLink`.
- Portátil em `dist/WinLink`: distribuir a pasta inteira, incluindo `_internal`, não somente o executável.
- Instalador em `dist/WinLink-Setup-0.1.0.exe`; inclui runtime Python e dependências.
- Dados padrão em `%APPDATA%\WinLink`: configuração, histórico, cache e logs JSON/arquivo.
- Sem serviço, banco de dados ou monitoramento automático como dependência da aplicação atual.

## Build e validação

```powershell
uv sync --extra dev --extra build
.\scripts\build.ps1 -Iscc 'C:\caminho\Inno Setup 6\ISCC.exe'
.venv\Scripts\python.exe scripts\validate_distribution.py 'C:\caminho\Inno Setup 6\ISCC.exe'
```

O validador usa AppId e diretório de dados separados dentro de `build/distribution-test`; preserva os resultados de teste para inspeção. Relatório atual: `docs/validacao/redesign-distribution.json`. O relatório `phase5-distribution.json` preserva a execução histórica anterior ao redesign. Capturas, testes e limites atuais: [redesign](../validacao/REDESIGN.md).

O spec restringe descoberta de DLLs ao Python do build e ao Windows para evitar ICU/UCRT externos vindos do PATH. O primeiro build anterior à correção falhou ao importar QtWidgets; não distribuí-lo. Evidências históricas e hashes do build validado: [fase 5](../validacao/FASE5.md).

## Instalação e desinstalação

Configuração/cache/log padrão são removidos na desinstalação. O desinstalador pergunta sobre manter histórico; em modo silencioso o preserva, salvo `/DELETEHISTORY`. Não percorre dados migrados/junctions nem apaga caminhos personalizados de log/histórico. Configurações e histórico são do usuário; preservar compatibilidade na implementação da UI.

Leitura/junctions não exigem elevação geral do aplicativo. Symlinks dependem das permissões do Windows/Modo de Desenvolvedor; não prometer solicitação automática de elevação por operação. O pacote não é assinado digitalmente.

## Pendências antes do lançamento

Homologar em máquina Windows limpa sem Python, Windows 10 mínimo e criação real de symlinks com privilégios apropriados. PATH isolado no host de desenvolvimento não substitui outra instalação do Windows. [Plano](../planejamento/PLANO.md) e [limites da validação](../validacao/FASE5.md).
