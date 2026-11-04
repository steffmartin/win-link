# Plano de desenvolvimento — WinLink

## Fases e estado

| Fase | Escopo | Estado |
|---|---|---|
| 1 | Planejamento e especificação | Concluída; escopo vigente consolidado na especificação |
| 2 | Infraestrutura Python/PyQt6, configurações e testes | Concluída |
| 3 | Domínio de links e operações de arquivos | Base entregue; não inclui todas as ideias históricas |
| 4 | Interface PyQt6 atual | Entregue |
| 5 | Integração, segurança, cache e distribuição | Implementação entregue; homologação externa pendente |
| 6 | Redesign, prototipagem e melhorias | Protótipo visual aprovado e cobertura acrescida; implementação local é o próximo trabalho |
| 7 | Documentação final e lançamento | Pendente |

## Fase 6 — implementação local do design aprovado

O estudo/protótipo externo foi revisado localmente. Não refazer o diagnóstico nem substituir a direção visual aprovada. Referências: [guia de implementação](../guias/IMPLEMENTACAO-UI.md), [demo](../../prototypes/ui/README.md), [especificação](../produto/ESPECIFICACAO.md) e [melhorias](MELHORIAS.md).

### 6.6 Redesign e melhorias aprovadas — próxima etapa

- [ ] Portar o shell de navegação, componentes, tokens, temas, estados e microcopy para PyQt6.
- [ ] Manter toda a cobertura da lista, criação, prévia, progresso, reversão, propriedades, histórico e configurações detalhada no guia.
- [ ] Reutilizar serviços Python, validação de identidade, cópia, cancelamento e recuperação; não transportar as simulações React.
- [ ] Implementar tipo de link padrão persistente e migração compatível das configurações antigas.
- [ ] Implementar restaurar padrões e descartar rascunho; restaurar prepara campos e exige salvar.
- [ ] Ampliar histórico com resultado, datas manuais, detalhes e indicação de criação já desfeita; manter operação, períodos rápidos, total e verificação real antes de desfazer.
- [ ] Distinguir symlinks de arquivo/diretório na apresentação e filtros sem criar tipo novo no domínio.
- [ ] Acrescentar troca rápida de tema preservando modo automático.
- [ ] Acrescentar reversão pelas propriedades com as mesmas confirmações e proteções.
- [ ] Conectar Explorer, seletores, logs, notificações e preferências aos serviços reais. Retirar controles de cenário, exemplos e temporizadores da interface de produção.
- [ ] Validar os fluxos e a migração de dados/preferências em diretórios de teste isolados.

### Critérios para concluir a implementação

Paridade com as funcionalidades existentes; novidades aprovadas implementadas; confirmação obrigatória e preservação mantidas; UI responsiva; temas claro/escuro/automático; teclado/foco e leitura de caminhos; rolagem até o último controle em janela reduzida e alta escala. Testes Python e verificações de estilo/tipos passando, com evidências das alterações. Não considerar testes da demo prova de segurança das operações reais.

## Homologação ainda pendente da fase 5

- [ ] Instalar/executar em Windows limpo sem Python.
- [ ] Validar Windows 10 mínimo, além do host Windows 11 usado nos testes.
- [ ] Validar sucesso real de symlinks com Modo de Desenvolvedor/permissões apropriadas.

O build atual não é assinado. Evidências e limites: [validação](../validacao/FASE5.md).

## Fase 7 — documentação final e lançamento

- [ ] Atualizar guia de instalação/uso e capturas a partir do aplicativo real após o redesign.
- [ ] Documentar backup, reversão, permissões, recuperação, desinstalação e limites.
- [ ] Fechar homologação externa e revisar distribuição/offline e compatibilidade.
- [ ] Definir licença, versão e notas de lançamento.
- [ ] Publicar somente após os critérios técnicos e a revisão do usuário.

Ideias não aprovadas para esta entrega permanecem em [MELHORIAS.md](MELHORIAS.md), separadas da etapa 6.6.
