"""Verifica del lockfile: hash completi rispetto a PyPI, ultima versione, OSV, wheel per cp315.
Uso: python -I verifica-lockfile.py <requirements.lock.txt>"""
import json, re, sys, urllib.request

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

txt = open(sys.argv[1]).read()
blocks = re.findall(r"^([A-Za-z0-9_.\-]+)==([^\s\\]+) \\\n((?:\s+--hash=sha256:[0-9a-f]+(?: \\)?\n)+)", txt, re.M)
pins = {}
for n, v, h in blocks:
    pins[n] = (v, set(re.findall(r"sha256:([0-9a-f]+)", h)))
print("pacchetti:", len(pins), "hash totali:", sum(len(p[1]) for p in pins.values()))
queries = []
for n, (v, hs) in pins.items():
    j = get(f"https://pypi.org/pypi/{n}/json")
    latest = j["info"]["version"]
    files = get(f"https://pypi.org/pypi/{n}/{v}/json")["urls"]
    remote = {f["digests"]["sha256"] for f in files}
    missing = remote - hs
    extra = hs - remote
    cp315 = [f["filename"] for f in files if "cp315" in f["filename"] or "py3-none-any" in f["filename"] or "abi3" in f["filename"]]
    yanked = [f["filename"] for f in files if f.get("yanked")]
    print(f"{n}=={v} latest={latest}{'' if latest==v else ' <-- DIVERSA'} hash_lock={len(hs)} hash_pypi={len(remote)} mancanti={len(missing)} extra={len(extra)} yanked={len(yanked)} wheel_3.15_compat={len(cp315)}")
    queries.append({"package": {"name": n, "ecosystem": "PyPI"}, "version": v})
res = get("https://api.osv.dev/v1/querybatch", json.dumps({"queries": queries}).encode())
for q, r in zip(queries, res["results"]):
    print("OSV", q["package"]["name"], q["version"], [x["id"] for x in r.get("vulns", [])] or "nessuna")
