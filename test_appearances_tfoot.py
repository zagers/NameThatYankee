import requests
from bs4 import BeautifulSoup
from bs4 import Comment

url = "https://www.baseball-reference.com/players/j/jeterde01.shtml"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, "html.parser")

comments = soup.find_all(string=lambda text: isinstance(text, Comment))
for comment in comments:
    if 'id="appearances"' in comment:
        c_soup = BeautifulSoup(comment, "html.parser")
        table = c_soup.find("table", id="appearances")
        tfoot = table.find("tfoot")
        if tfoot:
            for row in tfoot.find_all("tr"):
                for th in row.find_all("th"):
                    print("TH:", th.get_text(strip=True))
                for td in row.find_all("td"):
                    print("TD:", td.get("data-stat"), td.get_text(strip=True))
