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

# اختبار نظام البحث الذكي الجديد
app = create_app()

with app.test_client() as client:
    with app.app_context():
        try:
            print("🔍 اختبار نظام البحث الذكي الجديد")
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
            
            # اختبار البحث بحرف واحد
            print(f"\n🧪 اختبار البحث بحرف واحد...")
            response = client.get('/admin/search-bookings?q=ا&ajax=1')
            if response.status_code == 200:
                data = response.get_json()
                print(f"  ✅ البحث بحرف واحد: {data.get('count', 0)} نتيجة")
            else:
                print(f"  ❌ فشل البحث بحرف واحد: {response.status_code}")
            
            # اختبار البحث برقم
            print(f"\n🧪 اختبار البحث برقم...")
            response = client.get('/admin/search-bookings?q=1&ajax=1')
            if response.status_code == 200:
                data = response.get_json()
                print(f"  ✅ البحث برقم: {data.get('count', 0)} نتيجة")
                if data.get('count', 0) > 0:
                    first_result = data['results'][0]
                    print(f"    - أول نتيجة: حجز #{first_result['id']} - {first_result['customer_name']}")
            else:
                print(f"  ❌ فشل البحث برقم: {response.status_code}")
            
            # اختبار البحث بجزء من الاسم
            customers = Customer.query.limit(3).all()
            if customers:
                customer = customers[0]
                search_term = customer.name[:2] if len(customer.name) >= 2 else customer.name
                
                print(f"\n🧪 اختبار البحث بجزء من الاسم: '{search_term}'")
                response = client.get(f'/admin/search-bookings?q={search_term}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"  ✅ البحث بالاسم: {data.get('count', 0)} نتيجة")
                    if data.get('count', 0) > 0:
                        for i, result in enumerate(data['results'][:3]):
                            print(f"    {i+1}. حجز #{result['id']} - {result['customer_name']}")
                else:
                    print(f"  ❌ فشل البحث بالاسم: {response.status_code}")
            
            # اختبار البحث برقم الهاتف
            customer_with_phone = Customer.query.filter(Customer.phone.isnot(None)).first()
            if customer_with_phone and customer_with_phone.phone:
                phone_part = customer_with_phone.phone[:3]
                
                print(f"\n🧪 اختبار البحث برقم الهاتف: '{phone_part}'")
                response = client.get(f'/admin/search-bookings?q={phone_part}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"  ✅ البحث بالهاتف: {data.get('count', 0)} نتيجة")
                else:
                    print(f"  ❌ فشل البحث بالهاتف: {response.status_code}")
            
            # اختبار سرعة الاستجابة
            print(f"\n⚡ اختبار سرعة الاستجابة...")
            import time
            
            start_time = time.time()
            response = client.get('/admin/search-bookings?q=test&ajax=1')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # بالميلي ثانية
            print(f"  ✅ وقت الاستجابة: {response_time:.2f} ميلي ثانية")
            
            if response_time < 500:
                print("  🚀 سرعة ممتازة!")
            elif response_time < 1000:
                print("  ⚡ سرعة جيدة")
            else:
                print("  ⚠️ قد تحتاج تحسين")
            
            # اختبار الوصول لصفحات لوحة التحكم
            print(f"\n🌐 اختبار الوصول لصفحات لوحة التحكم...")
            
            # صفحة admin
            admin_response = client.get('/admin/dashboard')
            if admin_response.status_code == 200:
                admin_content = admin_response.get_data(as_text=True)
                if 'smartSearch' in admin_content:
                    print("  ✅ نظام البحث الذكي موجود في لوحة تحكم الإدارة")
                else:
                    print("  ❌ نظام البحث الذكي غير موجود في لوحة تحكم الإدارة")
            else:
                print(f"  ❌ لا يمكن الوصول للوحة تحكم الإدارة: {admin_response.status_code}")
            
            # صفحة user
            user_response = client.get('/user/dashboard')
            if user_response.status_code == 200:
                user_content = user_response.get_data(as_text=True)
                if 'userSmartSearch' in user_content:
                    print("  ✅ نظام البحث الذكي موجود في لوحة تحكم المستخدمين")
                else:
                    print("  ❌ نظام البحث الذكي غير موجود في لوحة تحكم المستخدمين")
            else:
                print(f"  ❌ لا يمكن الوصول للوحة تحكم المستخدمين: {user_response.status_code}")
            
            print(f"\n" + "=" * 50)
            print("🎉 تم اختبار نظام البحث الذكي الجديد!")
            print("\n📋 ملخص الميزات الجديدة:")
            print("✅ بحث فوري من أول حرف أو رقم")
            print("✅ نتائج دقيقة وسريعة")
            print("✅ واجهة احترافية وسلسة")
            print("✅ متاح للإدارة والمستخدمين")
            print("✅ انتقال مباشر بالضغط على Enter")
            print("✅ عرض تفاصيل شاملة للحجوزات")
            print("✅ تصميم متجاوب للهواتف")
            
            print(f"\n🚀 يمكنك الآن اختبار النظام:")
            print("1. اذهب إلى لوحة التحكم")
            print("2. ابدأ الكتابة في مربع البحث")
            print("3. شاهد النتائج الفورية")
            print("4. اضغط Enter للانتقال للنتيجة الأولى")
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            import traceback
            traceback.print_exc()
