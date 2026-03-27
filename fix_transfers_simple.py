import sqlite3

# إصلاح سريع لجدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    # التحقق من الجدول
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='room_transfers'")
    result = cursor.fetchone()
    
    if result:
        print("Table exists:", result[0])
        
        # إضافة الأعمدة المفقودة
        try:
            cursor.execute("ALTER TABLE room_transfers ADD COLUMN transfer_time DATETIME DEFAULT CURRENT_TIMESTAMP")
            print("Added transfer_time column")
        except:
            print("transfer_time column already exists")
        
        try:
            cursor.execute("ALTER TABLE room_transfers ADD COLUMN transferred_by_user_id INTEGER DEFAULT 1")
            print("Added transferred_by_user_id column")
        except:
            print("transferred_by_user_id column already exists")
        
        try:
            cursor.execute("ALTER TABLE room_transfers ADD COLUMN reason TEXT")
            print("Added reason column")
        except:
            print("reason column already exists")
        
        try:
            cursor.execute("ALTER TABLE room_transfers ADD COLUMN notes TEXT")
            print("Added notes column")
        except:
            print("notes column already exists")
    else:
        # إنشاء الجدول من الصفر
        cursor.execute("""
            CREATE TABLE room_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                from_room_id INTEGER NOT NULL,
                to_room_id INTEGER NOT NULL,
                transfer_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                transferred_by_user_id INTEGER DEFAULT 1,
                reason TEXT,
                notes TEXT
            )
        """)
        print("Created room_transfers table")
    
    # تحديث السجلات الفارغة
    cursor.execute("UPDATE room_transfers SET transfer_time = datetime('now') WHERE transfer_time IS NULL")
    cursor.execute("UPDATE room_transfers SET transferred_by_user_id = 1 WHERE transferred_by_user_id IS NULL")
    
    conn.commit()
    print("Database fixed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
