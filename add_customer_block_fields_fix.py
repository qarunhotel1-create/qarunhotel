#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إضافة حقول الحظر لجدول العملاء - إصلاح سريع
"""

import sqlite3
import os
from datetime import datetime

def add_customer_block_fields():
    """إضافة حقول الحظر لجدول العملاء"""
    
    # مسار قاعدة البيانات
    db_path = os.path.join('instance', 'hotel.db')
    
    if not os.path.exists(db_path):
        print(f"قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("فحص الحقول الموجودة...")
        
        # فحص بنية الجدول الحالية
        cursor.execute("PRAGMA table_info(customers)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"الحقول الموجودة: {columns}")
        
        # قائمة الحقول المطلوبة
        required_fields = [
            ('is_blocked', 'INTEGER DEFAULT 0'),
            ('block_reason', 'TEXT'),
            ('blocked_at', 'DATETIME'),
            ('blocked_by', 'TEXT')
        ]
        
        # إضافة الحقول المفقودة
        for field_name, field_definition in required_fields:
            if field_name not in columns:
                try:
                    sql = f"ALTER TABLE customers ADD COLUMN {field_name} {field_definition}"
                    print(f"إضافة حقل: {field_name}")
                    cursor.execute(sql)
                    print(f"تم إضافة حقل {field_name} بنجاح")
                except Exception as e:
                    print(f"خطأ في إضافة حقل {field_name}: {str(e)}")
            else:
                print(f"حقل {field_name} موجود بالفعل")
        
        # حفظ التغييرات
        conn.commit()
        
        # التحقق من النتيجة النهائية
        cursor.execute("PRAGMA table_info(customers)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"الحقول النهائية: {final_columns}")
        
        # إغلاق الاتصال
        conn.close()
        
        print("تم إضافة حقول الحظر بنجاح!")
        return True
        
    except Exception as e:
        print(f"خطأ في إضافة حقول الحظر: {str(e)}")
        return False

if __name__ == '__main__':
    print("بدء إضافة حقول الحظر...")
    success = add_customer_block_fields()
    
    if success:
        print("تم الانتهاء بنجاح!")
    else:
        print("فشل في العملية!")
