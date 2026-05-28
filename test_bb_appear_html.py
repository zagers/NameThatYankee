import requests
from bs4 import BeautifulSoup
from bs4 import Comment

url = "https://www.baseball-reference.com/players/b/butlebi03.shtml"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, "html.parser")

comments = soup.find_all(string=lambda text: isinstance(text, Comment))
for comment in comments:
    if 'id="appearances"' in comment:
        c_soup = BeautifulSoup(comment, "html.parser")
        table = c_soup.find("table", id="appearances")
        print(table.select("tbody tr th")[0:5] if table else "No table body th")
        for row in table.select("tbody tr"):
            th = row.find("th")
            if not th: continue
            print("TH:", th.get_text(strip=True))
            for td in row.find_all("td"):
                print("  TD:", td.get("data-stat"), "=", td.get_text(strip=True))
        break
