import sqlite3
from datetime import datetime

# إضافة عمود transfer_date إلى جدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    print("إضافة عمود transfer_date...")
    
    # التحقق من الأعمدة الموجودة
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'transfer_date' not in columns:
        # إضافة العمود
        cursor.execute("ALTER TABLE room_transfers ADD COLUMN transfer_date DATETIME DEFAULT CURRENT_TIMESTAMP")
        print("✅ تم إضافة عمود transfer_date")
        
        # تحديث السجلات الموجودة
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"UPDATE room_transfers SET transfer_date = '{current_time}' WHERE transfer_date IS NULL")
        print("✅ تم تحديث السجلات الموجودة")
        
        conn.commit()
    else:
        print("✅ عمود transfer_date موجود بالفعل")
    
    # التحقق النهائي
    cursor.execute("PRAGMA table_info(room_transfers)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"الأعمدة النهائية: {final_columns}")
    
    print("🎉 تم الإصلاح بنجاح!")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    conn.close()
