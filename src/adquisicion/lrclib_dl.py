"""Fase 2 (fallback 2) — Letras faltantes vía LRCLIB, canción por canción.

Para cada canción del canon sin letra en las fuentes ya bajadas, consulta
https://lrclib.net/api/search y acepta solo matches estrictos: título
normalizado idéntico Y nombre de artista que contenga el token esperado.

Reanudable. Salida: data/raw/lyrics_lrclib/{ficha}.jsonl

Uso: .venv/bin/python -u src/adquisicion/lrclib_dl.py
"""

import json
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
DESTINO = ROOT / "data/raw/lyrics_lrclib"
UA = {"User-Agent": "RadaSentiment/0.1 (investigacion de letras)"}
PAUSA = 0.6

ARTISTAS = {
    "ruben_rada": ("Ruben Rada", "rada"),
    "jaime_roos": ("Jaime Roos", "roos"),
    "alfredo_zitarrosa": ("Alfredo Zitarrosa", "zitarrosa"),
    "fernando_cabrera": ("Fernando Cabrera", "cabrera"),
    "eduardo_mateo": ("Eduardo Mateo", "mateo"),
    "jorge_drexler": ("Jorge Drexler", "drexler"),
    "el_kinto": ("El Kinto", "kinto"),
    "totem": ("Totem", "totem"),
}


def norm_fuerte(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)
    s = re.sub(r"[^a-z0-9ñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def faltantes():
    cat = pd.read_csv(ROOT / "data/catalogo/catalogo.csv")
    cat["n"] = cat.cancion.map(norm_fuerte)
    cat = cat.sort_values("anio_album").drop_duplicates(["ficha", "n"], keep="first")
    tengo = set()
    for f in (ROOT / "data/raw").glob("lyrics*/*.jsonl"):
        with open(f) as fh:
            for linea in fh:
                d = json.loads(linea)
                tengo.add((d["ficha"], norm_fuerte(d["titulo"])))
    out = {}
    for _, fila in cat.iterrows():
        if fila.ficha in ARTISTAS and (fila.ficha, fila.n) not in tengo and fila.n:
            out.setdefault(fila.ficha, []).append((fila.cancion, fila.n))
    return out


def buscar(nombre_artista, token, titulo, titulo_n):
    r = requests.get("https://lrclib.net/api/search",
                     params={"artist_name": nombre_artista, "track_name": titulo},
                     headers=UA, timeout=20)
    if r.status_code != 200:
        return None
    for c in r.json():
        if not c.get("plainLyrics"):
            continue
        if norm_fuerte(c.get("trackName", "")) != titulo_n:
            continue
        if token not in norm_fuerte(c.get("artistName", "")):
            continue
        return c
    return None


def main():
    pend = faltantes()
    for ficha, canciones in pend.items():
        nombre, token = ARTISTAS[ficha]
        destino = DESTINO / f"{ficha}.jsonl"
        destino.parent.mkdir(parents=True, exist_ok=True)
        ya = set()
        if destino.exists():
            with open(destino) as fh:
                ya = {json.loads(l)["titulo_norm"] for l in fh if l.strip()}
        print(f"{ficha}: {len(canciones)} faltantes, {len(ya)} ya consultadas", flush=True)
        nuevas = 0
        with open(destino, "a") as fh:
            for titulo, titulo_n in canciones:
                if titulo_n in ya:
                    continue
                time.sleep(PAUSA)
                try:
                    c = buscar(nombre, token, titulo, titulo_n)
                except requests.exceptions.RequestException:
                    time.sleep(10)
                    continue
                if not c:
                    continue
                fh.write(json.dumps({
                    "ficha": ficha,
                    "titulo": titulo,
                    "titulo_norm": normalizar_simple(titulo),
                    "lrclib_artista": c.get("artistName", ""),
                    "lrclib_track": c.get("trackName", ""),
                    "letra": c["plainLyrics"],
                }, ensure_ascii=False) + "\n")
                fh.flush()
                nuevas += 1
        print(f"{ficha}: {nuevas} letras nuevas via LRCLIB", flush=True)


def normalizar_simple(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


if __name__ == "__main__":
    main()
