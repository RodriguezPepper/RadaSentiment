# Comparación estadística — valencia por canción

Corpus principal: 572 canciones de 6 solistas (+ 35 de El Kinto/Tótem para las épocas de Rada).

## Kruskal-Wallis
H = 41.45, p = 7.59e-08, epsilon² = 0.073 (n=572, k=6)

## Medianas con IC bootstrap BCa 95%

| artista | n | mediana | IC 95% |
|---|---|---|---|
| ruben_rada | 96 | -0.013 | [-0.103, +0.138] |
| eduardo_mateo | 62 | -0.029 | [-0.116, +0.076] |
| jorge_drexler | 138 | -0.063 | [-0.086, -0.017] |
| jaime_roos | 72 | -0.172 | [-0.308, -0.058] |
| fernando_cabrera | 143 | -0.224 | [-0.293, -0.176] |
| alfredo_zitarrosa | 61 | -0.272 | [-0.403, -0.179] |

## Post-hoc de Dunn (p ajustada Holm)

|                   |   alfredo_zitarrosa |   eduardo_mateo |   fernando_cabrera |   jaime_roos |   jorge_drexler |   ruben_rada |
|:------------------|--------------------:|----------------:|-------------------:|-------------:|----------------:|-------------:|
| alfredo_zitarrosa |              1      |          0.0074 |             1      |       0.7806 |          0.0011 |       0.001  |
| eduardo_mateo     |              0.0074 |          1      |             0.0031 |       0.3252 |          1      |       1      |
| fernando_cabrera  |              1      |          0.0031 |             1      |       0.7806 |          0.0001 |       0.0001 |
| jaime_roos        |              0.7806 |          0.3252 |             0.7806 |       1      |          0.1595 |       0.1272 |
| jorge_drexler     |              0.0011 |          1      |             0.0001 |       0.1595 |          1      |       1      |
| ruben_rada        |              0.001  |          1      |             0.0001 |       0.1272 |          1      |       1      |

## Delta de Cliff: Rada vs. cada comparador

| par | delta crudo | delta décadas solapadas | décadas | interpretación (restr.) |
|---|---|---|---|---|
| rada vs jaime_roos | +0.206 | +0.191 | 1970, 1980, 1990, 2000, 2010 | chico |
| rada vs alfredo_zitarrosa | +0.320 | +0.158 | 1970, 1980 | chico |
| rada vs fernando_cabrera | +0.310 | +0.333 | 1980, 1990, 2000, 2010 | mediano |
| rada vs eduardo_mateo | +0.027 | -0.023 | 1970, 1990, 2000 | insignificante |
| rada vs jorge_drexler | +0.086 | +0.172 | 1990, 2000, 2010, 2020 | chico |

## Mediana de valencia por ficha × década (celdas con n>=5)

| ficha             |    1960 |    1970 |    1980 |    1990 |    2000 |    2010 |    2020 |
|:------------------|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| alfredo_zitarrosa |  -0.394 |  -0.271 |  -0.403 | nan     | nan     | nan     | nan     |
| eduardo_mateo     | nan     |  -0.385 | nan     |   0.061 |   0.071 | nan     | nan     |
| el_kinto          | nan     |  -0.273 | nan     | nan     | nan     | nan     | nan     |
| fernando_cabrera  | nan     | nan     |  -0.136 |  -0.239 |  -0.219 |  -0.197 | nan     |
| jaime_roos        | nan     |  -0.28  |  -0.316 |   0.052 |  -0.248 |   0.191 | nan     |
| jorge_drexler     | nan     | nan     | nan     |  -0.069 |  -0.028 |  -0.087 |  -0.027 |
| ruben_rada        | nan     |  -0.21  |  -0.081 |   0.049 |  -0.036 |   0.319 |   0.139 |
| totem             | nan     |  -0.158 | nan     | nan     | nan     | nan     | nan     |

## Rada por época (incluye El Kinto y Tótem en la época 1)

| epoca            |   n |   mediana |   alegria |   tristeza |
|:-----------------|----:|----------:|----------:|-----------:|
| El Kinto / Tótem |  39 |    -0.16  |     0.183 |      0.216 |
| Solista 70s-80s  |  32 |    -0.167 |     0.124 |      0.229 |
| Retorno          |  27 |     0.161 |     0.232 |      0.183 |
| Tardía           |  28 |     0.136 |     0.168 |      0.165 |

## Emoción dominante por canción
chi² = 58.4 (gl=20), p = 1.26e-05, V de Cramér = 0.160

| ficha             |   anger |   fear |   joy |   others |   sadness |
|:------------------|--------:|-------:|------:|---------:|----------:|
| alfredo_zitarrosa |       0 |      0 |     0 |       52 |         9 |
| eduardo_mateo     |       1 |      0 |     5 |       52 |         4 |
| fernando_cabrera  |       2 |      1 |     4 |      131 |         5 |
| jaime_roos        |       1 |      0 |    10 |       59 |         2 |
| jorge_drexler     |       0 |      0 |     4 |      133 |         1 |
| ruben_rada        |       2 |      0 |    14 |       70 |        10 |

## Sensibilidad
- Ranking con vs. sin deduplicar coros: Spearman = 1.000
- Ranking total vs. solo canciones <=50% irónicas (n=96): Spearman = -0.086
- ADVERTENCIA pre-registrada: el detector de ironía satura fuera de dominio (mediana 83% de estrofas irónicas en todos los artistas); el corte con/sin ironía es poco informativo y se reporta solo por completitud.
