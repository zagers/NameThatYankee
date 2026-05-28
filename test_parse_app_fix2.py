import requests
from bs4 import BeautifulSoup
from bs4 import Comment

def parse_appearances_new(soup):
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
        tfoot = table.find("tfoot")
        if tfoot:
            for row in tfoot.find_all("tr"):
                th = row.find("th")
                text = th.get_text(strip=True) if th else ""
                if text and ("Yr" in text) and "(" not in text:
                    for td in row.find_all("td"):
                        stat = td.get("data-stat", "")
                        if stat.startswith("games_at_") and stat not in ["games_at_ph", "games_at_pr"]:
                            pos = stat.replace("games_at_", "").upper()
                            val = td.get_text(strip=True)
                            if val and val != "0":
                                pos_data[pos] = val
                    break # We found the career total row
    return pos_data

for p_url in ["b/butlebi03.shtml", "j/jeterde01.shtml", "r/riverma01.shtml"]:
    resp = requests.get(f"https://www.baseball-reference.com/players/{p_url}", headers={"User-Agent": "Mozilla/5.0"})
    s = BeautifulSoup(resp.content, "html.parser")
    print(p_url, "->", parse_appearances_new(s))
