import requests
from bs4 import BeautifulSoup
from bs4 import Comment

url = "https://www.baseball-reference.com/players/b/butlebi03.shtml"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, "html.parser")

pos_data = {}
comments = soup.find_all(string=lambda text: isinstance(text, Comment))
table = None
for comment in comments:
    if 'id="appearances"' in comment:
        c_soup = BeautifulSoup(comment, "html.parser")
        table = c_soup.find("table", id="appearances")
        break

if not table:
    table = soup.find("table", id="appearances")

if table:
    for row in table.select("tbody tr"):
        th = row.find("th")
        if not th: continue
        pos = th.get_text(strip=True)
        if pos in ["Total", "Year", "Age", "Team", "Lg"]: continue
        g_td = row.find("td", {"data-stat": "G_def"}) or row.find("td", {"data-stat": "G"})
        if g_td:
            pos_data[pos] = g_td.get_text(strip=True)

print("Positions:", pos_data)
