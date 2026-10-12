"""Post-hoc de Dunn (tras Kruskal-Wallis) con corrección por empates y ajuste de p.

Implementación propia: scikit-posthocs 0.16.0 es incompatible con
statsmodels>=0.15 (importa de statsmodels.sandbox, eliminado). La equivalencia
con el test de Mann-Whitney asintótico en el caso de 2 grupos se verifica en
src/smoke_test.py.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


def posthoc_dunn(df, val_col, group_col, p_adjust="holm"):
    """Matriz simétrica de p-valores del test de Dunn entre todos los pares de grupos.

    p_adjust: método de statsmodels.multipletests ('holm', 'bonferroni', ...) o None.
    """
    datos = df[[val_col, group_col]].dropna()
    valores = datos[val_col].to_numpy(dtype=float)
    grupos = datos[group_col].to_numpy()
    nombres = list(pd.unique(grupos))
    n = len(valores)
    rangos = stats.rankdata(valores)

    _, conteos = np.unique(valores, return_counts=True)
    correccion_empates = (conteos**3 - conteos).sum() / (12 * (n - 1))

    media_rango = {g: rangos[grupos == g].mean() for g in nombres}
    tam = {g: int((grupos == g).sum()) for g in nombres}

    pares, zs = [], []
    for i, gi in enumerate(nombres):
        for gj in nombres[i + 1:]:
            var = (n * (n + 1) / 12 - correccion_empates) * (1 / tam[gi] + 1 / tam[gj])
            zs.append((media_rango[gi] - media_rango[gj]) / np.sqrt(var))
            pares.append((gi, gj))

    p = 2 * stats.norm.sf(np.abs(zs))
    if p_adjust:
        p = multipletests(p, method=p_adjust)[1]

    m = pd.DataFrame(np.ones((len(nombres), len(nombres))), index=nombres, columns=nombres)
    for (gi, gj), pv in zip(pares, p):
        m.loc[gi, gj] = m.loc[gj, gi] = pv
    return m
