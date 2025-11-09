CURRENT_DIR=$(pwd)
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
if [ -z "$1" ]; then
  echo "Uso: tasma <nome_do_arquivo>"
  exit 1
fi
FILE_NAME="$1"
if [[ "$FILE_NAME" = /* ]] || [[ "$FILE_NAME" = ~* ]]; then
  FULL_FILE_PATH="$FILE_NAME"
else
  FULL_FILE_PATH="$CURRENT_DIR/$FILE_NAME"
fi

if [ ! -f "$FULL_FILE_PATH" ]; then
  touch "$FULL_FILE_PATH"
fi
"$SCRIPT_DIR/run.sh" "$FULL_FILE_PATH"