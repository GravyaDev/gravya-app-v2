"""Mutanti di scripts/fornitura-locale.py contro tests/test_fornitura_locale.py.

Costruisce un albero minimo in `lavoro-mutanti/` (copia di scripts/, del test, di ci.yml,
lockfile, .gitignore dal worktree ci-locale), applica una mutazione alla volta e lancia il
test. SOPRAVVISSUTO = il test e' ancora verde = i test non proverebbero quell'errore ingoiato.
Uso: python3 mutanti.py <worktree> <python-del-worktree>
"""
import shutil, subprocess, sys
from pathlib import Path

wt, py = Path(sys.argv[1]).resolve(), sys.argv[2]
qui = Path(__file__).resolve().parent
lavoro = qui / "lavoro-mutanti"

MUTANTI = {
 "esegui: timeout -> codice 0": ('CompletedProcess(cmd, 124, e.stdout or "", f"tempo scaduto', 'CompletedProcess(cmd, 0, e.stdout or "", f"tempo scaduto'),
 "esegui: comando non eseguibile (OSError) -> codice 0": ('CompletedProcess(cmd, 127, "", f"comando non eseguibile', 'CompletedProcess(cmd, 0, "", f"comando non eseguibile'),
 "pip-compile fallito ingoiato (lockfile invariato => 'gia' aggiornato')": ('    if r.returncode != 0:\n        raise ErroreAggiornamento(f"pip-compile non riuscito', '    if False:\n        raise ErroreAggiornamento(f"pip-compile non riuscito'),
 "installazione di pip-tools fallita ingoiata": ('    if r.returncode != 0:\n        raise ErroreAggiornamento(f"installazione di', '    if False:\n        raise ErroreAggiornamento(f"installazione di'),
 "_git: ogni errore di git ingoiato (fetch, worktree, switch, commit, push)": ('    r = run(["git", "-C", str(cwd), *args], timeout=timeout)\n    if r.returncode != 0:', '    r = run(["git", "-C", str(cwd), *args], timeout=timeout)\n    if False:'),
 "solo il push ingoiato": ('        _git(run, sorgente, "push", REMOTO, branch, timeout=TIMEOUT_LUNGO_SECONDI)', '        run(["git", "-C", str(sorgente), "push", REMOTO, branch], timeout=TIMEOUT_LUNGO_SECONDI)'),
 "solo il fetch ingoiato": ('        _git(run, radice, "fetch", REMOTO, BRANCH_PRINCIPALE, timeout=TIMEOUT_LUNGO_SECONDI)', '        run(["git", "-C", str(radice), "fetch", REMOTO, BRANCH_PRINCIPALE], timeout=TIMEOUT_LUNGO_SECONDI)'),
 "gh pr list fallito ingoiato": ('        if aperte.returncode != 0:\n            raise', '        if False:\n            raise'),
 "branch locale gia' esistente ignorato": ('        if run(["git", "-C", str(radice), "rev-parse", "--verify", "--quiet", branch]).returncode == 0:', '        if False:'),
 "gh issue list fallito => si procede (duplicati)": ('    if r.returncode != 0:\n        return ERRORE_ISSUE, [f"issue: elenco', '    if False:\n        return ERRORE_ISSUE, [f"issue: elenco'),
 "gh issue create fallito ingoiato": ('        if c.returncode != 0:\n            codice |= ERRORE_ISSUE', '        if False:\n            codice |= ERRORE_ISSUE'),
 "osv: codice 2 (errore) => OK": ('    return Esito(ERRORE_CONTROLLO, [("controllo", "Controllo OSV non riuscito', '    return Esito(OK, [("controllo", "Controllo OSV non riuscito'),
 "digest: valore non valido accettato": ('    if not re.fullmatch(r"sha256:[0-9a-f]{64}", ora):\n        return Esito(ERRORE_CONTROLLO', '    if False:\n        return Esito(ERRORE_CONTROLLO'),
 "creazione venv di lavoro ingoiata": ('        if r.returncode != 0:\n            raise ErroreAggiornamento(f"venv di lavoro', '        if False:\n            raise ErroreAggiornamento(f"venv di lavoro'),
 "intestazione senza pip-compile => nessun errore": ('        raise ErroreAggiornamento(f"intestazione di {LOCKFILE} senza il comando pip-compile")', '        return ["--upgrade"]'),
}

def prepara():
    if lavoro.exists():
        shutil.rmtree(lavoro)
    (lavoro / "tests").mkdir(parents=True)
    shutil.copytree(wt / "scripts", lavoro / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    (lavoro / ".github/workflows").mkdir(parents=True)
    shutil.copy(wt / ".github/workflows/ci.yml", lavoro / ".github/workflows/ci.yml")
    for f in ("requirements.lock.txt", ".gitignore"):
        shutil.copy(wt / f, lavoro / f)
    shutil.copy(wt / "tests/test_fornitura_locale.py", lavoro / "tests/")

def corri():
    r = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--basetemp={lavoro}/bt", "-x", "tests/test_fornitura_locale.py"],
                       cwd=lavoro, text=True, capture_output=True)
    return r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]

prepara()
print("base:", corri())
orig = (wt / "scripts/fornitura-locale.py").read_text(encoding="utf-8")
for nome, (a, b) in MUTANTI.items():
    assert orig.count(a) == 1, f"pattern non unico/assente: {nome}"
    (lavoro / "scripts/fornitura-locale.py").write_text(orig.replace(a, b), encoding="utf-8")
    rc, riga = corri()
    print(("UCCISO      " if rc != 0 else "SOPRAVVISSUTO"), "|", nome, "|", riga)
shutil.rmtree(lavoro)
