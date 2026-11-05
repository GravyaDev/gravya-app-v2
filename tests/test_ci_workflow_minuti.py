"""Workflow di GitHub a basso consumo di minuti (DECISIONS §6 «Minuti di GitHub Actions»).

Niente PyYAML (non e' nel lockfile): si legge il testo dei workflow, che ha
una struttura semplice. Il filtro dei percorsi di GitHub e' riprodotto da
`corrisponde`: `*` non attraversa `/`, `**` si'. Un push NON avvia il workflow
se `paths-ignore` copre TUTTI i file modificati, oppure se `paths` non ne
copre nessuno (documentazione: «Workflow syntax for GitHub Actions»,
`on.<push>.<paths>`).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
CI = RADICE / ".github" / "workflows" / "ci.yml"
FORNITURA = RADICE / ".github" / "workflows" / "fornitura.yml"


def _senza_commenti(testo: str) -> str:
    return "\n".join(re.sub(r"(^|\s)#.*$", "", r).rstrip() for r in testo.splitlines())


def blocco_on(percorso: Path) -> dict[str, dict[str, list[str]]]:
    """{evento: {filtro: [pattern]}} dal blocco top-level `on:`."""
    righe = _senza_commenti(percorso.read_text(encoding="utf-8")).splitlines()
    inizio = righe.index("on:")
    risultato: dict[str, dict[str, list[str]]] = {}
    evento = filtro = None
    for r in righe[inizio + 1:]:
        if r.strip() and not r.startswith(" "):
            break
        if not r.strip():
            continue
        m = re.fullmatch(r"  ([a-z_]+):\s*(.*)", r)
        if m:
            evento, filtro = m.group(1), None
            risultato[evento] = {}
            continue
        m = re.fullmatch(r"    ([a-z_-]+):\s*(.*)", r)
        if m and evento:
            filtro = m.group(1)
            risultato[evento][filtro] = []
            continue
        m = re.fullmatch(r'      - "?([^"]+)"?', r)
        if m and evento and filtro:
            risultato[evento][filtro].append(m.group(1))
    return risultato


def corrisponde(pattern: str, percorso: str) -> bool:
    regex, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            regex += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            regex += ".*"
            i += 2
        elif pattern[i] == "*":
            regex += "[^/]*"
            i += 1
        else:
            regex += re.escape(pattern[i])
            i += 1
    return re.fullmatch(regex, percorso) is not None


def avvia_ref(filtri: dict[str, list[str]], ref: str) -> bool:
    """Filtro dei ref di `push`: con `branches` e senza `tags`, un tag non avvia il workflow
    (documentazione: «Workflow syntax for GitHub Actions», `on.<push>.<branches|tags>`: se si definisce
    solo un tipo di filtro, il workflow non parte per l'altro tipo di ref)."""
    if ref.startswith("refs/tags/"):
        return "tags" in filtri and any(corrisponde(p, ref.removeprefix("refs/tags/")) for p in filtri["tags"])
    if ref.startswith("refs/heads/"):
        return "branches" not in filtri or any(corrisponde(p, ref.removeprefix("refs/heads/")) for p in filtri["branches"])
    return False


def avvia(filtri: dict[str, list[str]], modificati: list[str]) -> bool:
    if "paths-ignore" in filtri:
        return any(not any(corrisponde(p, f) for p in filtri["paths-ignore"]) for f in modificati)
    if "paths" in filtri:
        return any(any(corrisponde(p, f) for p in filtri["paths"]) for f in modificati)
    return True


SOLO_DOCUMENTI = [
    ["docs/DECISIONS.md"],
    ["docs/revisioni/ci-locale/report-implementer.md", "docs/revisioni/ci-locale/risposta.json"],
    ["stato/handoff-sessione.md"],
    ["README.md", "docs/index.md"],
    ["src/LEGGIMI.md"],
    [".claude/agents/implementer.md"],
    ["docs/a.md", "stato/b.md", ".claude/c.md", "README.md"],
]
CON_CODICE = [
    ["src/gravya_e1/x.py"],
    ["docs/a.md", "tests/test_x.py"],
    ["requirements.lock.txt"],
    [".github/workflows/ci.yml"],
    ["scripts/osv-check.py", "stato/x.md"],
    ["pyproject.toml"],
]


@pytest.mark.parametrize("workflow", [CI, FORNITURA], ids=["ci", "fornitura"])
def test_solo_push_e_manuale(workflow):
    eventi = blocco_on(workflow)
    assert set(eventi) == {"push", "workflow_dispatch"}  # niente pull_request, niente schedule
    testo = workflow.read_text(encoding="utf-8")
    assert "schedule" not in _senza_commenti(testo) and "pull_request" not in _senza_commenti(testo)


@pytest.mark.parametrize("workflow", [CI, FORNITURA], ids=["ci", "fornitura"])
def test_concurrency_annulla_lo_stesso_branch(workflow):
    testo = _senza_commenti(workflow.read_text(encoding="utf-8"))
    m = re.search(r"^concurrency:\n  group: (.+)\n  cancel-in-progress: true$", testo, re.M)
    assert m, "concurrency con cancel-in-progress: true assente"
    assert "github.ref" in m.group(1) and "github.workflow" in m.group(1)


@pytest.mark.parametrize("file", [f for gruppo in SOLO_DOCUMENTI for f in [gruppo]], ids=lambda g: "+".join(g)[:40])
@pytest.mark.parametrize("workflow", [CI, FORNITURA], ids=["ci", "fornitura"])
def test_commit_di_soli_documenti_non_avvia_nulla(workflow, file):
    assert avvia(blocco_on(workflow)["push"], file) is False


@pytest.mark.parametrize("file", CON_CODICE, ids=lambda g: "+".join(g)[:40])
def test_ci_parte_se_cambia_altro(file):
    assert avvia(blocco_on(CI)["push"], file) is True


@pytest.mark.parametrize(
    "file,atteso",
    [
        (["requirements.lock.txt"], True),
        (["scripts/osv-check.py"], True),
        (["docs/a.md", ".github/workflows/fornitura.yml"], True),
        (["src/gravya_e1/x.py"], False),
        (["tests/test_ci_osv_check.py"], False),
        ([".github/workflows/ci.yml"], False),
        (["scripts/agenti.py"], False),
    ],
)
def test_osv_su_github_solo_se_cambiano_lockfile_script_o_workflow(file, atteso):
    assert avvia(blocco_on(FORNITURA)["push"], file) is atteso


def test_fornitura_ha_solo_il_job_osv():
    testo = _senza_commenti(FORNITURA.read_text(encoding="utf-8"))
    assert re.findall(r"^  ([a-z0-9-]+):$", testo.split("\njobs:\n", 1)[1], re.M) == ["osv"]


def test_il_filtro_riprodotto_distingue_asterischi():
    assert corrisponde("**/*.md", "README.md") and corrisponde("**/*.md", "a/b/c.md")
    assert corrisponde("docs/**", "docs/a/b.txt")
    assert not corrisponde("*.md", "docs/a.md")  # `*` non attraversa `/`


@pytest.mark.parametrize("workflow", [CI, FORNITURA], ids=["ci", "fornitura"])
def test_un_push_di_tag_non_avvia_nulla_un_push_di_branch_si(workflow):
    push = blocco_on(workflow)["push"]
    assert push.get("branches") == ["**"] and "tags" not in push and "tags-ignore" not in push
    assert avvia_ref(push, "refs/tags/v1.0.0") is False
    assert avvia_ref(push, "refs/tags/rilascio/2026") is False
    for ref in ("refs/heads/main", "refs/heads/impl/ci-locale", "refs/heads/impl/lockfile-2026-11-09"):
        assert avvia_ref(push, ref) is True


def test_il_modello_dei_ref_distingue_i_filtri():
    assert avvia_ref({"tags": ["v*"]}, "refs/tags/v1") is True
    assert avvia_ref({"branches": ["main"]}, "refs/heads/altro") is False
