"""Fase 4 — Scoring de estrofas con pysentimiento (local, sin APIs).

Corre los tres analizadores RoBERTuito (sentimiento POS/NEG/NEU, emociones,
ironía) sobre cada estrofa del corpus del análisis principal y guarda las
probabilidades crudas (regla METODO.md: siempre las probas, no solo la clase).

Reanudable por lotes: guarda checkpoint cada tanda.

Salida: data/processed/scores_estrofas.parquet
Uso:    .venv/bin/python -u src/analisis/local_pysent.py
"""

import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SALIDA = ROOT / "data/processed/scores_estrofas.parquet"
LOTE = 128


def main():
    corpus = pd.read_parquet(ROOT / "data/processed/corpus_analisis.parquet")
    estrofas = pd.read_parquet(ROOT / "data/processed/estrofas.parquet")
    estrofas = estrofas[estrofas.cancion_id.isin(set(corpus.cancion_id))].reset_index(drop=True)
    print(f"{len(estrofas)} estrofas de {corpus.cancion_id.nunique()} canciones", flush=True)

    hechas = pd.DataFrame()
    if SALIDA.exists():
        hechas = pd.read_parquet(SALIDA)
        claves = set(zip(hechas.cancion_id, hechas.estrofa_idx))
        estrofas = estrofas[[(c, i) not in claves for c, i in
                             zip(estrofas.cancion_id, estrofas.estrofa_idx)]].reset_index(drop=True)
        print(f"reanudando: {len(hechas)} ya puntuadas, {len(estrofas)} pendientes", flush=True)
    if not len(estrofas):
        print("nada pendiente", flush=True)
        return

    from pysentimiento import create_analyzer
    print("cargando modelos (la primera vez descarga ~1GB)...", flush=True)
    analizadores = {
        "sent": create_analyzer(task="sentiment", lang="es"),
        "emo": create_analyzer(task="emotion", lang="es"),
        "iro": create_analyzer(task="irony", lang="es"),
    }

    filas = []
    t0 = time.time()
    for inicio in range(0, len(estrofas), LOTE):
        tanda = estrofas.iloc[inicio:inicio + LOTE]
        textos = tanda.texto.tolist()
        res = {k: a.predict(textos) for k, a in analizadores.items()}
        for j, (_, e) in enumerate(tanda.iterrows()):
            fila = {"cancion_id": e.cancion_id, "estrofa_idx": e.estrofa_idx,
                    "n_palabras": e.n_palabras}
            for pref, outs in res.items():
                o = outs[j]
                fila[f"{pref}_pred"] = o.output
                for clase, p in o.probas.items():
                    fila[f"{pref}_{clase}"] = round(float(p), 5)
            filas.append(fila)
        parcial = pd.concat([hechas, pd.DataFrame(filas)], ignore_index=True)
        parcial.to_parquet(SALIDA, index=False)
        hechos_n = len(parcial)
        total = hechos_n + len(estrofas) - inicio - len(tanda)
        velocidad = len(filas) / (time.time() - t0)
        print(f"  {hechos_n}/{total} estrofas ({velocidad:.1f}/s)", flush=True)

    print("listo -> scores_estrofas.parquet", flush=True)


if __name__ == "__main__":
    main()
