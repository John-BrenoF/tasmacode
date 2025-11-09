# Tasmacode - Editor de Código via Terminal

![Tasmacode Welcome Screen](midias/icon/buo.jpeg "Tela de boas-vindas do Tasmacode")

## 1. Introdução e Objetivo

**Tasmacode** é um editor de código leve e rápido que roda diretamente no seu terminal. Inspirado na eficiência de editores como Vim, mas com uma curva de aprendizado muito mais suave, seu objetivo é fornecer uma experiência de desenvolvimento ágil e descomplicada, focada no essencial.

A filosofia do Tasmacode é ser:
- **Simples de Usar**: Atalhos intuitivos baseados em `Ctrl` e `Alt`, familiares para a maioria dos usuários.
- **Leve e Rápido**: Inicia instantaneamente e consome poucos recursos, ideal para qualquer máquina.
- **Extensível na Medida Certa**: Oferece funcionalidades modernas como integração Git, terminal embutido e navegação de código, sem sobrecarregar o usuário.

## 2. Arquitetura e Estrutura do Projeto

O Tasmacode é construído em Python usando a biblioteca `curses` para renderizar sua interface no terminal. A arquitetura é modular, com cada componente cuidando de uma parte específica da interface ou da lógica.

### Como Tudo se Comunica

O fluxo principal é orquestrado pelo arquivo `main.py`. Ele funciona em um ciclo contínuo:

1.  **`main.py`**: Inicia todos os componentes (Editor, Sidebar, Console, etc.).
2.  **Loop Principal**:
    a. **`draw()`**: Desenha a interface de todos os componentes visíveis na tela (abas, texto, sidebar, status bar).
    b. **`getch()`**: Aguarda a entrada do usuário (uma tecla pressionada).
    c. **`handle_key()`**: A tecla é enviada para o `key_handler.py`, que atua como um cérebro central.
3.  **`key_handler.py`**: Analisa a tecla e o contexto atual (qual janela está ativa?) e delega a ação para o módulo apropriado. Por exemplo, se o usuário pressionar `Ctrl+S`, o `key_handler` chama o método `save_file()` do `Editor`. Se pressionar uma seta na `Sidebar`, ele chama os métodos de navegação da `Sidebar`.

Essa arquitetura centralizada no `key_handler` mantém a lógica de interação organizada e desacoplada dos componentes da interface do usuário.

### Explicação dos Arquivos Principais

- **`main.py`**: O coração do aplicativo. Responsável por inicializar o `curses`, gerenciar o ciclo principal de desenho e entrada, e orquestrar a exibição de todos os outros componentes.
- **`key_handler.py`**: O cérebro do editor. Captura todas as teclas pressionadas e decide qual ação tomar, delegando para os outros módulos. É aqui que os atalhos são mapeados para as suas respectivas funções.
- **`editor.py`**: Gerencia os buffers de texto. Cuida da lógica de edição, como inserir/deletar caracteres, movimentar o cursor, copiar, colar, desfazer/refazer e gerenciar as abas.
- **`sidebar.py`**: Controla a barra lateral de arquivos e pastas. Lida com a navegação no sistema de arquivos, abertura de projetos, criação, renomeação e exclusão de itens.
- **`console.py`**: Implementa o painel do terminal integrado. Permite executar comandos no shell, capturar a saída e exibi-la na interface.
- **`structbar.py`**: A barra de estrutura de código. Analisa o arquivo aberto usando expressões regulares (`regex`) para encontrar definições de classes e funções, permitindo navegar rapidamente pelo código.
- **`find_replace.py`**: Contém a lógica para a funcionalidade de "Localizar e Substituir" (`Shift+S`), gerenciando a busca interativa e as substituições.
- **`execution_handler.py`**: Define como executar diferentes tipos de arquivos (`.py`, `.js`, `.c`, etc.) quando o atalho `Ctrl+E` é pressionado.
- **`help_window.py`, `git_window.py`, `config_window.py`, `whats_new_window.py`**: Módulos que implementam janelas pop-up para funcionalidades específicas (Ajuda, Git, Configurações, Novidades), cada um gerenciando seu próprio estado e desenho.
- **`utils.py`**: Uma coleção de funções utilitárias usadas em todo o projeto, como prompts para o usuário, manipulação do sistema de arquivos e abertura de terminais externos.

## 3. Recursos e Mecânicas
s<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/bc4d75c5-bcbd-4ec3-bea1-47539ff68837" />


- **Edição de Texto Moderna**: Suporte a múltiplas abas, destaque de sintaxe para várias linguagens, seleção de texto, duplicar linha, mover linha para cima/baixo e comentar/descomentar código.
- **Gerenciamento de Projeto**: Uma barra lateral (`Ctrl+F`) para navegar facilmente entre arquivos e pastas. Permite criar, renomear e deletar itens diretamente.
- **Execução de Código Integrada**: Execute o arquivo atual com `Ctrl+E`. A saída aparece no console integrado, que pode ser alternado com `Alt+T`.
- **Navegação Rápida de Código**: A barra de estrutura (`Alt+L`) lista todas as funções e classes do arquivo, permitindo pular diretamente para uma definição.
- **Busca Poderosa**:
    - **Localizar e Substituir**: Busca interativa no arquivo atual com `Shift+S`.
    - **Busca no Projeto**: Procure por texto em todos os arquivos do projeto com `Ctrl+Shift+F`.
- **Integração com Git**: Uma janela dedicada (`Alt+G`) para visualizar o status dos arquivos, adicionar (`S`), confirmar (`C`), enviar (`Shift+P`) e baixar (`p`) alterações.
- **Servidor Local**: Inicie um servidor web simples na pasta do seu projeto com `Alt+S`, útil para desenvolvimento front-end.
- **Customização**: Altere configurações como tema, visibilidade de números de linha e modo de navegação Vim (`h,j,k,l`) através da janela de configurações (`Alt+C`).

## 4. Atalhos

Esta é uma lista completa dos atalhos disponíveis no Tasmacode.

### Atalhos Globais
| Atalho | Função |
|---|---|
| `Ctrl + Q` | Sair do editor (com confirmação se houver alterações não salvas) |
| `Ctrl + S` | Salvar o arquivo atual |
| `Ctrl + N` | Abrir uma nova aba (arquivo em branco) |
| `Ctrl + W` | Fechar a aba atual |
| `Ctrl + Tab` | Ir para a próxima aba |
| `Shift + Ctrl + Tab` | Ir para a aba anterior |
| `F1` | Mostrar/Esconder a janela de ajuda |
| `Alt + N` | Mostrar a janela de novidades da versão |

### Painéis e Ferramentas
| Atalho | Função |
|---|---|
| `Ctrl + F` | Mostrar/Esconder a barra lateral de arquivos (Sidebar) |
| `Alt + T` | Mostrar/Esconder o painel do console |
| `Alt + L` | Mostrar/Esconder a barra de estrutura do código |
| `Alt + G` | Abrir o painel de controle do Git |
| `Alt + C` | Abrir a janela de configurações |
| `Ctrl + T` | Abrir um novo terminal na pasta do projeto |
| `Alt + S` | Iniciar/Parar o servidor web local |

### Edição de Texto
| Atalho | Função |
|---|---|
| `Ctrl + C` / `Ctrl + V` | Copiar / Colar |
| `Ctrl + X` | Recortar (linha atual ou seleção) |
| `Ctrl + D` | Duplicar a linha atual |
| `Ctrl + /` | Comentar/Descomentar a linha ou seleção |
| `Ctrl + Z` / `Ctrl + Y` | Desfazer / Refazer |
| `Alt + ↑ / ↓` | Mover a linha atual para cima ou para baixo |
| `Shift + Setas` | Selecionar texto |
| `Shift + S` | Localizar e Substituir no arquivo atual |
| `Ctrl + Shift + F` | Buscar texto em todo o projeto |

### Navegação na Barra Lateral (Sidebar)
| Atalho | Função |
|---|---|
| `Setas ↑ / ↓` | Navegar na lista de arquivos |
| `Enter` | Abrir arquivo ou pasta |
| `Backspace` | Voltar para a pasta pai |
| `Alt + ← / →` | Navegar pelo histórico de pastas visitadas |
| `Shift + A` | Criar um novo arquivo na pasta atual |
| `Alt + P` | Criar uma nova pasta na pasta atual |
| `R` | Renomear o item selecionado |
| `D` | Deletar o item selecionado |

### Janela do Git (`Alt+G`)
| Atalho | Função |
|---|---|
| `TAB` | Alternar entre os painéis (Status, Branches, etc.) |
| `S` | Adicionar arquivo para o commit (Stage) |
| `U` | Remover arquivo do commit (Unstage) |
| `C` | Fazer commit das alterações em "stage" |
| `Shift + P` | Enviar alterações para o remoto (Push) |
| `p` | Baixar alterações do remoto (Pull) |
| `D` | Descartar TODAS as alterações não salvas no projeto |

---
