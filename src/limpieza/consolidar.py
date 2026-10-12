"""Fase 3 (parte mecánica) — Consolidación del corpus.

1. Junta las letras de las 3 fuentes y deduplica por canción
   (prioridad: letras.com > Genius > LRCLIB — letras.com trae estrofas
   limpias y el campo Composición).
2. Matchea contra el canon: exacto por título normalizado, después fuzzy
   (difflib >= 0.85) para los huérfanos.
3. Detecta idioma por heurística de stopwords (es/en/otro).
4. Segmenta en estrofas (separador: línea en blanco; saca headers [Coro] etc.).

Salidas:
  data/processed/corpus.parquet     una fila por canción con letra
  data/processed/estrofas.parquet   una fila por estrofa
  data/processed/canon_sin_letra.csv  canciones del canon aún sin letra (para
                                      el análisis de sesgo de faltantes)

Uso: .venv/bin/python src/limpieza/consolidar.py
"""

import difflib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FUENTES = ["lyrics_letrascom", "lyrics", "lyrics_lrclib"]  # orden de prioridad

STOP_ES = {"el", "la", "los", "las", "de", "del", "que", "y", "en", "un", "una",
           "por", "con", "para", "mi", "tu", "su", "me", "te", "se", "no", "es",
           "al", "lo", "como", "más", "mas", "pero", "sus", "le", "ya", "o"}
STOP_EN = {"the", "of", "and", "to", "in", "a", "is", "it", "you", "that", "he",
           "was", "for", "on", "are", "with", "as", "his", "they", "at", "be",
           "this", "have", "from", "or", "one", "had", "by", "but", "not", "what"}


def norm_fuerte(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)
    s = re.sub(r"[^a-z0-9ñ ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def detectar_idioma(texto):
    palabras = re.findall(r"[a-záéíóúüñ']+", texto.lower())
    if len(palabras) < 10:
        return "otro"
    es = sum(1 for p in palabras if p in STOP_ES) / len(palabras)
    en = sum(1 for p in palabras if p in STOP_EN) / len(palabras)
    if es >= 0.12 and es > en:
        return "es"
    if en >= 0.12 and en > es:
        return "en"
    return "otro"


def limpiar_letra(texto):
    texto = re.sub(r"^\[[^\]\n]{1,60}\]\s*$", "", texto, flags=re.M)  # [Coro], [Verse 1]
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def segmentar(texto, max_palabras=80):
    """Estrofas por línea en blanco; una estrofa demasiado larga (p.ej. letras
    de LRCLIB sin separadores) se re-parte en bloques de hasta 6 líneas, para
    quedar holgados bajo el límite de ~128 tokens de RoBERTuito."""
    crudas = [e.strip() for e in re.split(r"\n\s*\n", texto) if e.strip()]
    out = []
    for e in crudas:
        if len(e.split()) <= max_palabras:
            out.append(e)
            continue
        lineas = [l for l in e.split("\n") if l.strip()]
        for i in range(0, len(lineas), 6):
            bloque = "\n".join(lineas[i:i + 6]).strip()
            if bloque:
                out.append(bloque)
    return out


def cargar_letras():
    """Una letra por (ficha, titulo_norm), respetando prioridad de fuentes."""
    vistas, filas = set(), []
    for fuente in FUENTES:
        for f in (ROOT / "data/raw" / fuente).glob("*.jsonl"):
            with open(f) as fh:
                for linea in fh:
                    d = json.loads(linea)
                    clave = (d["ficha"], norm_fuerte(d["titulo"]))
                    if not clave[1] or clave in vistas:
                        continue
                    vistas.add(clave)
                    filas.append({
                        "ficha": d["ficha"],
                        "titulo_fuente": d["titulo"],
                        "titulo_norm": clave[1],
                        "fuente": fuente.replace("lyrics_", "").replace("lyrics", "genius"),
                        "composicion": d.get("composicion", ""),
                        "letra": limpiar_letra(d["letra"]),
                    })
    return pd.DataFrame(filas)


def main():
    cat = pd.read_csv(ROOT / "data/catalogo/catalogo.csv")
    cat["titulo_norm"] = cat.cancion.map(norm_fuerte)
    cat = (cat.sort_values("anio_album")
              .drop_duplicates(["ficha", "titulo_norm"], keep="first"))
    let = cargar_letras()

    corpus = []
    canon_sin_letra = []
    for ficha, g in cat.groupby("ficha"):
        lg = let[let.ficha == ficha].set_index("titulo_norm")
        pendientes_let = dict(lg.titulo_fuente)  # norm -> titulo fuente sin usar
        for _, c in g.iterrows():
            fila = None
            if c.titulo_norm in lg.index:
                d = lg.loc[c.titulo_norm]
                d = d.iloc[0] if isinstance(d, pd.DataFrame) else d
                fila = d
                pendientes_let.pop(c.titulo_norm, None)
            else:
                cerca = difflib.get_close_matches(c.titulo_norm, list(pendientes_let), n=1, cutoff=0.85)
                if cerca:
                    d = lg.loc[cerca[0]]
                    d = d.iloc[0] if isinstance(d, pd.DataFrame) else d
                    fila = d
                    pendientes_let.pop(cerca[0], None)
            if fila is None:
                canon_sin_letra.append({"ficha": ficha, "cancion": c.cancion,
                                        "album": c.album, "anio_album": c.anio_album})
                continue
            corpus.append({
                "cancion_id": f"{ficha}:{c.rg_mbid[:8]}:{int(c.pos):02d}",
                "ficha": ficha,
                "cancion": c.cancion,
                "album": c.album,
                "anio_album": c.anio_album,
                "fuente": fila.fuente,
                "titulo_fuente": fila.titulo_fuente,
                "composicion": fila.composicion,
                "idioma": detectar_idioma(fila.letra),
                "letra": fila.letra,
            })

    corpus = pd.DataFrame(corpus)
    destino = ROOT / "data/processed"
    destino.mkdir(parents=True, exist_ok=True)
    corpus.to_parquet(destino / "corpus.parquet", index=False)
    pd.DataFrame(canon_sin_letra).to_csv(destino / "canon_sin_letra.csv", index=False)

    estrofas = []
    for _, c in corpus.iterrows():
        for i, e in enumerate(segmentar(c.letra)):
            estrofas.append({"cancion_id": c.cancion_id, "estrofa_idx": i,
                             "n_palabras": len(e.split()), "texto": e})
    pd.DataFrame(estrofas).to_parquet(destino / "estrofas.parquet", index=False)

    print("=== corpus consolidado (canciones con letra matcheada al canon) ===")
    resumen = corpus.groupby("ficha").agg(
        canciones=("cancion_id", "size"),
        es=("idioma", lambda s: (s == "es").sum()),
        en=("idioma", lambda s: (s == "en").sum()),
        otro=("idioma", lambda s: (s == "otro").sum()),
    )
    resumen["canon"] = cat.groupby("ficha").size()
    resumen["cobertura"] = (resumen.canciones / resumen.canon).map("{:.0%}".format)
    print(resumen.to_string())
    print(f"\nestrofas totales: {len(estrofas)} | mediana por canción: "
          f"{pd.DataFrame(estrofas).groupby('cancion_id').size().median():.0f}")
    print(f"canon sin letra: {len(canon_sin_letra)} canciones -> canon_sin_letra.csv")


if __name__ == "__main__":
    main()
