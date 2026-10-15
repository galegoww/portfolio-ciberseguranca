#!/usr/bin/env bash
set -euo pipefail
umask 077
lab_dir="$(mktemp -d "${TMPDIR:-/tmp}/portfolio-permissoes.XXXXXX")"
trap 'rm -rf -- "$lab_dir"' EXIT
mkdir "$lab_dir/financeiro"
printf '%s
' 'DADOS FICTICIOS: receita=1000' > "$lab_dir/financeiro/relatorio.txt"
chmod 755 "$lab_dir/financeiro"
chmod 644 "$lab_dir/financeiro/relatorio.txt"
printf 'Antes: pasta=%s arquivo=%s
' "$(stat -c '%a' "$lab_dir/financeiro")" "$(stat -c '%a' "$lab_dir/financeiro/relatorio.txt")"
chmod 700 "$lab_dir/financeiro"
chmod 600 "$lab_dir/financeiro/relatorio.txt"
printf 'Depois: pasta=%s arquivo=%s
' "$(stat -c '%a' "$lab_dir/financeiro")" "$(stat -c '%a' "$lab_dir/financeiro/relatorio.txt")"
test "$(stat -c '%a' "$lab_dir/financeiro")" = 700
test "$(stat -c '%a' "$lab_dir/financeiro/relatorio.txt")" = 600
printf '%s
' 'OK: somente o proprietario possui permissoes POSIX na pasta e no arquivo.'
