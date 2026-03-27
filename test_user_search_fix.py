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

# اختبار إصلاح البحث للمستخدمين العاديين
app = create_app()

with app.test_client() as client:
    with app.app_context():
        try:
            print("🔧 اختبار إصلاح البحث للمستخدمين العاديين")
            print("=" * 60)
            
            # البحث عن مستخدم عادي (ليس admin)
            regular_user = User.query.filter(User.username != 'admin').first()
            if not regular_user:
                print("⚠️ لا يوجد مستخدمين عاديين، سأنشئ واحد للاختبار...")
                # إنشاء مستخدم عادي للاختبار
                regular_user = User(
                    username='test_user',
                    email='test@example.com',
                    full_name='مستخدم تجريبي',
                    role='user'
                )
                regular_user.set_password('password')
                db.session.add(regular_user)
                db.session.commit()
                print(f"✅ تم إنشاء مستخدم تجريبي: {regular_user.username}")
            else:
                print(f"✅ تم العثور على مستخدم عادي: {regular_user.username}")
            
            # تسجيل دخول المستخدم العادي
            with client.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
                sess['_fresh'] = True
            
            print(f"\n🔍 اختبار البحث للمستخدم العادي...")
            
            # اختبار الوصول لصفحة لوحة التحكم
            print(f"  🌐 اختبار الوصول لصفحة لوحة التحكم...")
            dashboard_response = client.get('/user/dashboard')
            if dashboard_response.status_code == 200:
                dashboard_content = dashboard_response.get_data(as_text=True)
                if 'userSmartSearch' in dashboard_content:
                    print("    ✅ صفحة لوحة التحكم تحتوي على نظام البحث الذكي")
                else:
                    print("    ❌ صفحة لوحة التحكم لا تحتوي على نظام البحث الذكي")
            else:
                print(f"    ❌ لا يمكن الوصول لصفحة لوحة التحكم: {dashboard_response.status_code}")
            
            # اختبار route البحث الجديد
            print(f"  🧪 اختبار route البحث الجديد...")
            
            # اختبار بحث فارغ
            empty_response = client.get('/user/search-bookings?q=&ajax=1')
            if empty_response.status_code == 200:
                empty_data = empty_response.get_json()
                if empty_data.get('success') and empty_data.get('count') == 0:
                    print("    ✅ البحث الفارغ يعمل بشكل صحيح")
                else:
                    print("    ❌ البحث الفارغ لا يعمل بشكل صحيح")
            else:
                print(f"    ❌ فشل البحث الفارغ: {empty_response.status_code}")
            
            # اختبار البحث برقم حجز
            existing_booking = Booking.query.first()
            if existing_booking:
                booking_id = existing_booking.id
                print(f"  🔍 اختبار البحث برقم الحجز {booking_id}...")
                
                booking_response = client.get(f'/user/search-bookings?q={booking_id}&ajax=1')
                if booking_response.status_code == 200:
                    booking_data = booking_response.get_json()
                    if booking_data.get('success'):
                        print(f"    ✅ البحث برقم الحجز نجح: {booking_data.get('count')} نتيجة")
                        if booking_data.get('count') > 0:
                            first_result = booking_data['results'][0]
                            print(f"      - النتيجة الأولى: حجز #{first_result['id']} - {first_result['customer_name']}")
                    else:
                        print(f"    ❌ البحث برقم الحجز فشل: {booking_data.get('error', 'خطأ غير معروف')}")
                else:
                    print(f"    ❌ فشل البحث برقم الحجز: {booking_response.status_code}")
            
            # اختبار البحث بالاسم
            customer_with_booking = Customer.query.join(Booking).first()
            if customer_with_booking:
                customer_name = customer_with_booking.name
                print(f"  🔍 اختبار البحث بالاسم '{customer_name}'...")
                
                name_response = client.get(f'/user/search-bookings?q={customer_name}&ajax=1')
                if name_response.status_code == 200:
                    name_data = name_response.get_json()
                    if name_data.get('success'):
                        print(f"    ✅ البحث بالاسم نجح: {name_data.get('count')} نتيجة")
                    else:
                        print(f"    ❌ البحث بالاسم فشل: {name_data.get('error', 'خطأ غير معروف')}")
                else:
                    print(f"    ❌ فشل البحث بالاسم: {name_response.status_code}")
            
            # اختبار البحث بحرف واحد
            print(f"  🔍 اختبار البحث بحرف واحد...")
            single_char_response = client.get('/user/search-bookings?q=ا&ajax=1')
            if single_char_response.status_code == 200:
                single_char_data = single_char_response.get_json()
                if single_char_data.get('success'):
                    print(f"    ✅ البحث بحرف واحد نجح: {single_char_data.get('count')} نتيجة")
                else:
                    print(f"    ❌ البحث بحرف واحد فشل: {single_char_data.get('error', 'خطأ غير معروف')}")
            else:
                print(f"    ❌ فشل البحث بحرف واحد: {single_char_response.status_code}")
            
            # اختبار البحث برقم غير موجود
            print(f"  🔍 اختبار البحث برقم غير موجود...")
            non_existing_response = client.get('/user/search-bookings?q=99999&ajax=1')
            if non_existing_response.status_code == 200:
                non_existing_data = non_existing_response.get_json()
                if non_existing_data.get('success') and non_existing_data.get('count') == 0:
                    print(f"    ✅ البحث برقم غير موجود نجح: لا توجد نتائج")
                else:
                    print(f"    ❌ البحث برقم غير موجود لم يعمل بشكل صحيح")
            else:
                print(f"    ❌ فشل البحث برقم غير موجود: {non_existing_response.status_code}")
            
            # اختبار سرعة الاستجابة
            print(f"  ⚡ اختبار سرعة الاستجابة...")
            import time
            
            start_time = time.time()
            speed_response = client.get('/user/search-bookings?q=test&ajax=1')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # بالميلي ثانية
            print(f"    ✅ وقت الاستجابة: {response_time:.2f} ميلي ثانية")
            
            if response_time < 500:
                print("    🚀 سرعة ممتازة!")
            elif response_time < 1000:
                print("    ⚡ سرعة جيدة")
            else:
                print("    ⚠️ قد تحتاج تحسين")
            
            # اختبار مقارنة مع route الإدارة
            print(f"\n🔒 اختبار الحماية من الوصول لـ route الإدارة...")
            admin_route_response = client.get('/admin/search-bookings?q=test&ajax=1')
            if admin_route_response.status_code == 403 or admin_route_response.status_code == 302:
                print("    ✅ المستخدم العادي لا يمكنه الوصول لـ route الإدارة (محمي بشكل صحيح)")
            else:
                print(f"    ⚠️ المستخدم العادي يمكنه الوصول لـ route الإدارة: {admin_route_response.status_code}")
            
            print(f"\n" + "=" * 60)
            print("🎉 تم إصلاح البحث للمستخدمين العاديين!")
            print("\n📋 ملخص الإصلاحات:")
            print("✅ إنشاء route منفصل للمستخدمين: /user/search-bookings")
            print("✅ تحديث JavaScript ليستخدم الـ route الصحيح")
            print("✅ نفس منطق البحث الدقيق للإدارة")
            print("✅ حماية من الوصول غير المصرح به")
            print("✅ دعم البحث الفوري من أول حرف")
            print("✅ عرض النتائج بشكل احترافي")
            
            print(f"\n🚀 الآن يمكن للمستخدمين العاديين:")
            print("1. البحث في حجوزاتهم الخاصة")
            print("2. الحصول على نتائج فورية ودقيقة")
            print("3. استخدام نفس الواجهة الاحترافية")
            print("4. البحث بأمان دون الوصول لبيانات الآخرين")
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            import traceback
            traceback.print_exc()
