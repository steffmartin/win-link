# Especificação do Sistema - WinLink

## 1. Visão Geral

WinLink é um aplicativo Windows para gerenciamento de junções NTFS (NTFS Junctions), permitindo aos usuários criar, listar, gerenciar e desfazer links simbólicos/junções de diretórios e arquivos no sistema de arquivos NTFS. O sistema segue os mesmos princípios do script `migrar_pastas.ps1` existente, mas com uma interface gráfica moderna e funcionalidades adicionais.

## 2. Definições

### 2.1 Junção NTFS (NTFS Junction)
Uma junção NTFS é um tipo especial de reparse point no sistema de arquivos NTFS que permite que um diretório aponte para outro diretório. Diferente de atalhos, junções são transparentes para a maioria das aplicações e do sistema operacional.

### 2.2 Link Simbólico (Symbolic Link)
Um link simbólico pode apontar para diretórios ou arquivos e é mais flexível que junções, mas requer permissões especiais.

### 2.3 Origem (Source)
Pasta onde os arquivos realmente existem (ex: `D:\Cache\.vscode`).

### 2.4 Destino (Target)
Pasta que direciona para a origem (ex: `C:\Users\steff\.vscode`).

## 3. Requisitos Funcionais

### 3.1 Descoberta e Listagem de Junções

#### RF-01: Listagem Automática
O sistema deve identificar e listar todas as junções NTFS e links simbólicos existentes no sistema, incluindo:
- Diretórios em `C:\Users\<usuario>` e subdiretórios
- Outras localizações configuráveis pelo usuário
- Detecção de atributos `ReparsePoint` no sistema de arquivos

#### RF-02: Descoberta Guiada
Se a listagem automática não for completa, o sistema deve permitir descoberta guiada onde o usuário pode:
- Especificar diretórios para escanear
- Adicionar manualmente junções conhecidas
- Importar configurações de scripts ou arquivos de registro

#### RF-03: Informações da Lista
Cada item na lista deve exibir:
- **Caminho de Origem**: Localização real dos arquivos
- **Caminho de Destino**: Localização da junção
- **Criador**: Classificação de origem (App, Existente, SO, Usuário)
- **Tipo**: Junção NTFS ou Link Simbólico
- **Tamanho**: Tamanho total dos arquivos na origem
- **Data de Criação**: Quando a junção foi criada
- **Status**: Ativo, Quebrado, ou Inacessível

### 3.2 Criação de Junções

#### RF-04: Criação com Preservação
O sistema deve permitir criar novas junções seguindo o modelo do script anexo:
- Arquivos existentes no destino são preservados
- Se o destino existir, os arquivos são copiados para a origem antes de criar a junção
- Se o destino já for uma junção, não é modificado
- Cópia preserva atributos, timestamps e metadados (equivalente a `robocopy /E /COPY:DAT`)

#### RF-05: Criação de Nova Pasta
Se a pasta de origem não existir:
- Criar diretório de origem vazio
- Criar junção apontando para a origem
- Opção opcional de iniciar com arquivos template

#### RF-06: Validação Antes de Criação
Antes de criar uma junção, o sistema deve:
- Verificar se o destino já é uma junção
- Verificar se há arquivos em uso que bloqueariam a operação
- Calcular espaço necessário no disco
- Solicitar confirmação do usuário

### 3.3 Gerenciamento de Junções

#### RF-07: Desfazer Junção
O sistema deve permitir desfazer junções com opções:
- **Remover apenas a junção**: Deixa a junção como diretório normal vazio
- **Mover arquivos de volta**: Move arquivos da origem para o destino
- **Duplicar arquivos**: Copia arquivos da origem para o destino sem remover da origem
- **Manter origem**: Mantém os arquivos na origem como backup

#### RF-08: Atualização de Junção
O sistema deve permitir modificar uma junção existente:
- Alterar o destino da junção
- Reconstruir junção quebrada
- Sincronizar arquivos entre origem e destino

#### RF-09: Verificação de Integridade
O sistema deve periodicamente ou sob demanda:
- Verificar se a origem ainda existe
- Verificar se a junção está funcional
- Identificar junções quebradas ou órfãs

### 3.4 Suporte a Arquivos

#### RF-10: Junção de Arquivos
Se o Windows permitir junção de arquivos (hard links ou symbolic links para arquivos), o sistema deve suportar:
- Criação de hard links para arquivos
- Criação de symbolic links para arquivos
- Listagem e gerenciamento de links de arquivos
- Distinção visual entre links de diretórios e arquivos

### 3.5 Gerenciamento de Processos

#### RF-11: Detecção de Arquivos em Uso
Antes de operações que movem/copiam arquivos, o sistema deve:
- Identificar processos que podem ter arquivos abertos
- Oferecer opção de encerrar processos automaticamente
- Sugerir ao usuário quais processos fechar manualmente
- Permitir operação se os arquivos não estiverem bloqueados

## 4. Requisitos Não-Funcionais

### 4.1 Interface

#### RNF-01: Tema Windows 11
- Interface moderna compatível com Windows 11
- Suporte a tema claro e escuro seguindo configuração do sistema
- Uso de Fluent Design System (Mica, Acrylic, etc.)
- Ícones modernos e consistentes com padrões Windows 11

#### RNF-02: Responsividade
- Interface adaptável a diferentes tamanhos de janela
- Suporte a monitores com alto DPI (scaling)
- Layout que funciona bem em telas pequenas e grandes

### 4.2 Performance

#### RNF-03: Listagem Rápida
- Listagem de junções deve ser rápida (< 3 segundos para sistemas típicos)
- Operações de escaneamento não devem bloquear a interface
- Lazy loading para grandes quantidades de junções

#### RNF-04: Operações em Segundo Plano
- Operações de cópia/movimentação de arquivos devem ser executadas em segundo plano
- Progresso visível ao usuário
- Capacidade de cancelar operações em andamento

### 4.3 Segurança

#### RNF-05: Validação de Operações
- Operações destrutivas devem exigir confirmação explícita
- Undo/redo para operações críticas (se possível)
- Log de todas as operações realizadas

#### RNF-06: Proteção Contra Perda de Dados
- Nunca apagar arquivos sem confirmação
- Backup automático antes de operações destrutivas
- Rollback automático em caso de falha durante operação

### 4.4 Compatibilidade

#### RNF-07: Versões do Windows
- Suporte mínimo: Windows 10 (versão 1903 ou superior)
- Otimizado para: Windows 11
- Requer permissões de administrador para algumas operações

#### RNF-08: Permissões
- Funcionalidades básicas sem elevação (leitura, listagem)
- Elevation request para operações que requerem administrador
- Detecção de privilégios e UI adaptativa

## 5. Casos de Uso

### UC-01: Listar Junções Existentes
**Ator**: Usuário
**Pré-condições**: Aplicativo aberto
**Fluxo Principal**:
1. Usuário abre o aplicativo
2. Sistema automaticamente escaneia e lista todas as junções
3. Usuário visualiza lista com origem, destino, criador e status
4. Usuário pode filtrar, ordenar e buscar na lista

### UC-02: Criar Nova Junção
**Ator**: Usuário
**Pré-condições**: Aplicativo aberto, usuário com permissões
**Fluxo Principal**:
1. Usuário clica em "Nova Junção"
2. Usuário informa caminho de destino (ex: `C:\Users\steff\.vscode`)
3. Usuário informa caminho de origem (ex: `D:\Cache\.vscode`)
4. Sistema valida caminhos e verifica pré-condições
5. Sistema mostra preview do que será feito
6. Usuário confirma
7. Sistema cria junção, copiando arquivos se necessário
8. Sistema notifica sucesso

**Fluxos Alternativos**:
- 4a: Destino já é junção → Sistema avisa e aborta
- 4b: Arquivos em uso → Sistema sugere fechar programas
- 4c: Espaço insuficiente → Sistema avisa e aborta

### UC-03: Desfazer Junção
**Ator**: Usuário
**Pré-condições**: Junção selecionada na lista
**Fluxo Principal**:
1. Usuário seleciona uma junção
2. Usuário clica em "Desfazer"
3. Sistema apresenta opções (remover, mover, duplicar)
4. Usuário escolhe opção
5. Sistema executa operação escolhida
6. Sistema atualiza lista

### UC-04: Gerenciar Junção Existente
**Ator**: Usuário
**Pré-condições**: Junção existente criada fora do app
**Fluxo Principal**:
1. Sistema detecta junção criada manualmente (ex: pelo script)
2. Sistema classifica como "Existente"
3. Usuário pode visualizar detalhes e gerenciar
4. Usuário pode desfazer ou modificar a junção

### UC-05: Sincronizar Arquivos
**Ator**: Usuário
**Pré-condições**: Junção ativa com arquivos em ambos os lados
**Fluxo Principal**:
1. Usuário seleciona junção
2. Usuário clica em "Sincronizar"
3. Sistema compara arquivos em origem e destino
4. Sistema mostra diferenças
5. Usuário confirma sincronização
6. Sistema sincroniza arquivos

## 6. Limitações e Restrições

### 6.1 Limitações Técnicas
- Hard links funcionam apenas no mesmo volume
- Links simbólicos podem requerer configuração de desenvolvedor no Windows
- Algumas operações requerem elevação de privilégios
- Aplicativos que monitoram mudanças no sistema podem reagir à criação de junções

### 6.2 Restrições de Desenvolvimento
- Durante o desenvolvimento, nenhuma junção real deve ser modificada
- Todas as operações de teste devem usar pasta de teste dedicada
- Validação deve ser feita em ambiente isolado

## 7. Dados de Referência para Validação

### 7.1 Pastas Conhecidas
Para validação inicial, o sistema deve detectar:
- Junções em `D:\Cache` apontando para `C:\Users\steff`
- Junção específica: `C:\Users\steff\OneDrive\Documentos\Finanças\Backup jFinanças\auto`

Essas devem aparecer como criadas "por fora do app" (status: Existente).

## 8. Integrações

### 8.1 Integração com Script Existente
O sistema deve ser capaz de:
- Ler configurações do script `migrar_pastas.ps1`
- Importar listas de pastas do script
- Coexistir com operações manuais do script

### 8.2 Integração com OneDrive
Reconhecer e respeitar links criados pelo OneDrive ou que envolvam pastas OneDrive, considerando:
- Sincronização do OneDrive pode interagir com junções
- Pastas OneDrive podem ter comportamento especial
