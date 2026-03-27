"""
إضافة حقول الحظر مباشرة لقاعدة البيانات SQLite
"""
import sqlite3
import os

def fix_customer_block_db():
    # البحث عن قاعدة البيانات
    possible_paths = [
        'instance/hotel.db',
        'hotel.db',
        'instance\\hotel.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ لم يتم العثور على قاعدة البيانات")
        print("المسارات المفحوصة:")
        for path in possible_paths:
            print(f"  - {os.path.abspath(path)}")
        return False
    
    print(f"📁 تم العثور على قاعدة البيانات: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # فحص هيكل الجدول الحالي
        cursor.execute("PRAGMA table_info(customers)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"الحقول الموجودة حالياً: {existing_columns}")
        
        # إضافة الحقول المطلوبة
        fields_to_add = [
            ("is_blocked", "INTEGER DEFAULT 0"),
            ("block_reason", "TEXT"),
            ("blocked_at", "DATETIME"),
            ("blocked_by", "TEXT")
        ]
        
        added_fields = []
        for field_name, field_definition in fields_to_add:
            if field_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE customers ADD COLUMN {field_name} {field_definition}"
                    cursor.execute(sql)
                    print(f"✅ تم إضافة حقل: {field_name}")
                    added_fields.append(field_name)
                except sqlite3.Error as e:
                    print(f"❌ خطأ في إضافة حقل {field_name}: {e}")
            else:
                print(f"⚠️ حقل {field_name} موجود بالفعل")
        
        # تحديث القيم الافتراضية للحقول الجديدة
        if 'is_blocked' in added_fields:
            cursor.execute("UPDATE customers SET is_blocked = 0 WHERE is_blocked IS NULL")
            print("✅ تم تحديث القيم الافتراضية لحقل is_blocked")
        
        # حفظ التغييرات
        conn.commit()
        
        # التحقق من النتيجة النهائية
        cursor.execute("PRAGMA table_info(customers)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"الحقول النهائية: {final_columns}")
        
        # عد العملاء
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        print(f"عدد العملاء في قاعدة البيانات: {customer_count}")
        
        print("✅ تم إضافة حقول الحظر بنجاح!")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    success = fix_customer_block_db()
    if success:
        print("\n🎉 يمكنك الآن تشغيل النظام - مشكلة قاعدة البيانات تم حلها!")
    else:
        print("\n❌ فشل في إصلاح قاعدة البيانات")
