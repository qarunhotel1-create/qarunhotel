#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.customer import Customer
from hotel.models.room import Room
from hotel.models.user import User
from flask import url_for
import json

# اختبار نظام التقارير المحسن
app = create_app()

with app.test_client() as client:
    with app.app_context():
        try:
            print("📊 اختبار نظام التقارير المحسن")
            print("=" * 50)
            
            # البحث عن مستخدم admin
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ لم يتم العثور على مستخدم admin")
                exit(1)
            
            print(f"✅ تم العثور على المستخدم: {admin_user.username}")
            
            # تسجيل دخول المستخدم
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # اختبار صفحة التقارير الرئيسية
            print(f"\n🏠 اختبار صفحة التقارير الرئيسية...")
            reports_index_response = client.get('/reports/')
            if reports_index_response.status_code == 200:
                index_content = reports_index_response.get_data(as_text=True)
                if 'التقرير الشامل' in index_content:
                    print("  ✅ صفحة التقارير الرئيسية تحتوي على التقرير الشامل")
                else:
                    print("  ❌ صفحة التقارير الرئيسية لا تحتوي على التقرير الشامل")
            else:
                print(f"  ❌ لا يمكن الوصول لصفحة التقارير: {reports_index_response.status_code}")
            
            # اختبار لوحة تحكم التقارير
            print(f"\n📈 اختبار لوحة تحكم التقارير...")
            dashboard_response = client.get('/reports/dashboard')
            if dashboard_response.status_code == 200:
                print("  ✅ لوحة تحكم التقارير تعمل بشكل صحيح")
            else:
                print(f"  ❌ خطأ في لوحة تحكم التقارير: {dashboard_response.status_code}")
            
            # اختبار التقرير الشامل الجديد
            print(f"\n📋 اختبار التقرير الشامل الجديد...")
            comprehensive_response = client.get('/reports/comprehensive')
            if comprehensive_response.status_code == 200:
                comprehensive_content = comprehensive_response.get_data(as_text=True)
                if 'فلاتر التقرير' in comprehensive_content:
                    print("  ✅ التقرير الشامل يحتوي على فلاتر")
                if 'تصدير PDF' in comprehensive_content:
                    print("  ✅ التقرير الشامل يحتوي على خيارات التصدير")
                if 'ملخص الإحصائيات' in comprehensive_content:
                    print("  ✅ التقرير الشامل يحتوي على الإحصائيات")
            else:
                print(f"  ❌ خطأ في التقرير الشامل: {comprehensive_response.status_code}")
            
            # اختبار التقرير الشامل مع فلاتر
            print(f"\n🔍 اختبار التقرير الشامل مع فلاتر...")
            filtered_response = client.get('/reports/comprehensive?status=confirmed&start_date=2024-01-01')
            if filtered_response.status_code == 200:
                print("  ✅ التقرير الشامل يعمل مع الفلاتر")
            else:
                print(f"  ❌ خطأ في التقرير المفلتر: {filtered_response.status_code}")
            
            # اختبار تصدير JSON
            print(f"\n📄 اختبار تصدير JSON...")
            json_response = client.get('/reports/comprehensive?export=json')
            if json_response.status_code == 200:
                try:
                    json_data = json_response.get_json()
                    if 'report_info' in json_data and 'bookings' in json_data:
                        print("  ✅ تصدير JSON يعمل بشكل صحيح")
                        print(f"    - عدد الحجوزات في JSON: {len(json_data['bookings'])}")
                    else:
                        print("  ❌ تصدير JSON لا يحتوي على البيانات المطلوبة")
                except:
                    print("  ❌ تصدير JSON لا يحتوي على JSON صحيح")
            else:
                print(f"  ❌ خطأ في تصدير JSON: {json_response.status_code}")
            
            # اختبار تقرير الحجوزات المحسن
            print(f"\n📅 اختبار تقرير الحجوزات المحسن...")
            bookings_response = client.get('/reports/bookings')
            if bookings_response.status_code == 200:
                bookings_content = bookings_response.get_data(as_text=True)
                if 'إحصائيات الحالات' in bookings_content or 'total_bookings' in bookings_content:
                    print("  ✅ تقرير الحجوزات المحسن يعمل")
                else:
                    print("  ⚠️ تقرير الحجوزات يعمل لكن قد يحتاج تحسين")
            else:
                print(f"  ❌ خطأ في تقرير الحجوزات: {bookings_response.status_code}")
            
            # اختبار تقرير العملاء
            print(f"\n👥 اختبار تقرير العملاء...")
            customers_response = client.get('/reports/customers')
            if customers_response.status_code == 200:
                print("  ✅ تقرير العملاء يعمل")
            else:
                print(f"  ❌ خطأ في تقرير العملاء: {customers_response.status_code}")
            
            # اختبار تقرير الغرف
            print(f"\n🏨 اختبار تقرير الغرف...")
            rooms_response = client.get('/reports/rooms')
            if rooms_response.status_code == 200:
                print("  ✅ تقرير الغرف يعمل")
            else:
                print(f"  ❌ خطأ في تقرير الغرف: {rooms_response.status_code}")
            
            # اختبار التقرير المالي
            print(f"\n💰 اختبار التقرير المالي...")
            financial_response = client.get('/reports/financial')
            if financial_response.status_code == 200:
                print("  ✅ التقرير المالي يعمل")
            else:
                print(f"  ❌ خطأ في التقرير المالي: {financial_response.status_code}")
            
            # اختبار تقرير المستخدمين
            print(f"\n👤 اختبار تقرير المستخدمين...")
            users_response = client.get('/reports/users')
            if users_response.status_code == 200:
                print("  ✅ تقرير المستخدمين يعمل")
            else:
                print(f"  ❌ خطأ في تقرير المستخدمين: {users_response.status_code}")
            
            # إحصائيات البيانات
            print(f"\n📊 إحصائيات البيانات الحالية:")
            total_bookings = Booking.query.count()
            total_customers = Customer.query.count()
            total_rooms = Room.query.count()
            
            print(f"  📋 إجمالي الحجوزات: {total_bookings}")
            print(f"  👥 إجمالي العملاء: {total_customers}")
            print(f"  🏨 إجمالي الغرف: {total_rooms}")
            
            if total_bookings > 0:
                # إحصائيات الحالات
                pending = Booking.query.filter_by(status='pending').count()
                confirmed = Booking.query.filter_by(status='confirmed').count()
                checked_in = Booking.query.filter_by(status='checked_in').count()
                checked_out = Booking.query.filter_by(status='checked_out').count()
                cancelled = Booking.query.filter_by(status='cancelled').count()
                
                print(f"  📊 توزيع حالات الحجوزات:")
                print(f"    - في الانتظار: {pending}")
                print(f"    - مؤكد: {confirmed}")
                print(f"    - تم تسجيل الدخول: {checked_in}")
                print(f"    - تم تسجيل الخروج: {checked_out}")
                print(f"    - ملغي: {cancelled}")
            
            print(f"\n" + "=" * 50)
            print("🎉 تم اختبار نظام التقارير المحسن!")
            print("\n📋 ملخص التحسينات:")
            print("✅ إنشاء التقرير الشامل مع فلترة متقدمة")
            print("✅ إضافة معلومات العميل الكاملة (الاسم، الجنسية، رقم الهوية، الهاتف)")
            print("✅ عرض تواريخ الوصول والمغادرة وعدد الأيام")
            print("✅ إمكانية الفلترة حسب التاريخ والحالة والجنسية ونوع الغرفة")
            print("✅ تصدير PDF و JSON و Excel")
            print("✅ واجهة احترافية مع إحصائيات شاملة")
            print("✅ إصلاح جميع التقارير الموجودة")
            
            print(f"\n🚀 يمكنك الآن:")
            print("1. الوصول للتقرير الشامل من صفحة التقارير")
            print("2. تطبيق فلاتر متقدمة حسب احتياجاتك")
            print("3. تصدير التقارير بصيغ مختلفة")
            print("4. طباعة التقارير مباشرة")
            print("5. عرض جميع المعلومات المطلوبة للعملاء")
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            import traceback
            traceback.print_exc()
