"""Fase 3 — Exclusiones y créditos de autoría (v1).

Exclusiones (a nivel álbum y canción, todas documentadas con motivo):
  - infantil: discos para niños de Rada (regla METODO.md)
  - ingles: álbumes de proyectos en inglés (Richie Silver; Confidence si los
    datos lo confirman) + canciones sueltas con idioma != es
Créditos (v1, con lo que hay):
  - composicion de letras.com parseada -> autoria propia / coautoria / ajena
  - sin dato -> 'sin_credito' (se asume propia, con flag para sensibilidad)
  - fichas de banda (el_kinto, totem) -> 'ver_manual' (la asignación
    Rada-vs-Mateo de la época 1 es curaduría aparte)

Salidas:
  data/catalogo/exclusiones.csv   (versionable, auditable)
  data/catalogo/creditos.csv      (versionable: ids + crédito, sin letras)
  data/processed/corpus_analisis.parquet  corpus final del análisis principal

Uso: .venv/bin/python src/limpieza/exclusiones_creditos.py
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

ALBUMES_INFANTILES = {
    "Rada para niños",
    "Sueños de niño (Rada para niños)",
    "La escuela de Rada",
}
ALBUMES_INGLES_MANUAL = {
    "Richie Silver",  # proyecto en inglés de Rada (2006)
}
APELLIDOS = {
    "ruben_rada": ["rada"],
    "jaime_roos": ["roos"],
    "alfredo_zitarrosa": ["zitarrosa"],
    "fernando_cabrera": ["cabrera"],
    "eduardo_mateo": ["mateo"],
    "jorge_drexler": ["drexler"],
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def clasificar_autoria(ficha, composicion):
    if ficha not in APELLIDOS:
        return "ver_manual"
    comp = norm(composicion)
    comp = re.sub(r"^composicao( de)?:?|^composicion( de)?:?", "", comp).strip()
    if not comp:
        return "sin_credito"
    tiene_artista = any(a in comp for a in APELLIDOS[ficha])
    # heurística de nombres: separadores usuales en letras.com son / , y e
    otros = [p for p in re.split(r"[/,]| y | e ", comp) if p.strip()]
    solo_artista = tiene_artista and len(otros) <= 1
    if solo_artista:
        return "propia"
    if tiene_artista:
        return "coautoria"
    return "ajena"


def main():
    corpus = pd.read_parquet(ROOT / "data/processed/corpus.parquet")

    # ¿Confidence en inglés? decisión por datos: mayoría 'en' entre las matcheadas
    conf = corpus[corpus.album.str.startswith("Confidence", na=False)]
    albumes_ingles = set(ALBUMES_INGLES_MANUAL)
    for alb, g in conf.groupby("album"):
        if (g.idioma == "en").mean() >= 0.5:
            albumes_ingles.add(alb)
    print(f"albumes ingles: {sorted(albumes_ingles)}")
    if len(conf):
        print(f"  (Confidence matcheadas: {dict(conf.groupby('album').idioma.value_counts())})")

    exclusiones = []
    cat = pd.read_csv(ROOT / "data/catalogo/catalogo.csv")
    for _, c in cat.iterrows():
        motivo = None
        if c.album in ALBUMES_INFANTILES:
            motivo = "infantil"
        elif c.album in albumes_ingles:
            motivo = "album_ingles"
        if motivo:
            exclusiones.append({"ficha": c.ficha, "album": c.album,
                                "cancion": c.cancion, "motivo": motivo})
    excl_alb = pd.DataFrame(exclusiones)

    # canciones matcheadas con idioma != es (fuera de los álbumes ya excluidos)
    idioma_no_es = corpus[(corpus.idioma != "es")
                          & ~corpus.album.isin(albumes_ingles)
                          & ~corpus.album.isin(ALBUMES_INFANTILES)]
    excl_cancion = idioma_no_es[["ficha", "album", "cancion"]].assign(motivo="idioma_" + idioma_no_es.idioma)
    excl = pd.concat([excl_alb, excl_cancion], ignore_index=True)
    excl.to_csv(ROOT / "data/catalogo/exclusiones.csv", index=False)

    # créditos
    corpus["autoria"] = [clasificar_autoria(f, c) for f, c in zip(corpus.ficha, corpus.composicion)]
    creditos = corpus[["cancion_id", "ficha", "cancion", "album", "autoria", "composicion"]].rename(
        columns={"composicion": "composicion_raw"})
    creditos["fuente_credito"] = creditos.composicion_raw.map(lambda c: "letras.com" if c else "")
    creditos.to_csv(ROOT / "data/catalogo/creditos.csv", index=False)

    # corpus del análisis principal
    excluidas = set(zip(excl.ficha, excl.cancion))
    corpus["excluida"] = [((f, c) in excluidas) for f, c in zip(corpus.ficha, corpus.cancion)]
    final = corpus[~corpus.excluida & (corpus.idioma == "es") & (corpus.autoria != "ajena")].copy()
    final.to_parquet(ROOT / "data/processed/corpus_analisis.parquet", index=False)

    print("\n=== autoría (canciones con letra) ===")
    print(corpus.groupby(["ficha", "autoria"]).size().unstack(fill_value=0).to_string())
    print("\n=== corpus del análisis principal ===")
    canon = cat.copy()
    canon["excluida"] = [((f, c) in excluidas) for f, c in zip(canon.ficha, canon.cancion)]
    # denominador = canon sin exclusiones y sin las canciones de letra AJENA
    # conocida (METODO: el objeto es lo que cada uno escribió); para las no
    # matcheadas la autoría es desconocida y quedan en el denominador.
    denom = canon[~canon.excluida].drop_duplicates(["ficha", "cancion_norm"]).groupby("ficha").size()
    ajenas = corpus[corpus.autoria == "ajena"].groupby("ficha").size()
    resumen = final.groupby("ficha").size().to_frame("canciones")
    resumen["denominador"] = (denom - ajenas.reindex(denom.index).fillna(0)).astype(int)
    resumen["cobertura"] = (resumen.canciones / resumen.denominador).map("{:.0%}".format)
    print(resumen.to_string())
    print(f"\nexclusiones: {len(excl)} filas -> exclusiones.csv | ajenas fuera del principal: {(corpus.autoria == 'ajena').sum()}")


if __name__ == "__main__":
    main()
