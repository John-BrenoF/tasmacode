#!/bin/bash
cd "$(dirname "$0")"
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Criando ambiente virtual em '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
if ! python -c "import pyclip" &> /dev/null; then
    echo "Instalando 'pyclip'..."
    pip install pyclip
fi
if ! python -c "import pygments" &> /dev/null; then
    echo "Instalando 'pygments'..."
    pip install pygments
fi
if [ -n "$1" ]; then
    python -m ecte.main "$1"
else
    python -m ecte.main
fi