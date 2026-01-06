import sqlite3
import database as db

DB_NAME = 'keuangan.db'

def migrate():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if user_id column exists
    try:
        c.execute('SELECT user_id FROM transaksi LIMIT 1')
        print("Column user_id already exists.")
    except sqlite3.OperationalError:
        print("Adding user_id column...")
        # Add column
        c.execute('ALTER TABLE transaksi ADD COLUMN user_id INTEGER')
        
        # Assign all existing transactions to the first user (usually ID 1)
        # Assuming user with ID 1 exists. If not, they will be orphaned until assigned.
        c.execute('UPDATE transaksi SET user_id = 1 WHERE user_id IS NULL')
        
        conn.commit()
        print("Migration complete. user_id added and populated with default 1.")
        
    conn.close()

if __name__ == '__main__':
    migrate()
