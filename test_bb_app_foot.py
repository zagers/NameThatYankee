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
        tfoot = table.find("tfoot")
        for row in tfoot.find_all("tr"):
            th = row.find("th")
            print("TH:", th.get_text(strip=True))
            for td in row.find_all("td"):
                stat = td.get("data-stat", "")
                if stat.startswith("games_at_dh"):
                    print("  DH:", td.get_text(strip=True))
