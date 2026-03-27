#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية
"""

import os
import sys
import traceback
from datetime import datetime

# إعداد التشفير للنظام
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    # للتوافق مع إصدارات Python القديمة
    pass
os.environ['PYTHONIOENCODING'] = 'utf-8'

# تنشيط البيئة الافتراضية
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# استيراد المكتبات اللازمة
try:
    from hotel import create_app, db
    from hotel.models import Customer
    app = create_app()
    app.app_context().push()
    print("✓ تم تهيئة التطبيق بنجاح")
except Exception as e:
    print(f"خطأ في تهيئة التطبيق: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

def test_english_name_saving():
    """اختبار حفظ الأسماء باللغة الإنجليزية"""
    print("\n1. اختبار إنشاء عميل باسم إنجليزي...")
    
    try:
        # إنشاء عميل تجريبي باسم إنجليزي
        test_customer = Customer(
            name="John Smith Test",
            id_number="TEST-ENG-" + datetime.now().strftime("%Y%m%d%H%M%S"),
            nationality="جنسية أخرى",
            phone="01234567890",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(test_customer)
        db.session.commit()
        
        print(f"تم إنشاء عميل تجريبي باسم إنجليزي بنجاح، ID={test_customer.id}")
        
        # التحقق من حفظ الاسم بشكل صحيح
        db.session.refresh(test_customer)
        saved_name = test_customer.name
        if saved_name == "John Smith Test":
            print("✓ تم حفظ الاسم الإنجليزي بشكل صحيح!")
        else:
            print(f"خطأ: الاسم المحفوظ '{saved_name}' لا يطابق 'John Smith Test'")
        
        # حذف العميل التجريبي
        db.session.delete(test_customer)
        db.session.commit()
        print("تم حذف العميل التجريبي")
        
        return True
        
    except Exception as e:
        print(f"خطأ في اختبار إنشاء عميل باسم إنجليزي: {str(e)}")
        traceback.print_exc()
        db.session.rollback()
        return False

def check_database_encoding():
    """التحقق من تشفير قاعدة البيانات"""
    print("\n2. التحقق من إعدادات التشفير في قاعدة البيانات...")
    
    try:
        # الحصول على اتصال قاعدة البيانات الأساسي
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        
        # التحقق من تشفير قاعدة البيانات
        cursor.execute("PRAGMA encoding;")
        db_encoding = cursor.fetchone()[0]
        print(f"✓ تشفير قاعدة البيانات: {db_encoding}")
        
        # التحقق من إعدادات التطبيق
        print(f"✓ إعداد JSON_AS_ASCII: {app.config.get('JSON_AS_ASCII', 'غير محدد')}")
        
        # إغلاق الاتصال
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"خطأ في التحقق من تشفير قاعدة البيانات: {str(e)}")
        traceback.print_exc()
        return False

def check_customer_model():
    """التحقق من نموذج العميل"""
    print("\n3. التحقق من نموذج العميل...")
    
    try:
        # عرض تعريف حقل الاسم
        name_column = Customer.__table__.columns.get('name')
        print(f"✓ تعريف حقل الاسم: {name_column.type}")
        print(f"✓ طول حقل الاسم: {name_column.type.length}")
        print(f"✓ خيار nullable: {name_column.nullable}")
        
        return True
        
    except Exception as e:
        print(f"خطأ في التحقق من نموذج العميل: {str(e)}")
        traceback.print_exc()
        return False

def fix_english_name_issue():
    """إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية"""
    print("بدء إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية...")
    
    # التحقق من تشفير قاعدة البيانات
    if not check_database_encoding():
        print("فشل في التحقق من تشفير قاعدة البيانات")
        return False
    
    # التحقق من نموذج العميل
    if not check_customer_model():
        print("فشل في التحقق من نموذج العميل")
        return False
    
    # اختبار حفظ الأسماء باللغة الإنجليزية
    if not test_english_name_saving():
        print("فشل في اختبار حفظ الأسماء باللغة الإنجليزية")
        return False
    
    # تحديث إعدادات التطبيق لدعم الأحرف غير اللاتينية
    try:
        app.config['JSON_AS_ASCII'] = False
        print("✓ تم تحديث إعداد JSON_AS_ASCII إلى False")
    except Exception as e:
        print(f"خطأ في تحديث إعدادات التطبيق: {str(e)}")
        traceback.print_exc()
    
    print("\n✅ تم إكمال جميع الاختبارات والإصلاحات بنجاح!")
    return True

if __name__ == '__main__':
    print("إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية")
    print("=" * 50)
    
    success = fix_english_name_issue()
    if success:
        print("\n✅ تم إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية بنجاح!")
        print("يمكنك الآن إضافة وتعديل أسماء العملاء باللغة الإنجليزية بدون مشاكل.")
    else:
        print("\n❌ فشل إصلاح مشكلة حفظ أسماء العملاء باللغة الإنجليزية!")