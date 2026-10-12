"""Gráficas estáticas para LinkedIn (PNG 1080×1080 aprox, 200 dpi).

Tres piezas: distribución de tono por artista, arco temporal de Rada
(énfasis: Rada en color, el resto en gris), y proporción de alegría.

Salida: informe/linkedin/0{1,2,3}_*.png
Uso:    .venv/bin/python src/viz/linkedin_png.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "informe/linkedin"

NOMBRES = {"ruben_rada": "Rubén Rada", "eduardo_mateo": "Eduardo Mateo",
           "jorge_drexler": "Jorge Drexler", "jaime_roos": "Jaime Roos",
           "fernando_cabrera": "Fernando Cabrera", "alfredo_zitarrosa": "Alfredo Zitarrosa"}
ORDEN = ["ruben_rada", "eduardo_mateo", "jorge_drexler",
         "jaime_roos", "fernando_cabrera", "alfredo_zitarrosa"]
COLOR = {"ruben_rada": "#2a78d6", "eduardo_mateo": "#eb6834",
         "jorge_drexler": "#1baf7a", "jaime_roos": "#eda100",
         "fernando_cabrera": "#e87ba4", "alfredo_zitarrosa": "#008300"}
SURFACE, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
GRIS = "#c3c2b7"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": INK2,
    "axes.grid": False, "svg.fonttype": "none",
})

PIE = "análisis propio · 607 canciones (1966–2024) · clasificación por estrofa con RoBERTuito"


def marco(fig, titulo, subtitulo):
    lineas = titulo.count("\n") + 1
    fig.text(0.06, 0.97, titulo, fontsize=17, fontweight="bold", color=INK,
             va="top", linespacing=1.3)
    y_sub = 0.97 - 0.062 * lineas
    fig.text(0.06, y_sub, subtitulo, fontsize=11.5, color=INK2, va="top")
    fig.subplots_adjust(top=y_sub - 0.09)
    fig.text(0.06, 0.022, PIE, fontsize=8.5, color=MUTED)


def g1_distribucion(d):
    fig, ax = plt.subplots(figsize=(5.4, 5.4), dpi=200)
    fig.subplots_adjust(top=0.78, bottom=0.13, left=0.30, right=0.94)
    rng = np.random.default_rng(7)
    for i, f in enumerate(reversed(ORDEN)):
        g = d[d.ficha == f]
        y = i + rng.uniform(-0.2, 0.2, len(g))
        ax.scatter(g.valencia, y, s=14, color=COLOR[f], alpha=0.45, lw=0)
        med = g.valencia.median()
        ax.plot([med, med], [i - 0.3, i + 0.3], color=INK, lw=2.6, solid_capstyle="round")
    ax.axvline(0, color=GRID, lw=1, zorder=0)
    ax.set_yticks(range(len(ORDEN)))
    ax.set_yticklabels([NOMBRES[f] for f in reversed(ORDEN)], fontsize=11)
    ax.set_xlim(-1.05, 1.05)
    ax.set_xlabel("tono emocional de la letra  (− sombrío · + luminoso)",
                  fontsize=10, color=MUTED)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    marco(fig, "¿Quién escribe las letras más\nluminosas del cancionero uruguayo?",
          "cada punto es una canción · la barra negra es la mediana")
    fig.savefig(DEST / "01_tono.png")
    plt.close(fig)


def g2_arco(d):
    fig, ax = plt.subplots(figsize=(5.4, 5.4), dpi=200)
    fig.subplots_adjust(top=0.78, bottom=0.13, left=0.13, right=0.90)
    for f in ORDEN:
        g = d[d.ficha == f].dropna(subset=["decada"])
        if f == "eduardo_mateo":
            g = g[g.decada <= 1990]
        cel = g.groupby("decada").valencia.agg(["median", "size"])
        cel = cel[cel["size"] >= 5]
        if f == "ruben_rada":
            ax.plot(cel.index, cel["median"], color=COLOR[f], lw=3, zorder=5,
                    marker="o", ms=7, mec=SURFACE, mew=1.2)
            ax.annotate("Rada", (cel.index[-1], cel["median"].iloc[-1]),
                        xytext=(8, 4), textcoords="offset points",
                        color=COLOR[f], fontsize=12, fontweight="bold")
        else:
            ax.plot(cel.index, cel["median"], color=GRIS, lw=1.4, zorder=2)
    ax.axhline(0, color=BASE, lw=1, zorder=0)
    ax.set_xticks([1960, 1970, 1980, 1990, 2000, 2010, 2020])
    ax.set_xticklabels(["'60", "'70", "'80", "'90", "'00", "'10", "'20"], fontsize=10)
    ax.set_ylabel("tono emocional mediano", fontsize=10, color=MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    marco(fig, "El arco de Rada:\ncada década más luminoso",
          "de −0.21 en los 70 a +0.32 en los 2010s · en gris, los otros cinco")
    fig.savefig(DEST / "02_arco.png")
    plt.close(fig)


def g3_alegria(d):
    fig, ax = plt.subplots(figsize=(5.4, 5.4), dpi=200)
    fig.subplots_adjust(top=0.78, bottom=0.10, left=0.30, right=0.90)
    vals = [(f, d[d.ficha == f].emo_joy.mean() * 100) for f in ORDEN]
    vals.sort(key=lambda x: x[1])
    for i, (f, v) in enumerate(vals):
        color = COLOR["ruben_rada"] if f == "ruben_rada" else GRIS
        ax.barh(i, v, height=0.55, color=color)
        ax.text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=11,
                color=INK if f == "ruben_rada" else INK2,
                fontweight="bold" if f == "ruben_rada" else "normal")
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels([NOMBRES[f] for f, _ in vals], fontsize=11)
    ax.set_xlim(0, 21)
    ax.set_xticks([])
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    marco(fig, "Cinco veces más alegría\nque Zitarrosa",
          "% de estrofas cuya emoción dominante es alegría")
    fig.savefig(DEST / "03_alegria.png")
    plt.close(fig)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    d = pd.read_parquet(ROOT / "data/processed/canciones_scores.parquet")
    d = d[d.ficha.isin(ORDEN)]
    g1_distribucion(d)
    g2_arco(d)
    g3_alegria(d)
    for f in sorted(DEST.glob("*.png")):
        print(f, f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
