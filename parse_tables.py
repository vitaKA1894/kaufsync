import sqlite3
import json

import markdown
from bs4 import BeautifulSoup
import uuid
import re

html = markdown.markdown(open("spec_database.md").read(), extensions=["tables"])
soup = BeautifulSoup(html, "html.parser")

def extract_tables(soup):
    tables = []
    for table in soup.find_all("table"):
        headers = [th.text.strip() for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.text.strip() for td in tr.find_all("td")]
            if cells:
                rows.append(dict(zip(headers, cells)))
        tables.append(rows)
    return tables

tables = extract_tables(soup)

def parse_tags(tag_str):
    if not tag_str:
        return []
    return [t.strip() for t in re.split(r",", tag_str) if t.strip()]

conn = sqlite3.connect("taxonomy.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS taxonomy_items (
    item_id TEXT PRIMARY KEY,
    primary_name TEXT NOT NULL,
    search_aliases JSON,
    category_name TEXT,
    available_tags JSON
)
""")
conn.commit()

for table in tables:
    for row in table:
        item_id = str(uuid.uuid4())
        primary_name = row.get("Artikelbezeichnung (Type-Ahead Ziel)", "")
        category = row.get("Primäre Warengruppe", "")
        quantities = parse_tags(row.get("Typische Mengen-Tags (Numerisch / Gebinde)", ""))
        constellations = parse_tags(row.get("Spezifische Konstellations-Tags (Ausprägungen)", ""))

        # very basic aliases processing
        aliases = []
        if "/" in primary_name:
            parts = [p.strip() for p in primary_name.split("/")]
            primary_name = parts[0]
            aliases = parts[1:]

        tags = {
            "quantities": quantities,
            "constellations": constellations,
            "global_meta": ["Dringend", "Angebot", "Wenn's passt"]
        }

        cursor.execute(
            "INSERT INTO taxonomy_items (item_id, primary_name, search_aliases, category_name, available_tags) VALUES (?, ?, ?, ?, ?)",
            (item_id, primary_name, json.dumps(aliases), category, json.dumps(tags))
        )
conn.commit()
conn.close()
print("Taxonomy seeded!")
