import sqlite3
import os

# Path to the SQLite database file
db_path = os.path.join('instance', 'hotel.db')

# Check if the database file exists
if not os.path.exists(db_path):
    print(f"Error: Database file not found at {db_path}")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the gender column already exists
    cursor.execute("PRAGMA table_info(customers)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'gender' not in column_names:
        # Add the gender column to the customers table
        print("Adding gender column to customers table...")
        cursor.execute("ALTER TABLE customers ADD COLUMN gender VARCHAR(10)")
        conn.commit()
        print("Gender column added successfully!")
    else:
        print("Gender column already exists in the customers table.")
        
    # Verify the column was added
    cursor.execute("PRAGMA table_info(customers)")
    columns = cursor.fetchall()
    print("\nCustomers table columns:")
    for column in columns:
        print(f"  {column[1]} ({column[2]})")
        
except sqlite3.Error as e:
    print(f"SQLite error: {e}")
    conn.rollback()
finally:
    # Close the connection
    conn.close()