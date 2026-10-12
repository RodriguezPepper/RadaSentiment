"""Fase 2 (fallback) — Descarga de letras desde letras.com.

Complementa a Genius en las fichas con cobertura baja. Además de la letra
(con estrofas ya separadas en <p>) captura el bloque "Composición" cuando
existe — insumo directo para los créditos de autoría de la Fase 3.

Reanudable por URL. Salida: data/raw/lyrics_letrascom/{ficha}.jsonl

Uso:
  .venv/bin/python -u src/adquisicion/letras_com_dl.py             # todas
  .venv/bin/python -u src/adquisicion/letras_com_dl.py ruben_rada  # una
"""

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DESTINO = ROOT / "data/raw/lyrics_letrascom"
BASE = "https://www.letras.com"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
PAUSA = 1.5

SLUGS = {
    "ruben_rada": "ruben-rada",
    "alfredo_zitarrosa": "alfredo-zitarrosa",
    "jaime_roos": "jaime-roos",
    "el_kinto": "el-kinto",
    "eduardo_mateo": "eduardo-mateo",
    "fernando_cabrera": "fernando-cabrera",
}


def normalizar(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def traer(url):
    for intento in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=30)
        except requests.exceptions.ConnectionError:
            time.sleep(10)
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(2 ** intento + 5, 60))
            continue
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.text
    raise RuntimeError(f"letras.com no responde: {url}")


def canciones_de(slug):
    html = traer(f"{BASE}/{slug}/")
    if not html:
        return []
    hrefs = set(re.findall(rf'href="(/{re.escape(slug)}/[^"/]+/)"', html))
    return sorted(h for h in hrefs if not h.endswith(".html/"))


def parsear_cancion(html):
    sopa = BeautifulSoup(html, "html.parser")
    cont = sopa.select_one("div.lyric-original")
    if not cont:
        return None
    estrofas = []
    for p in cont.find_all("p"):
        for br in p.find_all("br"):
            br.replace_with("\n")
        texto = p.get_text().strip()
        if texto:
            estrofas.append(texto)
    if not estrofas:
        return None
    h1 = sopa.find("h1")
    comp = sopa.select_one(".lyric-info-composition")
    return {
        "titulo": h1.get_text().strip() if h1 else "",
        "letra": "\n\n".join(estrofas),
        "composicion": re.sub(r"\s+", " ", comp.get_text()).strip() if comp else "",
    }


def bajar_ficha(ficha, slug):
    destino = DESTINO / f"{ficha}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    ya = set()
    if destino.exists():
        with open(destino) as fh:
            ya = {json.loads(l)["url"] for l in fh if l.strip()}

    urls = canciones_de(slug)
    print(f"{ficha}: {len(urls)} canciones listadas, {len(ya)} ya bajadas", flush=True)
    nuevas = vacias = 0
    with open(destino, "a") as fh:
        for path in urls:
            url = BASE + path
            if url in ya:
                continue
            time.sleep(PAUSA)
            html = traer(url)
            d = parsear_cancion(html) if html else None
            if not d:
                vacias += 1
                continue
            fh.write(json.dumps({
                "ficha": ficha,
                "titulo": d["titulo"],
                "titulo_norm": normalizar(d["titulo"]),
                "url": url,
                "composicion": d["composicion"],
                "letra": d["letra"],
            }, ensure_ascii=False) + "\n")
            fh.flush()
            nuevas += 1
    print(f"{ficha}: {nuevas} letras nuevas, {vacias} sin letra", flush=True)


def main():
    pedidas = sys.argv[1:] or list(SLUGS)
    for ficha in pedidas:
        if ficha not in SLUGS:
            sys.exit(f"ficha desconocida: {ficha} (validas: {list(SLUGS)})")
        bajar_ficha(ficha, SLUGS[ficha])


if __name__ == "__main__":
    main()
