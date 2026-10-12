"""Fase 6 — Capa léxica dimensional (normas Stadthagen-González et al. 2016).

Lematiza cada letra con spaCy y matchea contra las 14.031 palabras con normas
nativas de valencia y arousal (escala 1-9). Por canción: promedios centrados a
[-1, 1] y cobertura del léxico (% de palabras de contenido matcheadas).
Regla METODO.md: canciones con cobertura <30% se marcan y quedan fuera de la
capa dimensional.

También corre el chequeo de robustez pre-registrado: correlación del tono del
modelo vs. el tono léxico (por canción y por ranking de artistas).

Salida: data/processed/lexico_va.parquet
Uso:    .venv/bin/python src/analisis/lexico_va.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import spacy
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]


def main():
    lex = pd.read_csv(ROOT / "data/lexicons/stadthagen_va.csv",
                      encoding="latin-1", index_col=0)
    lex["w"] = lex.Word.astype(str).str.lower().str.strip()
    val = dict(zip(lex.w, lex.ValenceMean))
    aro = dict(zip(lex.w, lex.ArousalMean))
    print(f"léxico: {len(val)} palabras")

    corpus = pd.read_parquet(ROOT / "data/processed/corpus_analisis.parquet")
    nlp = spacy.load("es_core_news_md", disable=["parser", "ner"])

    filas = []
    docs = nlp.pipe(corpus.letra.tolist(), batch_size=64)
    for doc, (_, c) in zip(docs, corpus.iterrows()):
        vs, contenido = [], 0
        for t in doc:
            if not t.is_alpha or t.is_stop:
                continue
            contenido += 1
            w = t.lemma_.lower() if t.lemma_ else t.lower_
            v = val.get(w, val.get(t.lower_))
            if v is not None:
                a = aro.get(w, aro.get(t.lower_))
                vs.append((v, a))
        if contenido == 0:
            continue
        cob = len(vs) / contenido
        filas.append({
            "cancion_id": c.cancion_id, "ficha": c.ficha,
            "lex_cobertura": round(cob, 3),
            "lex_tono": round((np.mean([v for v, _ in vs]) - 5) / 4, 4) if vs else None,
            "lex_intensidad": round((np.mean([a for _, a in vs]) - 5) / 4, 4) if vs else None,
        })
    out = pd.DataFrame(filas)
    out.to_parquet(ROOT / "data/processed/lexico_va.parquet", index=False)

    ok = out[out.lex_cobertura >= 0.30].dropna(subset=["lex_tono"])
    print(f"{len(out)} canciones | cobertura mediana {out.lex_cobertura.median():.0%} | "
          f"con cobertura >=30%: {len(ok)}")

    scores = pd.read_parquet(ROOT / "data/processed/canciones_scores.parquet")
    m = ok.merge(scores[["cancion_id", "valencia"]], on="cancion_id")
    rho_c = stats.spearmanr(m.lex_tono, m.valencia).statistic
    med_mod = m.groupby("ficha").valencia.median()
    med_lex = m.groupby("ficha").lex_tono.median()
    rho_r = stats.spearmanr(med_mod, med_lex.reindex(med_mod.index)).statistic
    print(f"robustez modelo vs. léxico — por canción: Spearman = {rho_c:.3f} | "
          f"ranking de artistas: Spearman = {rho_r:.3f}")
    print("\ntono léxico mediano por ficha:")
    print(med_lex.sort_values(ascending=False).round(3).to_string())


if __name__ == "__main__":
    main()
