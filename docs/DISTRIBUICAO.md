# Distribuição e dados — WinLink

## Implementação vigente

Aplicativo Python/PyQt6 empacotado por PyInstaller (`winlink.spec`) e instalador offline Inno Setup (`installer/winlink.iss`). Build: `scripts/build.ps1`. Não usar a estimativa de tamanho ou stacks alternativas dos estudos antigos como requisito.

- Instalador por usuário, sem elevação obrigatória, em `%LOCALAPPDATA%\Programs\WinLink`.
- Portátil em `dist/WinLink`: distribuir a pasta inteira, incluindo `_internal`, não somente o executável.
- Instalador em `dist/WinLink-Setup-0.1.3.exe`; inclui runtime Python e dependências.
- Dados padrão em `%APPDATA%\WinLink`: configuração, histórico, cache e logs JSON/arquivo.
- Sem serviço, banco de dados ou monitoramento automático como dependência da aplicação atual.

## Build e validação

```powershell
uv sync --extra dev --extra build
.\scripts\build.ps1 -Iscc 'C:\caminho\Inno Setup 6\ISCC.exe'
.venv\Scripts\python.exe scripts\validate_distribution.py 'C:\caminho\Inno Setup 6\ISCC.exe'
```

O validador usa AppId e diretório de dados separados dentro de `build/distribution-test`; preserva os resultados de teste para inspeção. Relatório atual: `build/distribution-test/distribution-report.json`. O relatório `phase5-distribution.json` preserva a execução histórica anterior ao redesign. Capturas, testes e limites atuais: [redesign](arquivo/v0.1.0/validacao/REDESIGN.md).

O spec restringe descoberta de DLLs ao Python do build e ao Windows para evitar ICU/UCRT externos vindos do PATH. O primeiro build anterior à correção falhou ao importar QtWidgets; não distribuí-lo. Evidências históricas e hashes do build validado: [fase 5](arquivo/v0.1.0/validacao/FASE5.md).

## Instalação e desinstalação

Configuração/cache/log padrão são removidos na desinstalação. O desinstalador pergunta sobre manter histórico; em modo silencioso o preserva, salvo `/DELETEHISTORY`. Não percorre dados migrados/junctions nem apaga caminhos personalizados de log/histórico. Configurações e histórico são do usuário; preservar compatibilidade na implementação da UI.

Leitura/junctions não exigem elevação geral do aplicativo. Symlinks dependem das permissões do Windows/Modo de Desenvolvedor; não prometer solicitação automática de elevação por operação. O pacote não é assinado digitalmente.

## Limites aceitos para a release inicial

Em 04/11/2026, o mantenedor dispensou o teste manual de sucesso de symlinks com privilégios apropriados e autorizou a release inicial. Windows limpo sem Python e Windows 10 também foram dispensados e permanecem não homologados. PATH isolado no host não substitui outra instalação do Windows. Acompanhar em [continuidade](CONTINUIDADE.md).

## Publicação

Gerar `dist/WinLink-Portable-0.1.3.zip` com a pasta inteira `WinLink/` e publicar junto do instalador e de `SHA256SUMS.txt`. Não enviar o instalador de validação, caches ou diretórios intermediários. A tag `v0.1.3` deve apontar para o commit do patch validado; não alterar a tag ou os assets da v0.1.0. A nova release deve usar as [notas de versão](NOTAS-DE-VERSAO.md).
