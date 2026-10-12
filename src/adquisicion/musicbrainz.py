"""Fase 1 — Canon discográfico desde MusicBrainz.

Para cada ficha (solistas del estudio + El Kinto/Tótem/Opa) baja los
release-groups tipo álbum (sin compilados/en vivo), toma el año de primera
edición y el tracklist de la edición oficial más temprana, y arma la tabla
canónica base.

Escritura incremental y reanudable: cada álbum se agrega a catalogo.csv apenas
baja; al relanzar, saltea los release-groups ya presentes. Ante 503/429 espera
con backoff (respeta Retry-After) y una ficha que falla no corta las demás.

Salidas:
  data/catalogo/catalogo.csv        una fila por pista
  data/catalogo/fase1_reporte.txt   decisiones auditables (append por corrida)

Uso:
  .venv/bin/python -u src/adquisicion/musicbrainz.py
"""

import csv
import sys
import time
import unicodedata
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[2]
MB = "https://musicbrainz.org/ws/2"
UA = {"User-Agent": "RadaSentiment/0.1 (proyecto de investigacion de letras; ver README del repo)"}
PAUSA = 1.5
CAMPOS = ["ficha", "album", "anio_album", "pos", "cancion", "cancion_norm",
          "rg_mbid", "release_mbid", "letrista", "es_instrumental", "fuente_creditos"]

_ultimo = [0.0]


def mb_get(path, **params):
    espera = PAUSA - (time.monotonic() - _ultimo[0])
    if espera > 0:
        time.sleep(espera)
    for intento in range(8):
        try:
            r = requests.get(f"{MB}/{path}", params={**params, "fmt": "json"}, headers=UA, timeout=30)
        except requests.exceptions.ConnectionError:
            _ultimo[0] = time.monotonic()
            espera = min(2 ** intento + 10, 90)
            print(f"  [conexion reseteada] espero {espera:.0f}s ({path})", flush=True)
            time.sleep(espera)
            continue
        _ultimo[0] = time.monotonic()
        if r.status_code in (429, 500, 502, 503, 504):
            # MB llega a mandar Retry-After: 0 — nunca esperar menos que el backoff propio
            ra = float(r.headers.get("Retry-After") or 0)
            espera = max(ra, min(2 ** intento + 3, 60))
            print(f"  [throttle {r.status_code}] espero {espera:.0f}s ({path})", flush=True)
            time.sleep(espera)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"MusicBrainz siguió devolviendo {r.status_code} en {path}")


def buscar_artista(nombre):
    data = mb_get("artist", query=f'artist:"{nombre}"', limit=5)
    return [{
        "id": a["id"],
        "nombre": a.get("name", ""),
        "score": int(a.get("score", 0)),
        "pais": a.get("country", ""),
        "area": (a.get("begin-area") or {}).get("name", ""),
        "des": a.get("disambiguation", ""),
    } for a in data.get("artists", [])]


def es_uruguayo(c):
    campos = f'{c["pais"]} {c["area"]} {c["des"]}'.lower()
    return c["pais"] == "UY" or "uruguay" in campos or "montevideo" in campos


def elegir_mbid(nombre, reporte):
    cands = buscar_artista(nombre)
    for c in cands:
        if c["score"] >= 90 and es_uruguayo(c):
            reporte.append(f"[mbid] {nombre} -> {c['id']} (score {c['score']}, {c['pais']}/{c['area']}, '{c['des']}')")
            return c["id"]
    reporte.append(f"[mbid] {nombre} -> SIN CANDIDATO CLARO; revisar a mano:")
    for c in cands:
        reporte.append(f"        {c['id']} score={c['score']} {c['pais']}/{c['area']} '{c['des']}' ({c['nombre']})")
    return None


def release_groups(mbid, reporte, ficha):
    rgs, offset = [], 0
    while True:
        data = mb_get("release-group", artist=mbid, type="album", limit=100, offset=offset)
        lote = data.get("release-groups", [])
        for rg in lote:
            sec = rg.get("secondary-types") or []
            if rg.get("primary-type") != "Album" or sec:
                reporte.append(f"[excluido] {ficha}: '{rg.get('title')}' ({rg.get('first-release-date','?')}) {rg.get('primary-type')}/{'+'.join(sec) or '-'}")
                continue
            rgs.append({"id": rg["id"], "titulo": rg["title"], "fecha": rg.get("first-release-date", "")})
        offset += len(lote)
        if offset >= data.get("release-group-count", 0) or not lote:
            break
    return sorted(rgs, key=lambda r: r["fecha"] or "9999")


def tracklist(rg_id):
    data = mb_get("release", **{"release-group": rg_id, "inc": "recordings+media", "status": "official", "limit": 100})
    releases = [r for r in data.get("releases", []) if r.get("media")]
    if not releases:
        return None, []
    releases.sort(key=lambda r: r.get("date") or "9999")
    rel = releases[0]
    pistas, n = [], 0
    for medio in rel["media"]:
        for t in medio.get("tracks", []):
            n += 1
            pistas.append((n, t.get("title", "").strip()))
    return rel["id"], pistas


def normalizar(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def main():
    cfg = yaml.safe_load((ROOT / "config/artistas.yaml").read_text())
    reporte = []

    fichas = {}
    for grupo in ("sujeto", "set_principal"):
        for slug, a in cfg[grupo].items():
            fichas[slug] = {"nombre": a["nombre"], "mbid": a.get("mbid")}
    for slug, b in cfg["sujeto"]["ruben_rada"]["fichas_adicionales"].items():
        nombre = {"el_kinto": "El Kinto", "totem": "Tótem", "opa": "Opa"}[slug]
        fichas[slug] = {"nombre": nombre, "mbid": b.get("mbid")}

    destino = ROOT / "data/catalogo"
    destino.mkdir(parents=True, exist_ok=True)
    csv_path = destino / "catalogo.csv"

    hechos = set()  # rg_mbids ya bajados (reanudación)
    if csv_path.exists():
        with open(csv_path) as fh:
            hechos = {fila["rg_mbid"] for fila in csv.DictReader(fh)}
        print(f"reanudando: {len(hechos)} álbumes ya en catalogo.csv", flush=True)

    fh = open(csv_path, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=CAMPOS)
    if not hechos and fh.tell() == 0:
        w.writeheader()

    fallas = 0
    for slug, f in fichas.items():
        try:
            mbid = f["mbid"] or elegir_mbid(f["nombre"], reporte)
            if not mbid:
                print(f"!! {f['nombre']}: sin mbid claro, salteado (ver reporte)", flush=True)
                continue
            f["mbid"] = mbid
            rgs = release_groups(mbid, reporte, slug)
            pendientes = [rg for rg in rgs if rg["id"] not in hechos]
            print(f"{f['nombre']}: {len(rgs)} álbumes de estudio ({len(pendientes)} pendientes)", flush=True)
            for rg in pendientes:
                try:
                    rel_id, pistas = tracklist(rg["id"])
                except Exception as e:
                    print(f"  !! álbum '{rg['titulo']}': {e} — sigo con el próximo", flush=True)
                    reporte.append(f"[FALLA ALBUM] {slug}: '{rg['titulo']}' rg={rg['id']}: {e}")
                    fallas += 1
                    continue
                if not pistas:
                    reporte.append(f"[sin tracklist] {slug}: '{rg['titulo']}' ({rg['fecha']}) rg={rg['id']}")
                    continue
                anio = (rg["fecha"] or "")[:4]
                for pos, titulo in pistas:
                    w.writerow({
                        "ficha": slug, "album": rg["titulo"], "anio_album": anio,
                        "pos": pos, "cancion": titulo, "cancion_norm": normalizar(titulo),
                        "rg_mbid": rg["id"], "release_mbid": rel_id,
                        "letrista": "", "es_instrumental": "", "fuente_creditos": "",
                    })
                fh.flush()
                print(f"  + {rg['titulo']} ({anio}): {len(pistas)} pistas", flush=True)
        except Exception as e:
            fallas += 1
            print(f"!! {f['nombre']}: {e} — sigo con la próxima ficha", flush=True)
            reporte.append(f"[FALLA] {slug}: {e}")

    fh.close()
    reporte.append("mbids: " + ", ".join(f"{s}={f['mbid']}" for s, f in fichas.items()))
    with open(destino / "fase1_reporte.txt", "a") as rf:
        rf.write("\n".join(reporte) + "\n")

    with open(csv_path) as fh2:
        filas = list(csv.DictReader(fh2))
    por_ficha = {}
    for fila in filas:
        por_ficha[fila["ficha"]] = por_ficha.get(fila["ficha"], 0) + 1
    print(f"\ncatalogo.csv: {len(filas)} pistas | fichas con falla: {fallas}", flush=True)
    for s, n in sorted(por_ficha.items()):
        print(f"  {s}: {n}", flush=True)
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
