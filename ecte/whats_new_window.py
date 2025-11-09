import curses

class WhatsNewWindow:
    def __init__(self):         
        self.visible = False
        self.content = [
            ("Novidades da Versão 1.3.0", curses.A_BOLD),
            ("", 0),
            ("- [NOVO] Integração com Git (Alt+G)", 0),
            ("  - Versione seu código com Git diretamente do editor.", curses.A_DIM),
            ("", 0),
            ("- [NOVO] extenções", 0),
            ("  - posibilidade de usa extenções para pesonaliza o  seu tasma", curses.A_DIM),
            ("  - para habilita vá na janela de config", curses.A_DIM),
            ("  - adiciona extenções é necessario ir na documentação no github", curses.A_DIM),
            ("", 0),
            ("- [NOVO] Servidor Local (Alt+S)", 0),
            ("  - Crie um servidor local na pasta do projeto.", curses.A_DIM),
            ("", 0),
            ("- [NOVO] Confirmação de Saída (Ctrl+Q)", 0),
            ("  - O editor agora pergunta antes de fechar.", curses.A_DIM),
            ("  - Evita o fechamento acidental e perda de dados.", curses.A_DIM),
            ("", 0),
            ("- [NOVO] Janela de Novidades (Alt + N)", 0),
            ("  - Você está vendo esta janela agora mesmo!", curses.A_DIM),
            ("", 0),
            ("- [MELHORIA] Tela de Boas-Vindas", 0),
            ("  - Adicionado número da versão.", curses.A_DIM),
            ("", 0),
            ("- [MELHORIA] Janela de Ajuda (F1)", 0),
            ("  - Adicionado número da versão e novos atalhos.", curses.A_DIM),
            ("", 0),
            ("- [NOVO] Destaque de Sintaxe para Python", 0),
            ("  - O código em arquivos .py e outros agora tem cores!", curses.A_DIM),
            ("  - Renomeie (R) e delete (D) arquivos/pastas na sidebar.", curses.A_DIM),
            ("", 0),
            ("- [NOVO] Histórico de Comandos no Console", 0),
            ("  - Navegue pelos comandos com as setas ↑ e ↓.", curses.A_DIM),
            ("", 0),
            ("- [MELHORIA] Otimizações no sistema de desfazer/refazer.", curses.A_DIM),
            ("", 0),
            ("Obrigado por usar o tasmacode 👻", 0),
            ("Pressione Alt+N ou ESC para fechar.", (curses.A_ITALIC | curses.A_DIM)),
        ]

    def toggle(self):
        self.visible = not self.visible

    def draw(self, stdscr):
        if not self.visible:
            return

        h, w = stdscr.getmaxyx()
        win_h, win_w = len(self.content) + 4, 70
        win_y, win_x = (h - win_h) // 2, (w - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.bkgd(' ', curses.color_pair(7))
        win.box()
        win.addstr(1, (win_w - 22) // 2, " Novidades da Versão ", curses.A_BOLD)

        for i, (text, attr) in enumerate(self.content):
            win.addstr(i + 2, 3, text, attr)
        win.noutrefresh()