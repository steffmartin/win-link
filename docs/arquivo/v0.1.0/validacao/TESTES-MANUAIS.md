# Checklist de testes manuais — WinLink

Versão testada: 0.1.0 · Windows: 11 · Data: 04/11/2026

Registro histórico da validação manual da v0.1.0. As issues do GitHub são a fonte vigente de bugs e melhorias.

Use somente arquivos e pastas descartáveis. Prepare uma pasta com alguns arquivos, uma pasta vazia e um arquivo separado para testar links de arquivo. Escolha caminhos novos para cada criação. Antes de confirmar, confira qual é o **Local dos dados** e qual é o **Caminho do novo link**.

Em cada cenário, preencha **Resultado** com passou, falhou ou não testado e acrescente um comentário breve. Não é necessário guardar evidências. Quando houver várias opções no mesmo cenário, diga no comentário quais testou. Não precisa provocar falhas difíceis, alterar permissões do sistema ou encher o disco.

## Funcionamento

### 1. Abrir e navegar

Abra o aplicativo, visite as quatro páginas e confira a versão em Sobre. Se usar o portátil, mantenha toda a pasta `_internal` junto do executável.

**Esperado:** abre normalmente, com ícones e controles funcionando.

**Resultado:** __________ · **Comentário:** Na janela 'sobre' deveria ter link para o git do projeto, o botão de acesso a essa janela deveria ser um ícone de "?" e não um botão com texto. No menu lateral, selecionar uma opção cria uma borda branca ao redor do texto que some ao interagir com a janela, a linha não devia ser apresentada pois o menu (icon + text) já fica com fundo destacado. Botao de tema na tela principal tem um submenu (remover o submenu, os cliques intercambeaveis no botão trocam o tema entre dark light auto, é preciso ter um ícone para o auto).

### 2. Configurações

Configure somente a pasta de testes para descoberta. Altere o tipo de link padrão e a preferência de backup, salve e reabra. Experimente Descartar alterações e Restaurar padrões sem salvar.

**Esperado:** o que foi salvo persiste; descartar recupera os valores salvos; restaurar padrões só prepara alterações até clicar em Salvar. A confirmação de operações destrutivas permanece obrigatória.

**Resultado:** __________ · **Comentário:**  A pagina de configurações não está responsiva (reduzir tamanho está ok mas ao maximizar a janela os componentes não acompanham). O "confirmar operações destrutivas" é obrigatório e não pode ser desabilitado mas o checkbox tem a mesma cor dos demais, colocar ele com efeito disabled. Os 4 checkbox devem ter um ícone de 'info' que abre um tooltip com o que aquela opção faz, também para o 'tipo de link padrao'. O botão de salvar (Já azul) não apresenta nenhum efeito hover/click como os demais, ele deve ter efeitos de ação.

### 3. Criar junction

Crie uma junction apontando para a pasta com arquivos. Abra os arquivos pelo novo link. Repita com uma pasta de dados nova/vazia.

**Esperado:** o link permite acessar os dados corretos; os arquivos originais continuam intactos.

**Resultado:** __________ · **Comentário:** O ícone "i" parece um emoji e não um SVG, tem um fundo azul e não transparente, este ícone esta fora do padrão do app. Ao criar uma junção com sucesso, aparecem 2 janelas de confirmação (a de progresso e o dialog), é desnecessário o dialog já que a de progresso traz o feedback. Após criação com sucesso, o formulário deveria ser resetado mas continua preenchido. Após criar a junction, ela é marcada como 'inacessível', e acessar propriedades e depois 'abrir destino' faz o programa fechar, ao reiniciar o programa a mesma junção apareceu como ativo e sem erro ao abrir destino.

### 4. Migrar uma pasta existente

Use uma cópia descartável com arquivos no caminho que será o link e escolha uma pasta nova como local dos dados. Revise a prévia e confirme.

**Esperado:** os arquivos ficam no local dos dados e continuam acessíveis pelo endereço anterior, agora como link, sem perda de conteúdo.

**Resultado:** __________ · **Comentário:** Na tela 'Criar Novo' mudar os labels "1. Local dos dados (Origem)" para "1. Ponto de Acesso" e "2. Caminho do novo link" para "2. Dados Físicos", as nomenclaturas origem/destino confundem. A prévia no cenário onde origem é uma nova pasta e destino é uma pasta existente está confusa, a prévia diz que o diretório de origem existe e que irá criar o diretório de 'origem' em vez destino, e diz que criará a junção duas vezes (a junção é criada corretamente apesar disso). Clicar nos botões de 'procurar' pasta logo após selecionar uma pasta não navega para a pasta já selecionada.

### 5. Links de arquivo e symlinks

Crie um hard link para o arquivo separado, no mesmo volume. Se seu Windows permitir, teste também symlink de arquivo e de diretório. Abra o conteúdo pelos links. Use nomes novos em cada tentativa.

**Esperado:** cada link aponta para o conteúdo correto e aparece com o tipo certo. Se faltar permissão para symlink, o aplicativo informa a falha e preserva os dados; isso não comprova o caminho de sucesso. Não é necessário alterar as permissões do Windows.

**Resultado:** __________ · **Comentário (tipos testados):** Padronizar os ícones de info "I" na janela de prévia. O hardlink funcionou com txt mas com um docx após criar o arquivo ele apareceu, mas ao editar o arquivo original no word o arquivo 'linkado' sumiu. Já o symlink de arquivo funcionou com ambas extensões, para criar o symlink foi preciso executar como administrador (a janela de erro antes fala sobre 'permissões do volume', altere para 'execute como administrador', além disso as opções de criar symlink devem ter o ícone de 'escudo' típico de proteção elevada).

### 6. Descoberta e atualização

Atualize a lista após criar links. Feche e reabra o aplicativo; use F5 e Início. Se tiver um link criado fora do app na pasta de testes, confira se ele também aparece.

**Esperado:** encontra os links das pastas configuradas, atualiza sem travar e não duplica itens. Início limpa busca/filtros e atualiza.

**Resultado:** __________ · **Comentário:** Se abrir a tela de propriedades com duplo clique no item, o botão 'fechar' da janela de propriedades reabre a janela e é preciso fechar novamente, não reabrindo na segunda vez, este comportamento não ocorre se abrir a janela de propriedades pelos 3 pontinhos. Não consegui identificar com o filtro 'Manual' nenhum item, todos já existentes caíram no filtro 'Existente'.

### 7. Lista, busca e filtros

Alterne cartões/visão compacta; busque pelos dois caminhos; combine filtros de tipo, status e criador; teste ordenação. Mude um filtro e cancele; depois aplique. Busque algo inexistente.

**Esperado:** resultados e contagens coerentes; cancelar preserva filtros anteriores; ausência de resultados é clara.

**Resultado:** __________ · **Comentário:** A visão compacta mostra uma tabela com linhas largas (não é compacto) e o lado esquerdo da tabela tem um espaço extra sem informação como uma coluna vazia. Padronize os nomes 'Caminho do link' e 'Local dos dados' na ordenação para 'Ponto de Acesso' e 'Dados Físicos'. Os inputs de ordenação devem ficar no dialog de filtro (melhoria), e o 'inicio' que serve para reservar filtros deve ficar ao lado do botão de filtros com nome apropriado (melhoria).

### 8. Propriedades e abertura de pastas

Abra propriedades por duplo clique ou menu de contexto. Confira caminhos, tipo, estatísticas e histórico relacionado; recalcule e use as ações de abrir pasta disponíveis.

**Esperado:** informações correspondem ao link selecionado e o Explorer abre o local correto.

**Resultado:** __________ · **Comentário:** Abrir as propriedades do link existente "8311edb5893cb8d699a0ec62c6ef8eef" estoura o layout da tela devido ao tamanho do path. Algumas junções marcadas como inacessível (como "Recent") estão acessíveis e foi possível abrir as duas pastas.

### 9. Desfazer links de diretório

Em cópias novas para cada tentativa, teste remover somente o link, mover os arquivos de volta e duplicar. Teste manter origem como backup quando disponível. Confira os arquivos nos caminhos informados depois de cada operação.

**Esperado:** cada estratégia faz o que a prévia descreve; remover somente o link mantém os dados no local original e deixa pasta vazia no endereço do link; restauração e backup preservam o conteúdo conforme escolhido.

**Resultado:** __________ · **Comentário (estratégias testadas):** . A lista so é atualizada após um tempo, no caso de criação/remoção de links deve ser feita a varreduda instantânea do objeto afetado para já adicionar ou remover o mesmo do cache.

### 10. Desfazer links de arquivo

Desfaça o hard link criado no cenário 5 e os symlinks de arquivo que conseguiu criar. Abra o arquivo original depois.

**Esperado:** remove apenas o nome do link escolhido; o arquivo original e seu conteúdo permanecem acessíveis. Não oferece mover/duplicar pastas para um link de arquivo.

**Resultado:** __________ · **Comentário:** remoção de link de arquivo só tem uma opção (remover arquivo de ponto de acesso), funcionou mas devia ter as mesmas 3 opções.

### 11. Histórico

Confira criações/reversões e seus detalhes. Experimente filtros de operação, resultado e datas. Exporte com um filtro ativo: o arquivo deve conter todo o histórico. Ao final dos demais testes, tente Limpar, primeiro cancelando e depois confirmando.

**Esperado:** registros corretos; exportação completa; cancelar não limpa; confirmar limpa registros sem apagar links ou dados. Não é necessário guardar a exportação.

**Resultado:** __________ · **Comentário:**

### 12. Tema, teclado e janela pequena

Teste claro/escuro e Seguir sistema, os atalhos principais (Ctrl+N, Ctrl+H, Ctrl+vírgula, Ctrl+F, F5), Tab e Escape. Diminua a janela e confira se alcança todos os controles por rolagem. Use Abrir pasta de logs nas configurações.

**Esperado:** leitura e foco claros, sem controles cortados; atalhos funcionam; pasta de logs abre. Se disponível, confira também escala de tela alta.

**Resultado:** __________ · **Comentário:**

## Travas de segurança

### 13. Entradas inválidas e conflitos

Tente criar com campos vazios, caminhos relativos, caminhos iguais ou um dentro do outro; tente usar pasta para hard link e arquivo inexistente para link de arquivo. Tente criar sobre um link/arquivo já existente. Na migração, prepare arquivos de mesmo nome e conteúdos diferentes nos dois lados.

**Esperado:** bloqueia entradas incompatíveis e conflitos sem sobrescrever dados. Uma pasta normal existente só pode ser migrada pelo fluxo explícito de prévia e confirmação.

**Resultado:** __________ · **Comentário (tentativas realizadas):**

### 14. Cancelamento e confirmação

Feche a prévia de criação e a confirmação de reversão sem confirmar. Se uma cópia durar tempo suficiente, clique Cancelar durante a operação e aguarde. Durante essa operação, tente iniciar outra ou fechar o app, sem forçar encerramento pelo Windows.

**Esperado:** cancelar antes de confirmar não altera nada; cancelamento em andamento preserva dados e informa o resultado; impede operação concorrente e fechamento inseguro. Se a cópia terminar rápido demais, registre essa parte como não testada.

**Resultado:** __________ · **Comentário:**

### 15. Link quebrado e reversão repetida

Em uma junction descartável, renomeie temporariamente a pasta dos dados, atualize e confira o aviso; restaure o nome ao terminar. Após uma reversão bem-sucedida, tente desfazer novamente a mesma criação pelo histórico.

**Esperado:** caminho indisponível não é apresentado como pasta vazia válida; ações que não possam preservar/verificar os dados são impedidas. Criação já desfeita não é revertida novamente.

**Resultado:** __________ · **Comentário:**

### 16. Identidade substituída (opcional)

Descubra um hard link descartável. Sem atualizar a seleção no app, remova pelo Explorer somente esse novo nome, preservando o arquivo base, e crie um arquivo normal diferente no mesmo caminho. Tente desfazer a seleção antiga.

**Esperado:** recusa remover o substituto; preserva tanto o arquivo novo quanto o arquivo base. Pule este cenário se não estiver seguro sobre qual nome remover.

**Resultado:** __________ · **Comentário:**

### 17. Instalar e desinstalar (opcional)

Somente em conta/ambiente de testes: instale, abra e depois desinstale, escolhendo manter ou apagar o histórico. Confira os arquivos de teste e destinos dos links depois.

**Esperado:** instalação funciona; desinstalação respeita a escolha do histórico e não apaga os dados acessados pelos links. Não use a instalação pessoal para provocar esse cenário.

**Resultado:** __________ · **Comentário:** MIT deve ter versão em português e inglês conforme interface do instalador (o instalador já reconhece o idioma). Foi possível abrir 2 instâncias após instalar, o que não é desejável (reabrir o link vai pra instancia já aberta). O fechamento fica travado até o scan terminar, devia interromper o scan salvando o que já foi encontrado. Instalação limpa está trazendo 2 diretórios pré configurados indevidamente, assim como ao restaurar padrões, o diretorio padrao inicial deve ser apenas a pasta do usuario e nao deve ficar fixo no perfil deste usuário.

## Revisão posterior

Comentários gerais:

Conclusão após revisar os cenários preenchidos:

Issues relacionadas ou abertas, **somente se a revisão indicar necessidade**:

Uma observação pode ser comportamento esperado, limitação do ambiente, dúvida de uso ou defeito/melhoria. Conferir as [Issues existentes](https://github.com/steffmartin/win-link/issues) antes de abrir outra. Funcionalidades já propostas, como manual no menu Ajuda, filtro inicial salvo e desativação de tipos de link, ainda não são requisitos entregues da v0.1.0.

Este checklist não exige provocar falta de espaço, falha de disco, falha de gravação de histórico ou de limpeza. Se ocorrerem naturalmente, comente no cenário correspondente e não repita uma operação sem conferir os dados. Os testes antes dispensados para a release continuam dispensados; itens não executados aqui não contam como aprovados.
