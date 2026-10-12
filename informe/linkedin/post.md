# Posteo para LinkedIn (borrador)

🎶🇺🇾 ¿Quién escribe las letras más luminosas del cancionero uruguayo?

La partida de Rubén Rada me dejó con ganas de responder esta pregunta con datos. Armé un corpus de 607 canciones de seis grandes de nuestra música — Rada, Zitarrosa, Mateo, Cabrera, Roos y Drexler — y analicé el tono emocional de cada letra, estrofa por estrofa, con un modelo de lenguaje en español.

Lo que encontré:

☀️ Rada es el más luminoso del grupo: casi 5 veces más estrofas de alegría que Zitarrosa (17.8% vs 3.6%) — y sin resignar tristeza, en la que también está arriba. Amplitud emocional pura: el candombe que festeja y llora a la vez.

🌑 En el otro polo, Zitarrosa y Cabrera escriben el cancionero más sombrío. La solemnidad de la milonga, medida en números.

📈 El arco de Rada es hermoso: el de los 70 escribía oscuro (−0.21), el de los 2010 luminoso (+0.32). La bisagra fue su regreso en los 90: el Rada consagrado es el Rada alegre.

⚖️ Y un detalle metodológico que me encantó: comparando solo las décadas en que ambos grabaron, la mitad de la diferencia entre Rada y Zitarrosa resultó ser de época, no de artista. Controlar confundidos importa.

Todo en Python: corpus armado desde MusicBrainz y tres fuentes de letras, reglas de análisis pre-registradas antes de correr nada, estadística no paramétrica, y un chequeo con un método léxico independiente (el ranking se sostiene). Resultados exploratorios, con sus limitaciones documentadas — las letras no son tweets y los modelos se toman con pinzas.

Gracias Rada por tanta luz 🕯️

#DataScience #NLP #Python #MúsicaUruguaya #Rada #Candombe

---
*Adjuntar: 01_tono.png, 02_arco.png, 03_alegria.png (en esta misma carpeta).*
