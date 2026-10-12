"""Cruce de cobertura: canciones únicas del catálogo vs letras bajadas.

Primer corte por título normalizado exacto (el matching fino con fuzzy y
alias de títulos es de la Fase 3). Reporta por ficha el % de canciones del
canon con letra encontrada, contra el umbral pre-registrado del 60%.

Uso: .venv/bin/python src/limpieza/cobertura.py
"""

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
UMBRAL = 0.60


def norm_fuerte(s):
    """Normalización agresiva para matching: minúsculas, sin acentos, sin
    bloques entre paréntesis/corchetes, sin puntuación, espacios colapsados."""
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)          # (en vivo), [feat. X]
    s = re.sub(r"[^a-z0-9ñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    cat = pd.read_csv(ROOT / "data/catalogo/catalogo.csv")
    cat["cancion_norm"] = cat.cancion.map(norm_fuerte)
    # canción única = primer registro por (ficha, titulo normalizado); el año
    # queda el menor (proxy de primera grabación hasta la curaduría de Fase 3)
    cat = (cat.sort_values("anio_album")
              .drop_duplicates(["ficha", "cancion_norm"], keep="first"))

    letras = []
    for f in (ROOT / "data/raw").glob("lyrics*/*.jsonl"):
        with open(f) as fh:
            for linea in fh:
                d = json.loads(linea)
                letras.append({"ficha": d["ficha"], "titulo_norm": norm_fuerte(d["titulo"])})
    let = pd.DataFrame(letras).drop_duplicates()

    print(f"{'ficha':22} {'canon':>6} {'letras':>7} {'match':>6} {'cobertura':>10}  gate")
    for ficha, g in cat.groupby("ficha"):
        titulos_let = set(let[let.ficha == ficha].titulo_norm)
        n_match = g.cancion_norm.isin(titulos_let).sum()
        cob = n_match / len(g) if len(g) else 0
        gate = "OK" if cob >= UMBRAL else "BAJO"
        print(f"{ficha:22} {len(g):6d} {len(titulos_let):7d} {n_match:6d} {cob:9.0%}  {gate}")

    # letras que no matchearon con el canon (útiles: pueden ser el mismo tema con otro título)
    huerfanas = 0
    for ficha, g in let.groupby("ficha"):
        canon = set(cat[cat.ficha == ficha].cancion_norm)
        huerfanas += (~g.titulo_norm.isin(canon)).sum()
    print(f"\nletras sin match en el canon (revisar en Fase 3): {huerfanas}")


if __name__ == "__main__":
    main()
