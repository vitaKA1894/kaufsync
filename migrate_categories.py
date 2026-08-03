import sqlite3
import os

def migrate():
    db_paths = ['backend/kaufsync.db', 'backend/shopping_list.db']

    for db_path in db_paths:
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            print(f"Skipping {db_path} (not found or empty)")
            continue

        print(f"Migrating {db_path}...")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if items table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
            if not cursor.fetchone():
                print(f"  Table 'items' not found in {db_path}")
                continue

            cursor.execute("UPDATE items SET category = 'Sonstiges' WHERE category = 'Allgemein'")
            rowcount = cursor.rowcount
            conn.commit()

            print(f"  Migrated {rowcount} items from 'Allgemein' to 'Sonstiges'.")

            cursor.execute("SELECT count(*) FROM items WHERE category = 'Allgemein'")
            remaining = cursor.fetchone()[0]
            print(f"  Remaining items with category 'Allgemein': {remaining}")

        except sqlite3.Error as e:
            print(f"  Database error: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

if __name__ == '__main__':
    migrate()
