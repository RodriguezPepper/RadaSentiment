"""Smoke test del entorno: importa y usa mínimamente cada librería pineada.

Condición para dar el stack por congelado (METODO.md / Fase 0).
Uso: .venv/bin/python src/smoke_test.py
"""

import sys
import tempfile
from pathlib import Path

FALLOS = []
TMP = Path(tempfile.mkdtemp(prefix="smoke_"))


def paso(nombre):
    def deco(fn):
        try:
            fn()
            print(f"  OK  {nombre}")
        except Exception as e:
            print(f"FALLO {nombre}: {type(e).__name__}: {e}")
            FALLOS.append(nombre)
    return deco


@paso("numpy/pandas/pyarrow (DataFrame + parquet ida y vuelta)")
def _():
    import numpy as np
    import pandas as pd

    df = pd.DataFrame({"artista": ["rada", "roos"] * 5, "valencia": np.linspace(-1, 1, 10)})
    p = TMP / "t.parquet"
    df.to_parquet(p)
    assert len(pd.read_parquet(p)) == 10


@paso("scipy (bootstrap IC)")
def _():
    import numpy as np
    from scipy import stats

    r = stats.bootstrap((np.random.default_rng(1).normal(size=50),), np.median, n_resamples=200)
    assert r.confidence_interval.low < r.confidence_interval.high


@paso("posthoc de Dunn propio (validado contra Mann-Whitney en 2 grupos)")
def _():
    import numpy as np
    import pandas as pd
    from scipy import stats

    from estadistica.posthoc import posthoc_dunn

    rng = np.random.default_rng(2)
    a = np.round(rng.normal(0, 1, 40), 1)  # redondeo: fuerza empates
    b = np.round(rng.normal(0.8, 1, 35), 1)
    df = pd.DataFrame({"v": np.concatenate([a, b]), "g": ["a"] * 40 + ["b"] * 35})
    p_dunn = posthoc_dunn(df, "v", "g", p_adjust=None).loc["a", "b"]
    p_mwu = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic", use_continuity=False).pvalue
    assert abs(p_dunn - p_mwu) < 1e-8, (p_dunn, p_mwu)
    df3 = pd.DataFrame({"v": rng.normal(size=30), "g": ["a", "b", "c"] * 10})
    m = posthoc_dunn(df3, "v", "g", p_adjust="holm")
    assert m.shape == (3, 3) and m.loc["a", "b"] == m.loc["b", "a"]


@paso("statsmodels (OLS)")
def _():
    import numpy as np
    import statsmodels.api as sm

    x = sm.add_constant(np.arange(10.0))
    sm.OLS(np.arange(10.0) * 2 + 1, x).fit()


@paso("scikit-learn (PCA)")
def _():
    import numpy as np
    from sklearn.decomposition import PCA

    PCA(n_components=2).fit_transform(np.random.default_rng(0).normal(size=(20, 5)))


@paso("lexicalrichness (MTLD)")
def _():
    from lexicalrichness import LexicalRichness

    LexicalRichness("quien va a cantar esta noche en el barrio sur la voz del candombe").mtld()


@paso("matplotlib/seaborn (violinplot a png)")
def _():
    import matplotlib

    matplotlib.use("Agg")
    import pandas as pd
    import seaborn as sns

    df = pd.DataFrame({"g": ["a"] * 20 + ["b"] * 20, "v": list(range(20)) * 2})
    ax = sns.violinplot(data=df, x="g", y="v")
    ax.figure.savefig(TMP / "t.png")


@paso("plotly (figura a html)")
def _():
    import plotly.express as px

    px.scatter(x=[1, 2, 3], y=[3, 1, 2]).write_html(TMP / "t.html")


@paso("spacy es_core_news_md (lematización)")
def _():
    import spacy

    nlp = spacy.load("es_core_news_md")
    lemas = [t.lemma_ for t in nlp("las canciones tristes del invierno")]
    assert "canción" in lemas


@paso("lyricsgenius (import + instanciación)")
def _():
    import lyricsgenius

    lyricsgenius.Genius("token_de_prueba")  # sin llamada de red


@paso("pysentimiento (inferencia real de sentimiento)")
def _():
    from pysentimiento import create_analyzer

    an = create_analyzer(task="sentiment", lang="es")
    r1 = an.predict("qué alegría enorme, esta noche tocamos candombe")
    r2 = an.predict("me quedé solo y triste en el invierno")
    assert r1.output == "POS" and r2.output == "NEG", (r1.output, r2.output)


@paso("sentence-transformers (encode multilingüe)")
def _():
    from sentence_transformers import SentenceTransformer

    m = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    assert m.encode(["una canción de candombe"]).shape[0] == 1


if FALLOS:
    print(f"\n{len(FALLOS)} fallos: {FALLOS}")
    sys.exit(1)
print("\nEntorno OK — stack congelado.")
