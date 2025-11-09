import curses
class HelpWindow:
    def __init__(self):
        self.visible = False
        self.scroll_offset = 0
        self.commands = [
            ("Atalhos Globais", ""),
            ("F1", "Mostrar/Esconder esta ajuda"),
            ("Ctrl + Q", "Sair do editor"),
            ("Ctrl + S", "Salvar o arquivo atual"),
            ("Ctrl + N", "Nova aba (arquivo em branco)"),
            ("Ctrl + W", "Fechar aba atual"),
            ("Ctrl + Tab", "Próxima aba"),
            ("Shift + Ctrl + Tab", "Aba anterior"),
            ("Ctrl + F", "Mostrar/Esconder a barra lateral"),
            ("Ctrl + E", "Executar arquivo no console"),
            ("Alt + T", "Mostrar/Esconder o console"),
            ("Alt + N", "Mostrar janela de novidades da versão"),
            ("Alt + S", "Iniciar/Parar servidor local"),
            ("Alt + L", "Mostrar/Esconder a estrutura do código"),
            ("Alt + G", "Abrir painel de controle do Git"),
            ("Alt + C", "Abrir janela de configurações"),
            ("Ctrl + T", "Abrir terminal na pasta do projeto"),
            ("Ctrl + P", "Buscar pastas no projeto"),
            ("Ctrl + Shift + F", "Buscar texto em todo o projeto"),
            ("Shift + S", "Localizar e substituir texto"),
            ("", ""),
            ("Edição de Texto", ""),
            ("Ctrl + D", "Duplicar a linha atual"),
            ("Shift + Setas", "Selecionar texto"),
            ("Ctrl + C", "Copiar seleção"),
            ("Ctrl + V", "Colar da área de transferência"),
            ("Ctrl + X", "Cortar seleção (ou linha atual)"),
            ("Ctrl + /", "Comentar/Descomentar a linha atual"),
            ("Ctrl + Z", "Desfazer a última ação"),
            ("Ctrl + Y", "Refazer a última ação"),
            ("Alt + ↑ / ↓", "Mover a linha atual para cima/baixo"),
            ("", ""),
            ("Git (Alt + G)",""),
            ("TAB", "Alternar entre painéis"),
            ("Enter", "Ação (ex: trocar de branch)"),
            ("S", "Adicionar arquivo selecionado (Stage)"),
            ("U", "Remover arquivo selecionado (Unstage)"),
            ("C", "Confirmar (Commit) alterações 'staged'"),
            ("D", "Descartar TODAS as alterações no projeto"),
            ("Shift + P","Enviar alterações para o remoto (Push)"),
            ("p", "Baixar alterações do remoto (Pull)"),
            ("z / x", "Guardar (Stash)/Aplicar (Pop) alterações"),
            ("", ""),
            ("Na Barra Lateral", ""),
            ("Setas Cima/Baixo","Navegar na lista de arquivos"),
            ("Enter", "Abrir pasta ou arquivo selecionado"),
            ("Backspace","Navegar para a pasta pai"),
            ("Shift + A","novo arquivo na pasta atual"),
            ("R", "Renomear arquivo/pasta selecionado"),
            ("D", "Deletar arquivo/pasta selecionado"),
            ("Alt + P","Criar uma nova pasta na pasta atual"),
            ("Alt + ← / →","Navegar pelo histórico de pastas"),
            ("Ctrl + O / ESC","Fechar a janela de busca"),
        ]

    def toggle(self):
        self.visible = not self.visible
        self.scroll_offset = 0 # Reseta a rolagem ao abrir

    def handle_key(self, key):
        """Processa a entrada do usuário para rolagem."""
        if key == curses.KEY_UP:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif key == curses.KEY_DOWN:
            # Limita a rolagem para não passar do final da lista
            max_scroll = len(self.commands) - (20) # 20 é a altura visível aproximada
            self.scroll_offset = min(max(0, max_scroll), self.scroll_offset + 1)
        elif key in (27, curses.KEY_F1): # ESC ou F1
            self.toggle()

    def draw(self, stdscr):
        if not self.visible:
            return

        h, w = stdscr.getmaxyx()
        win_h = min(len(self.commands) + 4, h - 4, 24) # Altura fixa, mas responsiva
        win_w = 70
        win_y, win_x = (h - win_h) // 2, (w - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.bkgd(' ', curses.color_pair(7))
        win.box()
        title = " Ajuda (F1/ESC para fechar) "
        win.addstr(1, (win_w - len(title)) // 2, title, curses.A_BOLD)
        win.addstr(win_h - 2, win_w - 15, "alpha v1.3", curses.A_DIM)

        content_h = win_h - 4
        visible_commands = self.commands[self.scroll_offset : self.scroll_offset + content_h]

        for i, (shortcut, desc) in enumerate(visible_commands):
            win.addstr(i + 2, 3, f"{shortcut:<20} {desc}")

        # Indicadores de rolagem
        if self.scroll_offset > 0:
            win.addstr(1, win_w - 4, "↑", curses.A_DIM)
        if self.scroll_offset + content_h < len(self.commands):
            win.addstr(win_h - 2, win_w - 4, "↓", curses.A_DIM)

        win.noutrefresh()	