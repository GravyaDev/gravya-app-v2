#!/usr/bin/env bash
# Dalla radice del worktree, .venv attiva. Mutanti in lavoro-mutanti/, cancellata a fine.
set -u
P="$(cd "$(dirname "$0")" && pwd)"; W="$P/lavoro-mutanti"; rm -rf "$W"; mkdir -p "$W"
python3 - "$W" <<'PY'
import sys, pathlib
W = pathlib.Path(sys.argv[1]); s = open("scripts/osv-check.py").read()
def m(nome, *sost):
    t = s
    for a, b in sost:
        assert a in t, nome; t = t.replace(a, b, 1)
    d = W / nome / "scripts"; d.mkdir(parents=True); (d / "osv-check.py").write_text(t)
    (W / nome / "tests").mkdir(); (W / nome / "tests" / "test_ci_osv_check.py").write_text(open("tests/test_ci_osv_check.py").read())
    (W / nome / "requirements.lock.txt").write_text(open("requirements.lock.txt").read())
m("s1_senza_controllo_stato", ('if risposta.status != HTTP_OK:', 'if False:'))
m("s2_senza_timeout", ('timeout=TIMEOUT_SECONDI', 'timeout=None'))
m("s3_lockfile_ignora_righe_e_conteggio", ('raise ErroreLockfile(f"riga {n}', 'continue; raise ErroreLockfile(f"riga {n}'), ('if len(trovati) != blocchi:', 'if False:'))
PY
for d in "$W"/*/; do n=$(basename "$d"); printf '%s, suite del branch: ' "$n"; python -I -m pytest -q -p no:cacheprovider --basetemp="$W/.bt" "$d/tests" 2>&1 | tail -1
  printf '%s, prova: ' "$n"; OSV_SCRIPT="$d/scripts/osv-check.py" python -I -m pytest -q -p no:cacheprovider --basetemp="$W/.bt" "$P/test_stato_e_timeout.py" 2>&1 | tail -1; done
printf 'BRANCH, prova: '; OSV_SCRIPT=scripts/osv-check.py python -I -m pytest -q -p no:cacheprovider --basetemp="$W/.bt" "$P/test_stato_e_timeout.py" 2>&1 | tail -1
rm -rf "$W"
