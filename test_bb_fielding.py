import requests
from bs4 import BeautifulSoup
from bs4 import Comment

url = "https://www.baseball-reference.com/players/b/butlebi03.shtml"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, "html.parser")

table = soup.find("table", id="players_standard_fielding")
if table:
    for row in table.select("tfoot tr"):
        th = row.find("th")
        if th:
            print("TFOOT TH:", th.get_text(strip=True))
        for td in row.find_all("td"):
            if td.get("data-stat") == "G":
                print("  TD G:", td.get_text(strip=True))
