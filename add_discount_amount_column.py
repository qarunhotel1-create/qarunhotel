import sqlite3

DB_PATH = 'instance/hotel.db'

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # إضافة العمود إذا لم يكن موجوداً
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'discount_amount' not in columns:
        cursor.execute("ALTER TABLE bookings ADD COLUMN discount_amount FLOAT DEFAULT 0.0;")
        print('✅ تم إضافة عمود discount_amount بنجاح!')
    else:
        print('ℹ️ العمود discount_amount موجود بالفعل.')
    conn.commit()
    conn.close()
except Exception as e:
    print(f'❌ خطأ أثناء تعديل قاعدة البيانات: {e}')
