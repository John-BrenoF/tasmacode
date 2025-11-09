import os
import subprocess
import curses
from curses.textpad import Textbox, rectangle
from pathlib import Path
import platform
from threading import Thread


def get_project_root() -> Path:
    return Path.cwd()

def create_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

def create_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)

FILE_TYPE_MAPPING = {
    ".py": "file_py",
    ".json": "file_json",
    ".md": "file_md",
    ".sh": "file_sh",
    ".html": "file_html",
    ".css": "file_css",
    ".js": "file_js",
    ".ts": "file_ts",
    ".c": "file_c",
    ".cpp": "file_cpp",
    ".java": "file_java",
    ".rs": "file_rust",
    ".go": "file_go",
    ".dockerfile": "file_docker",
    ".png": "file_img", ".jpg": "file_img", ".jpeg": "file_img", ".gif": "file_img",
    ".zip": "file_zip", ".tar": "file_zip", ".gz": "file_zip", ".rar": "file_zip",
    ".gitignore": "file_git",
}

def get_file_type(filename: str) -> str:
    if filename in FILE_TYPE_MAPPING:
        return FILE_TYPE_MAPPING[filename]
    ext = Path(filename).suffix.lower()
    return FILE_TYPE_MAPPING.get(ext, "file")

def list_dir(path: Path, include_parent: bool = False):
    items = []
    if include_parent and path.parent != path:
        items.append(("parent", "../", path.parent))

    for p in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        file_type = get_file_type(p.name)
        if p.is_dir():
            items.append(("folder", p.name + "/", p))
        else:
            items.append((file_type, p.name, p))
    return items

def prompt_for_input(stdscr, message: str) -> str | None:
    h, w = stdscr.getmaxyx()
    prompt_h, prompt_w = 5, w - 20
    prompt_y, prompt_x = (h - prompt_h) // 2, (w - prompt_w) // 2

    win = curses.newwin(prompt_h, prompt_w, prompt_y, prompt_x)
    win.box()
    win.addstr(1, 2, message)
    win.refresh()

    edit_win = curses.newwin(1, prompt_w - 4, prompt_y + 2, prompt_x + 2)
    box = Textbox(edit_win)

    box.edit()

    input_str = box.gather().strip()
    return input_str if input_str else None

def prompt_for_confirmation(stdscr, message: str) -> bool:
    h, w = stdscr.getmaxyx()
    prompt_h, prompt_w = 5, 40
    prompt_y, prompt_x = (h - prompt_h) // 2, (w - prompt_w) // 2

    win = curses.newwin(prompt_h, prompt_w, prompt_y, prompt_x)
    win.bkgd(' ', curses.color_pair(7))
    win.box()
    win.addstr(1, (prompt_w - len(message)) // 2, message)

    win.addstr(3, (prompt_w - 13) // 2, "[")
    win.addstr("s", curses.color_pair(2) | curses.A_BOLD)
    win.addstr("] sim / [")
    win.addstr("n", curses.color_pair(5) | curses.A_BOLD)
    win.addstr("] não")

    win.refresh()

    while True:
        key = stdscr.getch()
        if key in (ord('s'), ord('S')):
            return True
        if key in (ord('n'), ord('N'), 27):
            return False

def prompt_with_options(stdscr, title, options):
    """
    Exibe um prompt com uma lista de opções (botões) e retorna a opção selecionada.

    Args:
        stdscr: A janela principal do curses.
        title (str): A mensagem a ser exibida no prompt.
        options (list[str]): Uma lista de strings para os botões.

    Returns:
        str | None: O texto da opção selecionada, ou None se cancelado (ESC).
    """
    h, w = stdscr.getmaxyx()
    win_h = 7
    
    buttons_width = sum(len(o) + 4 for o in options) - 2
    win_w = max(len(title) + 6, buttons_width + 6)

    win_y, win_x = (h - win_h) // 2, (w - win_w) // 2

    win = curses.newwin(win_h, win_w, win_y, win_x)
    win.bkgd(' ', curses.color_pair(7))
    win.box()
    win.keypad(True)

    win.addstr(2, (win_w - len(title)) // 2, title)

    selected_option = 0
    while True:
        buttons_total_width = sum(len(o) + 4 for o in options) - 2
        button_x_start = (win_w - buttons_total_width) // 2
        for i, option in enumerate(options):
            button_style = curses.A_REVERSE if i == selected_option else curses.color_pair(7)
            win.addstr(4, button_x_start, f"  {option}  ", button_style)
            button_x_start += len(option) + 4

        key = win.getch()

        if key in (curses.KEY_LEFT, 9):
            selected_option = (selected_option - 1 + len(options)) % len(options)
        elif key in (curses.KEY_RIGHT, 9):
            selected_option = (selected_option + 1) % len(options)
        elif key == 10: # Enter
            return options[selected_option]
        elif key == 27: # ESC
            return None

def clone_repo(repo_url: str, sidebar_instance, console_instance):
    result: tuple[str, Path | None]
    try:
        repo_name = repo_url.split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]

        projects_dir = Path.home() / "TASMACODE_Projects"
        projects_dir.mkdir(exist_ok=True)
        clone_path = projects_dir / repo_name

        if clone_path.exists():
            result = f"Diretório '{repo_name}' já existe.", clone_path
        else:
            console_instance.clear_output()
            console_instance.add_output(f"Clonando de {repo_url}...")
            process = subprocess.Popen(
                ["git", "clone", "--progress", repo_url, str(clone_path)],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            for line in iter(process.stderr.readline, ''):
                console_instance.add_output(line.strip())
            
            process.wait()
            if process.returncode == 0:
                result = f"Repositório '{repo_name}' clonado!", clone_path
            else:
                result = "Falha na clonagem. Verifique o console.", None
    except subprocess.CalledProcessError as e:
        result = f"Erro ao clonar: {e.stderr.strip()}", None
    except Exception as e:
        result = f"Erro inesperado: {e}", None

    sidebar_instance.cloning_result = result

def open_terminal_at_path(path: Path) -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(f'start cmd /K "cd /d {path}"', shell=True)
        elif system == "Darwin":
            subprocess.Popen(['open', '-a', 'Terminal', str(path)])
        else:
            terminals = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'terminator', 'xterm']
            for terminal in terminals:
                if subprocess.run(['which', terminal], capture_output=True).returncode == 0:
                    subprocess.Popen([terminal, '--working-directory', str(path)])
                    return True
            return False
        return True
    except Exception:
        return False