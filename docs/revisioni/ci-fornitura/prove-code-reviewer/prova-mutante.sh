#!/usr/bin/env bash
# Da eseguire dalla radice del worktree .worktrees/ci-fornitura con la .venv attiva.
# Crea un mutante in una cartella di lavoro dentro la cartella del report e la cancella.
set -u
P="$(cd "$(dirname "$0")" && pwd)"; W="$P/lavoro-mutante"; rm -rf "$W"; mkdir -p "$W/scripts" "$W/tests"
cp tests/test_ci_osv_check.py "$W/tests/"
python3 - "$W/scripts/osv-check.py" <<'PY'
import sys
s = open("scripts/osv-check.py").read()
a = 'raise ErroreOsv(f"richiesta a {url} fallita: {e}") from e'
assert a in s
open(sys.argv[1], "w").write(s.replace(a, 'return {"results": [{} for _ in corpo["queries"]]}'))
PY
echo "== suite del branch sul MUTANTE (invia_http fail-open):"
python -I -m pytest -q -p no:cacheprovider --basetemp="$W/.bt" "$W/tests" 2>&1 | tail -1
echo "== prova del reviewer sul MUTANTE:"
OSV_SCRIPT="$W/scripts/osv-check.py" python -I -m pytest -q -p no:cacheprovider --basetemp="$W/.bt" "$P/test_invia_http_fail_closed.py" 2>&1 | tail -4
echo "== prova del reviewer sul codice del BRANCH:"
OSV_SCRIPT=scripts/osv-check.py python -I -m pytest -q -p no:cacheprovider --basetemp="$W/.bt" "$P/test_invia_http_fail_closed.py" 2>&1 | tail -4
rm -rf "$W"
