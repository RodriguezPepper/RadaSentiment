"""Fase 6 — Comparación estadística (reglas de METODO.md §7).

- Kruskal-Wallis + epsilon² sobre valencia por canción (6 solistas).
- Post-hoc de Dunn con Holm (implementación propia validada).
- Delta de Cliff para cada par Rada-vs-X: crudo Y restringido a décadas de
  solapamiento (>=5 canciones de cada uno) — el restringido es el interpretable.
- IC bootstrap BCa de la mediana por artista.
- Tabla ficha × década (mediana, celdas con n>=5).
- Épocas de Rada (config/artistas.yaml; El Kinto y Tótem cuentan en la época 1).
- Chi² + V de Cramér sobre emoción dominante por canción.
- Sensibilidad: sin dedup de coros, y con/sin canciones mayormente irónicas.

Salida: results/estadistica.md (+ impresión en consola)
Uso:    .venv/bin/python src/estadistica/tests.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from posthoc import posthoc_dunn  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SOLISTAS = ["ruben_rada", "jaime_roos", "alfredo_zitarrosa",
            "fernando_cabrera", "eduardo_mateo", "jorge_drexler"]


def cliff_delta(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(np.sign(a[:, None] - b[None, :]).mean())


def interpretar_delta(d):
    ad = abs(d)
    if ad < 0.147:
        return "insignificante"
    if ad < 0.33:
        return "chico"
    if ad < 0.474:
        return "mediano"
    return "grande"


def ci_mediana(x):
    r = stats.bootstrap((np.asarray(x, dtype=float),), np.median,
                        n_resamples=2000, method="BCa", random_state=42)
    return r.confidence_interval.low, r.confidence_interval.high


def main():
    d = pd.read_parquet(ROOT / "data/processed/canciones_scores.parquet")
    d6 = d[d.ficha.isin(SOLISTAS)].copy()
    md = ["# Comparación estadística — valencia por canción",
          f"\nCorpus principal: {len(d6)} canciones de 6 solistas "
          f"(+ {len(d) - len(d6)} de El Kinto/Tótem para las épocas de Rada).\n"]

    # 1. Kruskal-Wallis
    grupos = {f: g.valencia.to_numpy() for f, g in d6.groupby("ficha")}
    H, p = stats.kruskal(*grupos.values())
    n, k = len(d6), len(grupos)
    eps2 = H * (n + 1) / (n**2 - 1)
    md.append(f"## Kruskal-Wallis\nH = {H:.2f}, p = {p:.2e}, epsilon² = {eps2:.3f} (n={n}, k={k})\n")

    # 2. medianas con IC BCa
    md.append("## Medianas con IC bootstrap BCa 95%\n")
    md.append("| artista | n | mediana | IC 95% |")
    md.append("|---|---|---|---|")
    for f in sorted(grupos, key=lambda f: -np.median(grupos[f])):
        lo, hi = ci_mediana(grupos[f])
        md.append(f"| {f} | {len(grupos[f])} | {np.median(grupos[f]):+.3f} | [{lo:+.3f}, {hi:+.3f}] |")

    # 3. Dunn-Holm
    dunn = posthoc_dunn(d6, "valencia", "ficha", p_adjust="holm")
    md.append("\n## Post-hoc de Dunn (p ajustada Holm)\n")
    md.append(dunn.round(4).to_markdown())

    # 4. Cliff Rada vs X, crudo y por décadas solapadas
    md.append("\n## Delta de Cliff: Rada vs. cada comparador\n")
    md.append("| par | delta crudo | delta décadas solapadas | décadas | interpretación (restr.) |")
    md.append("|---|---|---|---|---|")
    rada = d6[d6.ficha == "ruben_rada"]
    for f in [x for x in SOLISTAS if x != "ruben_rada"]:
        otro = d6[d6.ficha == f]
        crudo = cliff_delta(rada.valencia, otro.valencia)
        dec_r = rada.groupby("decada").size()
        dec_o = otro.groupby("decada").size()
        comunes = sorted(set(dec_r[dec_r >= 5].index) & set(dec_o[dec_o >= 5].index))
        if comunes:
            rr = rada[rada.decada.isin(comunes)].valencia
            oo = otro[otro.decada.isin(comunes)].valencia
            restr = cliff_delta(rr, oo)
            md.append(f"| rada vs {f} | {crudo:+.3f} | {restr:+.3f} | "
                      f"{', '.join(str(int(c)) for c in comunes)} | {interpretar_delta(restr)} |")
        else:
            md.append(f"| rada vs {f} | {crudo:+.3f} | (sin solapamiento n>=5) | — | — |")

    # 5. ficha × década
    md.append("\n## Mediana de valencia por ficha × década (celdas con n>=5)\n")
    cel = (d.dropna(subset=["decada"]).groupby(["ficha", "decada"])
             .valencia.agg(["median", "size"]).reset_index())
    piv = cel[cel["size"] >= 5].pivot(index="ficha", columns="decada", values="median")
    md.append(piv.round(3).to_markdown())

    # 6. épocas de Rada (bandas cuentan en la época 1)
    cfg = yaml.safe_load((ROOT / "config/artistas.yaml").read_text())
    epocas = cfg["sujeto"]["ruben_rada"]["epocas"]
    filas_rada = d[d.ficha.isin(["ruben_rada", "el_kinto", "totem"])].copy()
    def epoca_de(fila):
        if fila.ficha in ("el_kinto", "totem"):
            return epocas[0]["nombre"]
        for e in epocas:
            if e["desde"] <= (fila.anio_album or 0) <= e["hasta"]:
                return e["nombre"]
        return None
    filas_rada["epoca"] = filas_rada.apply(epoca_de, axis=1)
    md.append("\n## Rada por época (incluye El Kinto y Tótem en la época 1)\n")
    ep = (filas_rada.dropna(subset=["epoca"]).groupby("epoca")
          .agg(n=("valencia", "size"), mediana=("valencia", "median"),
               alegria=("emo_joy", "mean"), tristeza=("emo_sadness", "mean")))
    orden = [e["nombre"] for e in epocas]
    md.append(ep.reindex(orden).round(3).to_markdown())

    # 7. emociones: chi² sobre emoción dominante
    emo_cols = [c for c in d6.columns if c.startswith("emo_")]
    dom = d6[emo_cols].idxmax(axis=1).str.replace("emo_", "")
    tabla = pd.crosstab(d6.ficha, dom)
    chi2, p_e, dof, _ = stats.chi2_contingency(tabla)
    v = np.sqrt(chi2 / (tabla.values.sum() * (min(tabla.shape) - 1)))
    md.append(f"\n## Emoción dominante por canción\nchi² = {chi2:.1f} (gl={dof}), "
              f"p = {p_e:.2e}, V de Cramér = {v:.3f}\n")
    md.append(tabla.to_markdown())

    # 8. sensibilidad
    med_ded = d6.groupby("ficha").valencia.median()
    med_sin = d6.groupby("ficha").valencia_sin_dedup.median()
    rho_dedup = stats.spearmanr(med_ded, med_sin).statistic
    sin_iro = d6[d6.prop_ironicas <= 0.5]
    med_sin_iro = sin_iro.groupby("ficha").valencia.median()
    rho_iro = stats.spearmanr(med_ded, med_sin_iro.reindex(med_ded.index)).statistic
    md.append("\n## Sensibilidad\n"
              f"- Ranking con vs. sin deduplicar coros: Spearman = {rho_dedup:.3f}\n"
              f"- Ranking total vs. solo canciones <=50% irónicas (n={len(sin_iro)}): "
              f"Spearman = {rho_iro:.3f}\n"
              "- ADVERTENCIA pre-registrada: el detector de ironía satura fuera de dominio "
              "(mediana 83% de estrofas irónicas en todos los artistas); el corte con/sin "
              "ironía es poco informativo y se reporta solo por completitud.\n")

    out = ROOT / "results/estadistica.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
