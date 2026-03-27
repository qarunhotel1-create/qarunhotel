import sqlite3

# إضافة عمود transferred_by إلى جدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    print("إضافة عمود transferred_by...")
    
    # التحقق من الأعمدة الموجودة
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"الأعمدة الموجودة: {columns}")
    
    if 'transferred_by' not in columns:
        # إضافة العمود
        cursor.execute("ALTER TABLE room_transfers ADD COLUMN transferred_by TEXT DEFAULT 'admin'")
        print("✅ تم إضافة عمود transferred_by")
        
        # تحديث السجلات الموجودة
        cursor.execute("UPDATE room_transfers SET transferred_by = 'admin' WHERE transferred_by IS NULL")
        print("✅ تم تحديث السجلات الموجودة")
        
        conn.commit()
    else:
        print("✅ عمود transferred_by موجود بالفعل")
    
    # التحقق النهائي
    cursor.execute("PRAGMA table_info(room_transfers)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"الأعمدة النهائية: {final_columns}")
    
    print("🎉 تم الإصلاح بنجاح!")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    conn.close()
