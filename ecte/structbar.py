import curses
import re
from typing import List, Tuple

class Structbar:
    """
    Uma barra lateral que exibe a estrutura do código do arquivo atual (funções, classes, etc.).
    """
    ICONS = {
        "class": "",
        "function": "",
        "html_id": "",
        "css_selector": "🎨",
    }

    def __init__(self):
        self.visible = False
        self.items: List[Tuple[str, str, int]] = []
        self.selected = 0
        self.scroll_offset = 0

    def toggle(self):
        """Alterna a visibilidade da barra de estrutura."""
        self.visible = not self.visible
        # Não precisa de refresh aqui, o parse é chamado no loop de desenho principal

    def _get_parser(self, file_extension: str):
        """Retorna a regex apropriada para a extensão do arquivo."""
        parsers = {
            ".py": r"^\s*(class|def)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            ".rb": r"^\s*(class|def|module)\s+([A-Z_][a-zA-Z0-9_:]*)",
            ".rs": r"^\s*(?:pub\s+)?(fn|struct|impl|trait)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            ".js": r"^\s*(?:export\s+)?(class|function|const|let)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)(?:\s*=\s*function|\s*=\s*\(?async)?",
            ".ts": r"^\s*(?:export\s+)?(class|function|interface|type|const|let)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)(?:\s*=\s*function|\s*=\s*\(?async)?",
            ".java": r"^\s*(?:public|private|protected)?\s*(?:static\s+|final\s+)?(class|interface|enum)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            ".kt": r"^\s*(?:public|private|internal)?\s*(?:open\s+)?(class|interface|fun|object)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            ".c": r"^\s*([a-zA-Z_][a-zA-Z0-9_*\s]+?)\s+([a-zA-Z_][a-zA-Z0-9_]+)\s*\(",
            ".cpp": r"^\s*(?:template<.*>\s*)?(?:class|struct|void|int|string|bool|float|double|auto|const|virtual)[\s\*&]+([a-zA-Z_:]+[a-zA-Z0-9_:]*)\s*(?:\(.*\))?\s*{?",
            ".cs": r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+|sealed\s+)?(class|interface|struct|enum|void|string|int|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            ".html": r'id="([^"]+)"',
            ".css": r"^\s*([#\.][a-zA-Z0-9\-_]+)",
        }
        return parsers.get(file_extension)

    def parse_code(self, lines: List[str], file_extension: str):
        """
        Analisa as linhas de código para extrair elementos estruturais.
        """
        self.items = []
        parser_regex = self._get_parser(file_extension)

        if not parser_regex:
            return

        struct_regex = re.compile(parser_regex)

        for i, line in enumerate(lines):
            match = struct_regex.match(line)
            if match:
                if file_extension == ".html":
                    item_type = "html_id"
                    item_name = match.group(1)
                elif file_extension == ".css":
                    item_type = "css_selector"
                    item_name = match.group(1)
                elif file_extension in (".c", ".cpp"):
                    # Regex de C/C++ pode ser mais complexa, pegamos o segundo grupo se houver
                    item_type = "function"
                    item_name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                else:
                    keyword = match.group(1)
                    item_name = match.group(2)
                    if keyword in ("class", "struct", "interface", "module", "enum", "object", "impl", "trait"):
                        item_type = "class"
                    else:
                        item_type = "function"

                # Evitar duplicados ou nomes vazios
                if item_name and not any(item[1] == item_name for item in self.items):
                    line_number = i
                    self.items.append((item_type, item_name, line_number))

    def draw(self, stdscr, editor_w: int, editor_h: int, tabs_bar_h: int):
        """Desenha a barra de estrutura na tela."""
        if not self.visible:
            return

        h, w = stdscr.getmaxyx()
        structbar_w = 25
        structbar_x = w - structbar_w

        # Fundo da structbar
        bg_color = curses.color_pair(7)
        for y in range(h):
            try:
                stdscr.addch(y, structbar_x - 1, "│", curses.A_DIM)
                for x in range(structbar_x, w):
                    stdscr.addch(y, x, " ", bg_color)
            except curses.error:
                pass

        title = " Estrutura "
        stdscr.addstr(0, structbar_x, title.center(structbar_w), curses.A_BOLD | bg_color)

        content_h = h - 2 # Altura para a lista, descontando título e borda inferior
        list_y_start = 1 # Linha onde a lista começa

        # Pega apenas os itens visíveis baseados na rolagem
        visible_items = self.items[self.scroll_offset : self.scroll_offset + content_h]

        for i, (typ, name, line_num) in enumerate(visible_items):
            # O índice real na lista completa de self.items
            original_index = self.scroll_offset + i

            if list_y_start + i >= h - 1:
                break
            
            icon = self.ICONS.get(typ, " ")
            line_text = f"{icon} {name}"[:structbar_w - 1]
            
            # Destaca o item se o índice original for o selecionado
            color = curses.A_REVERSE if original_index == self.selected else bg_color
            stdscr.addstr(list_y_start + i, structbar_x, line_text.ljust(structbar_w), color)

        # Indicadores de rolagem
        if self.scroll_offset > 0:
            stdscr.addstr(1, w - 2, "↑", bg_color | curses.A_DIM)
        if self.scroll_offset + content_h < len(self.items):
            stdscr.addstr(h - 2, w - 2, "↓", bg_color | curses.A_DIM)