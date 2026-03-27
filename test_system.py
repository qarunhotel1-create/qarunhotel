#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
import requests
from hotel import create_app

def test_app_creation():
    """اختبار إنشاء التطبيق"""
    try:
        print("🧪 اختبار إنشاء التطبيق...")
        app = create_app()
        print("✅ تم إنشاء التطبيق بنجاح")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء التطبيق: {e}")
        traceback.print_exc()
        return False

def test_routes():
    """اختبار routes الأساسية"""
    try:
        print("🧪 اختبار routes...")
        app = create_app()
        
        with app.test_client() as client:
            # اختبار الصفحة الرئيسية
            response = client.get('/')
            print(f"📄 الصفحة الرئيسية: {response.status_code}")
            
            # اختبار صفحة تسجيل الدخول
            response = client.get('/auth/login')
            print(f"🔐 صفحة تسجيل الدخول: {response.status_code}")
            
            # اختبار صفحة الحجز (قد تحتاج تسجيل دخول)
            response = client.get('/bookings/create')
            print(f"📝 صفحة الحجز: {response.status_code}")
            
        print("✅ تم اختبار routes بنجاح")
        return True
    except Exception as e:
        print(f"❌ خطأ في اختبار routes: {e}")
        traceback.print_exc()
        return False

def test_imports():
    """اختبار imports"""
    try:
        print("🧪 اختبار imports...")
        
        from hotel.models import User, Room, Customer, Booking, BookingGuest
        print("✅ تم استيراد النماذج بنجاح")
        
        from hotel.routes.booking import booking_bp
        from hotel.routes.booking_guest import booking_guest_bp
        print("✅ تم استيراد routes بنجاح")
        
        from hotel.forms.booking import BookingForm
        from hotel.forms.booking_guest import AddExistingGuestForm
        print("✅ تم استيراد النماذج بنجاح")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في imports: {e}")
        traceback.print_exc()
        return False

def test_server_connection():
    """اختبار الاتصال بالخادم"""
    try:
        print("🧪 اختبار الاتصال بالخادم...")
        
        response = requests.get('http://127.0.0.1:5000', timeout=5)
        print(f"🌐 حالة الخادم: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ الخادم يعمل بشكل صحيح")
            return True
        else:
            print(f"⚠️ الخادم يعمل لكن مع حالة: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ لا يمكن الاتصال بالخادم - الخادم غير مشغل")
        return False
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🔍 بدء فحص النظام...")
    print("=" * 50)
    
    tests = [
        ("اختبار imports", test_imports),
        ("اختبار إنشاء التطبيق", test_app_creation),
        ("اختبار routes", test_routes),
        ("اختبار الاتصال بالخادم", test_server_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append((test_name, result))
        print("-" * 30)
    
    print("\n📊 ملخص النتائج:")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{status} {test_name}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n🎯 النتيجة النهائية: {success_count}/{total_count} اختبارات نجحت")
    
    if success_count == total_count:
        print("🎉 جميع الاختبارات نجحت! النظام يعمل بشكل صحيح")
    else:
        print("⚠️ بعض الاختبارات فشلت. راجع الأخطاء أعلاه")

if __name__ == "__main__":
    main()
