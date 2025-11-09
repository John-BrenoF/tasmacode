#!/usr/bin/env python3
import curses
import os
import argparse
import locale
import random
from pathlib import Path
from ecte.editor import Editor
from ecte.sidebar import Sidebar
from ecte.console import Console
from ecte.structbar import Structbar
from ecte.key_handler import handle_key
from ecte.help_window import HelpWindow
from ecte.git_window import GitWindow
from ecte.whats_new_window import WhatsNewWindow
from ecte.config_window import ConfigWindow
from pygments import lex
from pygments.lexers import guess_lexer_for_filename, TextLexer
from pygments.token import Token
try:
    from pyfiglet import figlet_format
    FIGLET_AVAILABLE = True
except ImportError:
    FIGLET_AVAILABLE = False
from pygments.util import ClassNotFound

ASCII_ART = [
    "                                      ----            --                                            ",
    "                                  ----                                                              ",
    "                                                              --                                    ",
    "                                --                              --                                  ",
    "                                --                              --                                  ",
    "                                  ----      --                  --                                  ",
    "                                --####      ####                  --                                ",
    "                                --####      ######          ..    --                                ",
    "                                --####      ######          ..    --                                ",
    "                      ----::::                              ..    ::                                ",
    "                    --                            ::::::::::        --                              ",
    "                  --                  ####      ::          ::..    --                              ",
    "                              ..            ::                      --                              ",
    "                --        ......            ::                      --                              ",
    "                --      ........            ::::::                  --                              ",
    "                --        ......              ::  ::                ::                              ",
    "                  ----::::    ..      ..      ::..::                --                              ",
    "                    --    ::....      ..        ::..::                --                            ",
    "                          ::          ..      ..::..  ::::            --                            ",
    "                          ::..        ..      ....::..::::    ..      --                            ",
    "                          --          ..      ..  ..::::::    ....    --                            ",
    "                          --          ..      ........::::    ....      --                          ",
    "                          --          ..      ............::  ....      --                          ",
    "                          --          ..        ............    ....    --                          ",
    "                          --          ....      ..........      ....    --                          ",
    "                              ..      ....      ............      ....    ::                        ",
    "                              ........----..    ..............      ..    --..                      ",
    "                              ----  ......::::..  ....  ........    ..        --                    ",
    "                            ------        ::  ::          ..      ..                                ",
    "                                ------------::                                                      ",
    "                                      --    --::----::::--                      ..--                ",
    "                                                          ::::::::::  ----------------              ",
]
def draw(stdscr, editor, sidebar, console, structbar, help_window, git_window, whats_new_window, config_window: ConfigWindow, status):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    tabs_bar_h = 2
    structbar_w = 25 if structbar.visible else 0
    sidebar_w = 25 if sidebar.visible else 0
    editor_h = h - 2 - tabs_bar_h
    
    x_offset = 0
    for i, tab in enumerate(editor.tabs):
        is_active = (i == editor.active_tab_index)
        style = curses.A_REVERSE if is_active else curses.color_pair(7)
        
        name = tab.filepath.name if tab.filepath else "[Novo]"
        dirty_indicator = " ●" if tab.dirty else ""
        tab_text = f" {name}{dirty_indicator} "

        if x_offset + len(tab_text) < w - structbar_w:
            stdscr.addstr(0, x_offset, tab_text, style)
            x_offset += len(tab_text)
    stdscr.addstr(0, x_offset, " " * (w - x_offset), curses.color_pair(7))
    stdscr.addstr(1, 0, "─" * (w - sidebar_w - structbar_w))

    active_buffer = editor.active_buffer
    if not active_buffer:
        stdscr.noutrefresh()
        return

    show_line_numbers = config_window.get_setting("Exibir Números de Linha") == "Ativado"
    line_number_width = len(str(len(active_buffer.lines))) + 2 if show_line_numbers else 0
    editor_w = w - line_number_width - sidebar_w - structbar_w
    welcome_art = []

    if active_buffer.cursor_y < active_buffer.offset_y:
        active_buffer.offset_y = active_buffer.cursor_y
    elif active_buffer.cursor_y >= active_buffer.offset_y + editor_h:
        active_buffer.offset_y = active_buffer.cursor_y - editor_h + 1

    if active_buffer.cursor_x < active_buffer.offset_x:
        active_buffer.offset_x = active_buffer.cursor_x
    elif active_buffer.cursor_x >= active_buffer.offset_x + editor_w:
        active_buffer.offset_x = active_buffer.cursor_x - editor_w + 1




    try:
        lexer = guess_lexer_for_filename(active_buffer.filepath.name, "") if active_buffer.filepath else TextLexer()
    except ClassNotFound:
        lexer = TextLexer()

    selection_coords = editor.get_selection_coords()

    if not sidebar.current_path:
        welcome_art = ASCII_ART
        if FIGLET_AVAILABLE:
            try:
                name_art = figlet_format("tasmacode", font="---").splitlines()
            except:
                name_art = figlet_format("tasmacode", font="standard").splitlines()
        else:
            name_art = ["'pyfiglet' não está instalado.", "Execute: pip install pyfiglet"]
        
        full_art = welcome_art + [""] * 2 + name_art + ["", "alpha v1.3"]

        art_height = len(full_art)
        final_start_y = max(1, (editor_h - art_height) // 2)

        logo_gradient_colors = [10, 11, 12, 13, 14]
        num_logo_colors = len(logo_gradient_colors)
        
        name_gradient_colors = [16, 3, 4] # Azul, Azul, Ciano
        num_name_colors = len(name_gradient_colors)

        for i, line in enumerate(full_art):
            if final_start_y + i >= 0 and final_start_y + i < editor_h -1:
                start_x = max(0, (editor_w - len(line)) // 2)
                draw_y = final_start_y + i + tabs_bar_h
                if line == "alpha v1.3":
                    stdscr.addstr(draw_y, start_x, line[:editor_w - start_x], curses.A_DIM) # Desenha a versão
                elif i >= len(welcome_art) + 2 and i < len(welcome_art) + 2 + len(name_art):
                    if FIGLET_AVAILABLE:
                        name_line_index = i - (len(welcome_art) + 2)
                        color_index = name_gradient_colors[int((name_line_index / len(name_art)) * num_name_colors)]
                        color = curses.color_pair(color_index)
                        stdscr.addstr(draw_y, start_x, line[:editor_w - start_x], color | curses.A_BOLD)
                    else:
                        color = curses.color_pair(4)  # Ciano
                        stdscr.addstr(draw_y, start_x, "tasmacode"[:editor_w - start_x], color | curses.A_BOLD)
                else:
                    if i < len(welcome_art):
                        color_index = logo_gradient_colors[int((i / len(welcome_art)) * num_logo_colors)]
                        color = curses.color_pair(color_index)
                        stdscr.addstr(draw_y, start_x, line[:editor_w - start_x], color)
    else:
        if show_line_numbers:
            for i in range(editor_h):
                line_idx = active_buffer.offset_y + i
                if line_idx < len(active_buffer.lines):
                    line_num_str = str(line_idx + 1).rjust(line_number_width - 2) + " │"
                    
                    has_error = "erro" in active_buffer.lines[line_idx].lower() and config_window.get_setting("Destacar Linha com Erro") == "Ativado"
                    color = curses.color_pair(18) if has_error else curses.A_DIM
                    
                    stdscr.addstr(i + tabs_bar_h, 0, line_num_str, color)

        for i in range(editor_h):
            line_idx = active_buffer.offset_y + i
            if line_idx < len(active_buffer.lines):
                line = active_buffer.lines[line_idx]
                visible_line = line[active_buffer.offset_x : active_buffer.offset_x + editor_w]

                tokens = lex(visible_line, lexer)
                
                if selection_coords:
                    y1, x1, y2, x2 = selection_coords
                    if y1 <= line_idx <= y2:
                        start = x1 if line_idx == y1 else 0
                        end = x2 if line_idx == y2 else editor_w
                        for x_pos in range(start, end):
                            if line_number_width + x_pos - active_buffer.offset_x < w:
                                stdscr.addch(i + tabs_bar_h, line_number_width + x_pos, ' ', curses.A_REVERSE)
                x = line_number_width
                for ttype, tvalue in tokens:
                    color_pair = curses.color_pair(0)
                    if ttype in Token.Keyword:
                        color_pair = curses.color_pair(1)
                    elif ttype in Token.Literal.String:
                        color_pair = curses.color_pair(2)
                    elif ttype in Token.Comment:
                        color_pair = curses.color_pair(3)
                    elif ttype in Token.Literal.Number:
                        color_pair = curses.color_pair(4)
                    elif ttype in Token.Operator or ttype in Token.Punctuation:
                        color_pair = curses.color_pair(5)
                    elif ttype in Token.Name.Function or ttype in Token.Name.Class:
                        color_pair = curses.color_pair(6)
                    elif ttype in Token.Name.Variable:
                        color_pair = curses.color_pair(8)
                    elif ttype in Token.Name.Decorator:
                        color_pair = curses.color_pair(9)
                    elif ttype in Token.Name.Constant:
                        color_pair = curses.color_pair(10)
                    
                    for char in tvalue:
                        if x < w - sidebar_w - structbar_w:
                            is_selected = False
                            if selection_coords and not console.visible and editor.active_buffer.selecting:
                                real_x = x - line_number_width + active_buffer.offset_x
                                y1, x1, y2, x2 = selection_coords
                                if (y1 < line_idx < y2) or \
                                   (line_idx == y1 and line_idx == y2 and x1 <= real_x < x2) or \
                                   (line_idx == y1 and line_idx != y2 and real_x >= x1) or \
                                   (line_idx == y2 and line_idx != y1 and real_x < x2):
                                    is_selected = True
                            stdscr.addch(i + tabs_bar_h, x, char, color_pair | (curses.A_REVERSE if is_selected else 0))
                            x += 1
            else:
                if config_window.get_setting("Indicador de Linha Vazia (~)") == "Ativado":
                    draw_x = line_number_width
                    if draw_x < w: # Garante que não tentaremos desenhar fora da tela
                        stdscr.addstr(i + tabs_bar_h, draw_x, "~", curses.A_DIM)

    if sidebar.visible:
        sidebar_bg_color = curses.color_pair(7)
        sidebar_x = w - sidebar_w

        for y in range(h):
            try:
                stdscr.addch(y, sidebar_x - 1, "│", curses.A_DIM)
            except:
                pass
            for x in range(sidebar_x, w):
                try:
                    stdscr.addch(y, x, " ", sidebar_bg_color)
                except curses.error: pass
        if sidebar.mode == 'picker':
            title = " Selecionar Pasta "
        else:
            title = " Projeto "
        
        if sidebar.mode == 'search':
            title = f" Buscar Pasta: {sidebar.search_query} "

        stdscr.addstr(0, sidebar_x, title.center(sidebar_w), curses.A_BOLD | sidebar_bg_color)

        content_h = h - 2
        list_y_start = 1

        visible_items = sidebar.items[sidebar.scroll_offset : sidebar.scroll_offset + content_h]

        for i, (typ, name, _) in enumerate(visible_items):
            original_index = sidebar.scroll_offset + i

            if list_y_start + i >= h - 1: break
            icon = sidebar.ICONS.get(typ, " ")
            line = f"{icon} {name}"[:sidebar_w - 1]
            color = curses.A_REVERSE if original_index == sidebar.selected else sidebar_bg_color
            stdscr.addstr(list_y_start + i, sidebar_x, line.ljust(sidebar_w), color)

        if sidebar.scroll_offset > 0:
            stdscr.addstr(1, w - 2, "↑", sidebar_bg_color | curses.A_DIM)
        if sidebar.scroll_offset + content_h < len(sidebar.items):
            stdscr.addstr(h - 2, w - 2, "↓", sidebar_bg_color | curses.A_DIM)

    if structbar.visible:
        file_ext = active_buffer.filepath.suffix if active_buffer.filepath else ""
        structbar.parse_code(active_buffer.lines, file_ext)
        structbar.draw(stdscr, editor_w, editor_h, tabs_bar_h)

    dirty_indicator = " ●" if active_buffer.dirty else ""
    name = active_buffer.filepath.name if active_buffer.filepath else "[Novo]"
    
    left_status = f" {name}{dirty_indicator} | Ln {active_buffer.cursor_y+1}, Col {active_buffer.cursor_x+1} "
    if status:
        left_status += f" | {status}"
    left_status += " | Ajuda: F1"

    lang_name = lexer.name if lexer.name != "Text only" else "Texto"
    file_type_key = f"file_{active_buffer.filepath.suffix[1:]}" if active_buffer.filepath and active_buffer.filepath.suffix else 'file'
    lang_icon = sidebar.ICONS.get(file_type_key, sidebar.ICONS['file'])
    
    git_indicator = "|  Alt+G " if (sidebar.current_path and (sidebar.current_path / ".git").is_dir()) else ""

    right_status = f" {lang_icon} {lang_name} {git_indicator}"

    total_len = len(left_status) + len(right_status) + 1
    spacing = " " * (w - total_len - 1) if w > total_len else " "
    status_line = f"{left_status}{spacing}{right_status}"
    stdscr.addstr(h-1, 0, status_line[:w-1], curses.A_REVERSE)

    stdscr.noutrefresh()

    if console.visible:
        ch = h // 3
        console_win = curses.newwin(ch, w, h - ch, 0)
        console_win.box()
        
        spinner = "  चक्र " if console.running else ""
        console_win.addstr(0, 2, f" Console{spinner}(PgUp/PgDn para rolar) ", curses.A_BOLD)
        
        prompt = console.get_prompt()
        input_line = f"{prompt} {console.command}"
        console_win.addstr(ch - 2, 1, input_line[:w-2])

        output_h = ch - 4
        start_index = max(0, len(console.output) - output_h - console.output_scroll_offset)
        end_index = max(0, len(console.output) - console.output_scroll_offset)
        visible_output = console.output[start_index:end_index]

        for i, line in enumerate(visible_output):
            color = curses.color_pair(0)
            if line.startswith(("[ERRO]", "[EXCEÇÃO]")):
                color = curses.color_pair(5) # Vermelho
            elif line.startswith("---"):
                color = curses.A_DIM
            elif line.startswith(f"({console.cwd.name}) >") or line.startswith("(~"):
                color = curses.color_pair(15) # Amarelo

            console_win.addstr(i + 1, 1, line[:w-2], color)

        console_win.noutrefresh()
        stdscr.move(h - 2, len(prompt) + 1 + console.cursor_x) 

    if help_window.visible:
        help_window.draw(stdscr)

    if git_window.visible:
        git_window.draw()

    if whats_new_window.visible:
        whats_new_window.draw(stdscr)

    if config_window.visible:
        config_window.draw(stdscr)

    curses.doupdate()

def apply_theme(bg_color: int):
    curses.start_color()
    curses.use_default_colors()
    
    if bg_color == curses.COLOR_WHITE:
        curses.init_pair(7, curses.COLOR_BLACK, 242) 
    else:
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)

    curses.init_pair(1, curses.COLOR_MAGENTA, bg_color)
    curses.init_pair(2, curses.COLOR_GREEN, bg_color)
    curses.init_pair(3, curses.COLOR_BLUE, bg_color)
    curses.init_pair(4, curses.COLOR_CYAN, bg_color)
    curses.init_pair(5, curses.COLOR_RED, bg_color)
    curses.init_pair(6, curses.COLOR_YELLOW, bg_color)
    curses.init_pair(8, curses.COLOR_CYAN, bg_color)
    curses.init_pair(9, curses.COLOR_GREEN, bg_color)
    curses.init_pair(10, 197, bg_color)
    curses.init_pair(11, 201, bg_color)
    curses.init_pair(12, 159, bg_color)
    curses.init_pair(13, 117, bg_color)
    curses.init_pair(14, 81, bg_color)
    curses.init_pair(15, curses.COLOR_YELLOW, bg_color)
    curses.init_pair(16, curses.COLOR_BLUE, bg_color)
    curses.init_pair(17, curses.COLOR_GREEN, bg_color)
    curses.init_pair(18, curses.COLOR_RED, bg_color)
    curses.init_pair(19, curses.COLOR_MAGENTA, bg_color)
    curses.init_pair(20, curses.COLOR_RED, bg_color)
    curses.init_pair(21, 88, bg_color)

def main(stdscr, initial_filepath=None):
    curses.curs_set(1)
    stdscr.keypad(True)
    curses.raw() 
    
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    stdscr.addstr("\x1b[?2004h")

    apply_theme(-1) 

    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_BLUE, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_YELLOW, -1) 
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_CYAN, -1)
    curses.init_pair(9, curses.COLOR_GREEN, -1)
    curses.init_pair(10, 197, -1)
    curses.init_pair(11, 201, -1)
    curses.init_pair(12, 159, -1)
    curses.init_pair(13, 117, -1)
    curses.init_pair(14, 81, -1)

    curses.init_pair(15, curses.COLOR_YELLOW, -1)
    curses.init_pair(16, curses.COLOR_BLUE, -1)
    curses.init_pair(17, curses.COLOR_GREEN, -1)
    curses.init_pair(18, curses.COLOR_RED, -1)
    curses.init_pair(19, curses.COLOR_MAGENTA, -1)
    
    curses.init_pair(20, curses.COLOR_RED, -1) 
    curses.init_pair(21, 88, -1) 

    editor = Editor()
    sidebar = Sidebar()
    console = Console()
    structbar = Structbar()
    help_window = HelpWindow()
    git_window = GitWindow(stdscr, sidebar.current_path)
    whats_new_window = WhatsNewWindow()
    config_window = ConfigWindow(editor)
    status = "TASMACODE | Ctrl+S salvar | Ctrl+Q sair"

    if initial_filepath and initial_filepath.is_file():
        editor.open_file(initial_filepath)
        sidebar.set_project_path(initial_filepath.parent)
        console.set_cwd(initial_filepath.parent)
    else:
        editor.new_file()

    while True:
        draw(stdscr, editor, sidebar, console, structbar, help_window, git_window, whats_new_window, config_window, status)
        
        stdscr.timeout(100) # Timeout de 100ms

        try:
            active_buffer = editor.active_buffer
            if active_buffer and not structbar.visible: # Não move o cursor se as barras estiverem visíveis
                show_line_numbers = config_window.get_setting("Exibir Números de Linha") == "Ativado"
                line_number_width = len(str(len(active_buffer.lines))) + 2 if show_line_numbers else 0
                
                stdscr.move(active_buffer.cursor_y - active_buffer.offset_y + 2, active_buffer.cursor_x - active_buffer.offset_x + line_number_width)
        except (curses.error, AttributeError):
            pass

        key = stdscr.getch() # Retorna -1 se o timeout for atingido

        if sidebar.cloning_thread and not sidebar.cloning_thread.is_alive():
            sidebar.cloning_thread.join()
            status_msg, new_path = sidebar.cloning_result or ("Erro desconhecido", None)
            if new_path:
                sidebar.set_project_path(new_path)
            sidebar.cloning_thread = None
            sidebar.cloning_result = None
            console.visible = False
            status = status_msg
        else:
            if key != -1:
                result = handle_key(key, stdscr, editor, sidebar, console, structbar, help_window, git_window, whats_new_window, config_window)
                if result == "exit" and not (sidebar.cloning_thread and sidebar.cloning_thread.is_alive()):
                    break
                if result:
                    status = result

    stdscr.addstr("\x1b[?2004l")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TasmaCode Text Editor")
    parser.add_argument("filepath", nargs="?", type=Path, help="Path to the file to open")
    args = parser.parse_args()

    os.chdir(Path(__file__).parent.parent)
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(main, initial_filepath=args.filepath)