import sqlite3
from datetime import datetime

# إصلاح أعمدة جدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    print("إصلاح جدول room_transfers...")
    
    # التحقق من الأعمدة الموجودة
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"الأعمدة الموجودة: {columns}")
    
    # إضافة الأعمدة المفقودة
    required_columns = {
        'from_room_check_in': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'from_room_check_out': 'DATETIME DEFAULT CURRENT_TIMESTAMP', 
        'to_room_check_in': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'transfer_time': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
        'transferred_by_user_id': 'INTEGER DEFAULT 1',
        'reason': 'TEXT',
        'notes': 'TEXT'
    }
    
    for column_name, column_type in required_columns.items():
        if column_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE room_transfers ADD COLUMN {column_name} {column_type}")
                print(f"تم إضافة عمود: {column_name}")
            except Exception as e:
                print(f"خطأ في إضافة عمود {column_name}: {e}")
        else:
            print(f"عمود {column_name} موجود بالفعل")
    
    # تحديث السجلات الفارغة
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    update_queries = [
        f"UPDATE room_transfers SET from_room_check_in = '{current_time}' WHERE from_room_check_in IS NULL",
        f"UPDATE room_transfers SET from_room_check_out = '{current_time}' WHERE from_room_check_out IS NULL",
        f"UPDATE room_transfers SET to_room_check_in = '{current_time}' WHERE to_room_check_in IS NULL",
        f"UPDATE room_transfers SET transfer_time = '{current_time}' WHERE transfer_time IS NULL",
        "UPDATE room_transfers SET transferred_by_user_id = 1 WHERE transferred_by_user_id IS NULL"
    ]
    
    for query in update_queries:
        try:
            cursor.execute(query)
            print(f"تم تحديث السجلات: {query.split('SET')[1].split('=')[0].strip()}")
        except Exception as e:
            print(f"خطأ في التحديث: {e}")
    
    conn.commit()
    
    # التحقق النهائي
    cursor.execute("PRAGMA table_info(room_transfers)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"\nالأعمدة النهائية: {final_columns}")
    
    print("\nتم إصلاح الجدول بنجاح!")
    
except Exception as e:
    print(f"خطأ عام: {e}")
finally:
    conn.close()
