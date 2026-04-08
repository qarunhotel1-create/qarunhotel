#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار مشكلة عدم حفظ تعديلات العميل
"""

import os
import sys
from flask import Flask
from hotel import create_app, db
from hotel.models import Customer
from hotel.forms.customer import CustomerForm

def test_customer_edit_issue():
    """اختبار مشكلة تعديل العميل"""
    
    print("🔍 بدء اختبار مشكلة تعديل العميل...")
    
    try:
        # إنشاء التطبيق
        app = create_app()
        
        with app.app_context():
            # البحث عن عميل للاختبار
            customer = Customer.query.first()
            
            if not customer:
                print("❌ لا يوجد عملاء في قاعدة البيانات للاختبار")
                return False
            
            print(f"✅ تم العثور على عميل للاختبار: {customer.name}")
            print(f"   - ID: {customer.id}")
            print(f"   - رقم الهوية: {customer.id_number}")
            print(f"   - الهاتف: {customer.phone}")
            print(f"   - الجنسية: {customer.nationality}")
            
            # اختبار النموذج
            print("\n🔧 اختبار نموذج العميل...")
            
            # إنشاء نموذج مع بيانات العميل الحالية
            form = CustomerForm(obj=customer)
            
            # التحقق من تحميل البيانات في النموذج
            print(f"   - اسم العميل في النموذج: {form.name.data}")
            print(f"   - رقم الهوية في النموذج: {form.id_number.data}")
            print(f"   - الهاتف في النموذج: {form.phone.data}")
            
            # محاكاة تعديل البيانات
            original_name = customer.name
            original_phone = customer.phone
            
            # تعديل البيانات
            new_name = f"{original_name} - محدث"
            new_phone = "01234567890"
            
            form.name.data = new_name
            form.phone.data = new_phone
            
            print(f"\n📝 محاكاة تعديل البيانات:")
            print(f"   - الاسم الجديد: {new_name}")
            print(f"   - الهاتف الجديد: {new_phone}")
            
            # التحقق من صحة النموذج
            if form.validate():
                print("✅ النموذج صحيح")
                
                # تطبيق التغييرات
                customer.name = form.name.data
                customer.phone = form.phone.data
                
                try:
                    db.session.commit()
                    print("✅ تم حفظ التغييرات بنجاح")
                    
                    # التحقق من الحفظ
                    updated_customer = Customer.query.get(customer.id)
                    if updated_customer.name == new_name and updated_customer.phone == new_phone:
                        print("✅ تم التحقق من حفظ البيانات الجديدة")
                        
                        # إعادة البيانات الأصلية
                        updated_customer.name = original_name
                        updated_customer.phone = original_phone
                        db.session.commit()
                        print("✅ تم إعادة البيانات الأصلية")
                        
                        return True
                    else:
                        print("❌ لم يتم حفظ البيانات الجديدة")
                        return False
                        
                except Exception as e:
                    print(f"❌ خطأ في حفظ البيانات: {str(e)}")
                    db.session.rollback()
                    return False
                    
            else:
                print("❌ النموذج غير صحيح:")
                for field, errors in form.errors.items():
                    print(f"   - {field}: {errors}")
                return False
                
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {str(e)}")
        return False

def test_form_validation():
    """اختبار التحقق من صحة النموذج"""
    
    print("\n🔍 اختبار التحقق من صحة النموذج...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # اختبار نموذج فارغ
            form = CustomerForm()
            
            if not form.validate():
                print("✅ النموذج الفارغ غير صحيح كما هو متوقع")
                print("   الأخطاء:")
                for field, errors in form.errors.items():
                    print(f"   - {field}: {errors}")
            else:
                print("❌ النموذج الفارغ صحيح (غير متوقع)")
                
            # اختبار نموذج بحد أدنى من البيانات
            form.name.data = "عميل تجريبي"
            form.id_number.data = "12345678901234"
            
            if form.validate():
                print("✅ النموذج مع البيانات الأساسية صحيح")
                return True
            else:
                print("❌ النموذج مع البيانات الأساسية غير صحيح:")
                for field, errors in form.errors.items():
                    print(f"   - {field}: {errors}")
                return False
                
    except Exception as e:
        print(f"❌ خطأ في اختبار التحقق: {str(e)}")
        return False

def check_route_functionality():
    """فحص وظائف المسار"""
    
    print("\n🔍 فحص وظائف مسار تعديل العميل...")
    
    try:
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                # البحث عن عميل للاختبار
                customer = Customer.query.first()
                
                if not customer:
                    print("❌ لا يوجد عملاء للاختبار")
                    return False
                
                # اختبار GET request
                response = client.get(f'/customers/{customer.id}/edit')
                
                if response.status_code == 200:
                    print("✅ صفحة تعديل العميل تعمل بشكل صحيح (GET)")
                else:
                    print(f"❌ خطأ في صفحة تعديل العميل: {response.status_code}")
                    return False
                
                # اختبار POST request
                data = {
                    'name': customer.name + " - محدث",
                    'id_number': customer.id_number,
                    'phone': customer.phone or "01234567890",
                    'nationality': customer.nationality or "مصري",
                    'csrf_token': 'test_token'  # في الاختبار الحقيقي نحتاج token صحيح
                }
                
                # ملاحظة: هذا الاختبار قد يفشل بسبب CSRF token
                # لكنه سيساعدنا في فهم المشكلة
                response = client.post(f'/customers/{customer.id}/edit', data=data)
                
                print(f"   - استجابة POST: {response.status_code}")
                
                if response.status_code in [200, 302]:  # 302 للتوجيه بعد النجاح
                    print("✅ مسار POST يعمل")
                    return True
                else:
                    print(f"❌ مشكلة في مسار POST: {response.status_code}")
                    if hasattr(response, 'data'):
                        print(f"   البيانات: {response.data.decode('utf-8')[:200]}...")
                    return False
                    
    except Exception as e:
        print(f"❌ خطأ في فحص المسار: {str(e)}")
        return False

def main():
    """الدالة الرئيسية"""
    
    print("=" * 60)
    print("🔧 تشخيص مشكلة عدم حفظ تعديلات العميل")
    print("=" * 60)
    
    # تشغيل الاختبارات
    tests = [
        ("اختبار تعديل العميل", test_customer_edit_issue),
        ("اختبار التحقق من النموذج", test_form_validation),
        ("فحص وظائف المسار", check_route_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"🧪 {test_name}")
        print(f"{'='*40}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ خطأ في {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # عرض النتائج النهائية
    print(f"\n{'='*60}")
    print("📊 ملخص النتائج")
    print(f"{'='*60}")
    
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{status} - {test_name}")
    
    # التوصيات
    print(f"\n{'='*60}")
    print("💡 التوصيات")
    print(f"{'='*60}")
    
    failed_tests = [name for name, result in results if not result]
    
    if not failed_tests:
        print("✅ جميع الاختبارات نجحت - المشكلة قد تكون في الواجهة الأمامية")
        print("   تحقق من:")
        print("   - ملفات JavaScript")
        print("   - معالجة النموذج في المتصفح")
        print("   - رسائل الخطأ في وحدة تحكم المتصفح")
    else:
        print("❌ فشلت الاختبارات التالية:")
        for test_name in failed_tests:
            print(f"   - {test_name}")
        
        print("\n🔧 خطوات الإصلاح المقترحة:")
        print("   1. تحقق من إعدادات قاعدة البيانات")
        print("   2. تحقق من نموذج العميل")
        print("   3. تحقق من مسار تعديل العميل")
        print("   4. تحقق من صلاحيات المستخدم")

if __name__ == "__main__":
    main()
