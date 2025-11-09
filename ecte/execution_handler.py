import os
from pathlib import Path
from typing import Iterator, Tuple

EXECUTION_COMMANDS = {
    ".py": 'python3 "{filepath}"',
    ".js": 'node "{filepath}"',
    ".sh": 'bash "{filepath}"',
    ".rb": 'ruby "{filepath}"',
    ".ts": 'ts-node "{filepath}"',
    ".go": 'go run "{filepath}"',

    ".c": 'gcc "{filepath}" -o "/tmp/{filename_no_ext}" && "/tmp/{filename_no_ext}"',
    ".cpp": 'g++ "{filepath}" -o "/tmp/{filename_no_ext}" && "/tmp/{filename_no_ext}"',
    ".rs": 'rustc "{filepath}" -o "/tmp/{filename_no_ext}" && "/tmp/{filename_no_ext}"',
    
    ".java": 'javac -d "/tmp" "{filepath}" && java -cp "/tmp" "{filename_no_ext}"',
    
    ".cs": 'mcs -out:"/tmp/{filename_no_ext}.exe" "{filepath}" && mono "/tmp/{filename_no_ext}.exe"',
}

def search_in_project(directory: Path, search_term: str) -> Iterator[Tuple[Path, int, str]]:
    """
    Busca por um termo em todos os arquivos de um diretório (projeto).
    Ignora diretórios .git e arquivos binários.
    """
    if not search_term:
        return

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != '.git']
        for file in files:
            filepath = Path(root) / file
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        if search_term in line:
                            yield (filepath.relative_to(directory), i + 1, line.strip())
            except Exception:
                continue # Ignora arquivos que não podem ser lidos

def get_execution_command(filepath: Path) -> str | None:
    """
    Determina o comando de execução para um determinado arquivo.
    """
    if not filepath:
        return None

    if os.access(filepath, os.X_OK) and not filepath.is_dir():
        return f'"{filepath}"'

    suffix = filepath.suffix.lower()
    command_template = EXECUTION_COMMANDS.get(suffix)

    if command_template:
        placeholders = {
            "filepath": str(filepath),
            "dirpath": str(filepath.parent),
            "filename": filepath.name,
            "filename_no_ext": filepath.stem,
        }
        return command_template.format(**placeholders)

    return None