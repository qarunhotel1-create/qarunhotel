#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إضافة حقل العلاقة إلى جدول booking_guests
"""

import sqlite3
import os
from hotel import create_app

def add_relationship_field():
    """إضافة حقل العلاقة"""
    
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
        
        # التحقق من وجود حقل relationship
        cursor.execute("PRAGMA table_info(booking_guests)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"الأعمدة الموجودة: {columns}")
        
        if 'relationship' not in columns:
            # إضافة حقل العلاقة
            cursor.execute("ALTER TABLE booking_guests ADD COLUMN relationship VARCHAR(100)")
            print("✅ تم إضافة حقل relationship")
            
            # حفظ التغييرات
            conn.commit()
            print("✅ تم حفظ التغييرات")
        else:
            print("✅ حقل relationship موجود بالفعل")
        
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
    add_relationship_field()
