import sqlite3
import os

def fix_block_system():
    db_path = os.path.join('instance', 'hotel.db')
    
    if not os.path.exists(db_path):
        print("Database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cursor.fetchall()]
        print("Existing columns:", columns)
        
        # Add missing fields
        required_fields = [
            ('is_blocked', 'INTEGER DEFAULT 0'),
            ('block_reason', 'TEXT'),
            ('blocked_at', 'DATETIME'),
            ('blocked_by', 'TEXT')
        ]
        
        for field_name, field_definition in required_fields:
            if field_name not in columns:
                try:
                    sql = f"ALTER TABLE customers ADD COLUMN {field_name} {field_definition}"
                    print(f"Adding field: {field_name}")
                    cursor.execute(sql)
                    print(f"Added field {field_name} successfully")
                except Exception as e:
                    print(f"Error adding field {field_name}: {str(e)}")
            else:
                print(f"Field {field_name} already exists")
        
        conn.commit()
        
        # Final check
        cursor.execute("PRAGMA table_info(customers)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print("Final columns:", final_columns)
        
        conn.close()
        print("Block fields added successfully!")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Starting block system fix...")
    success = fix_block_system()
    
    if success:
        print("Completed successfully!")
    else:
        print("Failed!")
