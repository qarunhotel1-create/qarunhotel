#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تحديث قاعدة البيانات لإضافة الأعمدة المفقودة
"""

import sqlite3
import os
from hotel import create_app

def update_database():
    """تحديث قاعدة البيانات"""
    
    # إنشاء التطبيق
    app = create_app()
    
    # مسار قاعدة البيانات
    db_path = os.path.join(app.instance_path, 'hotel.db')
    if not os.path.exists(db_path):
        db_path = 'instance/hotel.db'
    
    print(f"تحديث قاعدة البيانات: {db_path}")
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التحقق من وجود الأعمدة في جدول booking_guests
        cursor.execute("PRAGMA table_info(booking_guests)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"الأعمدة الموجودة في booking_guests: {columns}")
        
        # إضافة الأعمدة المفقودة
        missing_columns = []
        
        if 'added_by_user_id' not in columns:
            missing_columns.append('added_by_user_id')
            cursor.execute("ALTER TABLE booking_guests ADD COLUMN added_by_user_id INTEGER")
            print("✅ تم إضافة عمود added_by_user_id")
        
        if 'added_time' not in columns:
            missing_columns.append('added_time')
            cursor.execute("ALTER TABLE booking_guests ADD COLUMN added_time DATETIME")
            print("✅ تم إضافة عمود added_time")
        
        if 'removed_by_user_id' not in columns:
            missing_columns.append('removed_by_user_id')
            cursor.execute("ALTER TABLE booking_guests ADD COLUMN removed_by_user_id INTEGER")
            print("✅ تم إضافة عمود removed_by_user_id")
        
        if 'removed_time' not in columns:
            missing_columns.append('removed_time')
            cursor.execute("ALTER TABLE booking_guests ADD COLUMN removed_time DATETIME")
            print("✅ تم إضافة عمود removed_time")
        
        # تحديث البيانات الموجودة
        if missing_columns:
            # تعيين قيم افتراضية للبيانات الموجودة
            cursor.execute("UPDATE booking_guests SET added_by_user_id = 1 WHERE added_by_user_id IS NULL")
            cursor.execute("UPDATE booking_guests SET added_time = datetime('now') WHERE added_time IS NULL")
            print("✅ تم تحديث البيانات الموجودة")
        
        # إنشاء جدول room_transfers إذا لم يكن موجوداً
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS room_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                from_room_id INTEGER NOT NULL,
                to_room_id INTEGER NOT NULL,
                transfer_time DATETIME NOT NULL,
                transferred_by_user_id INTEGER NOT NULL,
                reason TEXT,
                notes TEXT,
                FOREIGN KEY (booking_id) REFERENCES bookings (id),
                FOREIGN KEY (from_room_id) REFERENCES rooms (id),
                FOREIGN KEY (to_room_id) REFERENCES rooms (id),
                FOREIGN KEY (transferred_by_user_id) REFERENCES users (id)
            )
        """)
        print("✅ تم إنشاء جدول room_transfers")
        
        # حفظ التغييرات
        conn.commit()
        print("✅ تم حفظ جميع التغييرات")
        
        # التحقق من النتيجة
        cursor.execute("PRAGMA table_info(booking_guests)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"الأعمدة بعد التحديث: {updated_columns}")
        
        conn.close()
        print("🎉 تم تحديث قاعدة البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في تحديث قاعدة البيانات: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    update_database()
