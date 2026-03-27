import sqlite3
import os

# مسار قاعدة البيانات
db_path = 'instance/hotel.db'

if os.path.exists(db_path):
    print(f"🔧 تحديث قاعدة البيانات: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # التحقق من وجود العمود
        cursor.execute("PRAGMA table_info(payments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("📝 إضافة عمود user_id...")
            cursor.execute("ALTER TABLE payments ADD COLUMN user_id INTEGER")
            
            # تحديث الدفعات الموجودة
            print("🔄 تحديث الدفعات الموجودة...")
            cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
            admin_row = cursor.fetchone()
            
            if admin_row:
                admin_id = admin_row[0]
                cursor.execute("UPDATE payments SET user_id = ? WHERE user_id IS NULL", (admin_id,))
                print(f"✅ تم تحديث {cursor.rowcount} دفعة")
            
            conn.commit()
            print("✅ تم إضافة العمود بنجاح!")
        else:
            print("ℹ️ العمود موجود بالفعل")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print(f"❌ لم يتم العثور على قاعدة البيانات: {db_path}")
