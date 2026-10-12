# METODO.md — Pre-registro del análisis (v1, 28/8/2026)

Reglas metodológicas fijadas **antes** de correr cualquier análisis. No se modifican después de ver resultados; cualquier cambio posterior se documenta como desviación del pre-registro con su justificación.

## 1. Objeto de estudio

Se analiza **lo que cada artista escribió** (autoría de la letra), no su repertorio cantado.

- **Sujeto:** Rubén Rada (obra 1965–2025, corpus cerrado). Incluye su producción con El Kinto y Tótem (fichas de banda), filtrada por autoría.
- **Set de comparación:** Jaime Roos, Alfredo Zitarrosa, Fernando Cabrera, Eduardo Mateo, Jorge Drexler.
- **Excluidos del análisis de autoría:** Daniel Viglietti y Eduardo Darnauchans (musicalizan/cantan mayormente textos de otros poetas). Podrán entrar en un subanálisis de repertorio, claramente separado.
- Cada canción lleva crédito de letrista en `data/catalogo/creditos.csv`. Covers quedan fuera del corpus principal. Coautorías se marcan con flag y el análisis se reporta **con y sin ellas** (sensibilidad).

## 2. Corpus y exclusiones

- Canon discográfico por artista desde MusicBrainz, cruzado con Wikipedia ES y Discogs.
- Año asignado = **año de primera grabación** (nunca el del compilado o regrabación).
- Tabla de exclusiones (se versiona): instrumentales; canciones en inglés/portugués (incl. Opa, que queda como subcorpus aparte, fuera del análisis principal); música infantil de Rada (post-1999, subcorpus aparte).
- Época 1 de Rada (El Kinto/Tótem, 1967–1973): si tras la limpieza queda con <10 canciones con letra y autoría propia, se fusiona con la solista temprana. La decisión se documenta antes de correr el análisis.
- Canciones **sin año** asignable: entran solo al análisis transversal, nunca al temporal.

## 3. Cobertura y sesgo de faltantes

- Denominador por artista = canciones del canon con autoría propia y letra en español.
- Umbral de cobertura: **60%** de letras obtenidas sobre ese denominador.
- **Regla fijada: no habrá transcripción manual (0 horas).** Si un artista queda bajo el umbral, se publica igual con una sección obligatoria de análisis del sesgo de faltantes: qué épocas/álbumes concentran los huecos y en qué dirección plausible sesgan el resultado.

## 4. Unidades y agregación

- **Unidad de clasificación:** estrofa/segmento de ≤100 tokens (el clasificador trunca a ~128 tokens; una canción entera no entra).
- **Unidad estadística:** la **canción** (las estrofas de una canción están correlacionadas; tratarlas como independientes sería pseudoreplicación).
- Valencia por canción = media **ponderada por longitud** de `P(POS) − P(NEG)` de sus estrofas, en [−1, 1]. Emociones por canción = proporción de estrofas por emoción dominante.
- **Coros repetidos:** para sentimiento se deduplican estrofas idénticas; la repetitividad se mide aparte (ratio de compresión gzip) como feature propia. Sensibilidad: el análisis principal se reporta también sin deduplicar.

## 5. Clasificadores

- **Candidato principal:** pysentimiento 0.7.3 — `robertuito-sentiment-analysis` (POS/NEG/NEU), `robertuito-emotion-analysis` (7 clases) y `robertuito-irony`. Entrenados con tweets en español (incluye subset Uruguay de TASS 2020). Se guardan siempre las probabilidades crudas en parquet.
- **Capa léxica dimensional:** normas nativas de valencia y arousal de Stadthagen-González et al. 2016 (14.031 palabras), vía lematización con spaCy `es_core_news_md`. Se reporta la **cobertura del léxico por canción**; canciones con cobertura <30% se marcan y se excluyen de la capa dimensional.
- **Ironía:** las canciones con flag de ironía se reportan siempre **con y sin ellas** en la agregación; nunca se descartan ad-hoc.
- Limitación declarada: ambos métodos vienen de dominios ajenos a la letra poética (tweets / normas de palabras aisladas).

## 6. Confianza en el clasificador (regla fijada: sin anotación manual)

- **No habrá gold standard anotado a mano.** pysentimiento es el clasificador principal por defecto, sin validación en dominio.
- Chequeo de robustez automático (sin trabajo humano): se compara el **ranking de artistas** según pysentimiento vs. según la capa léxica (correlación de Spearman entre rankings y entre valencias por canción). Si los dos métodos ordenan a los artistas igual, el resultado es más creíble; si divergen, la divergencia se reporta tal cual.
- Limitación declarada de forma prominente en el informe: los scores no fueron validados contra anotación humana en este dominio; los resultados se leen como **exploratorios**.

## 7. Estadística

- Comparación entre artistas sobre valencia por canción: Kruskal-Wallis + epsilon²; post-hoc de Dunn con corrección de Holm; **delta de Cliff** para cada par Rada-vs-X.
- El delta de Cliff se calcula también **restringido a las décadas de solapamiento** entre ambos artistas, y esa es la versión interpretable del informe (Zitarrosa termina en 1989, Drexler empieza en 1992: el delta crudo confunde artista con época).
- Control del confundido artista × década: comparación estratificada por década y regresión valencia ~ artista + década.
- IC bootstrap (BCa) para todo agregado. Las proporciones de clase se reportan advirtiendo el sesgo de classify-and-count.
- Emociones: chi-cuadrado + V de Cramér + residuos estandarizados, con IC bootstrap a nivel canción.
- Complementos descriptivos: diversidad léxica (MTLD, MATTR), longitud, repetitividad (gzip). Temas vía embeddings + clustering, solo como complemento cualitativo, no inferencial.

## 8. Publicación

- Repo público: **nunca** se versionan letras ni texto derivado de letras (`data/raw/`, `data/processed/`, `data/lexicons/` gitignorados).
- En el informe solo agregados, features derivadas y citas breves (≤2 versos) con fines de análisis.
