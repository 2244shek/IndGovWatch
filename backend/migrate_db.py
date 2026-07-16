import sqlite3
import os

def migrate():
    db_path = "./indgovwatch.db"
    # If not found directly, check relative to the file location
    if not os.path.exists(db_path):
        alternative = os.path.abspath(os.path.join(os.path.dirname(__file__), "indgovwatch.db"))
        if os.path.exists(alternative):
            db_path = alternative
        else:
            print(f"Database file not found at {db_path} or {alternative}. It will be created when the FastAPI app starts.")
            return

    print(f"Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check existing columns in regulations
    cursor.execute("PRAGMA table_info(regulations);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "easy_view_headline" not in columns:
        print("Adding easy_view_headline to regulations table...")
        cursor.execute("ALTER TABLE regulations ADD COLUMN easy_view_headline TEXT;")
        
    if "easy_view_explanation" not in columns:
        print("Adding easy_view_explanation to regulations table...")
        cursor.execute("ALTER TABLE regulations ADD COLUMN easy_view_explanation TEXT;")
        
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
