from pathlib import Path
from ecte.utils import list_dir, create_file, create_folder, prompt_for_input, clone_repo, prompt_for_confirmation
from ecte.execution_handler import search_in_project
from threading import Thread
import http.server
import socketserver
import os
import shutil

class Sidebar:
    ICONS = {
        "git_clone": "",
        "prompt": "",
        "picker_select": "",
        "picker_create": "",
        "folder": "",
        "file": "",
        "file_py": "",
        "file_json": "",
        "file_md": "",
        "file_sh": "",
        "file_html": "",
        "file_css": "",
        "file_js": "",
        "file_rb": "",
        "file_ts": "",
        "file_c": "",
        "file_cpp": "",
        "file_cs": "",
        "file_java": "",
        "file_kt": "",
        "file_rust": "",
        "file_php": "",
        "file_swift": "",
        "file_sql": "",
        "file_yaml": "",
        "file_go": "",
        "file_docker": "",
        "file_img": "",
        "file_zip": "",
        "file_git": "",
        "parent": "",
        "info": "",
    }

    UNSUPPORTED_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp',
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
        '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.rar', '.7z', '.tar', '.gz', '.exe', '.dll', '.so', '.bin', '.iso',
    }

    def __init__(self):
        self.visible = False
        self.current_path: Path | None = None
        self.mode = "prompt"
        self.items = []
        self.selected = 0
        self.scroll_offset = 0
        self._history = []
        self._history_index = -1
        self.cloning_thread = None
        self.cloning_result = None
        self.local_server_thread = None
        self.httpd = None
        self.search_query = ""
        self._folder_cache = []
        self._cache_base_path = None
        self.refresh()

    def refresh(self):
        if self.mode == "picker" and self.current_path:
            picker_items = [
                ("picker_select", "[Abrir esta pasta]", self.current_path),
                ("picker_create", "[Criar nova pasta]", self.current_path),
            ]
            self.items = picker_items + list_dir(self.current_path, include_parent=True)
            self.selected = min(self.selected, len(self.items) - 1) if self.items else 0
        elif self.mode == "project" and self.current_path:
            self.items = list_dir(self.current_path)
            if self.items:
                self.selected = min(self.selected, len(self.items) - 1)
            else:
                self.selected = 0
        elif self.mode == "search":
            self.items = self._filter_folder_cache()
            self.selected = min(self.selected, len(self.items) - 1) if self.items else 0
        else:
            self.mode = "prompt"
            self.items = [
                ("prompt", "Abrir pasta...", None),
                ("git_clone", "[Clonar repositório]", None),
            ]
            self.selected = 0

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.refresh()

    def set_project_path(self, path: Path):
        self.mode = "project"
        self.current_path = path
        self._history = [path]
        self._history_index = 0
        self.refresh()

    def _update_history(self, new_path: Path):
        if self._history_index < len(self._history) - 1:
            self._history = self._history[:self._history_index + 1]
        if not self._history or self._history[-1] != new_path:
            self._history.append(new_path)
            self._history_index += 1
    def _build_folder_cache(self):
        if not self.current_path or self._cache_base_path == self.current_path:
            return
        self._folder_cache = []
        self._cache_base_path = self.current_path
        try:
            for p in self.current_path.rglob("*"):
                if p.is_dir():
                    relative_path = p.relative_to(self.current_path)
                    self._folder_cache.append(("folder", f"{relative_path}/", p))
        except PermissionError:
            pass

    def _filter_folder_cache(self) -> list:
        if not self.search_query:
            return self._folder_cache[:30]
        return [item for item in self._folder_cache if self.search_query.lower() in item[1].lower()]

    def toggle_search_mode(self):
        if self.mode == "search":
            return self.exit_search_mode()
        else:
            return self.start_search_mode()

    def start_search_mode(self):
        if not self.current_path:
            return "Abra um projeto para iniciar a busca."
        Thread(target=self._build_folder_cache, daemon=True).start()
        self.mode = "search"
        self.search_query = ""
        self.refresh()

    def exit_search_mode(self):
        self.mode = "picker"
        self.search_query = ""
        self.refresh()
        return "Busca cancelada"

    def start_project_search(self, stdscr, console):
        """Inicia a busca por texto em todo o projeto."""
        search_term = prompt_for_input(stdscr, "Buscar no projeto:")
        if not search_term:
            return "Busca cancelada."

        console.clear_output()
        console.add_output(f"Buscando por '{search_term}' em '{self.current_path.name}'...")
        console.visible = True

        results = list(search_in_project(self.current_path, search_term))
        if not results:
            console.add_output("Nenhum resultado encontrado.")
        for path, line_num, line_text in results:
            console.add_output(f"  {path}:{line_num} -> {line_text}")
        return f"{len(results)} resultados encontrados."

    def up(self):
        if self.selected > 0:
            self.selected -= 1

    def down(self):
        if self.items and self.selected < len(self.items) - 1:
            self.selected += 1

    def enter(self, editor, console, stdscr):
        if not self.items:
            return

        item_type, _, path = self.items[self.selected]

        if self.mode == "search":
            self.current_path = path
            self.exit_search_mode()
            console.set_cwd(self.current_path)
            self.refresh()
            return f"Navegou para: {path.name}"

        if item_type == "prompt":
            self.mode = "picker"
            self.current_path = Path.home()
            self._update_history(self.current_path)
            self.refresh()
            return "picker_started"
        elif item_type == "git_clone":
            if self.cloning_thread and self.cloning_thread.is_alive():
                return "Clonagem já em andamento..."

            repo_url = prompt_for_input(stdscr, "URL do repositório Git: ")
            if repo_url:
                console.visible = True
                self.cloning_thread = Thread(target=clone_repo, args=(repo_url, self, console), daemon=True)
                self.cloning_thread.start()
                return "Clonando..."
            return "Operação cancelada."

        elif item_type == "picker_select":
            if self.current_path:
                self.set_project_path(self.current_path)
                console.set_cwd(self.current_path)
                return f"Pasta aberta: {self.current_path.name}"
        elif item_type == "picker_create":
            if self.current_path:
                folder_name = prompt_for_input(stdscr, "Nome da nova pasta:")
                if folder_name:
                    new_folder_path = self.current_path / folder_name
                    create_folder(new_folder_path)
                    console.set_cwd(new_folder_path)
                    self.set_project_path(new_folder_path)
                    return f"Pasta '{folder_name}' criada e aberta."
        elif item_type in ("folder", "parent"):
            self._update_history(path)
            console.set_cwd(path)
            self.current_path = path
            self.refresh()
        elif item_type.startswith("file"):
            if path.suffix.lower() in self.UNSUPPORTED_EXTENSIONS:
                return f"Pré-visualização para '{path.suffix}' não disponível."
            editor.open_file(path)
            return f"Arquivo aberto: {path.name}"

    def add_file(self, stdscr):
        if not self.current_path or self.mode == "prompt":
            return "Abra uma pasta primeiro."
        file_name = prompt_for_input(stdscr, "Nome do novo arquivo:")
        if file_name:
            create_file(self.current_path / file_name)
            self.refresh()
            return f"Arquivo '{file_name}' criado."
        return "Criação de arquivo cancelada."

    def rename_item(self, stdscr):
        if not self.current_path or self.mode != "project" or not self.items:
            return "Selecione um item no projeto para renomear."

        _, item_name, item_path = self.items[self.selected]
        new_name = prompt_for_input(stdscr, f"Novo nome para '{item_name}':")

        if new_name:
            try:
                new_path = item_path.parent / new_name
                item_path.rename(new_path)
                self.refresh()
                return f"'{item_name}' renomeado para '{new_name}'."
            except Exception as e:
                return f"Erro ao renomear: {e}"
        return "Renomeação cancelada."

    def delete_item(self, stdscr):
        if not self.current_path or self.mode != "project" or not self.items:
            return "Selecione um item no projeto para deletar."

        _, item_name, item_path = self.items[self.selected]
        
        if prompt_for_confirmation(stdscr, f"Deletar '{item_name}'?"):
            try:
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()
                self.refresh()
                return f"'{item_name}' deletado."
            except Exception as e:
                return f"Erro ao deletar: {e}"
        return "Deleção cancelada."

    def add_folder(self, stdscr):
        if not self.current_path or self.mode == "prompt": return
        folder_name = prompt_for_input(stdscr, "Nome da nova pasta (Alt+P):")
        if folder_name:
            new_folder_path = self.current_path / folder_name
            create_folder(new_folder_path)
            console.set_cwd(new_folder_path)
            self.set_project_path(new_folder_path)
            return f"Pasta '{folder_name}' criada e aberta."
        return "Criação de pasta cancelada."

    def go_to_parent(self, console):
        if self.current_path and self.current_path.parent != self.current_path:
            if self.mode in ('picker', 'project'):
                parent_path = self.current_path.parent
                self._update_history(parent_path)
                console.set_cwd(parent_path)
                self.current_path = parent_path
                self.refresh()
                return "Navegando para diretório pai"
        return None

    def go_back(self):
        if self._history_index > 0:
            self._history_index -= 1
            self.current_path = self._history[self._history_index]
            console.set_cwd(self.current_path)
            self.refresh()
            return "Voltando no histórico"
        return None

    def go_forward(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self.current_path = self._history[self._history_index]
            console.set_cwd(self.current_path)
            self.refresh()
            return "Avançando no histórico"
        return None

    def toggle_local_server(self):
        if self.local_server_thread and self.local_server_thread.is_alive():
            return self.stop_local_server()
        else:
            return self.start_local_server()

    def start_local_server(self):
        if not self.current_path:
            return "Abra um projeto para iniciar o servidor."

        PORT = 8000

        def server_worker():
            os.chdir(self.current_path)
            handler = http.server.SimpleHTTPRequestHandler
            self.httpd = socketserver.TCPServer(("", PORT), handler)
            self.httpd.serve_forever()

        self.local_server_thread = Thread(target=server_worker, daemon=True)
        self.local_server_thread.start()
        return f"Servidor local iniciado em http://localhost:{PORT}"

    def stop_local_server(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
            self.local_server_thread = None
            return "Servidor local parado."
        return "Nenhum servidor local em execução."