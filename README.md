# WinLink - Gerenciador de Junções NTFS

Aplicativo Windows para gerenciamento de junções NTFS (NTFS Junctions) e links simbólicos. Permite criar, listar, gerenciar e desfazer links de diretórios e arquivos no sistema de arquivos NTFS com interface moderna compatível com Windows 11.

## Visão Geral

WinLink é uma interface gráfica para o conceito de junções NTFS, que permite que diretórios apontem para outros diretórios de forma transparente para o sistema operacional e a maioria das aplicações. É inspirado no script `migrar_pastas.ps1` existente, mas com funcionalidades expandidas e uma interface amigável.

## Funcionalidades Principais

- **Listagem Automática**: Descobre e lista todas as junções NTFS e links simbólicos do sistema
- **Criação de Junções**: Cria novas junções preservando arquivos existentes
- **Gerenciamento**: Permite desfazer, modificar e sincronizar junções
- **Suporte a Arquivos**: Suporte a hard links e symbolic links para arquivos (se suportado pelo Windows)
- **Interface Moderna**: Tema claro/escuro automático, design compatível com Windows 11
- **Segurança**: Validações, backups automáticos e proteção contra perda de dados

## Motivação

Muitos usuários Windows utilizam junções NTFS para mover pastas do perfil de usuário para outros discos (ex: `D:\Cache`), economizando espaço no SSD principal. O processo atual usando scripts PowerShell pode ser intimidador para usuários menos técnicos. WinLink torna esse processo acessível através de uma interface gráfica intuitiva.

## Status do Projeto

🚧 **Em Desenvolvimento**

Atualmente na fase de planejamento e especificação. Veja o plano de desenvolvimento em [PLANO.md](PLANO.md).

## Documentação

- [Especificação do Sistema](ESPECIFICACAO.md) - Requisitos funcionais e não-funcionais detalhados
- [Plano de Desenvolvimento](PLANO.md) - Fases e etapas do projeto
- [Tecnologias](TECNOLOGIAS.md) - Stack tecnológico e justificativas
- [Protótipo de Interface](PROTOTIPO.md) - Mockups e wireframes da interface

## Instalação

*Em desenvolvimento*

## Uso

*Em desenvolvimento*

## Contribuindo

Este é um projeto pessoal. Consulte o [PLANO.md](PLANO.md) para entender o roadmap.

## Licença

*Pendente de definição*

## Referências

- Script de referência: `D:\Cache\migrar_pastas.ps1`
- Documentação NTFS Junctions da Microsoft
- Windows 11 Design Guidelines
