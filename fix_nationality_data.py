#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إصلاح بيانات الجنسية في قاعدة البيانات
"""

import sqlite3
import os
from hotel import create_app

def fix_nationality_data():
    """إصلاح بيانات الجنسية"""
    
    # إنشاء التطبيق
    app = create_app()
    
    # مسار قاعدة البيانات
    db_path = os.path.join(app.instance_path, 'hotel.db')
    if not os.path.exists(db_path):
        db_path = 'instance/hotel.db'
    
    print(f"إصلاح بيانات الجنسية في: {db_path}")
    
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # عرض البيانات الحالية
        cursor.execute("SELECT id, name, nationality FROM customers WHERE nationality IS NOT NULL")
        customers = cursor.fetchall()
        
        print(f"العملاء الموجودين ({len(customers)}):")
        for customer in customers:
            print(f"  - {customer[1]}: {customer[2]}")
        
        # قاموس تحويل الجنسيات
        nationality_mapping = {
            'كويتي': 'كويتي',
            'مصري': 'مصري', 
            'سعودي': 'سعودي',
            'إماراتي': 'إماراتي',
            'قطري': 'قطري',
            'بحريني': 'بحريني',
            'عماني': 'عماني',
            'أردني': 'أردني',
            'لبناني': 'لبناني',
            'سوري': 'سوري',
            'عراقي': 'عراقي',
            'فلسطيني': 'فلسطيني',
            'ليبي': 'ليبي',
            'تونسي': 'تونسي',
            'جزائري': 'جزائري',
            'مغربي': 'مغربي',
            'سوداني': 'سوداني',
            'يمني': 'يمني'
        }
        
        # تحديث البيانات
        updates_made = 0
        for customer_id, name, nationality in customers:
            if nationality and nationality not in nationality_mapping:
                # إذا كانت الجنسية غير موجودة في القائمة، نحتاج لتحديدها
                print(f"\n⚠️  العميل {name} له جنسية غير معروفة: '{nationality}'")
                
                # محاولة تخمين الجنسية
                nationality_lower = nationality.lower()
                if 'كويت' in nationality_lower or 'kuwait' in nationality_lower:
                    new_nationality = 'كويتي'
                elif 'مصر' in nationality_lower or 'egypt' in nationality_lower:
                    new_nationality = 'مصري'
                elif 'سعود' in nationality_lower or 'saudi' in nationality_lower:
                    new_nationality = 'سعودي'
                elif 'إمارات' in nationality_lower or 'uae' in nationality_lower:
                    new_nationality = 'إماراتي'
                elif 'قطر' in nationality_lower or 'qatar' in nationality_lower:
                    new_nationality = 'قطري'
                else:
                    new_nationality = 'other'
                
                print(f"   سيتم تحديثها إلى: '{new_nationality}'")
                
                cursor.execute("UPDATE customers SET nationality = ? WHERE id = ?", 
                             (new_nationality, customer_id))
                updates_made += 1
        
        if updates_made > 0:
            conn.commit()
            print(f"\n✅ تم تحديث {updates_made} عميل")
        else:
            print("\n✅ جميع البيانات صحيحة، لا حاجة للتحديث")
        
        # عرض البيانات بعد التحديث
        cursor.execute("SELECT id, name, nationality FROM customers WHERE nationality IS NOT NULL")
        updated_customers = cursor.fetchall()
        
        print(f"\nالبيانات بعد التحديث:")
        for customer in updated_customers:
            print(f"  - {customer[1]}: {customer[2]}")
        
        conn.close()
        print("\n🎉 تم إصلاح بيانات الجنسية بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح البيانات: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    fix_nationality_data()
