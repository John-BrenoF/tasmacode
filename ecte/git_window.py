import curses
import subprocess
from pathlib import Path
import textwrap
from .utils import prompt_for_input

class GitWindow:
    def __init__(self, stdscr, project_path: Path | None):
        self.stdscr = stdscr
        self.visible = False
        self.project_path = project_path
        self.staged_files = []
        self.unstaged_files = []
        self.branches = []
        self.current_branch = ""
        self.diff_content = []
        self.selected_index = 0
        self.active_pane = "unstaged"
        self.error_message = None
        self.output_log: list[str] = []
        self.diff_scroll_offset = 0
        self.staged_scroll_offset = 0
        self.unstaged_scroll_offset = 0
        self.branch_scroll_offset = 0
        self.log_scroll_offset = 0

    def toggle(self, project_path: Path | None):
        self.visible = not self.visible
        if self.visible:
            self.output_log.clear()
            self.diff_scroll_offset = 0
            self.output_log.append("Painel Git aberto. Use TAB para alternar entre painéis.")
            self.staged_scroll_offset = 0
            self.unstaged_scroll_offset = 0
            self.branch_scroll_offset = 0
            self.log_scroll_offset = 0
            self.active_pane = "unstaged"
            self.selected_index = 0
            self.project_path = project_path
            self.refresh_status()

    def _run_git_command(self, command: list[str]) -> tuple[str, str, int]:
        if not self.project_path or not (self.project_path / ".git").is_dir():
            return "", "Não é um repositório Git ou nenhum projeto aberto.", 1
        try:
            process = subprocess.run(
                ["git", "-C", str(self.project_path)] + command,
                capture_output=True,
                text=True,
                check=False
            )
            return process.stdout, process.stderr, process.returncode
        except FileNotFoundError:
            return "", "Comando 'git' não encontrado. Ele está instalado e no seu PATH?", 1
        except Exception as e:
            return "", f"Erro inesperado: {e}", 1

    def refresh_status(self):
        self.staged_files = []
        self.unstaged_files = []
        self.error_message = None
        self._refresh_branch_info()
        stdout, stderr, returncode = self._run_git_command(["status", "--porcelain"])

        if returncode != 0:
            self.error_message = stderr.strip() if stderr else "Falha ao obter status do Git."
            return

        for line in stdout.strip().split('\n'):
            if not line: continue
            status, filename = line[:2], line[3:]
            if status[0] != ' ' and status[0] != '?':
                self.staged_files.append((status, filename))
            if status[1] != ' ':
                self.unstaged_files.append((status, filename))
            if status.strip() == '??':
                self.unstaged_files.append((status, filename))

        self._validate_selection()
        self.refresh_diff()

    def _refresh_branch_info(self):
        """Busca o branch atual e a lista de todos os branches locais."""
        self.branches = []
        # Pega o branch atual
        branch_stdout, _, _ = self._run_git_command(["branch", "--show-current"])
        self.current_branch = branch_stdout.strip()

        # Pega todos os branches locais
        all_branches_stdout, _, _ = self._run_git_command(["branch"])
        for line in all_branches_stdout.strip().split('\n'):
            self.branches.append(line.strip())

    def _get_current_list(self):
        if self.active_pane == "staged":
            return self.staged_files
        if self.active_pane == "branches":
            return self.branches
        return self.unstaged_files

    def _get_current_list_and_selection(self):
        current_list = self._get_current_list()
        if not current_list or not (0 <= self.selected_index < len(current_list)):
            return current_list, None
        return current_list, current_list[self.selected_index]

    def handle_key(self, key):
        if key in (ord('q'), 27): # q ou ESC
            self.toggle(None)
        elif key == curses.KEY_UP: # Seta para cima
            if self.active_pane == 'diff': # Rolagem no painel de diff
                self.diff_scroll_offset = max(0, self.diff_scroll_offset - 1)
            else: # Navegação nos painéis de arquivos
                self.selected_index = max(0, self.selected_index - 1)
                # Ajusta a rolagem se a seleção sair da tela por cima
                if self.active_pane == 'staged' and self.selected_index < self.staged_scroll_offset:
                    self.staged_scroll_offset = self.selected_index
                elif self.active_pane == 'unstaged' and self.selected_index < self.unstaged_scroll_offset:
                    self.unstaged_scroll_offset = self.selected_index
                elif self.active_pane == 'branches' and self.selected_index < self.branch_scroll_offset:
                    self.branch_scroll_offset = self.selected_index
                self.refresh_diff()
        elif key == curses.KEY_DOWN: # Seta para baixo
            if self.active_pane == 'diff': # Rolagem no painel de diff
                self.diff_scroll_offset = min(len(self.diff_content) - 1, self.diff_scroll_offset + 1)
            else: # Navegação nos painéis de arquivos
                current_list, _ = self._get_current_list_and_selection()
                self.selected_index = min(len(current_list) - 1, self.selected_index + 1)
                
                h, _ = self.stdscr.getmaxyx()
                main_h = (h - 4) * 2 // 3 - 3 # Altura da área superior
                if self.active_pane == 'staged':
                    pane_h = main_h // 2
                elif self.active_pane == 'unstaged':
                    pane_h = main_h - (main_h // 2)
                else: # branches
                    pane_h = main_h

                if self.active_pane == 'staged' and self.selected_index >= self.staged_scroll_offset + pane_h:
                    self.staged_scroll_offset = self.selected_index - pane_h + 1
                elif self.active_pane == 'unstaged' and self.selected_index >= self.unstaged_scroll_offset + pane_h:
                    self.unstaged_scroll_offset = self.selected_index - pane_h + 1
                elif self.active_pane == 'branches' and self.selected_index >= self.branch_scroll_offset + pane_h:
                    self.branch_scroll_offset = self.selected_index - pane_h + 1
                self.refresh_diff()
        elif key == 9:
            panes = ["unstaged", "staged", "branches", "diff"]
            current_idx = panes.index(self.active_pane)
            self.active_pane = panes[(current_idx + 1) % len(panes)]
            self._validate_selection()
            self.diff_scroll_offset = 0
            self.refresh_diff()
        elif key == ord('s'):
            self.stage_file()
        elif key == ord('u'):
            self.unstage_file()
        elif key == ord('c'):
            if self.staged_files:
                self.commit_changes()
            else:
                self.output_log.append("Nenhum arquivo no stage para commitar.")
        elif key == ord('d'):
            self.discard_changes()
        elif key == ord('P'):
            self.push_changes()
        elif key == ord('p'):
            self.pull_changes()
        elif key == ord('z'):
            self.stash_changes()
        elif key == ord('x'):
            self.stash_pop()
        elif key == 10: # Enter
            self.handle_enter()
        elif key == curses.KEY_PPAGE: # PageUp
            self.log_scroll_offset = min(self.log_scroll_offset + 1, len(self.output_log) -1)
        elif key == curses.KEY_NPAGE: # PageDown
            self.log_scroll_offset = max(0, self.log_scroll_offset - 1)

    def _validate_selection(self):
        current_list = self._get_current_list()
        if not current_list:
            self.selected_index = 0
        else:
            self.selected_index = min(self.selected_index, len(current_list) - 1)

    def handle_enter(self):
        if self.active_pane == 'branches':
            self.switch_branch()

    def switch_branch(self):
        if self.active_pane == 'branches' and self.branches:
            branch_name = self.branches[self.selected_index].replace('* ', '')
            self._run_git_command(["checkout", branch_name])
            self.output_log.append(f"Trocado para o branch: {branch_name}")
            self.refresh_status()
    def stage_file(self):
        if self.active_pane == 'unstaged' and self.unstaged_files:
            _, filename = self.unstaged_files[self.selected_index]
            self._run_git_command(["add", filename])
            self.output_log.append(f"Adicionado: {filename}")
            self.refresh_status()

    def unstage_file(self):
        if self.active_pane == 'staged' and self.staged_files:
            _, filename = self.staged_files[self.selected_index]
            self._run_git_command(["restore", "--staged", filename])
            self.output_log.append(f"Removido do stage: {filename}")
            self.refresh_status()

    def refresh_diff(self):
        self.diff_content = ["Selecione um arquivo para ver as alterações."]
        self.diff_scroll_offset = 0
        current_list, selected_item = self._get_current_list_and_selection()

        if not selected_item:
            return

        _, filename = selected_item
        command = ["diff", "--no-color"]

        if self.active_pane == 'staged' or (self.active_pane == 'diff' and not self.unstaged_files):
            command.append("--staged")

        command.append(filename)
        stdout, _, _ = self._run_git_command(command)

        if stdout:
            self.diff_content = stdout.strip().split('\n')

    def commit_changes(self):
        commit_message = prompt_for_input(self.stdscr, "Mensagem do Commit:")
        if commit_message:
            self.output_log.clear()
            self.output_log.append(f"Efetuando commit: '{commit_message}'")
            stdout, stderr, _ = self._run_git_command(["commit", "-m", commit_message])
            self.output_log.extend(stdout.strip().split('\n'))
            self.output_log.extend(stderr.strip().split('\n'))
            self.refresh_status()

    def push_changes(self):
        self.output_log.clear()
        self.output_log.append("Executando 'git push'...")
        stdout, stderr, _ = self._run_git_command(["push"])
        self.output_log.extend(stdout.strip().split('\n'))
        self.output_log.extend(stderr.strip().split('\n'))
        self.refresh_status()

    def pull_changes(self):
        self.output_log.clear()
        self.output_log.append("Executando 'git pull'...")
        stdout, stderr, _ = self._run_git_command(["pull"])
        self.output_log.extend(stdout.strip().split('\n'))
        self.output_log.extend(stderr.strip().split('\n'))
        self.refresh_status()

    def stash_changes(self):
        self.output_log.clear()
        self.output_log.append("Guardando alterações com 'git stash'...")
        stdout, stderr, _ = self._run_git_command(["stash"])
        self.output_log.extend(stdout.strip().split('\n'))
        self.output_log.extend(stderr.strip().split('\n'))
        self.refresh_status()

    def stash_pop(self):
        self.output_log.clear()
        self.output_log.append("Aplicando último stash com 'git stash pop'...")
        stdout, stderr, _ = self._run_git_command(["stash", "pop"])
        self.output_log.extend(stdout.strip().split('\n'))
        self.output_log.extend(stderr.strip().split('\n'))
        self.refresh_status()

    def discard_changes(self):
        self.output_log.clear()
        self.output_log.append("Descartando todas as alterações...")
        self._run_git_command(["restore", "."])
        self._run_git_command(["clean", "-fd"])
        self.output_log.append("Alterações descartadas.")
        self.refresh_status()

    def draw(self):
        if not self.visible:
            return

        h, w = self.stdscr.getmaxyx()
        win_h, win_w = h - 4, w - 4
        win_y, win_x = 2, 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.bkgd(' ', curses.color_pair(7))
        win.box()

        title = f" Git [{self.current_branch}] "
        win.addstr(0, (win_w - len(title)) // 2, title, curses.A_BOLD)

        help_text = "Q/ESC: Sair | TAB: Alternar Painéis | S: Stage | U: Unstage | C: Commit | Enter: Ação"
        win.addstr(win_h - 2, 2, help_text[:win_w-3], curses.A_DIM)

        list_w = max(20, win_w // 3)
        diff_w = win_w - list_w - 1
        top_h = (win_h * 2) // 3 - 3 # Altura da área superior (arquivos, diff)
        log_h = win_h - top_h - 4    # Altura do log

        win.vline(1, list_w, curses.ACS_VLINE, top_h + 1)
        win.hline(top_h + 2, 1, curses.ACS_HLINE, win_w - 2)

        main_h = top_h # Renomeando para consistência
        staged_h = main_h // 2
        unstaged_h = main_h - staged_h

        # --- Painel Staged ---
        staged_title = " Prontas para Commit (Staged) "
        staged_attr = curses.A_UNDERLINE | (curses.A_REVERSE if self.active_pane == 'staged' else 0)
        win.addstr(1, 2, staged_title, staged_attr)
        self._draw_file_list(win, self.staged_files, 2, 2, staged_h, list_w - 3, 'staged')
        win.hline(1 + staged_h, 1, curses.ACS_HLINE, list_w - 1)

        # --- Painel Unstaged ---
        unstaged_title = " Alterações (Unstaged) "
        unstaged_attr = curses.A_UNDERLINE | (curses.A_REVERSE if self.active_pane == 'unstaged' else 0)
        win.addstr(2 + staged_h, 2, unstaged_title, unstaged_attr)
        self._draw_file_list(win, self.unstaged_files, 3 + staged_h, 2, unstaged_h -1, list_w - 3, 'unstaged')
        win.hline(1 + staged_h + unstaged_h, 1, curses.ACS_HLINE, list_w - 1)

        # --- Painel Branches ---
        branch_h = 2 # Altura fixa para branches por enquanto
        branch_title = " Branches "
        branch_attr = curses.A_UNDERLINE | (curses.A_REVERSE if self.active_pane == 'branches' else 0)
        win.addstr(2 + staged_h + unstaged_h, 2, branch_title, branch_attr)
        self._draw_branch_list(win, self.branches, 3 + staged_h + unstaged_h, 2, main_h - (staged_h + unstaged_h) -1, list_w - 3)
        
        # --- Painel Diff ---
        diff_title = " Diff "
        diff_attr = curses.A_UNDERLINE | (curses.A_REVERSE if self.active_pane == 'diff' else 0)
        win.addstr(1, list_w + 2, diff_title, diff_attr)
        
        diff_content_h = main_h
        visible_diff_lines = self.diff_content[self.diff_scroll_offset : self.diff_scroll_offset + diff_content_h]
        for i, line in enumerate(visible_diff_lines):
            if i + 2 >= main_h + 1: break
            color = curses.color_pair(0)
            if line.startswith('+'): color = curses.color_pair(17) # Verde
            if line.startswith('-'): color = curses.color_pair(20) # Vermelho
            if line.startswith('@@'): color = curses.color_pair(4)  # Ciano
            win.addstr(i + 2, list_w + 2, textwrap.shorten(line, width=diff_w - 2, placeholder="..."), color)
        
        # Indicadores de rolagem do Diff
        if self.diff_scroll_offset > 0:
            win.addstr(1, win_w - 2, "↑", curses.A_DIM)
        if self.diff_scroll_offset + diff_content_h < len(self.diff_content):
            win.addstr(main_h, win_w - 2, "↓", curses.A_DIM)

        # --- Painel de Log ---
        win.addstr(main_h + 2, 2, " Saída do Comando (PgUp/PgDn) ", curses.A_UNDERLINE)
        log_y_start = main_h + 3
        
        start_index = max(0, len(self.output_log) - log_h - self.log_scroll_offset)
        end_index = max(0, len(self.output_log) - self.log_scroll_offset)
        visible_log = self.output_log[start_index:end_index]

        for i, line in enumerate(visible_log):
            if log_y_start + i >= win_h - 1: break
            win.addstr(log_y_start + i, 2, textwrap.shorten(line, width=win_w - 4, placeholder="..."))

        win.noutrefresh()

    def _draw_file_list(self, win, files, y_start, x_start, height, width, pane_name):
        is_active = self.active_pane == pane_name
        if self.error_message:
            win.addstr(y_start, x_start, self.error_message, curses.color_pair(5))
            return

        scroll_offset = 0
        if self.active_pane == 'staged':
            scroll_offset = self.staged_scroll_offset
        elif self.active_pane == 'unstaged':
            scroll_offset = self.unstaged_scroll_offset
        elif self.active_pane == 'branches':
            scroll_offset = self.branch_scroll_offset

        if not files:
            win.addstr(y_start, x_start, "Nenhuma alteração", curses.A_DIM)
            return

        visible_files = files[scroll_offset : scroll_offset + height]

        for i, (status, filename) in enumerate(visible_files):
            original_index = scroll_offset + i # O índice real na lista completa
            display_line = f"{status} {filename}"
            
            status_char = status.strip()
            color = curses.color_pair(0) # Padrão
            if 'M' in status_char: color = curses.color_pair(15) # Amarelo
            elif 'A' in status_char: color = curses.color_pair(17) # Verde
            elif 'D' in status_char: color = curses.color_pair(20) # Vermelho
            elif 'R' in status_char: color = curses.color_pair(19) # Magenta
            elif '??' in status_char: color = curses.color_pair(16) # Azul
            if is_active and original_index == self.selected_index:
                color |= curses.A_REVERSE

            win.addstr(y_start + i, x_start, textwrap.shorten(display_line, width=width, placeholder="..."), color)

        # Indicadores de rolagem da lista
        list_x_end = x_start + width
        if scroll_offset > 0:
            win.addstr(y_start, list_x_end - 1, "↑", curses.A_DIM)
        if scroll_offset + height < len(files):
            win.addstr(y_start + height - 1, list_x_end - 1, "↓", curses.A_DIM)

    def _draw_branch_list(self, win, branches, y_start, x_start, height, width):
        is_active = self.active_pane == 'branches'
        scroll_offset = self.branch_scroll_offset

        visible_branches = branches[scroll_offset : scroll_offset + height]

        for i, branch_name in enumerate(visible_branches):
            original_index = scroll_offset + i
            
            attr = curses.A_NORMAL
            if '*' in branch_name:
                attr = curses.A_BOLD
            
            if is_active and original_index == self.selected_index:
                attr |= curses.A_REVERSE

            win.addstr(y_start + i, x_start, textwrap.shorten(branch_name, width=width, placeholder="..."), attr)

        if scroll_offset > 0:
            win.addstr(y_start, x_start + width - 1, "↑", curses.A_DIM)
        if scroll_offset + height < len(branches):
            win.addstr(y_start + height - 1, x_start + width - 1, "↓", curses.A_DIM)