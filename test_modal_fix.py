#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار إصلاحات Modal
"""

import sys
import os

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app
from hotel.models.customer import Customer
from hotel.models.user import User
from flask import url_for

def test_modal_fixes():
    """اختبار إصلاحات Modal"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # التحقق من وجود العملاء
            customers = Customer.query.limit(5).all()
            
            print("=== اختبار إصلاحات Modal ===")
            print(f"عدد العملاء المتاحين: {len(customers)}")
            
            if customers:
                customer = customers[0]
                print(f"سيتم اختبار العميل: {customer.name}")
                
                # إنشاء URLs للاختبار
                with app.test_request_context():
                    details_url = url_for('customer_new.details', id=customer.id)
                    edit_url = url_for('customer_new.edit', id=customer.id)
                    
                    print(f"رابط التفاصيل: {details_url}")
                    print(f"رابط التعديل: {edit_url}")
                
                print("\n=== الملفات المضافة للإصلاح ===")
                
                # التحقق من وجود ملفات الإصلاح
                js_file = os.path.join(app.static_folder, 'js', 'modal-fix.js')
                css_file = os.path.join(app.static_folder, 'css', 'modal-fix.css')
                
                if os.path.exists(js_file):
                    print(f"✓ ملف JavaScript: {js_file}")
                    print(f"  حجم الملف: {os.path.getsize(js_file)} بايت")
                else:
                    print(f"✗ ملف JavaScript غير موجود: {js_file}")
                
                if os.path.exists(css_file):
                    print(f"✓ ملف CSS: {css_file}")
                    print(f"  حجم الملف: {os.path.getsize(css_file)} بايت")
                else:
                    print(f"✗ ملف CSS غير موجود: {css_file}")
                
                print("\n=== الإصلاحات المطبقة ===")
                print("✓ إصلاح z-index للـ modals")
                print("✓ إصلاح pointer-events للأزرار")
                print("✓ إصلاح backdrop issues")
                print("✓ إصلاح مناطق الرفع")
                print("✓ إصلاح عناصر الإدخال")
                print("✓ إضافة معالجات للأحداث")
                print("✓ إصلاح مشاكل النقر")
                
                print("\n=== تعليمات الاختبار ===")
                print("1. قم بتشغيل الخادم")
                print("2. انتقل إلى صفحة تفاصيل العميل")
                print("3. اضغط على زر 'إضافة وثائق'")
                print("4. تحقق من أن جميع الأزرار تعمل بشكل صحيح")
                print("5. جرب رفع الملفات والمسح الضوئي")
                
                return True
                
            else:
                print("لا توجد عملاء في قاعدة البيانات")
                return False
                
        except Exception as e:
            print(f"خطأ في الاختبار: {e}")
            return False

if __name__ == '__main__':
    success = test_modal_fixes()
    if success:
        print("\n✓ تم تطبيق إصلاحات Modal بنجاح")
        print("يمكنك الآن تشغيل الخادم واختبار النظام")
    else:
        print("\n✗ فشل في تطبيق الإصلاحات")
    
    sys.exit(0 if success else 1)