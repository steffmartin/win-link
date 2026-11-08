# Distribuição e dados — WinLink

## Implementação vigente

Aplicativo Python/PyQt6 empacotado por PyInstaller (`winlink.spec`) e instalador offline Inno Setup (`installer/winlink.iss`). Build: `scripts/build.ps1`. Não usar a estimativa de tamanho ou stacks alternativas dos estudos antigos como requisito.

- Instalador por usuário, sem elevação obrigatória, em `%LOCALAPPDATA%\Programs\WinLink`.
- Portátil em `dist/WinLink`: distribuir a pasta inteira, incluindo `_internal`, não somente o executável.
- Instalador em `dist/WinLink-Setup-1.0.0.exe`; inclui runtime Python e dependências.
- Dados padrão em `%APPDATA%\WinLink`: configuração, histórico, cache e logs JSON/arquivo.
- Sem serviço, banco de dados ou monitoramento automático como dependência da aplicação atual.

As imagens do assistente usam a marca do aplicativo nos modos claro e escuro do Inno Setup. Para regerá-las após atualizar a identidade visual, execute `.venv\Scripts\python.exe resources\wizard_artwork.py` e confira o assistente em português e inglês.

## Build e validação

```powershell
uv sync --extra dev --extra build
.\scripts\build.ps1 -Iscc 'C:\Program Files\Inno Setup 7\ISCC.exe'
.venv\Scripts\python.exe scripts\validate_distribution.py 'C:\Program Files\Inno Setup 7\ISCC.exe'
```

Use o compilador da instalação padrão do Inno Setup 7 em `C:\Program Files\Inno Setup 7\ISCC.exe`. O diretório `build/tools/inno/` não é mais necessário; builds e validações usam o compilador instalado.

O validador usa AppId e diretório de dados separados dentro de `build/distribution-test`; o relatório `distribution-report.json` e demais resultados ficam nessa pasta temporária.

O spec restringe descoberta de DLLs ao Python do build e ao Windows para evitar ICU/UCRT externos vindos do PATH.

## Instalação e desinstalação

Configuração/cache/log padrão são removidos na desinstalação. O desinstalador pergunta sobre manter histórico; em modo silencioso o preserva, salvo `/DELETEHISTORY`. Não percorre dados migrados/junctions nem apaga caminhos personalizados de log/histórico. Configurações e histórico são do usuário; preservar compatibilidade na implementação da UI.

Leitura/junctions não exigem elevação geral do aplicativo. Symlinks dependem das permissões do Windows/Modo de Desenvolvedor; não prometer solicitação automática de elevação por operação. O pacote não é assinado digitalmente.

## Limites aceitos para a release inicial

Em 04/11/2026, o mantenedor dispensou o teste manual de sucesso de symlinks com privilégios apropriados e autorizou a release inicial. Windows limpo sem Python e Windows 10 também foram dispensados e permanecem não homologados. PATH isolado no host não substitui outra instalação do Windows. Acompanhar em [continuidade](CONTINUIDADE.md).

## Preparação da v1.0.0 e publicação

Os artefatos v1.0.0 foram reconstruídos e validados após a revisão manual. Preparar o commit aprovado, criar a tag `v1.0.0` nesse commit e deixar a release como rascunho até a autorização explícita para publicar. Anexar `dist/WinLink-Portable-1.0.0.zip` com a pasta inteira `WinLink/`, `dist/WinLink-Setup-1.0.0.exe` e `dist/SHA256SUMS.txt`. Não enviar o instalador de validação, caches ou diretórios intermediários. Preservar as tags e os assets publicados de versões anteriores. Usar as [notas de versão](NOTAS-DE-VERSAO.md).

Na raiz do repositório, após o build e a validação, gerar o ZIP portátil e os checksums:

```powershell
Compress-Archive -Path .\dist\WinLink -DestinationPath .\dist\WinLink-Portable-1.0.0.zip -CompressionLevel Optimal -Force
$packages = @('.\dist\WinLink-Portable-1.0.0.zip', '.\dist\WinLink-Setup-1.0.0.exe')
$checksums = foreach ($package in $packages) {
    $hash = Get-FileHash $package -Algorithm SHA256
    '{0}  {1}' -f $hash.Hash.ToLowerInvariant(), (Split-Path $package -Leaf)
}
[System.IO.File]::WriteAllLines(
    (Join-Path $PWD 'dist\SHA256SUMS.txt'),
    $checksums,
    [System.Text.UTF8Encoding]::new($false)
)
```

Publicar somente o ZIP portátil, o instalador e o arquivo de checksums como assets da release. Não anexar `WinLink-Validation-Setup.exe`.

Ao editar o texto da release no Windows, preservar UTF-8 explicitamente ao ler e gravar arquivos com caracteres acentuados; a codificação padrão do PowerShell pode corrompê-los. Depois de atualizar a release, confira o texto retornado pela API do GitHub em UTF-8. A renderização do terminal pode exibir caracteres incorretos mesmo quando o conteúdo remoto está correto.
