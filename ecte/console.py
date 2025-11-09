import subprocess
import shlex
from threading import Thread
from pathlib import Path
import os
import json

class Console:
    def __init__(self):
        self.visible = False
        self.command = ""
        self.cursor_x = 0 
        self.output = []
        self.output_scroll_offset = 0
        self.running = False
        self.command_history = []
        self.history_index = -1
        self.cwd = Path.cwd()
        self.aliases = {}
        self._aliases_file = Path.home() / ".config" / "ecte" / "aliases.json"

        self._load_aliases()

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            if not self.output:
                self.output = ["Console aberto. Digite comandos..."]
        self.output_scroll_offset = 0 

    def set_cwd(self, new_path: Path):
        self.cwd = new_path

    def _apply_aliases(self, cmd_str: str) -> str:
        parts = cmd_str.split()
        if not parts:
            return cmd_str
        
        alias_cmd = parts[0]
        if alias_cmd in self.aliases:
            return self.aliases[alias_cmd] + " " + " ".join(parts[1:])
        return cmd_str

    def run_command(self, cmd: str):
        def worker():
            self.running = True
            args = []
            try:
                cmd_with_alias = self._apply_aliases(cmd)
                if isinstance(cmd, str):
                    parts = cmd_with_alias.split()
                    if len(parts) > 1:
                        command_executable = parts[0]
                        potential_path_str = " ".join(parts[1:])
                        potential_path = Path(potential_path_str).expanduser()
                        
                        if potential_path.exists():
                            args = [command_executable, str(potential_path)]
                        else:
                            args = shlex.split(cmd_with_alias)
                    else:
                        args = parts
                else:
                    args = cmd

                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                    cwd=self.cwd 
                )

                if result.stdout:
                    self.output.extend(result.stdout.splitlines())
                if result.stderr:
                    self.output.extend(f"[ERRO] {line}" for line in result.stderr.splitlines())
            except Exception as e:
                self.output.append(f"[EXCEÇÃO] {e}")
            finally:
                self.running = False

        Thread(target=worker, daemon=True).start()

    def get_prompt(self) -> str:
        try:
            project_root = Path.cwd() 
            relative_path = self.cwd.relative_to(project_root)
            prompt_path = f"~/{relative_path}" if relative_path != Path('.') else "~"
        except ValueError:
            prompt_path = self.cwd.name
        return f"({prompt_path}) >"

    def _load_aliases(self):
        if self._aliases_file.exists():
            try:
                with open(self._aliases_file, 'r') as f:
                    self.aliases = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.aliases = {} 

    def _save_aliases(self):
        try:
            self._aliases_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._aliases_file, 'w') as f:
                json.dump(self.aliases, f, indent=2)
        except IOError:
            self.output.append("[ERRO] Não foi possível salvar os aliases.")

    def _handle_builtins(self) -> bool:
        cmd = self.command.strip()
        if cmd == "clear":
            self.clear_output()
            return True
        if cmd.startswith("cd "):
            self._change_directory(cmd[3:])
            return True
        if cmd == "cd" or cmd == "cd ~":
            self._change_directory(str(Path.home()))
            return True
        if cmd == "exit":
            self.toggle()
            return True
        if cmd == "history":
            self.output.extend(f"  {i}: {c}" for i, c in enumerate(self.command_history))
            return True
        if cmd.startswith("alias "):
            parts = cmd.split(maxsplit=2)
            if len(parts) > 1 and '=' in parts[1]:
                name, value = parts[1].split('=', 1)
                self.aliases[name] = value.strip('"\'')
                self._save_aliases()
                self.output.append(f"Alias '{name}' definido.")
            return True
        if cmd == "alias":
            if not self.aliases:
                self.output.append("Nenhum alias definido.")
            self.output.extend(f"  {name} = '{value}'" for name, value in self.aliases.items())
            return True
        if cmd == "help":
            self.output.append("Comandos embutidos do console:")
            self.output.append("  cd [caminho] - Muda o diretório atual. 'cd' ou 'cd ~' vai para o home.")
            self.output.append("  clear          - Limpa a saída do console.")
            self.output.append("  history        - Mostra o histórico de comandos.")
            self.output.append("  alias          - Lista todos os aliases.")
            self.output.append("  alias NOME=VALOR - Cria um novo alias.")
            self.output.append("  exit           - Fecha o console.")
            return True
        return False

    def insert_char(self, char: str):
        self.command = self.command[:self.cursor_x] + char + self.command[self.cursor_x:]
        self.cursor_x += 1

    def delete_char(self):
        if self.cursor_x > 0:
            self.command = self.command[:self.cursor_x - 1] + self.command[self.cursor_x:]
            self.cursor_x -= 1

    def delete_forward(self):
        if self.cursor_x < len(self.command):
            self.command = self.command[:self.cursor_x] + self.command[self.cursor_x + 1:]

    def move_cursor(self, delta: int):
        self.cursor_x = max(0, min(len(self.command), self.cursor_x + delta))

    def submit_command(self):
        if self.command:
            if not self.command_history or self.command_history[-1] != self.command:
                self.command_history.append(self.command)
            prompt = self.get_prompt()
            self.output.append("---")
            self.output.append(f"{prompt} {self.command}")
            self.output_scroll_offset = 0 # Rola para o final

            if not self._handle_builtins():
                self.run_command(self.command)
            self.command = ""
            self.cursor_x = 0
        self.history_index = len(self.command_history)

    def previous_command(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.command = self.command_history[self.history_index]
            self.cursor_x = len(self.command)

    def next_command(self):
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command = self.command_history[self.history_index]
            self.cursor_x = len(self.command)
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.command = ""
            self.cursor_x = 0

    def autocomplete(self):
        cmd_part = self.command.split()
        if not cmd_part:
            return

        to_complete = cmd_part[-1]
        path_to_complete = Path(to_complete)
        
        search_dir = self.cwd / path_to_complete.parent
        prefix = path_to_complete.name

        try:
            matches = [
                p.name for p in search_dir.iterdir()
                if p.name.startswith(prefix)
            ]
            if len(matches) == 1:
                completed_path = path_to_complete.parent / matches[0]
                if (search_dir / matches[0]).is_dir():
                    completed_path = f"{completed_path}/"
                cmd_part[-1] = str(completed_path)
                self.command = " ".join(cmd_part)
                self.cursor_x = len(self.command)
            elif len(matches) > 1:
                common_prefix = os.path.commonprefix(matches)
                if common_prefix:
                    completed_path = path_to_complete.parent / common_prefix
                    cmd_part[-1] = str(completed_path)
                    self.command = " ".join(cmd_part)
                    self.cursor_x = len(self.command)
                self.output.append(" ".join(matches))
        except FileNotFoundError:
            pass 

    def _change_directory(self, path_str: str):
        try:
            new_path = (self.cwd / path_str).expanduser().resolve()
            if new_path.is_dir():
                self.cwd = new_path
            else:
                self.output.append(f"[ERRO] cd: '{path_str}' não é um diretório.")
        except Exception as e:
            self.output.append(f"[ERRO] cd: {e}")

    def clear_output(self):
        self.output.clear()

    def add_output(self, line: str):
        self.output.append(line)