import sqlite3
import os

# مسار قاعدة البيانات
db_path = 'instance/hotel.db'

print("إصلاح جدول room_transfers...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # التحقق من الأعمدة الموجودة
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"الأعمدة الموجودة: {columns}")
    
    # إضافة الأعمدة المفقودة
    if 'transfer_time' not in columns:
        cursor.execute("ALTER TABLE room_transfers ADD COLUMN transfer_time DATETIME")
        cursor.execute("UPDATE room_transfers SET transfer_time = datetime('now') WHERE transfer_time IS NULL")
        print("تم إضافة عمود transfer_time")
    
    if 'transferred_by_user_id' not in columns:
        cursor.execute("ALTER TABLE room_transfers ADD COLUMN transferred_by_user_id INTEGER")
        cursor.execute("UPDATE room_transfers SET transferred_by_user_id = 1 WHERE transferred_by_user_id IS NULL")
        print("تم إضافة عمود transferred_by_user_id")
    
    if 'reason' not in columns:
        cursor.execute("ALTER TABLE room_transfers ADD COLUMN reason TEXT")
        print("تم إضافة عمود reason")
    
    if 'notes' not in columns:
        cursor.execute("ALTER TABLE room_transfers ADD COLUMN notes TEXT")
        print("تم إضافة عمود notes")
    
    conn.commit()
    
    # التحقق النهائي
    cursor.execute("PRAGMA table_info(room_transfers)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"الأعمدة النهائية: {final_columns}")
    
    conn.close()
    print("تم الإصلاح بنجاح!")
    
except Exception as e:
    print(f"خطأ: {e}")
