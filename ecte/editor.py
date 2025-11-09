from pathlib import Path
import curses
import re
from typing import List, Optional, Tuple
import sys
import importlib

try:
    import pyclip
    PYCLIP_AVAILABLE = True
except ImportError:
    PYCLIP_AVAILABLE = False


PYTHON_KEYWORDS = {
    'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return', 'import', 'from',
    'as', 'with', 'try', 'except', 'finally', 'raise', 'assert', 'del', 'global',
    'nonlocal', 'in', 'is', 'lambda', 'not', 'or', 'and', 'pass', 'break', 'continue',
    'yield', 'async', 'await', 'True', 'False', 'None'
}

SYNTAX_REGEX = re.compile(
    r"(?P<STRING>\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"[^\"]*\"|'[^']*')"
    r"|(?P<COMMENT>#.*$)"
    r"|(?P<NUMBER>\b\d+(\.\d*)?\b)"
    r"|(?P<KEYWORD>\b(" + "|".join(PYTHON_KEYWORDS) + r")\b)"
)
class Buffer:
    def __init__(self, path: Optional[Path] = None):
        self.filepath: Optional[Path] = path
        self.lines: List[str] = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.offset_y = 0
        self.offset_x = 0
        self.selecting = False
        self.selection_anchor_x = -1
        self.selection_anchor_y = -1
        self._undo_stack = []
        self._redo_stack = []
        self.dirty = False

        if path and path.exists():
            self.lines = path.read_text(encoding="utf-8").splitlines() or [""]

    def save(self) -> bool:
        if not self.filepath:
            return False
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.filepath.write_text("\n".join(self.lines), encoding="utf-8")
            self.dirty = False
            return True
        except:
            return False

class Editor:
    def __init__(self):
        self.tabs: List[Buffer] = []
        self.active_tab_index = -1
        self.new_file() # Começa com uma aba vazia
        self.autocomplete_pairs = {}
        self.smart_auto_indent = True
        self.html_tag_autocomplete = True
        self.autocomplete_words = {}
        self.html_void_tags = set()

    def reload_config(self, config):
        autocomplete_status = config.get_setting("autocomplete_config.py")
        if autocomplete_status == "Ativado":
            try:
                module = importlib.import_module("extension.autocomplete_config")
                self.autocomplete_pairs = getattr(module, 'AUTOCOMPLETE_PAIRS', {})
                self.autocomplete_words = getattr(module, 'AUTOCOMPLETE_WORDS', {})
                self.html_void_tags = getattr(module, 'HTML_VOID_TAGS', set())
            except (ImportError, AttributeError):
                self.autocomplete_pairs = {}
        else: # Desativado ou não encontrado
            self.autocomplete_pairs = {}
            
        indent_status = config.get_setting("Auto Indentação Inteligente")
        self.smart_auto_indent = (indent_status == "Ativado")
        
        html_status = config.get_setting("Autocompletar Tags HTML")
        self.html_tag_autocomplete = (html_status == "Ativado")

    @property
    def active_buffer(self) -> Optional[Buffer]:
        if 0 <= self.active_tab_index < len(self.tabs):
            return self.tabs[self.active_tab_index]
        return None

    def open_file(self, path: Path):
        for i, tab in enumerate(self.tabs):
            if tab.filepath == path:
                self.active_tab_index = i
                return

        new_buffer = Buffer(path)
        if len(self.tabs) == 1 and not self.tabs[0].filepath and not self.tabs[0].dirty:
            self.tabs[0] = new_buffer
            self.active_tab_index = 0
        else:
            self.tabs.append(new_buffer)
            self.active_tab_index = len(self.tabs) - 1

    def save_file(self) -> bool:
        if self.active_buffer:
            return self.active_buffer.save()
        return False

    def new_file(self):
        new_buffer = Buffer()
        self.tabs.append(new_buffer)
        self.active_tab_index = len(self.tabs) - 1

    def _save_state_for_undo(self):
        if not self.active_buffer: return
        buf = self.active_buffer
        state = {
            'lines': [line for line in buf.lines],
            'cursor_x': buf.cursor_x,
            'cursor_y': buf.cursor_y,
        }
        buf._undo_stack.append(state)
        buf._redo_stack.clear()
        buf.dirty = True

    def insert_char(self, char: str):
        if not self.active_buffer: return

        if self.has_selection() and char in self.autocomplete_pairs:
            buf = self.active_buffer
            self._save_state_for_undo()
            selected_text = self.get_selected_text()
            closing_char = self.autocomplete_pairs[char]
            wrapped_text = char + selected_text + closing_char
            
            self.delete_selection() # Limpa a seleção e posiciona o cursor
            self.insert_text_at_cursor(wrapped_text) # Insere o texto envolvido
            return

        if self.has_selection():
            self.delete_selection()
        
        buf = self.active_buffer
        y, x = buf.cursor_y, buf.cursor_x
        current_line = buf.lines[y]

        closing_chars = self.autocomplete_pairs.values()
        if char in closing_chars and x < len(current_line) and current_line[x] == char:
            buf.cursor_x += 1
            return

        is_html = buf.filepath and buf.filepath.suffix.lower() in ['.html', '.htm']
        if self.html_tag_autocomplete and is_html and char == '>':
            line_before_cursor = current_line[:x]
            last_open_bracket = line_before_cursor.rfind('<')
            if last_open_bracket != -1:
                tag_content = line_before_cursor[last_open_bracket + 1:]
                tag_name = tag_content.split()[0]
                
                if tag_name and not tag_name.startswith('/') and tag_name not in self.html_void_tags:
                    self._save_state_for_undo()
                    closing_tag = f"</{tag_name}>"
                    buf.lines[y] = current_line[:x] + '>' + closing_tag + current_line[x:]
                    buf.cursor_x += 1
                    return

        self._save_state_for_undo()

        if char in self.autocomplete_pairs:
            closing_char = self.autocomplete_pairs[char]
            buf.lines[y] = current_line[:x] + char + closing_char + current_line[x:]
            buf.cursor_x += 1
        else:
            buf.lines[y] = current_line[:x] + char + current_line[x:]
            buf.cursor_x += 1

    def insert_text_at_cursor(self, text: str):
        if not self.active_buffer: return
        buf = self.active_buffer
        y, x = buf.cursor_y, buf.cursor_x
        
        lines_to_insert = text.split('\n')
        
        if len(lines_to_insert) == 1:
            buf.lines[y] = buf.lines[y][:x] + lines_to_insert[0] + buf.lines[y][x:]
            buf.cursor_x += len(lines_to_insert[0])
        else:
            self._save_state_for_undo()

            line_remainder = buf.lines[y][x:]

            buf.lines[y] = buf.lines[y][:x] + lines_to_insert[0]
            
            for i, line in enumerate(lines_to_insert[1:-1], start=y + 1):
                buf.lines.insert(i, line)

            last_line_index = y + len(lines_to_insert) - 1
            buf.lines.insert(last_line_index, lines_to_insert[-1] + line_remainder)

            buf.cursor_y += len(lines_to_insert) - 1
            buf.cursor_x = len(lines_to_insert[-1])
        buf.dirty = True

    def delete_char(self):
        if not self.active_buffer: return
        if self.has_selection():
            return self.delete_selection()
        buf = self.active_buffer
        self._save_state_for_undo()
        y, x = buf.cursor_y, buf.cursor_x
        if x > 0:
            buf.lines[y] = buf.lines[y][:x-1] + buf.lines[y][x:]
            buf.cursor_x -= 1
        elif y > 0:
            prev_len = len(buf.lines[y-1])
            current_line = buf.lines.pop(y)
            buf.lines[y-1] += current_line
            buf.cursor_y -= 1
            buf.cursor_x = prev_len
        
        line = buf.lines[buf.cursor_y]
        if x > 0 and x < len(line):
            char_before = line[x-1]
            char_after = line[x]
            if char_before in self.autocomplete_pairs and self.autocomplete_pairs[char_before] == char_after:
                buf.lines[buf.cursor_y] = line[:x] + line[x+1:]


    def new_line_with_indent(self):
        if not self.active_buffer: return
        if self.has_selection():
            self.delete_selection()
        self._save_state_for_undo()
        buf = self.active_buffer
        y, x = buf.cursor_y, buf.cursor_x
        current_line = buf.lines[y]
        
        if self.smart_auto_indent and x > 0 and x < len(current_line):
            char_before = current_line[x-1]
            char_after = current_line[x]
            if char_before in self.autocomplete_pairs and self.autocomplete_pairs[char_before] == char_after:
                indentation = "".join(char for char in current_line if char.isspace())
                
                buf.lines[y] = current_line[:x]
                buf.lines.insert(y + 1, indentation + "    ") # Linha do meio, indentada
                buf.lines.insert(y + 2, indentation + char_after) # Linha de baixo com o fechamento
                buf.lines[y+2] = buf.lines[y+2][:len(indentation)] + char_after + current_line[x+1:]
                buf.cursor_y += 1
                buf.cursor_x = len(indentation) + 4
                return

        indentation = ""
        for char in current_line:
            if char.isspace():
                indentation += char
            else:
                break
        
        remaining_text = current_line[x:]
        buf.lines[y] = current_line[:x]
        
        buf.lines.insert(y + 1, indentation + remaining_text)
        buf.cursor_y += 1
        buf.cursor_x = len(indentation)

    def duplicate_line(self):
        if not self.active_buffer: return
        self._save_state_for_undo()
        buf = self.active_buffer
        if 0 <= buf.cursor_y < len(buf.lines):
            buf.lines.insert(buf.cursor_y + 1, buf.lines[buf.cursor_y])
            buf.cursor_y += 1

    def move_line_up(self):
        if not self.active_buffer: return
        buf = self.active_buffer
        if buf.cursor_y > 0:
            self._save_state_for_undo()
            buf.lines[buf.cursor_y], buf.lines[buf.cursor_y - 1] = buf.lines[buf.cursor_y - 1], buf.lines[buf.cursor_y]
            buf.cursor_y -= 1

    def move_line_down(self):
        if not self.active_buffer: return
        buf = self.active_buffer
        if buf.cursor_y < len(buf.lines) - 1:
            self._save_state_for_undo()
            buf.lines[buf.cursor_y], buf.lines[buf.cursor_y + 1] = buf.lines[buf.cursor_y + 1], buf.lines[buf.cursor_y]
            buf.cursor_y += 1

    def toggle_comment(self):
        if not self.active_buffer: return
        buf = self.active_buffer
        if 0 <= buf.cursor_y < len(buf.lines):
            self._save_state_for_undo()
            line = buf.lines[buf.cursor_y]
            if line.lstrip().startswith("# "):
                buf.lines[buf.cursor_y] = line.replace("# ", "", 1)
            else:
                buf.lines[buf.cursor_y] = "# " + line

    def undo(self):
        if not self.active_buffer or not self.active_buffer._undo_stack:
            return False
        buf = self.active_buffer
        current_state = { 'lines': [l for l in buf.lines], 'cursor_x': buf.cursor_x, 'cursor_y': buf.cursor_y }
        buf._redo_stack.append(current_state)
        
        # Restaura o estado anterior
        last_state = buf._undo_stack.pop()
        buf.lines = last_state['lines']
        buf.cursor_x = last_state['cursor_x']
        buf.cursor_y = last_state['cursor_y']
        buf.dirty = True
        return True

    def redo(self):
        if not self.active_buffer or not self.active_buffer._redo_stack:
            return False
        buf = self.active_buffer
        buf._undo_stack.append({ 'lines': [l for l in buf.lines], 'cursor_x': buf.cursor_x, 'cursor_y': buf.cursor_y })
        
        next_state = buf._redo_stack.pop()
        buf.lines = next_state['lines']
        buf.cursor_x = next_state['cursor_x']
        buf.cursor_y = next_state['cursor_y']
        buf.dirty = True
        return True

    def start_selection(self):
        if not self.active_buffer: return
        buf = self.active_buffer
        if not buf.selecting:
            buf.selecting = True
            buf.selection_anchor_x = buf.cursor_x
            buf.selection_anchor_y = buf.cursor_y
        else:
            self.clear_selection()

    def clear_selection(self):
        if not self.active_buffer: return
        buf = self.active_buffer
        buf.selecting = False
        buf.selection_anchor_x = -1
        buf.selection_anchor_y = -1

    def has_selection(self) -> bool:
        if not self.active_buffer: return False
        buf = self.active_buffer
        return buf.selecting and (buf.selection_anchor_x != buf.cursor_x or buf.selection_anchor_y != buf.cursor_y)

    def get_selection_coords(self) -> Tuple[int, int, int, int] | None:
        if not self.has_selection():
            return None
        buf = self.active_buffer
        y1, x1 = buf.selection_anchor_y, buf.selection_anchor_x
        y2, x2 = buf.cursor_y, buf.cursor_x

        if (y1, x1) > (y2, x2):
            y1, x1, y2, x2 = y2, x2, y1, x1

        return y1, x1, y2, x2

    def get_selected_text(self) -> str:
        if not self.active_buffer: return ""
        coords = self.get_selection_coords()
        if not coords:
            return ""
        y1, x1, y2, x2 = coords

        if y1 == y2:
            return self.active_buffer.lines[y1][x1:x2]
        
        text_parts = [self.active_buffer.lines[y1][x1:]]
        for i in range(y1 + 1, y2):
            text_parts.append(self.active_buffer.lines[i])
        text_parts.append(self.active_buffer.lines[y2][:x2])
        
        return "\n".join(text_parts)

    def delete_selection(self):
        if not self.active_buffer: return
        coords = self.get_selection_coords()
        if not coords:
            return
        
        self._save_state_for_undo()
        buf = self.active_buffer
        y1, x1, y2, x2 = coords

        if y1 == y2:
            buf.lines[y1] = buf.lines[y1][:x1] + buf.lines[y1][x2:]
        else:
            buf.lines[y1] = buf.lines[y1][:x1] + buf.lines[y2][x2:]
            del buf.lines[y1+1:y2+1]

        buf.cursor_y, buf.cursor_x = y1, x1
        self.clear_selection()

    def attempt_autocomplete_word(self) -> bool:
        if not self.active_buffer: return False
        buf = self.active_buffer
        y, x = buf.cursor_y, buf.cursor_x
        line = buf.lines[y]

        start_x = x
        while start_x > 0 and line[start_x - 1].isalnum():
            start_x -= 1
        
        word_prefix = line[start_x:x]
        if not word_prefix: return False

        file_ext = buf.filepath.suffix if buf.filepath else ""
        words_to_check = self.autocomplete_words.get(file_ext, [])

        for word in words_to_check:
            if word.startswith(word_prefix) and word != word_prefix:
                self.insert_text_at_cursor(word[len(word_prefix):])
                return True
        return False

    def copy_selection(self) -> str:
        if not PYCLIP_AVAILABLE:
            return "pyclip não está instalado. Copiar/colar desativado."
        
        import pyclip
        selected_text = self.get_selected_text()
        if selected_text:
            pyclip.copy(selected_text)
            self.clear_selection()
            return "Copiado para a área de transferência."
        return "Nada selecionado para copiar."

    def cut_selection(self) -> str:
        if not self.active_buffer: return "Nenhuma aba ativa."
        if not self.has_selection():
            self._save_state_for_undo()
            buf = self.active_buffer
            line = buf.lines[buf.cursor_y]
            if PYCLIP_AVAILABLE:
                import pyclip
                pyclip.copy(line)
            self.delete_char() # Simula um corte de linha
            return "Linha cortada."

        status = self.copy_selection()
        if "Copiado" in status:
            self.delete_selection()
            return "Texto cortado."
        return status

    def paste(self) -> str:
        if not PYCLIP_AVAILABLE:
            return "pyclip não está instalado. Copiar/colar desativado."
        
        import pyclip
        text_to_paste = pyclip.paste()

        if isinstance(text_to_paste, bytes):
            try:
                text_to_paste = text_to_paste.decode('utf-8')
            except UnicodeDecodeError:
                return "Erro ao decodificar texto da área de transferência."

        if self.has_selection():
            self.delete_selection()
        if text_to_paste:
            self.insert_text_at_cursor(text_to_paste.replace('\t', '    '))
            return "Colado."
        return "Área de transferência vazia."