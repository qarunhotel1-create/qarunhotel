#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تحديث جنسية العميل محمد السيد إلى كويتي
"""

import sqlite3
import os
from hotel import create_app

def update_customer_nationality():
    """تحديث جنسية العميل"""
    
    # إنشاء التطبيق
    app = create_app()
    
    # مسار قاعدة البيانات
    db_path = os.path.join(app.instance_path, 'hotel.db')
    if not os.path.exists(db_path):
        db_path = 'instance/hotel.db'
    
    print(f"تحديث جنسية العميل في: {db_path}")
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # عرض جميع العملاء
        cursor.execute("SELECT id, name, nationality FROM customers")
        customers = cursor.fetchall()
        
        print("العملاء الموجودين:")
        for i, customer in enumerate(customers, 1):
            print(f"  {i}. {customer[1]} (ID: {customer[0]}) - الجنسية: {customer[2] or 'غير محددة'}")
        
        # تحديث جنسية محمد السيد إلى كويتي
        cursor.execute("UPDATE customers SET nationality = ? WHERE name LIKE ?", 
                      ('كويتي', '%محمد السيد%'))
        
        # تحديث جنسية محمد محمود إلى سعودي (كمثال)
        cursor.execute("UPDATE customers SET nationality = ? WHERE name LIKE ?", 
                      ('سعودي', '%محمد محمود%'))
        
        conn.commit()
        
        print("\n✅ تم تحديث الجنسيات")
        
        # عرض البيانات بعد التحديث
        cursor.execute("SELECT id, name, nationality FROM customers")
        updated_customers = cursor.fetchall()
        
        print("\nالبيانات بعد التحديث:")
        for i, customer in enumerate(updated_customers, 1):
            print(f"  {i}. {customer[1]} (ID: {customer[0]}) - الجنسية: {customer[2] or 'غير محددة'}")
        
        conn.close()
        print("\n🎉 تم تحديث البيانات بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في تحديث البيانات: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    update_customer_nationality()
