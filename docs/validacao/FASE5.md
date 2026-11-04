# Fase 5 — implementação e validação

Data: 2026-11-03 (America/Sao_Paulo).

**Estado: implementação entregue; homologação em máquina limpa ainda pendente.**
A implementação da fase 5 é a base do aplicativo antes do redesign. Não marcar o lançamento como aprovado antes da homologação externa.
Este relatório prevalece sobre os handoffs históricos e registra também o código encontrado já iniciado.
Mudanças anteriores foram preservadas; o working tree continua sem commit.

## Entregas verificadas

- Criação de junctions, symlinks de diretório, hard links e symlinks de arquivo na interface. Arquivos usam uma origem existente e um novo caminho de link; não substituem arquivos do usuário. Hard links exigem o mesmo volume.
- Descoberta de hard links com outro nome do mesmo arquivo como origem; propriedades, filtros, prévia e remoção do nome selecionado. Junções externas também podem ser gerenciadas pelo menu de contexto, com confirmação.
- Validação, prévia, estatísticas, criação e restauração em QThread. Uma operação mutável por vez; QThreadPool não é necessário para esse limite. O loop Qt continua atendendo eventos.
- Cancelamento cooperativo entre arquivos e em blocos de 1 MiB para arquivos maiores que 8 MiB. A cópia publica cada arquivo por rename, preservando colisões surgidas durante a operação e limpando temporários cancelados.
- Verificações de identidade, tamanho e modificação antes de substituir/remover árvores; alterações externas detectadas preservam os originais. Falha de restauração informa onde ficou o backup. Estas verificações não equivalem a um snapshot transacional do sistema de arquivos.
- Cache JSON atômico, vinculado aos diretórios da consulta; versões desconhecidas são rejeitadas. A janela exibe o cache ao abrir e sempre atualiza com uma varredura nova. F5 e operações concluídas não reutilizam uma lista antiga.
- Tamanho de diretórios calculado sob demanda nas propriedades, evitando percorrer novamente cada árvore durante a descoberta. QTableView solicita dados das células visíveis; teste com 10 mil registros e carregamento do cache em menos de 3 segundos.
- Histórico com filtros/exportação e ação para desfazer uma criação específica, revalidando a integridade do link antes de abrir o fluxo de desfazer.
- Ícone próprio na janela/executável, ícones da toolbar, Ctrl+F, Ctrl+H, Ctrl+vírgula, Ctrl+N, F5 e Ctrl+Q. Transições de 120 ms nos diálogos respeitam a preferência de animações do Windows.
- Confirmação destrutiva permanece obrigatória; a opção de configurações informa essa regra, em vez de oferecer uma preferência sem efeito.
- Build PyInstaller e instalador Inno Setup. Instalação por usuário, sem exigir administrador, em `%LOCALAPPDATA%\Programs\WinLink`; leitura/junctions não exigem elevação geral. Symlinks dependem das permissões do Windows.
- Desinstalação remove configurações/cache/log padrão e oferece manter/apagar histórico. Em modo silencioso preserva o histórico, salvo `/DELETEHISTORY`. Não percorre caminhos de junctions ou dados migrados.

## Evidências

- **278 testes passaram**, nenhum ignorado: `phase5-tests.xml`.
- Ruff, Black e mypy passaram. Mypy verifica corpos sem anotação nos 30 arquivos do aplicativo; os imports PyQt6 são tratados como APIs externas sem tipos por causa de sintaxe inválida nos stubs 6.12. Os stubs do fornecedor não foram alterados.
- Hard links/junctions reais, nomes Unicode, caminhos maiores que 260 caracteres, rollback, cancelamento, colisões e 10 mil registros exercitados em diretórios temporários isolados.
- Inspeção somente de leitura, sem recursão, de `D:\Cache` e `C:\Users\steff`: 0 e 17 links respectivamente; duração de 0,005 s e 0,011 s. Isto não mede uma varredura completa do perfil. Evidência: `phase5-readonly-scan.json`.
- Executável portátil e instalado abrem com PATH restrito ao sistema e sem PYTHONPATH/PYTHONHOME. Instalação/desinstalação testadas em diretório isolado do projeto e AppId de validação separado, nos dois modos de histórico; junction de teste e arquivo permaneceram intactos. Resultado: `phase5-distribution.json`.
- Estudos e capturas anteriores foram removidos após a consolidação. A referência de implementação é o [guia vigente](../IMPLEMENTACAO-UI.md) e o código da demo, sem relação com operações reais.

O primeiro executável apresentou erro ao importar QtWidgets. A causa foi a coleta de ICU/UCRT de ferramentas externas presentes no PATH do agente. O spec agora restringe os caminhos de descoberta ao Python do build e ao Windows; os testes isolados acima exercitam a correção. Não distribuir builds anteriores a essa correção.

## Reproduzir

```powershell
uv sync --extra dev --extra build
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check src resources
.venv\Scripts\python.exe -m black --check src resources
.venv\Scripts\python.exe -m mypy src
.\scripts\build.ps1 -Iscc 'C:\caminho\Inno Setup 6\ISCC.exe'
.venv\Scripts\python.exe scripts\validate_distribution.py 'C:\caminho\Inno Setup 6\ISCC.exe'
```

O validador instala apenas uma variante com identidade e diretório de dados próprios dentro de `build/distribution-test`; não instala o pacote de produção sobre uma instalação do usuário. Os diretórios e dados de teste são preservados para inspeção.

Artefatos: `dist/WinLink/WinLink.exe` (distribuir a pasta inteira) e `dist/WinLink-Setup-0.1.0.exe`.
O instalador ocupa 30.632.846 bytes (aproximadamente 29,2 MiB). Tamanho e SHA-256 estão em `phase5-artifacts.json`. A estimativa histórica de 100–200 MB não é um tamanho mínimo.
O instalador é offline; dependências e runtime Python acompanham o aplicativo.
Referências do empacotamento: [PyInstaller spec](https://pyinstaller.org/en/stable/spec-files.html), [Inno Setup](https://jrsoftware.org/ishelp/topic_admininstallmode.htm).

## Homologação externa necessária

1. Executar o instalador de produção em uma máquina/VM Windows limpa sem Python. Windows Sandbox não está disponível neste host. O teste com PATH isolado comprova independência dos caminhos de desenvolvimento, mas não substitui outro Windows.
2. Validar criação real de symlinks com Modo de Desenvolvedor ou privilégio apropriado. Neste host, a API negou a criação com erro 1314; o fluxo de falha e a preservação do arquivo foram testados. Não habilitamos privilégios nem alteramos configurações do Windows.
3. Confirmar compatibilidade no Windows 10 mínimo, além deste Windows 11. O build não foi assinado digitalmente.

## Auditoria do escopo histórico

Os documentos antigos usam "Fase 1/2/3" também como gerações do produto; isso não é a mesma numeração do PLANO, atual, com sete fases. O estado vigente está no [plano](../../PLANO.md).

| Requisito | Situação verificada |
| --- | --- |
| RF-01 a RF-07 | Descoberta nos diretórios configurados, lista, criação/prévia e desfazer implementados. "Todas as junções do sistema" exige configurar as raízes desejadas; não significa scan global obrigatório. |
| RF-08 | Sincronização foi explicitamente deixada para evolução do produto no backlog de evolução. Alterar destino/reconstruir pelo menu não foi entregue como fluxo dedicado; existem APIs do domínio. Não anunciar como funcionalidade da UI. |
| RF-09 | Integridade verificada durante varredura e antes de desfazer; verificação periódica é evolução descrita no backlog de evolução. |
| RF-10 | UI de arquivos implementada; hard links reais verificados. Sucesso real de symlinks depende da homologação de permissões acima. |
| RF-11 | Detecção/aviso sobre processos implementados. Encerrar processos automaticamente não faz parte do fluxo entregue. |
| RNF-01 a RNF-06 | Temas, threads, cache, dados sob demanda, confirmação, logs e backups cobertos pela suíte. Garantias absolutas contra mudanças simultâneas externas não são prometidas. |
| RNF-07/RNF-08 | Windows 11 atual validado; Windows 10/máquina limpa pendentes. Sem elevação automática por operação; o erro orienta conferir permissões. |

Não confundir essas divergências históricas com funcionalidades implementadas. Sincronização, edição/reconstrução dedicada, terminação automática de processos e elevação automática continuam fora da entrega atual e devem ser discutidas no escopo da evolução do produto.
