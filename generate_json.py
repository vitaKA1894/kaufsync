import sqlite3
import json

conn = sqlite3.connect("backend/taxonomy.db")
cursor = conn.cursor()
cursor.execute("SELECT item_id, primary_name, search_aliases, category_name, available_tags FROM taxonomy_items")
rows = cursor.fetchall()

taxonomy = []
for row in rows:
    taxonomy.append({
        "id": row[0],
        "name": row[1],
        "aliases": json.loads(row[2]) if row[2] else [],
        "category": row[3],
        "tags": json.loads(row[4]) if row[4] else {}
    })

with open("frontend/src/assets/taxonomy.json", "w") as f:
    json.dump(taxonomy, f, indent=2, ensure_ascii=False)

conn.close()
print("Generated frontend/src/assets/taxonomy.json")
