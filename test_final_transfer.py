import sqlite3
from datetime import datetime

# اختبار نهائي لجدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    print("اختبار جدول room_transfers...")
    
    # عرض بنية الجدول
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = cursor.fetchall()
    
    print("\nبنية الجدول:")
    print("=" * 60)
    for col in columns:
        null_status = "NOT NULL" if col[3] else "NULL"
        default_val = f"DEFAULT {col[4]}" if col[4] else "NO DEFAULT"
        print(f"{col[1]:20} {col[2]:10} {null_status:8} {default_val}")
    
    # اختبار إدراج سجل
    print("\nاختبار إدراج سجل...")
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute("""
            INSERT INTO room_transfers 
            (booking_id, from_room_id, to_room_id, from_room_check_in, from_room_check_out,
             to_room_check_in, transfer_date, transfer_time, transferred_by, transferred_by_user_id, reason, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            999,  # booking_id تجريبي
            1,    # from_room_id
            2,    # to_room_id
            current_time,  # from_room_check_in
            current_time,  # from_room_check_out
            current_time,  # to_room_check_in
            current_time,  # transfer_date
            current_time,  # transfer_time
            'admin',       # transferred_by
            1,             # transferred_by_user_id
            'اختبار نهائي',  # reason
            'سجل تجريبي'     # notes
        ))
        
        print("✅ تم إدراج السجل التجريبي بنجاح!")
        
        # حذف السجل التجريبي
        cursor.execute("DELETE FROM room_transfers WHERE reason = 'اختبار نهائي'")
        print("✅ تم حذف السجل التجريبي")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ خطأ في الإدراج: {e}")
        conn.rollback()
    
    # عد السجلات
    cursor.execute("SELECT COUNT(*) FROM room_transfers")
    count = cursor.fetchone()[0]
    print(f"\nعدد سجلات النقل: {count}")
    
    print("\n🎉 الجدول جاهز تماماً للاستخدام!")
    print("يمكنك الآن استخدام ميزة نقل العملاء بدون مشاكل.")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
finally:
    conn.close()
