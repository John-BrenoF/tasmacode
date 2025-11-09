import curses
from pathlib import Path
import json

class ConfigWindow:
    def __init__(self, editor):
        self.visible = False
        self.editor = editor  # Referência ao editor para recarregar configs
        self.config_file = Path("config.json")

        self.selected_option_index = 0
        self.scroll_offset = 0
        self.settings = {
            "Geral": {
                "Suporte ao Mouse": ["Ativado", "Desativado"],
                "Exibir Números de Linha": ["Ativado", "Desativado"],
            },
            "Aparência": {
                "Indicador de Linha Vazia (~)": ["Ativado", "Desativado"],
                "Animação do Ponteiro": ["Ativado", "Desativado"],
                "Destacar Linha com Erro": ["Desativado", "Ativado"],
            },
            "Edição": {
                "Auto Indentação Inteligente": ["Ativado", "Desativado"],
                "Autocompletar Tags HTML": ["Ativado", "Desativado"],
            },
            "Navegação": {
                "Modo de Navegação (Vim)": ["Padrão", "Vim (h,j,k,l)"],
            },
        }
        self._discover_extensions()
        self._load_settings()

    def _discover_extensions(self):
        extension_path = Path("extension")
        if not extension_path.is_dir():
            return

        extension_settings = {}
        for f in extension_path.glob("*.py"):
            if f.name != "__init__.py":
                extension_settings[f.name] = ["Ativado", "Desativado"]
        
        if extension_settings:
            self.settings["Extensões"] = extension_settings

    def _load_settings(self):
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            for category_name, options in self.settings.items():
                for option_name, values in options.items():
                    if option_name in loaded_settings:
                        saved_value = loaded_settings[option_name]
                        if saved_value in values:
                            values.remove(saved_value)
                            values.insert(0, saved_value)
        except (json.JSONDecodeError, IOError):
            pass

    def _save_settings(self):
        settings_to_save = {
            name: values[0] for category in self.settings.values() for name, values in category.items()
        }
        self.config_file.write_text(json.dumps(settings_to_save, indent=4), encoding='utf-8')

    def get_setting(self, setting_name: str) -> str:
        for category in self.settings.values():
            if setting_name in category:
                return category[setting_name][0]
        return ""

    def toggle(self):
        self.visible = not self.visible
        self.selected_option_index = 0
        self.scroll_offset = 0

    def handle_key(self, key, win_h=20):
        options = [opt for cat in self.settings.values() for opt in cat.keys()]
        if not options: return

        content_h = win_h - 4 # Altura visível para as opções

        if key == curses.KEY_UP:
            self.selected_option_index = (self.selected_option_index - 1) % len(options)
            if self.selected_option_index < self.scroll_offset:
                self.scroll_offset = self.selected_option_index

        elif key == curses.KEY_DOWN:
            self.selected_option_index = (self.selected_option_index + 1) % len(options)
            if self.selected_option_index >= self.scroll_offset + content_h:
                self.scroll_offset = self.selected_option_index - content_h + 1

        elif key in (curses.KEY_RIGHT, curses.KEY_LEFT, 10): # Enter também alterna
            selected_key = options[self.selected_option_index]
            for category in self.settings.values():
                if selected_key in category:
                    category[selected_key].append(category[selected_key].pop(0))
                    
                    self._save_settings()

                    self.editor.reload_config(self)
                    break

    def draw(self, stdscr):
        if not self.visible:
            return

        h, w = stdscr.getmaxyx()
        win_h = min(20, h - 4)
        win_w = min(70, w - 10)
        win_y, win_x = (h - win_h) // 2, (w - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.bkgd(' ', curses.color_pair(7))
        win.border()
        win.addstr(1, 2, "Configurações (Pressione Alt+C para fechar)", curses.A_BOLD)

        content_h = win_h - 4
        all_options = [(name, values) for opts in self.settings.values() for name, values in opts.items()]
        all_option_keys = [opt[0] for opt in all_options]

        visible_options = all_options[self.scroll_offset : self.scroll_offset + content_h]

        for i, (name, values) in enumerate(visible_options):
            y = i + 3 # Ajusta o y para começar um pouco mais abaixo
            
            option_index = all_option_keys.index(name)
            style = curses.A_REVERSE if option_index == self.selected_option_index else 0
            
            display_value = values[0]
            if display_value == "Ativado": display_value = "✔"
            elif display_value == "Desativado": display_value = "✖"

            win.addstr(y, 4, f"{name}: ".ljust(35) + f"[{display_value}]", style)
        
        if self.scroll_offset > 0:
            win.addstr(1, win_w - 4, "↑", curses.A_DIM)
        if self.scroll_offset + content_h < len(all_options):
            win.addstr(win_h - 2, win_w - 4, "↓", curses.A_DIM)

        stdscr.refresh()
        win.refresh()