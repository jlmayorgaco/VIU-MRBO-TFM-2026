"""Verifica que la campana SP1 que adjudica H1b y H1c sigue siendo reproducible:
los hashes de config y generador del manifiesto deben coincidir con el arbol.

Uso: python final-hardening/verify_sp1_provenance.py
"""
import hashlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN = os.path.join(ROOT, "pre-thesis", "evidence", "generated-figures-manifest.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    m = json.load(io.open(MAN, encoding="utf8"))
    print("manifiesto generado:", m.get("generated_at_utc"))
    print("git_commit declarado:", m.get("git_commit"))
    print("nota:", str(m.get("working_tree_note"))[:120])
    print()

    ok = bad = missing = 0
    for camp in m.get("campaigns", []):
        name = camp.get("experiment_id") or camp.get("id") or "(sin id)"
        print("=== %s ===" % name)
        for key, label in (("config", "config"), ("generator", "generador")):
            p = camp.get(key)
            hkey = {"config": "config_sha256", "generator": "generator_sha256"}[key]
            declared = camp.get(hkey)
            if not p or not declared:
                continue
            full = os.path.join(ROOT, p)
            if not os.path.exists(full):
                print("  %-10s AUSENTE  %s" % (label, p))
                missing += 1
                continue
            actual = sha256(full)
            state = "COINCIDE" if actual == declared else "DIFIERE"
            if actual == declared:
                ok += 1
            else:
                bad += 1
            print("  %-10s %-9s %s" % (label, state, p))
            if actual != declared:
                print("             declarado %s" % declared[:32])
                print("             actual    %s" % actual[:32])
    print()
    print("coinciden: %d | difieren: %d | ausentes: %d" % (ok, bad, missing))
    return 1 if (bad or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
