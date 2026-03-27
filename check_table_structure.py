import sqlite3

# فحص بنية جدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    # عرض بنية الجدول
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = cursor.fetchall()
    
    print("بنية جدول room_transfers:")
    print("=" * 50)
    for col in columns:
        print(f"العمود: {col[1]}")
        print(f"  النوع: {col[2]}")
        print(f"  NOT NULL: {'نعم' if col[3] else 'لا'}")
        print(f"  القيمة الافتراضية: {col[4] if col[4] else 'لا توجد'}")
        print("-" * 30)
    
    # عرض SQL الخاص بإنشاء الجدول
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='room_transfers'")
    create_sql = cursor.fetchone()
    if create_sql:
        print("\nSQL إنشاء الجدول:")
        print("=" * 50)
        print(create_sql[0])
    
except Exception as e:
    print(f"خطأ: {e}")
finally:
    conn.close()
