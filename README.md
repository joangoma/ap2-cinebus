# Cine Bus

Troba la peli que més s'adeqüi a les teves preferències i ves-hi utilitzant el bus de Barcelona! De moment només està disponible en cinemes de Barcelona, ampliem zones de Catalunya pròximament.



## Configuració del projecte

L'aplicació utilitza les següents llibreries (vegeu la versió exacte en el fitxer `requirements.txt`):

- `requests` per baixar-vos fitxers de dades.
- `beatifulsoup` per llegir els arbres HTML.
- `networkx` per a manipular grafs.
- `osmnx` per a obtenir grafs de llocs (Barcelona en aquest cas).
- `haversine` per a calcular distàncies entre coordenades.
- `staticmap` per pintar mapes.

- `rich` per l'aplicació de la terminal.

Totes es poden instal·lar amb `pip3 install`. Podeu utilitzar el fitxer `requirements.txt` per intal·lar-les totes alhora.

## Funcionament
Executeu el fitxer `demo.py` i, tot seguit, es crearan els grafs necessaris per calcular com anar de manera ràpida al cinema. Això pot tardar una mica. Tot seguit sortirà el menú principal amb totes les opcions. Esperem que trobeu una pel·licula que us agradi i hi pogueu arribar de la millor manera possible!