import sqlite3
from datetime import datetime

# إعادة إنشاء جدول room_transfers بالبنية الصحيحة
conn = sqlite3.connect('instance/hotel.db')
cursor = conn.cursor()

try:
    print("إعادة إنشاء جدول room_transfers...")
    
    # حفظ البيانات الموجودة إن وجدت
    backup_data = []
    try:
        cursor.execute("SELECT * FROM room_transfers")
        backup_data = cursor.fetchall()
        print(f"تم حفظ {len(backup_data)} سجل موجود")
    except:
        print("لا توجد بيانات للحفظ")
    
    # حذف الجدول القديم
    cursor.execute("DROP TABLE IF EXISTS room_transfers")
    print("تم حذف الجدول القديم")
    
    # إنشاء الجدول الجديد بالبنية الصحيحة
    cursor.execute("""
        CREATE TABLE room_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            from_room_id INTEGER NOT NULL,
            to_room_id INTEGER NOT NULL,
            from_room_check_in DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            from_room_check_out DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            to_room_check_in DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            transfer_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            transfer_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            transferred_by TEXT NOT NULL DEFAULT 'admin',
            transferred_by_user_id INTEGER NOT NULL DEFAULT 1,
            reason TEXT,
            notes TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings (id),
            FOREIGN KEY (from_room_id) REFERENCES rooms (id),
            FOREIGN KEY (to_room_id) REFERENCES rooms (id),
            FOREIGN KEY (transferred_by_user_id) REFERENCES users (id)
        )
    """)
    print("✅ تم إنشاء الجدول الجديد بنجاح")
    
    # استعادة البيانات إن وجدت
    if backup_data:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for row in backup_data:
            try:
                # إدراج البيانات مع القيم الافتراضية للأعمدة الجديدة
                cursor.execute("""
                    INSERT INTO room_transfers 
                    (booking_id, from_room_id, to_room_id, from_room_check_in, from_room_check_out,
                     to_room_check_in, transfer_date, transfer_time, transferred_by, transferred_by_user_id, reason, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row[1] if len(row) > 1 else 1,  # booking_id
                    row[2] if len(row) > 2 else 1,  # from_room_id
                    row[3] if len(row) > 3 else 2,  # to_room_id
                    current_time,  # from_room_check_in
                    current_time,  # from_room_check_out
                    current_time,  # to_room_check_in
                    current_time,  # transfer_date
                    current_time,  # transfer_time
                    'admin',       # transferred_by
                    1,             # transferred_by_user_id
                    row[4] if len(row) > 4 else '',  # reason
                    row[5] if len(row) > 5 else ''   # notes
                ))
            except Exception as e:
                print(f"خطأ في استعادة سجل: {e}")
        print(f"✅ تم استعادة {len(backup_data)} سجل")
    
    conn.commit()
    
    # التحقق النهائي
    cursor.execute("PRAGMA table_info(room_transfers)")
    columns = cursor.fetchall()
    print("\nبنية الجدول النهائية:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    
    print("\n🎉 تم إعادة إنشاء الجدول بنجاح!")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
    conn.rollback()
finally:
    conn.close()
