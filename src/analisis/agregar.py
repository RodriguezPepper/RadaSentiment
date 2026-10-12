"""Fase 4 — Agregación estrofa → canción (reglas de METODO.md).

- Valencia por estrofa: P(POS) − P(NEG), en [−1, 1].
- Valencia por canción (principal): media ponderada por n_palabras sobre
  estrofas DEDUPLICADAS (coros repetidos cuentan una vez).
- Sensibilidad: misma media SIN deduplicar (se guardan ambas).
- Emociones: proporción de estrofas (deduplicadas) por emoción dominante.
- Ironía: proporción de estrofas irónicas + flag (>=1 estrofa irónica).
- Repetitividad: ratio de compresión gzip de la letra completa (feature aparte).

Salida: data/processed/canciones_scores.parquet
Uso:    .venv/bin/python src/analisis/agregar.py
"""

import gzip
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def norm_texto(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip()


def ratio_gzip(texto):
    crudo = texto.encode()
    return len(gzip.compress(crudo)) / max(len(crudo), 1)


def main():
    corpus = pd.read_parquet(ROOT / "data/processed/corpus_analisis.parquet")
    estr = pd.read_parquet(ROOT / "data/processed/estrofas.parquet")
    scores = pd.read_parquet(ROOT / "data/processed/scores_estrofas.parquet")

    df = estr.merge(scores.drop(columns=["n_palabras"]),
                    on=["cancion_id", "estrofa_idx"], how="inner")
    df["valencia"] = df.sent_POS - df.sent_NEG
    df["texto_norm"] = df.texto.map(norm_texto)

    emo_clases = sorted(c.replace("emo_", "") for c in scores.columns
                        if c.startswith("emo_") and c != "emo_pred")

    filas = []
    for cid, g in df.groupby("cancion_id"):
        dedup = g.drop_duplicates("texto_norm")
        w, wd = g.n_palabras, dedup.n_palabras
        fila = {
            "cancion_id": cid,
            "n_estrofas": len(g),
            "n_estrofas_dedup": len(dedup),
            "valencia": np.average(dedup.valencia, weights=wd),
            "valencia_sin_dedup": np.average(g.valencia, weights=w),
            "prop_ironicas": (dedup.iro_pred == "ironic").mean(),
            "flag_ironia": bool((dedup.iro_pred == "ironic").any()),
        }
        for c in emo_clases:
            fila[f"emo_{c}"] = (dedup.emo_pred == c).mean()
        filas.append(fila)

    out = pd.DataFrame(filas).merge(
        corpus[["cancion_id", "ficha", "cancion", "album", "anio_album",
                "autoria", "fuente", "letra"]],
        on="cancion_id")
    out["repetitividad_gzip"] = out.letra.map(ratio_gzip)
    out["n_palabras_letra"] = out.letra.str.split().str.len()
    out["decada"] = (out.anio_album // 10 * 10).astype("Int64")
    out = out.drop(columns=["letra"])
    out.to_parquet(ROOT / "data/processed/canciones_scores.parquet", index=False)

    print(f"{len(out)} canciones agregadas")
    print("\n=== valencia mediana por ficha (primer vistazo, SIN estadística aún) ===")
    r = out.groupby("ficha").agg(
        n=("valencia", "size"),
        val_mediana=("valencia", "median"),
        pct_ironia=("flag_ironia", "mean"),
        emo_dominante=("cancion_id", lambda _: ""),
    )
    emos = out.groupby("ficha")[[f"emo_{c}" for c in emo_clases]].mean()
    r["emo_dominante"] = emos.drop(columns=["emo_others"], errors="ignore").idxmax(axis=1).str.replace("emo_", "")
    print(r.round(3).to_string())


if __name__ == "__main__":
    main()
