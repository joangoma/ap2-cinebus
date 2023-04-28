# FITXER PER MIRAR QUE ELS CODIS DEL CHAT GPT FUNCIONIN COM DIU XD

import json

from bs4 import BeautifulSoup

html = """
<ul>
  <li><em data-times="[15:30, 17:17]" id="96064690">15:30</em></li>
  <li><em data-times="[18:00, 20:00]" id="96064691">18:00</em></li>
  <li><em data-times="[22:15, 23:45]" id="96064692">22:15</em></li>
</ul>
"""

soup = BeautifulSoup(html, "html.parser")
ul = soup.find("ul")
ems = ul.find_all("em")

for em in ems:
    times = em["data-times"][1:-1]
    times = [int(t) for t in times_str.split(",")]
