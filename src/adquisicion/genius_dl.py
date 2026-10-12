"""Fase 2 — Descarga de letras desde Genius.

Para cada ficha con genius_id en config/artistas.yaml enumera sus canciones
vía la API oficial (artists/{id}/songs) y baja la letra de las que están
completas. Reanudable: saltea lo que ya está en el .jsonl de salida.

Requiere GENIUS_ACCESS_TOKEN en .env (token gratuito: genius.com/api-clients).

Uso:
  .venv/bin/python src/adquisicion/genius_dl.py            # todas las fichas
  .venv/bin/python src/adquisicion/genius_dl.py jaime_roos # una sola
"""

import json
import sys
import time
import unicodedata
from pathlib import Path

import lyricsgenius
import yaml

ROOT = Path(__file__).resolve().parents[2]
DESTINO = ROOT / "data/raw/lyrics"
PAUSA = 1.0  # cortesía entre canciones, además del sleep interno de lyricsgenius


def leer_env(clave):
    env = ROOT / ".env"
    if env.exists():
        for linea in env.read_text().splitlines():
            if linea.startswith(f"{clave}="):
                return linea.split("=", 1)[1].strip()
    return None


def normalizar(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def fichas_con_genius(cfg):
    out = {}
    for grupo in ("sujeto", "set_principal", "subanalisis_repertorio"):
        for slug, a in cfg.get(grupo, {}).items():
            if a.get("genius_id"):
                out[slug] = a
    for slug, b in cfg["sujeto"]["ruben_rada"].get("fichas_adicionales", {}).items():
        if b.get("genius_id"):
            out[slug] = {"nombre": slug, **b}
    return out


def bajar_ficha(genius, slug, artista):
    destino = DESTINO / f"{slug}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    ya = set()
    if destino.exists():
        with open(destino) as fh:
            ya = {json.loads(l)["genius_id"] for l in fh if l.strip()}

    pagina, canciones = 1, []
    while pagina:
        resp = genius.artist_songs(artista["genius_id"], per_page=50, page=pagina, sort="title")
        canciones += resp.get("songs", [])
        pagina = resp.get("next_page")
    print(f"{slug}: {len(canciones)} canciones listadas, {len(ya)} ya bajadas", flush=True)

    nuevas, sin_letra = 0, 0
    with open(destino, "a") as fh:
        for c in canciones:
            if c["id"] in ya:
                continue
            if c.get("lyrics_state") != "complete":
                sin_letra += 1
                continue
            # se baja todo lo asociado al artista; si es o no su autoría lo decide
            # el crédito de letrista en Fase 3, no la ficha de Genius
            prim = c.get("primary_artist", {})
            try:
                letra = genius.lyrics(song_url=c["url"], remove_section_headers=False)
            except Exception as e:
                print(f"  error en '{c.get('title')}': {e}", flush=True)
                continue
            if not letra or not letra.strip():
                sin_letra += 1
                continue
            fh.write(json.dumps({
                "genius_id": c["id"],
                "ficha": slug,
                "titulo": c.get("title", ""),
                "titulo_norm": normalizar(c.get("title", "")),
                "titulo_completo": c.get("full_title", ""),
                "url": c["url"],
                "fecha_genius": (c.get("release_date_components") or {}).get("year"),
                "es_artista_principal": prim.get("id") == artista["genius_id"],
                "artista_principal_genius": prim.get("name", ""),
                "letra": letra,
            }, ensure_ascii=False) + "\n")
            fh.flush()
            nuevas += 1
            time.sleep(PAUSA)
    print(f"{slug}: {nuevas} letras nuevas, {sin_letra} sin letra completa", flush=True)


def main():
    token = leer_env("GENIUS_ACCESS_TOKEN")
    if not token:
        sys.exit("Falta GENIUS_ACCESS_TOKEN en .env (cp .env.example .env y pegá el token)")
    cfg = yaml.safe_load((ROOT / "config/artistas.yaml").read_text())
    fichas = fichas_con_genius(cfg)
    pedidas = sys.argv[1:]
    if pedidas:
        fichas = {s: a for s, a in fichas.items() if s in pedidas}
        if not fichas:
            sys.exit(f"Ninguna ficha coincide con {pedidas}")

    genius = lyricsgenius.Genius(token, timeout=15, retries=3, sleep_time=0.5, skip_non_songs=True)
    for slug, artista in fichas.items():
        bajar_ficha(genius, slug, artista)


if __name__ == "__main__":
    main()
