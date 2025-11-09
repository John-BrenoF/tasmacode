import curses
from .utils import prompt_for_input, prompt_with_options

def find_all_occurrences(lines: list[str], search_term: str) -> list[tuple[int, int]]:
    """Encontra todas as ocorrências de um termo nas linhas e retorna suas coordenadas (y, x)."""
    occurrences = []
    if not search_term:
        return occurrences
    for i, line in enumerate(lines):
        start_index = 0
        while True:
            index = line.find(search_term, start_index)
            if index == -1:
                break
            occurrences.append((i, index))
            start_index = index + 1
    return occurrences

def start_find_replace(stdscr, buffer):
    """Inicia o fluxo de localizar e substituir."""
    
    # 1. Obter os termos de busca e substituição do usuário
    search_term = prompt_for_input(stdscr, "Localizar:")
    if not search_term:
        return "Operação cancelada."

    replace_term = prompt_for_input(stdscr, f"Substituir '{search_term}' por:")
    if replace_term is None: # Permite substituição por string vazia
        return "Operação cancelada."

    # 2. Encontrar todas as ocorrências
    occurrences = find_all_occurrences(buffer.lines, search_term)
    if not occurrences:
        return f"Nenhuma ocorrência de '{search_term}' encontrada."

    # 3. Iniciar o processo de substituição interativa
    original_lines = [line for line in buffer.lines]
    original_cursor = (buffer.cursor_y, buffer.cursor_x)
    
    i = 0
    replacements_count = 0
    
    while i < len(occurrences):
        y, x = occurrences[i]
        
        # Move o cursor para a ocorrência atual para que o usuário a veja
        buffer.cursor_y = y
        buffer.cursor_x = x
        
        # Redesenha a tela para mostrar a nova posição do cursor
        # (Esta é uma simplificação, o ideal seria ter o loop principal redesenhando)
        stdscr.clear() 
        # Precisamos de uma forma de redesenhar a UI principal aqui.
        # Por enquanto, vamos focar na lógica e usar um prompt.

        # Mostra o prompt de opções
        options = ["Substituir", "Ignorar", "Substituir Tudo", "Cancelar"]
        choice = prompt_with_options(
            stdscr, 
            f"Substituir '{search_term}'? ({i+1}/{len(occurrences)})",
            options
        )

        if choice == "Substituir":
            # Aplica a substituição na linha
            line = buffer.lines[y]
            buffer.lines[y] = line[:x] + replace_term + line[x + len(search_term):]
            
            # Atualiza as coordenadas das ocorrências futuras na mesma linha
            offset = len(replace_term) - len(search_term)
            for j in range(i + 1, len(occurrences)):
                if occurrences[j][0] == y:
                    occurrences[j] = (y, occurrences[j][1] + offset)
            
            replacements_count += 1
            i += 1

        elif choice == "Ignorar":
            i += 1

        elif choice == "Substituir Tudo":
            # Salva o estado para undo antes da substituição em massa
            # A lógica de undo está no editor, não no buffer diretamente.
            # Esta parte precisaria de uma refatoração maior para suportar undo.
            # Por enquanto, a substituição em massa não será "desfazível".
            # Substitui a atual e todas as restantes
            for j in range(i, len(occurrences)):
                y_rem, x_rem = occurrences[j]
                # Recalcula a posição x se já houve substituições na linha
                line_rem = buffer.lines[y_rem]
                # Esta lógica de recalcular o x pode ser complexa. Uma abordagem mais simples:
            
            # Abordagem mais simples para "Substituir Tudo"
            new_lines = [line.replace(search_term, replace_term) for line in original_lines]
            final_replacements = sum(line.count(search_term) for line in original_lines)
            buffer.lines = new_lines
            buffer.dirty = True
            return f"{final_replacements} ocorrências substituídas."

        elif choice is None or choice == "Cancelar":
            buffer.lines = original_lines # Restaura o estado original
            buffer.cursor_y, buffer.cursor_x = original_cursor
            return "Operação cancelada."

    buffer.dirty = True
    return f"{replacements_count} ocorrências substituídas."