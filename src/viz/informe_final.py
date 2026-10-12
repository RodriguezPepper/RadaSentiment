"""Fase 7 — Informe final integrado (HTML standalone).

Reusa las figuras de figuras.py, agrega el mapa tono×intensidad de la capa
léxica (small multiples, un artista por panel) y la narrativa con los
resultados estadísticos.

Salida: informe/informe.html
Uso:    .venv/bin/python src/viz/informe_final.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent))
from figuras import (COLOR, FONT, GRID, INK, INK2, MUTED, NOMBRES, ORDEN,  # noqa: E402
                     PAGE, SURFACE, BASE, ROOT, fig_decadas, fig_distribucion,
                     fig_emociones, fig_epocas, layout, tabla_resumen)


def fig_va(scores, va):
    d = scores.merge(va[["cancion_id", "lex_tono", "lex_intensidad", "lex_cobertura"]],
                     on="cancion_id")
    d = d[(d.ficha.isin(ORDEN)) & (d.lex_cobertura >= 0.30)].dropna(subset=["lex_tono"])
    fig = make_subplots(rows=2, cols=3, subplot_titles=[NOMBRES[f] for f in ORDEN],
                        horizontal_spacing=0.06, vertical_spacing=0.14)
    for i, f in enumerate(ORDEN):
        g = d[d.ficha == f]
        r, c = i // 3 + 1, i % 3 + 1
        fig.add_trace(go.Scatter(
            x=g.lex_tono, y=g.lex_intensidad, mode="markers", showlegend=False,
            marker={"color": COLOR[f], "size": 6, "opacity": 0.55,
                    "line": {"width": 1, "color": SURFACE}},
            customdata=g.cancion,
            hovertemplate="<b>%{customdata}</b><br>tono %{x:+.2f} · intensidad %{y:+.2f}"
                          f"<extra>{NOMBRES[f]}</extra>"), row=r, col=c)
        fig.add_vline(x=0, line={"color": GRID, "width": 1}, row=r, col=c)
        fig.add_hline(y=0, line={"color": GRID, "width": 1}, row=r, col=c)
    fig.update_xaxes(range=[-0.35, 0.85], gridcolor=GRID, tickfont={"color": MUTED, "size": 10})
    fig.update_yaxes(range=[-0.45, 0.45], gridcolor=GRID, tickfont={"color": MUTED, "size": 10})
    for a in fig.layout.annotations:
        a.font = {"size": 12, "color": INK2, "family": FONT}
    fig.add_annotation(text="→ tono léxico (sombrío · luminoso) — ↑ intensidad emocional",
                       xref="paper", yref="paper", x=0.5, y=-0.12, showarrow=False,
                       font={"color": MUTED, "size": 11})
    return layout(fig, 520, "Mapa léxico por canción (normas nativas en español, cobertura ≥30%)")


def main():
    scores = pd.read_parquet(ROOT / "data/processed/canciones_scores.parquet")
    va = pd.read_parquet(ROOT / "data/processed/lexico_va.parquet")
    d6 = scores[scores.ficha.isin(ORDEN)]

    figs = {
        "dist": fig_distribucion(d6),
        "dec": fig_decadas(d6),
        "emo": fig_emociones(d6),
        "ep": fig_epocas(scores),
        "va": fig_va(scores, va),
    }
    html = {}
    primera = True
    for k, f in figs.items():
        html[k] = f.to_html(full_html=False, include_plotlyjs=primera,
                            config={"displayModeBar": False, "responsive": True})
        primera = False

    css = f"""
  body {{ margin:0; background:{PAGE}; color:{INK}; font-family:{FONT}; }}
  main {{ max-width: 880px; margin: 0 auto; padding: 34px 20px 60px; }}
  h1 {{ font-size: 26px; margin: 0 0 6px; line-height: 1.2; }}
  h2 {{ font-size: 18px; margin: 34px 0 6px; }}
  p {{ font-size: 14.5px; line-height: 1.55; color:{INK2}; margin: 8px 0; }}
  p b, li b {{ color:{INK}; }}
  .sub {{ color:{MUTED}; font-size: 13.5px; margin-bottom: 26px; }}
  section.fig {{ background:{SURFACE}; border:1px solid rgba(11,11,11,0.10);
                 border-radius: 10px; padding: 14px 14px 4px; margin: 14px 0 6px; }}
  .caveats {{ font-size: 13px; color:{INK2}; background:{SURFACE};
              border:1px solid rgba(11,11,11,0.10); border-radius:10px;
              padding: 14px 18px; margin-top: 26px; }}
  ul {{ color:{INK2}; font-size: 14.5px; line-height: 1.55; }}
  details {{ font-size: 13px; color:{INK2}; margin: 10px 0 6px; }}
  table {{ border-collapse: collapse; margin-top: 10px; font-variant-numeric: tabular-nums; }}
  td, th {{ padding: 5px 12px; border-bottom: 1px solid {GRID}; text-align: right; }}
  td:first-child, th:first-child {{ text-align: left; }}
  .ficha-tec {{ font-size: 12.5px; color:{MUTED}; margin-top: 30px;
                border-top: 1px solid {GRID}; padding-top: 12px; }}
"""

    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>El tono del cancionero uruguayo</title><style>{css}</style></head><body><main>

<h1>El tono emocional del cancionero uruguayo:<br>Rubén Rada frente a cinco cantautores</h1>
<p class="sub">607 canciones · 1966–2024 · análisis por estrofa con un modelo de lenguaje
en español, agregado por canción · corpus, reglas y estadística pre-registradas</p>

<p><b>Rada es el letrista más luminoso del set.</b> Sobre 572 canciones de seis
cantautores, las suyas concentran casi <b>cinco veces más estrofas de alegría que las
de Zitarrosa</b> (17.8% contra 3.6%) sin resignar tristeza (19.3%): amplitud emocional,
no simpleza. En el otro polo, Zitarrosa y Cabrera escriben el cancionero más sombrío;
Mateo y Drexler acompañan a Rada en el polo luminoso y Roos queda en el medio, no
distinguible de ninguno.</p>

<h2>Cada canción, un punto</h2>
<section class="fig">{html['dist']}</section>
<p>La diferencia global entre artistas es estadísticamente significativa
(Kruskal-Wallis H = 41.45, p = 7.6×10⁻⁸; ε² = 0.073) y el post-hoc de Dunn
separa dos grupos: <b>{{Rada, Mateo, Drexler}}</b> frente a
<b>{{Cabrera, Zitarrosa}}</b> (p ≤ 0.007 en todos los cruces entre grupos).</p>
{tabla_resumen(d6)}

<h2>Controlar la época importa</h2>
<section class="fig">{html['dec']}</section>
<p>Zitarrosa dejó de grabar en 1989; Drexler empezó en 1992: comparar crudo mezcla
artista con época. El delta de Cliff Rada–Zitarrosa pasa de +0.32 (crudo) a
<b>+0.16 restringido a las décadas que compartieron</b> — la mitad de la diferencia
era época. El contraste más sólido del estudio es <b>Rada–Cabrera: +0.33 (efecto
mediano) en cuatro décadas compartidas</b>. Rada–Mateo: −0.02, indistinguibles.</p>

<h2>El arco de Rada: cada década más luminoso</h2>
<section class="fig">{html['ep']}</section>
<p>El Rada de El Kinto, Tótem y los 70 escribía en tonos sombríos (mediana −0.16 a
−0.17). La bisagra es el <b>Retorno (1993–2002): +0.16</b>, y la etapa tardía sostiene
(+0.14). En la serie por décadas, sube de −0.21 (70s) a <b>+0.32 (2010s)</b>.</p>
<p>Ojo con una paradoja aparente: Tótem tiene la <i>mayor</i> proporción de alegría del
corpus (19.6%) y aun así tono negativo. No es contradicción: la alegría cuenta solo las
estrofas alegres; el tono es el <i>saldo</i> — y en Tótem las estrofas negativas (37%)
más que duplican a las positivas (17%). El joven Rada de banda ya tenía la alegría,
pero convivía con una carga oscura enorme; <b>el Rada maduro no sumó alegría — soltó
la oscuridad</b>.</p>

<h2>Perfil de emociones</h2>
<section class="fig">{html['emo']}</section>
<p>Los perfiles difieren significativamente (χ² = 58.4, p = 1.3×10⁻⁵; V = 0.16).
Rada lidera en alegría y a la vez queda arriba en tristeza — el candombe que festeja
y llora. Zitarrosa es el caso extremo opuesto: casi sin alegría.</p>

<h2>Chequeo con un método independiente</h2>
<section class="fig">{html['va']}</section>
<p>La capa léxica (normas de 14.031 palabras valoradas por hablantes nativos,
cobertura mediana 78%) ordena a los artistas de forma consistente con el modelo
(Spearman = 0.55) y <b>reproduce los polos: Rada y Mateo arriba, Cabrera y Zitarrosa
abajo</b>. Además, con el léxico todos los promedios dan positivos — la negatividad
absoluta del modelo es sesgo de nivel, no de orden: por eso este informe lee
diferencias relativas, nunca valores absolutos.</p>

<div class="caveats"><b>Limitaciones (pre-registradas):</b> resultados exploratorios,
sin validación con anotación humana en este dominio; el clasificador viene de tweets y
su tono absoluto tira a negativo (se leen diferencias relativas); el detector de ironía
satura fuera de dominio y no discrimina; cobertura de letras de Rada 42% del canon, con
faltantes concentrados en discos infantiles, proyectos en inglés e instrumentales
tardíos (el núcleo candombero histórico está bien cubierto); años de ediciones póstumas
de Mateo excluidos de la serie temporal; créditos de autoría verificados solo donde hay
fuente (el resto se asume propio y se marca).</div>

<p class="ficha-tec">Corpus: canon discográfico de MusicBrainz (107 álbumes de estudio,
1.295 pistas) × letras de Genius, letras.com y LRCLIB (1.575 letras; 607 en el corpus
principal tras exclusiones y autoría). Clasificación por estrofa con RoBERTuito
(pysentimiento: sentimiento, emociones, ironía), agregación ponderada con coros
deduplicados, capa léxica Stadthagen-González et al. (2016). Estadística: Kruskal-Wallis,
Dunn-Holm, delta de Cliff por décadas compartidas, IC bootstrap BCa. Python; todo
reproducible desde el repositorio. Las letras no se redistribuyen.</p>

</main></body></html>"""
    out = ROOT / "informe/informe.html"
    out.write_text(pagina)
    print(f"{out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
