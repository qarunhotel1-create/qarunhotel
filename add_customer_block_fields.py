"""
إضافة حقول الحظر للعملاء - محسن للعمل مع SQLite
"""
import sqlite3
import os

def add_block_fields():
    # مسار قاعدة البيانات
    db_path = os.path.join('instance', 'hotel.db')
    
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة في: {db_path}")
        return
    
    try:
        # الاتصال بقاعدة البيانات مباشرة
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # فحص الحقول الموجودة
        cursor.execute("PRAGMA table_info(customers)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"الحقول الموجودة: {existing_columns}")
        
        # إضافة الحقول إذا لم تكن موجودة
        fields_to_add = [
            ("is_blocked", "INTEGER DEFAULT 0"),
            ("block_reason", "TEXT"),
            ("blocked_at", "DATETIME"),
            ("blocked_by", "TEXT")
        ]
        
        for field_name, field_type in fields_to_add:
            if field_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE customers ADD COLUMN {field_name} {field_type}")
                    print(f"✅ تم إضافة حقل {field_name}")
                except Exception as e:
                    print(f"❌ خطأ في إضافة حقل {field_name}: {str(e)}")
            else:
                print(f"⚠️ حقل {field_name} موجود بالفعل")
        
        # تحديث القيم الافتراضية
        cursor.execute("UPDATE customers SET is_blocked = 0 WHERE is_blocked IS NULL")
        affected_rows = cursor.rowcount
        print(f"تم تحديث {affected_rows} صف بالقيم الافتراضية")
        
        # حفظ التغييرات
        conn.commit()
        
        # فحص النتيجة النهائية
        cursor.execute("PRAGMA table_info(customers)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"الحقول النهائية: {final_columns}")
        
        print("✅ تم إضافة جميع حقول الحظر بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ عام: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_block_fields()
