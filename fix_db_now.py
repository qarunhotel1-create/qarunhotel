#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

def fix_database():
    db_path = 'instance/hotel.db'
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Checking room_transfers table...")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='room_transfers'")
        if not cursor.fetchone():
            print("Creating room_transfers table...")
            cursor.execute("""
                CREATE TABLE room_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booking_id INTEGER NOT NULL,
                    from_room_id INTEGER NOT NULL,
                    to_room_id INTEGER NOT NULL,
                    transfer_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    transferred_by_user_id INTEGER NOT NULL DEFAULT 1,
                    reason TEXT,
                    notes TEXT,
                    FOREIGN KEY (booking_id) REFERENCES bookings (id),
                    FOREIGN KEY (from_room_id) REFERENCES rooms (id),
                    FOREIGN KEY (to_room_id) REFERENCES rooms (id),
                    FOREIGN KEY (transferred_by_user_id) REFERENCES users (id)
                )
            """)
            print("Table created successfully!")
        else:
            print("Table exists, checking columns...")
            
            # Get current columns
            cursor.execute("PRAGMA table_info(room_transfers)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Current columns: {columns}")
            
            # Add missing columns
            if 'transfer_time' not in columns:
                print("Adding transfer_time column...")
                cursor.execute("ALTER TABLE room_transfers ADD COLUMN transfer_time DATETIME DEFAULT CURRENT_TIMESTAMP")
                cursor.execute("UPDATE room_transfers SET transfer_time = datetime('now') WHERE transfer_time IS NULL")
            
            if 'transferred_by_user_id' not in columns:
                print("Adding transferred_by_user_id column...")
                cursor.execute("ALTER TABLE room_transfers ADD COLUMN transferred_by_user_id INTEGER DEFAULT 1")
                cursor.execute("UPDATE room_transfers SET transferred_by_user_id = 1 WHERE transferred_by_user_id IS NULL")
            
            if 'reason' not in columns:
                print("Adding reason column...")
                cursor.execute("ALTER TABLE room_transfers ADD COLUMN reason TEXT")
            
            if 'notes' not in columns:
                print("Adding notes column...")
                cursor.execute("ALTER TABLE room_transfers ADD COLUMN notes TEXT")
        
        conn.commit()
        
        # Final check
        cursor.execute("PRAGMA table_info(room_transfers)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"Final columns: {final_columns}")
        
        conn.close()
        print("Database fixed successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    fix_database()
