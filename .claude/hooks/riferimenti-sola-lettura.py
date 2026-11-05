#!/usr/bin/env python3
"""Hook PreToolUse: i repository di riferimento sono in SOLA LETTURA (vincolo dell'utente, 2026-11-05).

I clone locali di gravya-app e gravya-app-kloudify sono lavoro in corso dell'utente:
nessuna sessione aperta in questo repository (coordinator, subagenti, `claude -p`
lanciato da scripts/agenti.py) può modificarli.

- Read, Grep, Glob: ammessi (non scrivono).
- Edit, Write, NotebookEdit: bloccati se il percorso è dentro un repository protetto.
- Bash: bloccato se la cartella corrente è dentro un repository protetto o se il
  comando ne nomina il percorso. Anche comandi "di lettura" come `git status`
  scrivono (`.git/index`): per leggere si usano Read, Grep e Glob.

Uscita 2 = chiamata rifiutata (vale anche in modalità bypassPermissions).
Unico punto in cui stanno i percorsi protetti.
"""
import json
import os
import re
import sys

PROTETTI = [os.path.realpath(os.path.expanduser(p)) for p in (
    "~/Antigravity/gravya-app",
    "~/Antigravity/gravya-app-kloudify",
)]
NOMI = sorted({os.path.basename(p) for p in PROTETTI}, key=len, reverse=True)
# Un nome protetto come componente di percorso (…/gravya-app, ~/…/gravya-app-kloudify/x),
# non come prefisso di un altro nome (gravya-app-v2, gravya-app-tester…).
RE_PERCORSO = re.compile(r"/(?:" + "|".join(map(re.escape, NOMI)) + r")" + r"(?![\w-])")
RE_NOME = re.compile(r"(?<![\w./-])(?:" + "|".join(map(re.escape, NOMI)) + r")(?![\w-])")


def dentro(percorso: str) -> bool:
    if not percorso:
        return False
    p = os.path.realpath(os.path.expanduser(percorso))
    return any(p == r or p.startswith(r + os.sep) for r in PROTETTI)


def blocca(motivo: str) -> None:
    print(
        f"BLOCCATO: {motivo}. I repository di riferimento ({', '.join(PROTETTI)}) sono in sola "
        "lettura per vincolo dell'utente: si leggono solo con Read, Grep e Glob. "
        "Hook .claude/hooks/riferimenti-sola-lettura.py.",
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> None:
    try:
        dati = json.load(sys.stdin)
    except Exception:
        blocca("input dell'hook non leggibile (rifiuto per prudenza)")
    strumento = dati.get("tool_name", "")
    inp = dati.get("tool_input") or {}
    cwd = dati.get("cwd") or os.getcwd()

    if strumento in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        p = inp.get("file_path") or inp.get("notebook_path") or ""
        if p and not os.path.isabs(p):
            p = os.path.join(cwd, p)
        if dentro(p):
            blocca(f"{strumento} su {p}")
    elif strumento == "Bash":
        cmd = inp.get("command", "")
        if dentro(cwd):
            blocca(f"comando eseguito dentro {cwd}")
        if RE_PERCORSO.search(cmd):
            blocca("il comando nomina il percorso di un repository di riferimento")
        genitori = {os.path.dirname(r) for r in PROTETTI}
        if os.path.realpath(cwd) in genitori and RE_NOME.search(cmd):
            blocca("il comando nomina un repository di riferimento dalla sua cartella madre")
    sys.exit(0)


if __name__ == "__main__":
    main()
