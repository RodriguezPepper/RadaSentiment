"""Gráficas estáticas para LinkedIn y el README (PNG 1080×1080).

Tres piezas con el mismo sistema visual: Rada en azul, los otros cinco en
gris, para que en las tres se lea la misma historia.

  01_tono.png     distribución del tono por canción, artista por artista
  02_arco.png     tono mediano de Rada por década contra el resto
  03_alegria.png  proporción de estrofas cuya emoción dominante es alegría
  04_amplitud.png alegría contra tristeza: la amplitud emocional de Rada

Salida: informe/linkedin/0{1,2,3,4}_*.png
Uso:    .venv/bin/python src/viz/linkedin_png.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "informe/linkedin"

NOMBRES = {"ruben_rada": "Rubén Rada", "eduardo_mateo": "Eduardo Mateo",
           "jorge_drexler": "Jorge Drexler", "jaime_roos": "Jaime Roos",
           "fernando_cabrera": "Fernando Cabrera", "alfredo_zitarrosa": "Alfredo Zitarrosa"}
ORDEN = ["ruben_rada", "eduardo_mateo", "jorge_drexler",
         "jaime_roos", "fernando_cabrera", "alfredo_zitarrosa"]

SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
RADA = "#e34948"
OTROS = "#cfcec6"

LADO, DPI = 6.0, 180  # 1080 px
PIE = "607 canciones · tono por estrofa con RoBERTuito · github.com/RodriguezPepper/RadaSentiment"

plt.rcParams.update({
    "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": BASE, "axes.linewidth": 1,
    "xtick.color": MUTED, "ytick.color": INK2,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "xtick.major.pad": 8, "ytick.major.pad": 10,
    "axes.grid": False, "axes.axisbelow": True,
    "axes.formatter.use_locale": False,
})


def coma(x, dec=2, signo=True):
    """Formato rioplatense: coma decimal y signo menos tipográfico."""
    s = f"{x:+.{dec}f}" if signo else f"{x:.{dec}f}"
    return s.replace("-", "−").replace(".", ",")


def lienzo(titulo, subtitulo, ax_rect):
    fig = plt.figure(figsize=(LADO, LADO), dpi=DPI)
    x0 = 0.075
    fig.text(x0, 0.935, titulo, fontsize=19, fontweight="bold", color=INK,
             va="top", linespacing=1.15)
    lineas = titulo.count("\n") + 1
    fig.text(x0, 0.935 - 0.052 * lineas - 0.018, subtitulo, fontsize=11.5,
             color=INK2, va="top", linespacing=1.35)
    fig.add_artist(plt.Line2D([x0, 1 - x0], [0.062, 0.062], color=GRID, lw=0.8))
    fig.text(x0, 0.036, PIE, fontsize=7.6, color=MUTED, va="center")
    ax = fig.add_axes(ax_rect)
    for s in ax.spines.values():
        s.set_visible(False)
    return fig, ax


def g1_distribucion(d):
    fig, ax = lienzo("¿Quién escribe las letras más\nluminosas del cancionero uruguayo?",
                     "Cada punto es una canción; la marca oscura es la mediana\nde cada artista.",
                     [0.29, 0.17, 0.56, 0.54])
    rng = np.random.default_rng(7)
    n = len(ORDEN)
    for i, f in enumerate(ORDEN):
        y0 = n - 1 - i
        g = d[d.ficha == f]
        es_rada = f == "ruben_rada"
        y = y0 + rng.uniform(-0.22, 0.22, len(g))
        ax.scatter(g.valencia, y, s=17, color=RADA if es_rada else OTROS,
                   alpha=0.75 if es_rada else 0.9, lw=0, zorder=2)
        med = g.valencia.median()
        ax.plot([med, med], [y0 - 0.34, y0 + 0.34], color=INK, lw=2.4,
                solid_capstyle="round", zorder=4)
        ax.text(1.12, y0, coma(med), ha="left", va="center", fontsize=10.5,
                color=INK if es_rada else INK2,
                fontweight="bold" if es_rada else "normal")
    ax.text(1.12, n - 0.35, "Mediana", ha="left", va="bottom", fontsize=8.5, color=MUTED)
    ax.axvline(0, color=BASE, lw=1, zorder=1)
    ax.set_yticks(range(n))
    ax.set_yticklabels([NOMBRES[f] for f in reversed(ORDEN)], fontsize=11.5)
    ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.get_yticklabels()[-1].set_color(INK)
    ax.set_xlim(-1.02, 1.02)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    ax.set_xticklabels(["−1", "−0,5", "0", "+0,5", "+1"], fontsize=9.5)
    ax.text(-1.02, -1.25, "← Más sombrío", ha="left", va="top", fontsize=9.5, color=INK2,
            transform=ax.transData)
    ax.text(1.02, -1.25, "Más luminoso →", ha="right", va="top", fontsize=9.5, color=INK2,
            transform=ax.transData)
    fig.savefig(DEST / "01_tono.png", facecolor=SURFACE)
    plt.close(fig)


def g2_arco(d):
    fig, ax = lienzo("Del Rada sombrío de los 70\nal luminoso de los 2010",
                     "Tono mediano de sus letras por década. En gris, los otros\ncinco cantautores.",
                     [0.135, 0.15, 0.76, 0.55])
    for f in ORDEN[1:]:
        g = d[d.ficha == f].dropna(subset=["decada"])
        if f == "eduardo_mateo":
            g = g[g.decada <= 1990]
        cel = g.groupby("decada").valencia.agg(["median", "size"])
        cel = cel[cel["size"] >= 5]
        ax.plot(cel.index, cel["median"], color=OTROS, lw=1.6, zorder=2,
                solid_capstyle="round", solid_joinstyle="round")

    g = d[d.ficha == "ruben_rada"].dropna(subset=["decada"])
    cel = g.groupby("decada").valencia.agg(["median", "size"])
    cel = cel[cel["size"] >= 5]["median"]
    ax.plot(cel.index, cel.values, color=RADA, lw=3, zorder=5,
            solid_capstyle="round", solid_joinstyle="round")
    ax.scatter(cel.index, cel.values, s=70, color=RADA, edgecolor=SURFACE,
               linewidth=2, zorder=6)

    notas = {1970: ("Los 70", (-12, 0)), 1990: ("El regreso", (0, 16)),
             2010: ("Los 2010", (0, 16))}
    for dec, (txt, off) in notas.items():
        v = cel[dec]
        ax.annotate(f"{txt}\n{coma(v)}", (dec, v), xytext=off, textcoords="offset points",
                    ha="right" if off[0] < 0 else "center",
                    va="center" if off[1] == 0 else "bottom", fontsize=10,
                    color=INK, linespacing=1.25,
                    fontweight="bold" if dec != 1990 else "normal")
    ax.annotate("Rada", (cel.index[-1], cel.values[-1]), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=11,
                fontweight="bold", color=INK)

    for y in (-0.4, -0.2, 0.2, 0.4):
        ax.axhline(y, color=GRID, lw=0.8, zorder=0)
    ax.axhline(0, color=BASE, lw=1.2, zorder=1)
    ax.set_ylim(-0.48, 0.48)
    ax.set_yticks([-0.4, -0.2, 0, 0.2, 0.4])
    ax.set_yticklabels(["−0,4", "−0,2", "0", "+0,2", "+0,4"], fontsize=9.5, color=MUTED)
    ax.set_xlim(1955, 2027)
    ax.set_xticks([1960, 1970, 1980, 1990, 2000, 2010, 2020])
    ax.set_xticklabels(["'60", "'70", "'80", "'90", "'00", "'10", "'20"], fontsize=10)
    fig.savefig(DEST / "02_arco.png", facecolor=SURFACE)
    plt.close(fig)


def barra(ax, y, v, alto, color, r_px=5):
    """Barra horizontal con la punta redondeada y la base recta."""
    fig = ax.figure
    fig.canvas.draw()
    bb = ax.get_window_extent()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    dx = (x1 - x0) / bb.width
    dy = (y1 - y0) / bb.height
    r = r_px * dx
    # se dibuja empezando en -r para que el redondeo izquierdo quede recortado por el eje
    p = FancyBboxPatch((-r, y - alto / 2), v + r, alto,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       mutation_aspect=dy / dx, lw=0, color=color, zorder=3)
    ax.add_patch(p)


def g3_alegria(d):
    fig, ax = lienzo("Casi cinco veces más alegría\nque Zitarrosa",
                     "Porcentaje de estrofas cuya emoción dominante es la alegría.",
                     [0.29, 0.15, 0.58, 0.58])
    vals = [(f, d[d.ficha == f].emo_joy.mean() * 100) for f in ORDEN]
    vals.sort(key=lambda x: x[1])
    ax.set_xlim(0, 20)
    ax.set_ylim(-0.6, len(vals) - 0.4)
    for i, (f, v) in enumerate(vals):
        es_rada = f == "ruben_rada"
        barra(ax, i, v, 0.42, RADA if es_rada else OTROS)
        ax.text(v + 0.45, i, f"{coma(v, 1, signo=False)} %", va="center", fontsize=11.5,
                color=INK if es_rada else INK2,
                fontweight="bold" if es_rada else "normal")
    ax.axvline(0, color=BASE, lw=1.2, zorder=4)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels([NOMBRES[f] for f, _ in vals], fontsize=11.5)
    ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.get_yticklabels()[-1].set_color(INK)
    ax.set_xticks([])
    fig.savefig(DEST / "03_alegria.png", facecolor=SURFACE)
    plt.close(fig)


def g4_amplitud(d):
    fig, ax = lienzo("Rada festeja como nadie\ny llora como pocos",
                     "Porcentaje de estrofas dominadas por la alegría y por la\ntristeza, artista por artista.",
                     [0.15, 0.17, 0.74, 0.53])
    em = d.groupby("ficha")[["emo_joy", "emo_sadness"]].mean() * 100
    # Las etiquetas van al costado de cada punto; el desplazamiento evita choques
    offs = {"ruben_rada": (-12, 0, "right"), "alfredo_zitarrosa": (12, 0, "left"),
            "eduardo_mateo": (12, 6, "left"), "jaime_roos": (12, -6, "left"),
            "fernando_cabrera": (-12, 4, "right"), "jorge_drexler": (-12, -4, "right")}
    for f in ORDEN:
        x, y = em.loc[f, "emo_joy"], em.loc[f, "emo_sadness"]
        es_rada = f == "ruben_rada"
        ax.scatter(x, y, s=260 if es_rada else 150, color=RADA if es_rada else OTROS,
                   edgecolor=SURFACE, linewidth=2, zorder=4)
        dx, dy, ha = offs[f]
        ax.annotate(NOMBRES[f], (x, y), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=11, color=INK if es_rada else INK2,
                    fontweight="bold" if es_rada else "normal")

    for v in (5, 10, 15, 20):
        ax.axvline(v, color=GRID, lw=0.8, zorder=0)
    for v in (10, 15, 20):
        ax.axhline(v, color=GRID, lw=0.8, zorder=0)
    ax.set_xlim(0, 21)
    ax.set_ylim(7, 24)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.set_xticklabels(["0 %", "5 %", "10 %", "15 %", "20 %"], fontsize=9.5)
    ax.set_yticks([10, 15, 20])
    ax.set_yticklabels(["10 %", "15 %", "20 %"], fontsize=9.5, color=MUTED)
    ax.set_xlabel("Alegría →", fontsize=10.5, color=INK2, loc="right", labelpad=8)
    ax.set_ylabel("Tristeza →", fontsize=10.5, color=INK2, loc="top", labelpad=8)
    x, y = em.loc["ruben_rada", "emo_joy"], em.loc["ruben_rada", "emo_sadness"]
    ax.annotate("Ningún otro junta tanta\nalegría y tanta tristeza", (x, y), xytext=(0, -22),
                textcoords="offset points", ha="center", va="top", fontsize=9.5,
                color=MUTED, linespacing=1.3)
    fig.savefig(DEST / "04_amplitud.png", facecolor=SURFACE)
    plt.close(fig)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    d = pd.read_parquet(ROOT / "data/processed/canciones_scores.parquet")
    d = d[d.ficha.isin(ORDEN)]
    g1_distribucion(d)
    g2_arco(d)
    g3_alegria(d)
    g4_amplitud(d)
    for f in sorted(DEST.glob("*.png")):
        print(f, f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
