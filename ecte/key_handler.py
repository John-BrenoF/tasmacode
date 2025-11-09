import curses
import time
import random
from ecte.editor import Editor
from ecte.sidebar import Sidebar # Mantenha esta linha
from ecte.console import Console
from ecte.structbar import Structbar
from ecte.git_window import GitWindow
from ecte.whats_new_window import WhatsNewWindow

from ecte.utils import open_terminal_at_path, prompt_for_confirmation, prompt_with_options
from ecte.help_window import HelpWindow
from ecte.config_window import ConfigWindow
from ecte.find_replace import start_find_replace
from ecte.execution_handler import get_execution_command, search_in_project

def play_teleport_animation(stdscr, y, x):
    try:
        animation_frames = [
            [(0, 0, '◦', 6)],  # Quadro 1: Ponto amarelo brilhante no centro
            [(0, 0, '●', 4), (0, 1, '·', 3), (0, -1, '·', 3)], # Quadro 2: Expande horizontalmente
            [
                (0, 0, '✴', 4), (0, 1, '>', 19), (0, -1, '<', 19),
                (1, 0, 'v', 19), (-1, 0, '^', 19)
            ], # Quadro 3: Setas magentas se expandindo
            [
                (0, 2, '∙', 3), (0, -2, '∙', 3), (1, 1, '`', 3), (1, -1, '`', 3),
                (-1, 1, ',', 3), (-1, -1, ',', 3)
            ], # Quadro 4: Partículas azuis se afastando
        ]
        
        for frame in animation_frames:
            for dy, dx, char, color_idx in frame:
                try:
                    stdscr.addstr(y + dy, x + dx, char, curses.color_pair(color_idx) | curses.A_BOLD)
                except curses.error:
                    pass # Ignora se a partícula sair da tela
            stdscr.refresh()
            time.sleep(0.04)
    except curses.error:
        pass # Ignora erros se a animação tentar desenhar fora da tela

def handle_bracketed_paste(stdscr, editor: Editor):
    pasted_text = ""
    while True:
        try:
            char = stdscr.get_wch()
            if isinstance(char, str) and char.startswith('\x1b[201~'):
                pasted_text += char.split('\x1b[201~')[0]
                break
            pasted_text += str(char)
        except Exception:
            break
    
    if pasted_text:
        editor.insert_text_at_cursor(pasted_text)
    return "Texto colado."

def handle_key(key, stdscr, editor: Editor, sidebar: Sidebar, console: Console, structbar: Structbar, help_window: HelpWindow, git_window: GitWindow, whats_new_window: WhatsNewWindow, config_window: ConfigWindow):
    editor.reload_config(config_window)

    if key == curses.KEY_MOUSE:
        if config_window.get_setting("Suporte ao Mouse") == "Ativado":
            try:
                _, mx, my, _, bstate = curses.getmouse()
                
                if bstate & curses.BUTTON1_PRESSED:
                    h, w = stdscr.getmaxyx()
                    active_buffer = editor.active_buffer
                    tabs_bar_h = 2
                    sidebar_w = 25 if sidebar.visible else 0

                    if my < 1:
                        x_offset = 0
                        for i, tab in enumerate(editor.tabs):
                            name = tab.filepath.name if tab.filepath else "[Novo]"
                            dirty_indicator = " ◉" if tab.dirty else ""
                            tab_text = f" {name}{dirty_indicator} "
                            if x_offset <= mx < x_offset + len(tab_text):
                                editor.active_tab_index = i
                                return f"Aba '{name}' selecionada"
                            x_offset += len(tab_text)
                        return None

                    elif sidebar.visible and mx >= w - sidebar_w:
                        clicked_line = my - 1 # Desconta a linha do título da sidebar
                        if 0 <= clicked_line < len(sidebar.items):
                            sidebar.selected = sidebar.scroll_offset + clicked_line
                            return sidebar.enter(editor, console, stdscr)
                        return None

                    elif active_buffer:
                        show_line_numbers = config_window.get_setting("Exibir Números de Linha") == "Ativado"
                        line_number_width = len(str(len(active_buffer.lines))) + 2 if show_line_numbers else 0

                        if my >= tabs_bar_h and mx >= line_number_width:
                            new_cursor_y = my - tabs_bar_h + active_buffer.offset_y
                            new_cursor_x = mx - line_number_width

                            if config_window.get_setting("Animação do Ponteiro") == "Ativado":
                                play_teleport_animation(stdscr, my, mx)

                            active_buffer.cursor_y = min(len(active_buffer.lines) - 1, max(0, new_cursor_y))
                            active_buffer.cursor_x = min(len(active_buffer.lines[active_buffer.cursor_y]), max(0, new_cursor_x))
                            return None

            except curses.error:
                pass # Ignora erros de getmouse() se não houver evento
        return None

    if key == '\x1b[200~':
        return handle_bracketed_paste(stdscr, editor)

    if key == 17:
        if any(t.dirty for t in editor.tabs):
            options = ["Salvar e Sair", "Sair sem Salvar", "Cancelar"]
            choice = prompt_with_options(stdscr, "Você tem alterações não salvas. O que deseja fazer?", options)
            
            if choice == "Salvar e Sair":
                if editor.save_file():
                    return "exit"
                else:
                    return "Erro ao salvar. A saída foi cancelada."
            elif choice == "Sair sem Salvar":
                return "exit"
            else: # Cancelar ou ESC
                return None # Não faz nada
        elif prompt_for_confirmation(stdscr, "Tem certeza que quer sair?"):
                return "exit"
        return None
    if key == 19:
        if not editor.active_buffer or not editor.active_buffer.dirty:
            return "Nenhuma mudança para salvar."
        saved = editor.save_file()
        return "Salvo!" if saved else "Erro ao salvar"
    elif key == 14:
        editor.new_file()
        return "Novo arquivo"
    elif key == 23: # Ctrl + W para fechar aba
        if not editor.active_buffer: return None
        if editor.active_buffer.dirty:
            choice = prompt_for_confirmation(stdscr, f"Salvar alterações em '{editor.active_buffer.filepath.name if editor.active_buffer.filepath else '[Novo]'}'?")
            if choice:
                editor.save_file()
        
        editor.tabs.pop(editor.active_tab_index)
        if not editor.tabs: # Se fechou a última aba, cria uma nova
            editor.new_file()
        else:
            editor.active_tab_index = min(editor.active_tab_index, len(editor.tabs) - 1)
        return "Aba fechada"

    elif key == 4:
        editor.duplicate_line()
        editor.dirty = True
        return None
    elif key == 24:
        status = editor.cut_selection()
        editor.dirty = True
        return status
    elif key == 3:
        return editor.copy_selection()
    elif key == 22:
        status = editor.paste()
        editor.dirty = True
        return status
    elif key == 26:
        if editor.undo():
            editor.dirty = True
            return "Desfeito"
    elif key == 25:
        if editor.redo():
            return "Refeito"
    elif key == 5: # Ctrl + E para executar
        if not editor.active_buffer or not editor.active_buffer.filepath:
            return "Salve o arquivo antes de executá-lo."
        command = get_execution_command(editor.active_buffer.filepath)
        if command:
            console.run_command(command)
            console.visible = True
            return f"Executando {editor.active_buffer.filepath.name}..."
        return f"Não há um comando de execução definido para arquivos '{editor.active_buffer.filepath.suffix}'."
    elif key == 6:
        sidebar.toggle()
        return "Sidebar: " + ("visível" if sidebar.visible else "oculta")
    elif key == 20:
        if sidebar.current_path:
            if open_terminal_at_path(sidebar.current_path):
                return "Abrindo terminal no projeto..."
            return "Erro: Não foi possível encontrar um terminal compatível."
        return "Abra um projeto para usar o terminal."
    elif key == 16:
        return sidebar.toggle_search_mode()
    elif key == 335: # Ctrl + Shift + F
        if sidebar.current_path:
            return sidebar.start_project_search(stdscr, console)
        return "Abra um projeto para buscar."

    elif key == 15:
        if sidebar.mode == "search":
            return sidebar.exit_search_mode()
    elif key == curses.KEY_F1:
        help_window.toggle()
        return None
    elif key == 31:
        editor.toggle_comment()
        editor.dirty = True
        return None

    if key == 27:
        stdscr.nodelay(True)
        next_key = stdscr.getch()
        stdscr.nodelay(False)

        if next_key != -1:
            if next_key in (ord('p'), ord('P')):
                return sidebar.add_folder(stdscr)
            elif next_key in (ord('t'), ord('T')):
                console.toggle()
                return "Console: " + ("visível" if console.visible else "oculto")
            elif next_key == curses.KEY_LEFT:
                return sidebar.go_back()
            elif next_key == curses.KEY_RIGHT:
                return sidebar.go_forward()
            elif next_key == curses.KEY_UP and not sidebar.visible and not console.visible:
                editor.move_line_up()
                editor.dirty = True
            elif next_key == curses.KEY_DOWN and not sidebar.visible and not console.visible:
                editor.move_line_down()
                editor.dirty = True
            elif next_key in (ord('g'), ord('G')):
                git_window.toggle(sidebar.current_path)
                return "Janela Git: " + ("visível" if git_window.visible else "oculta")
            elif next_key in (ord('n'), ord('N')):
                whats_new_window.toggle()
                return "Novidades: " + ("visível" if whats_new_window.visible else "oculta")
            elif next_key in (ord('s'), ord('S')):
                return sidebar.toggle_local_server()
            elif next_key in (ord('c'), ord('C')):
                config_window.toggle()
                return "Configurações: " + ("visível" if config_window.visible else "oculta")
            elif next_key in (ord('l'), ord('L')):
                structbar.toggle()
                return "Estrutura: " + ("visível" if structbar.visible else "oculta")
            return None
        if sidebar.mode == "search":
            return sidebar.exit_search_mode()

    if whats_new_window.visible:
        if key == 27 or key == curses.KEY_F1:
            whats_new_window.toggle()
    if help_window.visible:
        help_window.handle_key(key)
        return "Navegando na ajuda"
    
    if config_window.visible:
        config_window.handle_key(key)
        return "Configuração alterada"

    if structbar.visible:
        h, _ = stdscr.getmaxyx()
        content_h = h - 2

        if key == curses.KEY_UP:
            structbar.selected = max(0, structbar.selected - 1)
            if structbar.selected < structbar.scroll_offset:
                structbar.scroll_offset = structbar.selected
        elif key == curses.KEY_DOWN:
            if structbar.items:
                structbar.selected = min(len(structbar.items) - 1, structbar.selected + 1)
                if structbar.selected >= structbar.scroll_offset + content_h:
                    structbar.scroll_offset = structbar.selected - content_h + 1
        elif key == 10: # Enter
            if editor.active_buffer and structbar.items:
                _, _, line_num = structbar.items[structbar.selected]
                editor.active_buffer.cursor_y = line_num
        return "Navegando na estrutura"

    elif git_window.visible:
        git_window.handle_key(key)
        return None

    elif console.visible:
        if key == 10:
            console.submit_command()
            return "Comando executado"
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            console.delete_char()
        elif key == curses.KEY_UP:
            console.previous_command()
        elif key == curses.KEY_DOWN:
            console.next_command()
        elif key == curses.KEY_LEFT:
            console.move_cursor(-1)
        elif key == curses.KEY_RIGHT:
            console.move_cursor(1)
        elif key == curses.KEY_HOME:
            console.cursor_x = 0
        elif key == curses.KEY_END:
            console.cursor_x = len(console.command)
        elif key == 9: # Tab
            console.autocomplete()
        elif key == curses.KEY_PPAGE: # PageUp
            console.output_scroll_offset = min(console.output_scroll_offset + 1, len(console.output) - 1)
        elif key == curses.KEY_NPAGE: # PageDown
            console.output_scroll_offset = max(0, console.output_scroll_offset - 1)
        elif 32 <= key <= 126:
            console.insert_char(chr(key))
        elif key == curses.KEY_DC: # Tecla Delete
            console.delete_forward()
        
        return "Entrada do console" # Impede que a tecla vaze para o editor

    elif sidebar.visible:
        if sidebar.mode == "search":
            if key in (curses.KEY_BACKSPACE, 127, 8): # Backspace
                sidebar.search_query = sidebar.search_query[:-1]
                sidebar.refresh()
            elif 32 <= key <= 126:
                sidebar.search_query += chr(key)
                sidebar.refresh()
            elif key == curses.KEY_UP: sidebar.up()
            elif key == curses.KEY_DOWN: sidebar.down()
            elif key == 10:
                return sidebar.enter(editor, console, stdscr)
            return None

        if key == ord('A') or key == ord('F'):
            return sidebar.add_file(stdscr)

        if key in (ord('r'), ord('R')):
            return sidebar.rename_item(stdscr)

        if key in (ord('d'), ord('D')):
            return sidebar.delete_item(stdscr)

        if key in (curses.KEY_BACKSPACE, 127, 8):
            return sidebar.go_to_parent(console)

        h, _ = stdscr.getmaxyx()
        content_h = h - 2 # Altura visível para itens, descontando título e borda

        if key == curses.KEY_UP:
            sidebar.up()
            if sidebar.selected < sidebar.scroll_offset:
                sidebar.scroll_offset = sidebar.selected
        elif key == curses.KEY_DOWN:
            sidebar.down()
            if sidebar.selected >= sidebar.scroll_offset + content_h:
                sidebar.scroll_offset = sidebar.selected - content_h + 1
        elif key == 10:
            return sidebar.enter(editor, console, stdscr)
        return "Navegando no projeto"

    elif key == ord('S') and not (sidebar.visible or console.visible or git_window.visible or help_window.visible): # Shift + S
        if editor.active_buffer:
            return start_find_replace(stdscr, editor.active_buffer)
        return "Nenhuma aba ativa para localizar e substituir."
    is_vim_mode = config_window.get_setting("Modo de Navegação (Vim)") == "Vim (h,j,k,l)"
    if is_vim_mode and editor.active_buffer and not any([sidebar.visible, console.visible, git_window.visible, help_window.visible, structbar.visible]):
        if key == ord('k'): # Cima
            editor.active_buffer.cursor_y = max(0, editor.active_buffer.cursor_y - 1)
            editor.active_buffer.cursor_x = min(editor.active_buffer.cursor_x, len(editor.active_buffer.lines[editor.active_buffer.cursor_y]))
            return None
        elif key == ord('j'): # Baixo
            editor.active_buffer.cursor_y = min(len(editor.active_buffer.lines) - 1, editor.active_buffer.cursor_y + 1)
            editor.active_buffer.cursor_x = min(editor.active_buffer.cursor_x, len(editor.active_buffer.lines[editor.active_buffer.cursor_y]))
            return None
        elif key == ord('h'): # Esquerda
            editor.active_buffer.cursor_x = max(0, editor.active_buffer.cursor_x - 1)
            return None
        elif key == ord('l'): # Direita
            editor.active_buffer.cursor_x = min(len(editor.active_buffer.lines[editor.active_buffer.cursor_y]), editor.active_buffer.cursor_x + 1)
            return None

    else:
        if key in (curses.KEY_BACKSPACE, 127, 8):
            editor.delete_char()
        elif key == 10:
            editor.new_line_with_indent()
            editor.dirty = True
        elif key == curses.KEY_RESIZE:
            pass
        elif key == 9: # Tab
            if not editor.attempt_autocomplete_word():
                if editor.active_tab_index < len(editor.tabs) - 1:
                    editor.active_tab_index += 1
                else:
                    editor.active_tab_index = 0
                return "Próxima aba"
        elif key == 353: # Shift + Tab
            if editor.active_tab_index > 0:
                editor.active_tab_index -= 1
            else:
                editor.active_tab_index = len(editor.tabs) - 1
            return "Aba anterior"
        elif 32 <= key <= 126:
            editor.insert_char(chr(key))
        elif key == curses.KEY_LEFT:
            if editor.active_buffer:
                editor.active_buffer.cursor_x = max(0, editor.active_buffer.cursor_x - 1)
        elif key == curses.KEY_RIGHT:
            if editor.active_buffer:
                editor.active_buffer.cursor_x = min(len(editor.active_buffer.lines[editor.active_buffer.cursor_y]), editor.active_buffer.cursor_x + 1)
        elif key == curses.KEY_UP:
            if editor.active_buffer:
                editor.active_buffer.cursor_y = max(0, editor.active_buffer.cursor_y - 1)
                editor.active_buffer.cursor_x = min(editor.active_buffer.cursor_x, len(editor.active_buffer.lines[editor.active_buffer.cursor_y]))
        elif key == curses.KEY_DOWN:
            if editor.active_buffer:
                editor.active_buffer.cursor_y = min(len(editor.active_buffer.lines) - 1, editor.active_buffer.cursor_y + 1)
                editor.active_buffer.cursor_x = min(editor.active_buffer.cursor_x, len(editor.active_buffer.lines[editor.active_buffer.cursor_y]))

        sleft = getattr(curses, 'KEY_SLEFT', -1)
        sright = getattr(curses, 'KEY_SRIGHT', -1)
        sup = getattr(curses, 'KEY_SUP', -1)
        sdown = getattr(curses, 'KEY_SDOWN', -1)
        if not editor.active_buffer: return None

        selection_keys = [k for k in (sleft, sright, sup, sdown) if k != -1]

        if key in selection_keys:
            if not editor.active_buffer.selecting:
                editor.start_selection()

            if key == sleft:
                editor.active_buffer.cursor_x = max(0, editor.active_buffer.cursor_x - 1)
            elif key == sright:
                editor.active_buffer.cursor_x = min(len(editor.active_buffer.lines[editor.active_buffer.cursor_y]), editor.active_buffer.cursor_x + 1)
            elif key == sup:
                editor.active_buffer.cursor_y = max(0, editor.active_buffer.cursor_y - 1)
                editor.active_buffer.cursor_x = min(editor.active_buffer.cursor_x, len(editor.active_buffer.lines[editor.active_buffer.cursor_y]))
            elif key == sdown:
                editor.active_buffer.cursor_y = min(len(editor.active_buffer.lines) - 1, editor.active_buffer.cursor_y + 1)
                editor.active_buffer.cursor_x = min(editor.active_buffer.cursor_x, len(editor.active_buffer.lines[editor.active_buffer.cursor_y]))
        else:
            if editor.active_buffer.selecting:
                editor.clear_selection()
    return None