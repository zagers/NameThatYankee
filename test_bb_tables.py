import requests
from bs4 import BeautifulSoup
from bs4 import Comment

url = "https://www.baseball-reference.com/players/b/butlebi03.shtml"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.content, "html.parser")

tables = soup.find_all("table")
for t in tables:
    print("Table ID:", t.get("id"))

comments = soup.find_all(string=lambda text: isinstance(text, Comment))
for comment in comments:
    if "table" in comment:
        c_soup = BeautifulSoup(comment, "html.parser")
        tables = c_soup.find_all("table")
        for t in tables:
            print("Comment Table ID:", t.get("id"))

