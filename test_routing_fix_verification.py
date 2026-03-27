#!/usr/bin/env python3
"""
اختبار إصلاح مشكلة التوجيه (Routing)
Test routing fix for werkzeug.routing.exceptions.BuildError
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app
from flask import url_for

def test_routing_fix():
    """اختبار إصلاح مشكلة التوجيه"""
    print("🔧 اختبار إصلاح مشكلة التوجيه...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # اختبار الروابط الأساسية
            routes_to_test = [
                ('main.index', 'الصفحة الرئيسية'),
                ('main.user_dashboard', 'لوحة تحكم المستخدم'),
                ('admin.dashboard', 'لوحة تحكم المسؤول'),
                ('auth.login', 'تسجيل الدخول'),
                ('customer_new.index', 'صفحة العملاء الجديدة'),
                ('booking.index', 'صفحة الحجوزات'),
            ]
            
            print("\n📋 اختبار الروابط:")
            all_passed = True
            
            for route, description in routes_to_test:
                try:
                    url = url_for(route)
                    print(f"✅ {description}: {route} -> {url}")
                except Exception as e:
                    print(f"❌ {description}: {route} -> خطأ: {e}")
                    all_passed = False
            
            # اختبار الروابط التي كانت تسبب مشاكل
            print("\n🔍 اختبار الروابط المُصلحة:")
            try:
                # هذا الرابط كان يسبب مشكلة
                url = url_for('main.user_dashboard')
                print(f"✅ main.user_dashboard (المُصلح): {url}")
            except Exception as e:
                print(f"❌ main.user_dashboard: خطأ: {e}")
                all_passed = False
            
            # اختبار أن main.dashboard لا يوجد (وهذا صحيح)
            try:
                url = url_for('main.dashboard')
                print(f"⚠️  main.dashboard: {url} (هذا لا يجب أن يعمل)")
                all_passed = False
            except Exception as e:
                print(f"✅ main.dashboard: غير موجود (هذا صحيح) - {e}")
            
            if all_passed:
                print("\n🎉 تم إصلاح مشكلة التوجيه بنجاح!")
                print("💡 الآن يمكن استخدام main.user_dashboard بدلاً من main.dashboard")
                return True
            else:
                print("\n❌ هناك مشاكل في التوجيه تحتاج إلى إصلاح")
                return False
                
        except Exception as e:
            print(f"❌ خطأ في اختبار التوجيه: {e}")
            return False

def test_template_fixes():
    """اختبار إصلاح القوالب"""
    print("\n🔧 اختبار إصلاح القوالب...")
    
    templates_fixed = [
        'hotel/templates/customer/index_new.html',
        'hotel/templates/customer/edit_new.html',
        'hotel/templates/customer/details_new.html',
        'hotel/templates/customer/create_new.html',
        'hotel/templates/customer/create.html'
    ]
    
    all_fixed = True
    for template_path in templates_fixed:
        full_path = os.path.join(os.path.dirname(__file__), template_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'main.dashboard' in content:
                        print(f"❌ {template_path}: لا يزال يحتوي على main.dashboard")
                        all_fixed = False
                    elif 'main.user_dashboard' in content:
                        print(f"✅ {template_path}: تم إصلاحه إلى main.user_dashboard")
                    else:
                        print(f"ℹ️  {template_path}: لا يحتوي على روابط main")
            except Exception as e:
                print(f"❌ خطأ في قراءة {template_path}: {e}")
                all_fixed = False
        else:
            print(f"⚠️  {template_path}: الملف غير موجود")
    
    return all_fixed

if __name__ == '__main__':
    print("🚀 بدء اختبار إصلاح مشكلة التوجيه...")
    
    routing_ok = test_routing_fix()
    templates_ok = test_template_fixes()
    
    if routing_ok and templates_ok:
        print("\n🎉 تم إصلاح جميع مشاكل التوجيه بنجاح!")
        print("\n📝 ملخص الإصلاحات:")
        print("   • تم تغيير main.dashboard إلى main.user_dashboard في جميع القوالب")
        print("   • تم التأكد من وجود جميع الروابط المطلوبة")
        print("   • النظام جاهز للاستخدام")
    else:
        print("\n❌ هناك مشاكل تحتاج إلى إصلاح إضافي")
    
    print("\n" + "="*50)