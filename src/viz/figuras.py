"""Fase 6/7 — Figuras exploratorias interactivas (Plotly → HTML standalone).

Colores: asignación fija por artista (validada CVD con el orden de aparición);
las emociones usan su propia secuencia validada; 'others' recede en gris.

Salida: informe/exploracion.html
Uso:    .venv/bin/python src/viz/figuras.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]

NOMBRES = {
    "ruben_rada": "Rubén Rada", "eduardo_mateo": "Eduardo Mateo",
    "jorge_drexler": "Jorge Drexler", "jaime_roos": "Jaime Roos",
    "fernando_cabrera": "Fernando Cabrera", "alfredo_zitarrosa": "Alfredo Zitarrosa",
}
# orden por mediana de valencia (fijo) y color fijo por entidad — secuencia validada
ORDEN = ["ruben_rada", "eduardo_mateo", "jorge_drexler",
         "jaime_roos", "fernando_cabrera", "alfredo_zitarrosa"]
COLOR = {"ruben_rada": "#2a78d6", "eduardo_mateo": "#eb6834",
         "jorge_drexler": "#1baf7a", "jaime_roos": "#eda100",
         "fernando_cabrera": "#e87ba4", "alfredo_zitarrosa": "#008300"}

EMO = [("emo_joy", "alegría", "#eda100"), ("emo_sadness", "tristeza", "#2a78d6"),
       ("emo_anger", "enojo", "#e34948"), ("emo_fear", "miedo", "#4a3aa7"),
       ("emo_surprise", "sorpresa", "#1baf7a"), ("emo_disgust", "asco", "#008300")]

SURFACE, PAGE = "#fcfcfb", "#f9f9f7"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def layout(fig, altura, titulo):
    fig.update_layout(
        title={"text": titulo, "font": {"size": 15, "color": INK}},
        height=altura, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font={"family": FONT, "size": 13, "color": INK2},
        margin={"l": 10, "r": 30, "t": 50, "b": 40},
        hoverlabel={"font": {"family": FONT, "size": 12}},
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=BASE, linecolor=BASE,
                     tickfont={"color": MUTED})
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=BASE, linecolor=BASE,
                     tickfont={"color": INK2})
    return fig


def fig_distribucion(d):
    fig = go.Figure()
    rng = np.random.default_rng(7)
    for i, f in enumerate(reversed(ORDEN)):
        g = d[d.ficha == f]
        y = i + rng.uniform(-0.22, 0.22, len(g))
        fig.add_trace(go.Scatter(
            x=g.valencia, y=y, mode="markers", name=NOMBRES[f], showlegend=False,
            marker={"color": COLOR[f], "size": 8, "opacity": 0.5,
                    "line": {"width": 1, "color": SURFACE}},
            customdata=np.stack([g.cancion, g.album, g.anio_album.fillna(0).astype(int)], axis=1),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} (%{customdata[2]})"
                          "<br>tono %{x:+.2f}<extra>" + NOMBRES[f] + "</extra>"))
        med = g.valencia.median()
        ci = stats.bootstrap((g.valencia.to_numpy(),), np.median, n_resamples=2000,
                             method="BCa", random_state=42).confidence_interval
        fig.add_trace(go.Scatter(x=[ci.low, ci.high], y=[i, i], mode="lines",
                                 line={"color": INK, "width": 2}, showlegend=False,
                                 hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=[med], y=[i], mode="markers", showlegend=False,
            marker={"symbol": "line-ns", "size": 22,
                    "line": {"width": 3, "color": INK}},
            hovertemplate=f"mediana {med:+.3f}<extra>{NOMBRES[f]}</extra>"))
    fig.update_yaxes(tickvals=list(range(len(ORDEN))),
                     ticktext=[NOMBRES[f] for f in reversed(ORDEN)],
                     showgrid=False)
    fig.update_xaxes(title={"text": "tono emocional de la letra   (− más sombrío · + más luminoso)",
                            "font": {"color": MUTED, "size": 12}},
                     range=[-1.05, 1.05])
    return layout(fig, 460, "Cada punto es una canción — tono emocional, con mediana (barra) e IC bootstrap 95%")


def fig_decadas(d):
    fig = go.Figure()
    for f in ORDEN:
        g = d[d.ficha == f].dropna(subset=["decada"])
        if f == "eduardo_mateo":
            g = g[g.decada <= 1990]  # ediciones póstumas sin curar el año real
        cel = g.groupby("decada").valencia.agg(["median", "size"]).reset_index()
        cel = cel[cel["size"] >= 5]
        fig.add_trace(go.Scatter(
            x=cel.decada, y=cel["median"], mode="lines+markers", name=NOMBRES[f],
            line={"color": COLOR[f], "width": 2},
            marker={"size": 8, "color": COLOR[f], "line": {"width": 1, "color": SURFACE}},
            customdata=cel["size"],
            hovertemplate="década %{x}: %{y:+.3f} (n=%{customdata})<extra>" + NOMBRES[f] + "</extra>"))
    for f, dy in (("ruben_rada", 0.05), ("alfredo_zitarrosa", -0.05)):
        g = d[d.ficha == f].dropna(subset=["decada"])
        cel = g.groupby("decada").valencia.agg(["median", "size"])
        cel = cel[cel["size"] >= 5]
        fig.add_annotation(x=cel.index.max(), y=cel["median"].iloc[-1] + dy,
                           text=NOMBRES[f], showarrow=False, xanchor="left", xshift=6,
                           font={"color": COLOR[f], "size": 12})
    fig.add_hline(y=0, line={"color": BASE, "width": 1})
    fig.update_xaxes(dtick=10, title={"text": "década (año de edición del álbum)",
                                      "font": {"color": MUTED, "size": 12}})
    fig.update_yaxes(title={"text": "tono emocional mediano", "font": {"color": MUTED, "size": 12}})
    fig.update_layout(legend={"orientation": "h", "y": -0.22, "yanchor": "top", "font": {"size": 12}})
    return layout(fig, 440, "Tono emocional mediano por década (celdas con n≥5; Mateo hasta 1990)")


def fig_emociones(d):
    fig = go.Figure()
    fichas = list(reversed(ORDEN))
    for col, nombre, color in EMO:
        vals = [d[d.ficha == f][col].mean() * 100 for f in fichas]
        fig.add_trace(go.Bar(
            y=[NOMBRES[f] for f in fichas], x=vals, name=nombre, orientation="h",
            marker={"color": color, "line": {"width": 2, "color": SURFACE}},
            text=[f"{v:.0f}%" if v >= 6 else "" for v in vals],
            textfont={"color": SURFACE, "size": 11},
            hovertemplate="%{x:.1f}% de estrofas<extra>" + nombre + "</extra>"))
    resto = [100 - sum(d[d.ficha == f][c].mean() * 100 for c, _, _ in EMO) for f in fichas]
    fig.add_trace(go.Bar(
        y=[NOMBRES[f] for f in fichas], x=resto, name="neutral / otras", orientation="h",
        marker={"color": GRID, "line": {"width": 2, "color": SURFACE}},
        hovertemplate="%{x:.1f}% de estrofas<extra>neutral / otras</extra>"))
    fig.update_layout(barmode="stack",
                      legend={"orientation": "h", "y": -0.18, "yanchor": "top", "font": {"size": 12}})
    fig.update_xaxes(title={"text": "% de estrofas por emoción dominante",
                            "font": {"color": MUTED, "size": 12}}, range=[0, 100])
    fig.update_yaxes(showgrid=False)
    return layout(fig, 400, "Perfil de emociones (proporción media de estrofas)")


def fig_epocas(d):
    import yaml
    cfg = yaml.safe_load((ROOT / "config/artistas.yaml").read_text())
    epocas = cfg["sujeto"]["ruben_rada"]["epocas"]
    filas = d[d.ficha.isin(["ruben_rada", "el_kinto", "totem"])].copy()
    def epoca_de(r):
        if r.ficha in ("el_kinto", "totem"):
            return epocas[0]["nombre"]
        for e in epocas:
            if e["desde"] <= (r.anio_album or 0) <= e["hasta"]:
                return e["nombre"]
        return None
    filas["epoca"] = filas.apply(epoca_de, axis=1)
    orden = [e["nombre"] for e in epocas]
    agg = (filas.dropna(subset=["epoca"]).groupby("epoca")
           .agg(n=("valencia", "size"), mediana=("valencia", "median")).reindex(orden))
    ramp = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
    fig = go.Figure(go.Bar(
        x=orden, y=agg.mediana, marker={"color": ramp, "line": {"width": 0}}, width=0.55,
        text=[f"{m:+.2f}" for m in agg.mediana], textposition="outside",
        textfont={"color": INK2, "size": 12},
        customdata=agg.n, hovertemplate="mediana %{y:+.3f} (n=%{customdata})<extra></extra>"))
    fig.add_hline(y=0, line={"color": BASE, "width": 1})
    fig.update_xaxes(tickfont={"color": INK2})
    fig.update_yaxes(title={"text": "valencia mediana", "font": {"color": MUTED, "size": 12}},
                     range=[-0.3, 0.3])
    return layout(fig, 380, "Rada por época (El Kinto y Tótem integran la primera)")


def tabla_resumen(d):
    filas = []
    for f in ORDEN:
        g = d[d.ficha == f]
        ci = stats.bootstrap((g.valencia.to_numpy(),), np.median, n_resamples=2000,
                             method="BCa", random_state=42).confidence_interval
        filas.append(f"<tr><td>{NOMBRES[f]}</td><td>{len(g)}</td>"
                     f"<td>{g.valencia.median():+.3f}</td>"
                     f"<td>[{ci.low:+.3f}, {ci.high:+.3f}]</td>"
                     f"<td>{g.emo_joy.mean():.1%}</td><td>{g.emo_sadness.mean():.1%}</td></tr>")
    return ("<details><summary>Vista de tabla (datos de las figuras)</summary>"
            "<table><thead><tr><th>artista</th><th>n</th><th>tono mediano</th><th>IC 95%</th>"
            "<th>alegría</th><th>tristeza</th></tr></thead><tbody>"
            + "".join(filas) + "</tbody></table></details>")


def main():
    d = pd.read_parquet(ROOT / "data/processed/canciones_scores.parquet")
    d6 = d[d.ficha.isin(ORDEN)]

    figs = [fig_distribucion(d6), fig_decadas(d6), fig_emociones(d6), fig_epocas(d)]
    html_figs = [figs[0].to_html(full_html=False, include_plotlyjs=True,
                                 config={"displayModeBar": False, "responsive": True})]
    html_figs += [f.to_html(full_html=False, include_plotlyjs=False,
                            config={"displayModeBar": False, "responsive": True})
                  for f in figs[1:]]

    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RadaSentiment — exploración</title>
<style>
  body {{ margin:0; background:{PAGE}; color:{INK}; font-family:{FONT}; }}
  main {{ max-width: 880px; margin: 0 auto; padding: 28px 20px 60px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }}
  p.sub {{ color:{INK2}; margin: 0 0 24px; font-size: 14px; }}
  section {{ background:{SURFACE}; border:1px solid rgba(11,11,11,0.10);
             border-radius: 10px; padding: 14px 14px 4px; margin-bottom: 22px; }}
  .caveats {{ font-size: 13px; color:{INK2}; background:{SURFACE};
              border:1px solid rgba(11,11,11,0.10); border-radius:10px; padding: 14px 18px; }}
  .caveats b {{ color:{INK}; }}
  details {{ font-size: 13px; color:{INK2}; margin: 10px 0 20px; }}
  table {{ border-collapse: collapse; margin-top: 10px; font-variant-numeric: tabular-nums; }}
  td, th {{ padding: 5px 12px; border-bottom: 1px solid {GRID}; text-align: right; }}
  td:first-child, th:first-child {{ text-align: left; }}
</style></head><body><main>
<h1>El sentimiento de las letras: Rada y cinco cantautores uruguayos</h1>
<p class="sub">Análisis exploratorio · 607 canciones · clasificador RoBERTuito por estrofa,
agregado por canción · corpus y método pre-registrados</p>
<section>{html_figs[0]}</section>
{tabla_resumen(d6)}
<section>{html_figs[1]}</section>
<section>{html_figs[2]}</section>
<section>{html_figs[3]}</section>
<div class="caveats"><b>Limitaciones (pre-registradas):</b> el tono absoluto
tira a negativo (modelo entrenado en tweets; leer diferencias relativas, no niveles);
sin validación con anotación humana en este dominio — resultados exploratorios;
el detector de ironía satura fuera de dominio y no discrimina; cobertura de letras de Rada
42% del canon con faltantes concentrados en discos infantiles, en inglés e instrumentales
tardíos; los años de Mateo posteriores a 1990 son ediciones póstumas y se excluyen de la
serie temporal.</div>
</main></body></html>"""
    out = ROOT / "informe/exploracion.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(pagina)
    print(f"{out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
