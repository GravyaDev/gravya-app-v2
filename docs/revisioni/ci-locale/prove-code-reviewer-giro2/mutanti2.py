"""Mutanti del giro 2 sul codice nuovo di scripts/fornitura-locale.py e scripts/agenti.py.
Copia scripts/, tests/ e i file letti dai test in `lavoro/` accanto a questo file, applica una mutazione
alla volta e lancia i test pertinenti. SOPRAVVISSUTO = i test restano verdi = il difetto passerebbe.
Uso: python3 mutanti2.py <worktree> <python-del-worktree> [sottostringa-del-nome ...]
"""
import shutil, subprocess, sys
from pathlib import Path

wt, py = Path(sys.argv[1]).resolve(), sys.argv[2]
qui = Path(__file__).resolve().parent
lavoro = qui / "lavoro"
FL = "scripts/fornitura-locale.py"
AG = "scripts/agenti.py"
TESTS = ["tests/test_fornitura_locale.py", "tests/test_fornitura_strumenti.py", "tests/test_agenti_unisci.py"]

M = [
 # fornitura-locale.py
 (FL, "_isola: eccezione => esito OK", '        if nome == "lockfile":\n            e = Esito(ERRORE_AGGIORNAMENTO', '        if True:\n            e = Esito(OK'),
 (FL, "_isola: eccezione non-lockfile => OK", '            e = Esito(ERRORE_CONTROLLO, [("controllo", f"Controllo «{nome}»: eccezione inattesa', '            e = Esito(OK, [("controllo", f"Controllo «{nome}»: eccezione inattesa'),
 (FL, "segnala in esegui_controlli: eccezione => codice OK", 'codice, messaggi = ERRORE_ISSUE, [f"issue: eccezione inattesa', 'codice, messaggi = OK, [f"issue: eccezione inattesa'),
 (FL, "esegui_controlli: codice di segnala perso", '    totale.codice |= codice\n    totale.messaggi += messaggi', '    totale.messaggi += messaggi'),
 (FL, "e_riuscita: la prova conta", 'if riga.get("prova") or not isinstance(esiti, dict)', 'if not isinstance(esiti, dict)'),
 (FL, "e_riuscita: errore del controllo ignorato", 'not esiti[c]["codice"] & BIT_ERRORE', 'True'),
 (FL, "e_riuscita: errore globale (issue) ignorato", ' and isinstance(riga.get("codice"), int) and not riga["codice"] & BIT_ERRORE', ''),
 (FL, "e_riuscita: basta un controllo", 'not all(c in esiti for c in CONTROLLI)', 'not any(c in esiti for c in CONTROLLI)'),
 (FL, "BIT_ERRORE senza ERRORE_ISSUE", 'BIT_ERRORE = ERRORE_CONTROLLO | ERRORE_AGGIORNAMENTO | ERRORE_ISSUE', 'BIT_ERRORE = ERRORE_CONTROLLO | ERRORE_AGGIORNAMENTO'),
 (FL, "BIT_ERRORE senza ERRORE_AGGIORNAMENTO", 'BIT_ERRORE = ERRORE_CONTROLLO | ERRORE_AGGIORNAMENTO | ERRORE_ISSUE', 'BIT_ERRORE = ERRORE_CONTROLLO | ERRORE_ISSUE'),
 (FL, "stato: soglia >= invece di >", '    if giorni > SOGLIA_ESECUZIONE_GIORNI:', '    if giorni >= SOGLIA_ESECUZIONE_GIORNI:'),
 (FL, "stato: soglia piu' larga", '    if giorni > SOGLIA_ESECUZIONE_GIORNI:', '    if giorni > SOGLIA_ESECUZIONE_GIORNI + 1:'),
 (FL, "stato: nessuna riuscita => OK", 'return STATO_SCADUTO, righe + [f"ATTENZIONE: nessuna esecuzione riuscita', 'return OK, righe + [f"ATTENZIONE: nessuna esecuzione riuscita'),
 (FL, "stato: scaduto => OK", 'return STATO_SCADUTO, righe + [f"ATTENZIONE: l\'ultimo controllo', 'return OK, righe + [f"ATTENZIONE: l\'ultimo controllo'),
 (FL, "ultima_riuscita: min invece di max", 'return max(riuscite, key=', 'return min(riuscite, key='),
 (FL, "registra: sovrascrive la traccia", 'with percorso.open("a", encoding="utf-8") as f:', 'with percorso.open("w", encoding="utf-8") as f:'),
 (FL, "main: traccia non scritta ignorata", '        esito.codice |= ERRORE_CONTROLLO\n        esito.messaggi.append(f"traccia:', '        esito.messaggi.append(f"traccia:'),
 (FL, "main: --digest-attuale ammesso senza --prova", 'if a.digest_attuale is not None and not a.prova:', 'if False:'),
 (FL, "main: --stato ignorato", '    if a.stato:\n        codice, righe', '    if False:\n        codice, righe'),
 (FL, "main: registra con prova sempre False", 'registra(esito, quali, a.prova, traccia, ora)', 'registra(esito, quali, False, traccia, ora)'),
 (FL, "segnala: commento anche se invariato", 'if _normalizza(ultimo) == _normalizza(corpo):', 'if False:'),
 (FL, "segnala: mai commento (contenuto cambiato ignorato)", 'if _normalizza(ultimo) == _normalizza(corpo):', 'if True:'),
 (FL, "segnala: ultimo = sempre corpo della issue", 'ultimo = commenti[-1].get("body") if commenti else esistente.get("body")', 'ultimo = esistente.get("body")'),
 (FL, "segnala: ultimo = primo commento", 'commenti[-1].get("body")', 'commenti[0].get("body")'),
 (FL, "segnala: commento fallito ignorato", '            if k.returncode != 0:\n                codice |= ERRORE_ISSUE', '            if False:\n                codice |= ERRORE_ISSUE'),
 (FL, "segnala: commento senza -R", '"gh", "issue", "comment", str(esistente.get("number")), "-R", repo,', '"gh", "issue", "comment", str(esistente.get("number")),'),
 (FL, "segnala: create senza -R", '"gh", "issue", "create", "-R", repo,', '"gh", "issue", "create",'),
 (FL, "segnala: list senza -R", '"gh", "issue", "list", "-R", repo,', '"gh", "issue", "list",'),
 (FL, "segnala: pr list senza -R", '"gh", "pr", "list", "-R", repo,', '"gh", "pr", "list",'),
 (FL, "segnala: pr create senza -R", '"gh", "pr", "create", "-R", repo,', '"gh", "pr", "create",'),
 (FL, "segnala: corpo issue non ripulito", 'corpo = ripulisci("\\n\\n".join(testi))', 'corpo = "\\n\\n".join(testi)'),
 (FL, "_coda: non ripulisce", 'testo = ripulisci((testo or "").strip())', 'testo = (testo or "").strip()'),
 (FL, "PR: corpo non ripulito", 'corpo = ripulisci("Il lockfile rigenerato', 'corpo = ("Il lockfile rigenerato'),
 (FL, "ripulisci: niente token gh*_", '    (re.compile(r"\\bgh[pousr]_[A-Za-z0-9]{10,}"), "[token rimosso]"),\n', ''),
 (FL, "ripulisci: niente github_pat_", '    (re.compile(r"\\bgithub_pat_[A-Za-z0-9_]{10,}"), "[token rimosso]"),\n', ''),
 (FL, "ripulisci: niente url con credenziali", '    (re.compile(r"(https?://)[^/\\s@]+@"), r"\\1[credenziali rimosse]@"),\n', ''),
 (FL, "segnala: limite >= -> >", 'if len(elenco) >= LIMITE_ISSUE_LETTE:', 'if len(elenco) > LIMITE_ISSUE_LETTE:'),
 (FL, "segnala: repository non determinabile => OK", 'return ERRORE_ISSUE, [f"issue: repository non determinabile', 'return OK, [f"issue: repository non determinabile'),
 (FL, "segnala: JSON illeggibile => OK", 'return ERRORE_ISSUE, [f"issue: elenco non leggibile', 'return OK, [f"issue: elenco non leggibile'),
 (FL, "locali: commit non pubblicati ignorati", '        if _testo(locali.stdout).strip():', '        if False:'),
 (FL, "base = main locale", 'base = f"{REMOTO}/{BRANCH_PRINCIPALE}"', 'base = BRANCH_PRINCIPALE'),
 (FL, "FILE_BASE senza pyproject", 'FILE_BASE_LOCKFILE = ("pyproject.toml", LOCKFILE, LOCKFILE_STRUMENTI)', 'FILE_BASE_LOCKFILE = (LOCKFILE, LOCKFILE_STRUMENTI)'),
 (FL, "FILE_BASE senza lockfile", 'FILE_BASE_LOCKFILE = ("pyproject.toml", LOCKFILE, LOCKFILE_STRUMENTI)', 'FILE_BASE_LOCKFILE = ("pyproject.toml", LOCKFILE_STRUMENTI)'),
 (FL, "OSV solo sul lockfile", 'LOCKFILE_CONTROLLATI = (LOCKFILE, LOCKFILE_STRUMENTI)', 'LOCKFILE_CONTROLLATI = (LOCKFILE,)'),
 (FL, "OSV solo sugli strumenti", 'LOCKFILE_CONTROLLATI = (LOCKFILE, LOCKFILE_STRUMENTI)', 'LOCKFILE_CONTROLLATI = (LOCKFILE_STRUMENTI,)'),
 (FL, "pip install senza --require-hashes", '"--disable-pip-version-check", "--require-hashes", "-r"', '"--disable-pip-version-check", "-r"'),
 (FL, "pip install: file requisiti sbagliato", '"-r", str(requisiti)]', '"-r", str(radice / "requirements.lock.txt")]'),
 (FL, "manca requisiti strumenti => procede", '    if not requisiti.is_file():\n        raise ErroreAggiornamento', '    if False:\n        raise ErroreAggiornamento'),
 (FL, "manca interprete => procede", '    if not interprete.is_file():\n        raise', '    if False:\n        raise'),
 (FL, "differenze: versioni cambiate ignorate", '        elif a[nome] != b[nome]:', '        elif False:'),
 (FL, "differenze: nuovi pacchetti ignorati", '        elif nome not in a:', '        elif False:'),
 (FL, "differenze: rimossi ignorati", '        if nome not in b:', '        if False:'),
 (FL, "PR gia' aperta ignorata", '        if PREFISSO_BRANCH_LOCKFILE in _testo(aperte.stdout):', '        if False:'),
 (FL, "repo_github: regex rimosso", '    if not m:\n        raise ErroreRepository', '    if False:\n        raise ErroreRepository'),
 (FL, "repo_github: remote fallito ignorato", '    if r.returncode != 0:\n        raise ErroreRepository', '    if False:\n        raise ErroreRepository'),
 (FL, "_testo: bytes non decodificati", '        return valore.decode("utf-8", "replace")', '        return valore'),
 (FL, "esegui: timeout senza testo", '        e.stdout, e.stderr = _testo(e.stdout), _testo(e.stderr)\n', ''),
 (FL, "prova del lockfile apre PR", '        if prova:\n            return Esito(OK, messaggi=[f"lockfile: AGGIORNAMENTO', '        if False:\n            return Esito(OK, messaggi=[f"lockfile: AGGIORNAMENTO'),
 (FL, "segnala in prova apre issue", 'if not problemi or prova:', 'if not problemi:'),
 (FL, "assegnatario mancante", ', "--assignee", ASSEGNATARIO])', '])'),
 (FL, "digest: 2 immagini accettate", 'if len(righe) != 1:', 'if len(righe) < 1:'),
 (FL, "worktree residuo non rimosso", '        if sorgente.exists():  # residuo', '        if False:  # residuo'),
 (FL, "worktree creato non rimosso a fine", '        if creato:\n            run(["git", "-C", str(radice), "worktree", "remove"', '        if False:\n            run(["git", "-C", str(radice), "worktree", "remove"'),
 # agenti.py
 (AG, "unisci: HEAD del worktree non controllato", '    if testa.returncode != 0 or punta.returncode != 0 or testa.stdout.strip() != punta.stdout.strip():', '    if False:'),
 (AG, "unisci: HEAD, solo errori di git", '    if testa.returncode != 0 or punta.returncode != 0 or testa.stdout.strip() != punta.stdout.strip():', '    if testa.returncode != 0 or punta.returncode != 0:'),
 (AG, "unisci: errore di git su HEAD ignorato", 'if testa.returncode != 0 or punta.returncode != 0 or testa.stdout', 'if testa.stdout'),
 (AG, "unisci: main antenato non controllato", '    if git("merge-base", "--is-ancestor", BRANCH_BASE, branch, check=False).returncode != 0:', '    if False:'),
 (AG, "unisci: fornitura non fresca ignorata", '    if not fresca:\n', '    if False:\n'),
 (AG, "unisci: forzatura sempre attiva", 'if not getattr(a, "forza_fornitura", False):', 'if False:'),
 (AG, "unisci: forzatura non scritta nel messaggio", '        messaggio = f"{a.messaggio.rstrip()}\\n\\nForzato:', '        messaggio_x = f"{a.messaggio.rstrip()}\\n\\nForzato:'),
 (AG, "unisci: stato_fornitura sempre fresca", '    return codice == f.OK, " | ".join(righe)', '    return True, " | ".join(righe)'),
 (AG, "unisci: stato_fornitura legge un altro file", 'codice, righe = f.stato(f.FILE_ESITI)', 'codice, righe = f.stato(f.FILE_ESITI.with_name("altro.jsonl"))'),
 (AG, "unisci: non-superuser tolto", '        ("prove con ruolo non superuser", ["bash", SCRIPT_NON_SUPERUSER]),\n', ''),
 (AG, "unisci: OSV strumenti tolto", '        ("controllo OSV dei lockfile degli strumenti", [py, SCRIPT_OSV, LOCKFILE_STRUMENTI]),\n', ''),
 (AG, "unisci: OSV lockfile su file strumenti", '[py, SCRIPT_OSV, LOCKFILE]),', '[py, SCRIPT_OSV, LOCKFILE_STRUMENTI]),'),
 (AG, "unisci: esito dei controlli ignorato", 'if subprocess.run(cmd, cwd=dove, env=env).returncode != 0:', 'if subprocess.run(cmd, cwd=dove, env=env).returncode == 99:'),
 (AG, "unisci: env del worktree non passato", 'env = dict(os.environ, **leggi_env_worktree(nome))', 'env = dict(os.environ)\n    leggi_env_worktree(nome)'),
 (AG, "unisci: merge fallito non annullato", '        git("merge", "--abort", check=False)\n', ''),
 (AG, "unisci: modifiche non committate ignorate", '    if s["sporco"]:', '    if False:'),
 (AG, "unisci: gia' unito ignorato", '    if s["unito"]:', '    if False:'),
 (AG, "unisci: main sporco ignorato", '    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():', '    if False:'),
 (AG, "unisci: merge fast-forward", 'git("merge", "--no-ff", branch, "-m", messaggio, check=False)', 'git("merge", "--ff", branch, "-m", messaggio, check=False)'),
]

def prepara():
    if lavoro.exists(): shutil.rmtree(lavoro)
    lavoro.mkdir(parents=True)
    ign = shutil.ignore_patterns("__pycache__", ".pytest_basetemp")
    for d in ("scripts", "tests", ".github", "systemd"):
        shutil.copytree(wt / d, lavoro / d, ignore=ign)
    for f in wt.iterdir():
        if f.is_file() and f.suffix in (".txt", ".in", ".toml") or f.name == ".gitignore":
            shutil.copy(f, lavoro / f.name)

def corri():
    r = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--basetemp={lavoro}/bt", "-x", *TESTS],
                       cwd=lavoro, text=True, capture_output=True)
    out = r.stdout.strip().splitlines()
    return r.returncode, (out[-1] if out else r.stderr[-200:])

prepara()
print("base:", corri(), flush=True)
orig = {f: (wt / f).read_text(encoding="utf-8") for f in (FL, AG)}
sopravvissuti = 0
FILTRO = sys.argv[3:]
for f, nome, a, b in M:
    if FILTRO and not any(x in nome for x in FILTRO): continue
    if orig[f].count(a) != 1:
        print("PATTERN NON UNICO/ASSENTE:", nome, orig[f].count(a), flush=True); continue
    (lavoro / f).write_text(orig[f].replace(a, b), encoding="utf-8")
    rc, riga = corri()
    sopravvissuti += rc == 0
    print(("UCCISO       " if rc != 0 else "SOPRAVVISSUTO"), "|", nome, "|", riga, flush=True)
    (lavoro / f).write_text(orig[f], encoding="utf-8")
print("sopravvissuti:", sopravvissuti, "su", len(M))
shutil.rmtree(lavoro)
