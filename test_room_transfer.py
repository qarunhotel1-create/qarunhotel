import sqlite3
from datetime import datetime

# اختبار جدول room_transfers
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    print("اختبار جدول room_transfers...")
    
    # عرض بنية الجدول
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = cursor.fetchall()
    
    print("\nبنية الجدول:")
    print("=" * 50)
    for col in columns:
        null_constraint = "NOT NULL" if col[3] else "NULL"
        default_value = f"DEFAULT {col[4]}" if col[4] else "NO DEFAULT"
        print(f"{col[1]:20} {col[2]:10} {null_constraint:8} {default_value}")
    
    # اختبار إدراج سجل تجريبي
    print("\nاختبار إدراج سجل تجريبي...")
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    test_data = {
        'booking_id': 1,
        'from_room_id': 1,
        'to_room_id': 2,
        'from_room_check_in': current_time,
        'from_room_check_out': current_time,
        'to_room_check_in': current_time,
        'transfer_time': current_time,
        'transferred_by_user_id': 1,
        'reason': 'اختبار',
        'notes': 'سجل تجريبي'
    }
    
    # محاولة الإدراج
    try:
        sql = """
        INSERT INTO room_transfers 
        (booking_id, from_room_id, to_room_id, from_room_check_in, from_room_check_out, 
         to_room_check_in, transfer_time, transferred_by_user_id, reason, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(sql, (
            test_data['booking_id'],
            test_data['from_room_id'], 
            test_data['to_room_id'],
            test_data['from_room_check_in'],
            test_data['from_room_check_out'],
            test_data['to_room_check_in'],
            test_data['transfer_time'],
            test_data['transferred_by_user_id'],
            test_data['reason'],
            test_data['notes']
        ))
        
        print("✅ تم إدراج السجل التجريبي بنجاح!")
        
        # حذف السجل التجريبي
        cursor.execute("DELETE FROM room_transfers WHERE reason = 'اختبار'")
        print("✅ تم حذف السجل التجريبي")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ خطأ في الإدراج: {e}")
        conn.rollback()
    
    # عد السجلات الموجودة
    cursor.execute("SELECT COUNT(*) FROM room_transfers")
    count = cursor.fetchone()[0]
    print(f"\nعدد سجلات النقل الموجودة: {count}")
    
    print("\n🎉 الجدول جاهز للاستخدام!")
    
except Exception as e:
    print(f"❌ خطأ عام: {e}")
finally:
    conn.close()
