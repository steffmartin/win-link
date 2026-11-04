# Plano de desenvolvimento — WinLink

## Fases e estado

| Fase | Escopo | Estado |
|---|---|---|
| 1 | Planejamento e especificação | Concluída; escopo vigente consolidado na especificação |
| 2 | Infraestrutura Python/PyQt6, configurações e testes | Concluída |
| 3 | Domínio de links e operações de arquivos | Base entregue; não inclui todas as ideias históricas |
| 4 | Interface PyQt6 atual | Entregue |
| 5 | Integração, segurança, cache e distribuição | Implementação entregue; homologação externa pendente |
| 6 | Redesign, prototipagem e melhorias | Implementação PyQt6 e melhorias entregues; validação local aprovada |
| 7 | Documentação final e lançamento | Guia, capturas, notas e pacotes preparados; homologação e publicação pendentes |

## Fase 6 — implementação local do design aprovado

O estudo/protótipo externo foi revisado localmente. Não refazer o diagnóstico nem substituir a direção visual aprovada. Referências: [guia de implementação](../guias/IMPLEMENTACAO-UI.md), [demo](../../prototypes/ui/README.md), [especificação](../produto/ESPECIFICACAO.md) e [melhorias](MELHORIAS.md).

### 6.6 Redesign e melhorias aprovadas — implementados

- [x] Portar o shell de navegação, componentes, tokens, temas, estados e microcopy para PyQt6.
- [x] Manter toda a cobertura da lista, criação, prévia, progresso, reversão, propriedades, histórico e configurações detalhada no guia.
- [x] Reutilizar serviços Python, validação de identidade, cópia, cancelamento e recuperação; não transportar as simulações React.
- [x] Implementar tipo de link padrão persistente e migração compatível das configurações antigas.
- [x] Implementar restaurar padrões e descartar rascunho; restaurar prepara campos e exige salvar.
- [x] Ampliar histórico com resultado, datas manuais, detalhes e indicação de criação já desfeita; manter operação, períodos rápidos, total e verificação real antes de desfazer.
- [x] Distinguir symlinks de arquivo/diretório na apresentação e filtros sem criar tipo novo no domínio.
- [x] Acrescentar troca rápida de tema preservando modo automático.
- [x] Acrescentar reversão pelas propriedades com as mesmas confirmações e proteções.
- [x] Conectar Explorer, seletores, logs, notificações e preferências aos serviços reais. Retirar controles de cenário, exemplos e temporizadores da interface de produção.
- [x] Validar os fluxos e a migração de dados/preferências em diretórios de teste isolados.

### Critérios para concluir a implementação

Paridade com as funcionalidades existentes; novidades aprovadas implementadas; confirmação obrigatória e preservação mantidas; UI responsiva; temas claro/escuro/automático; teclado/foco e leitura de caminhos; rolagem até o último controle em janela reduzida e alta escala. Testes Python e verificações de estilo/tipos passando, com evidências das alterações. Não considerar testes da demo prova de segurança das operações reais.

## Homologação ainda pendente da fase 5

- Dispensado pelo mantenedor em 04/11/2026: instalar/executar em Windows limpo sem Python. Não executado; não equivale a aprovação.
- Dispensado pelo mantenedor em 04/11/2026: validar Windows 10 mínimo. Compatibilidade não homologada.
- [ ] Validar sucesso real de symlinks com Modo de Desenvolvedor/permissões apropriadas.

O build atual não é assinado. Evidências e limites: [validação](../validacao/FASE5.md).

## Fase 7 — documentação final e lançamento

- [x] Atualizar guia de instalação/uso e capturas a partir do aplicativo real após o redesign.
- [x] Documentar backup, reversão, permissões, recuperação, desinstalação e limites.
- [ ] Fechar homologação externa e revisar distribuição/offline e compatibilidade.
- [x] Definir licença MIT (decisão do mantenedor em 04/11/2026), manter versão 0.1.0 e preparar notas de versão.
- [ ] Publicar somente após os critérios técnicos e a revisão do usuário.

Ideias não aprovadas para esta entrega permanecem em [MELHORIAS.md](MELHORIAS.md), separadas da etapa 6.6.

## Checkpoint vigente — 04/11/2026, 17:49; validação final após o checkpoint

Implementação local da etapa 6.6 entregue; testes e evidências atuais em [REDESIGN.md](../validacao/REDESIGN.md). Após decisão do mantenedor, Windows limpo e Windows 10 foram dispensados; resta o teste manual de symlinks com privilégios. Evidência do host: este host Windows 11 tem Python instalado, não oferece Windows Sandbox e negou a criação real dos dois tipos de symlink com WinError 1314. O trabalho local não substitui esses testes nem autoriza anunciar lançamento homologado.

## Revisão de interface — 04/11/2026

Comparação posterior com o protótipo corrigiu ícones ausentes, posições/dimensões dos botões, criação em duas colunas, ações do histórico, largura das preferências e apresentação dos diálogos. Capturas vigentes substituídas. Validação: 308 testes Python e nove testes de layout em escala 200%, com dimensões reduzidas reais. Evidência consolidada em REDESIGN.md; a revisão não declara homologados os testes dispensados ou ainda pendentes.
