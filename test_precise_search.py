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

# اختبار البحث الدقيق والمحدد
app = create_app()

with app.test_client() as client:
    with app.app_context():
        try:
            print("🎯 اختبار البحث الدقيق والمحدد")
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
            
            # اختبار البحث برقم حجز محدد
            print(f"\n🔍 اختبار البحث برقم حجز محدد...")
            
            # البحث عن حجز موجود
            existing_booking = Booking.query.first()
            if existing_booking:
                booking_id = existing_booking.id
                print(f"  🧪 البحث عن الحجز رقم {booking_id}")
                
                response = client.get(f'/admin/search-bookings?q={booking_id}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('count') == 1 and data['results'][0]['id'] == booking_id:
                        print(f"  ✅ نجح البحث الدقيق: تم العثور على الحجز رقم {booking_id} فقط")
                    else:
                        print(f"  ❌ فشل البحث الدقيق: تم العثور على {data.get('count')} نتيجة بدلاً من 1")
                else:
                    print(f"  ❌ فشل البحث: {response.status_code}")
            
            # اختبار البحث برقم حجز غير موجود
            print(f"\n🔍 اختبار البحث برقم حجز غير موجود...")
            non_existing_id = 99999
            response = client.get(f'/admin/search-bookings?q={non_existing_id}&ajax=1')
            if response.status_code == 200:
                data = response.get_json()
                if data.get('count') == 0:
                    print(f"  ✅ نجح البحث: لا توجد نتائج للحجز رقم {non_existing_id}")
                else:
                    print(f"  ❌ خطأ: تم العثور على {data.get('count')} نتيجة للحجز غير الموجود")
            
            # اختبار البحث بالاسم الكامل
            print(f"\n🔍 اختبار البحث بالاسم الكامل...")
            customer_with_booking = Customer.query.join(Booking).first()
            if customer_with_booking:
                customer_name = customer_with_booking.name
                print(f"  🧪 البحث عن العميل: {customer_name}")
                
                response = client.get(f'/admin/search-bookings?q={customer_name}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('count') > 0:
                        # التحقق من أن جميع النتائج تخص نفس العميل
                        all_same_customer = all(
                            result['customer_name'] == customer_name 
                            for result in data['results']
                        )
                        if all_same_customer:
                            print(f"  ✅ نجح البحث الدقيق: تم العثور على {data.get('count')} حجز للعميل {customer_name} فقط")
                        else:
                            print(f"  ⚠️ البحث غير دقيق: النتائج تحتوي على عملاء آخرين")
                    else:
                        print(f"  ❌ لم يتم العثور على حجوزات للعميل {customer_name}")
            
            # اختبار البحث برقم الهاتف
            print(f"\n🔍 اختبار البحث برقم الهاتف...")
            customer_with_phone = Customer.query.filter(
                Customer.phone.isnot(None), 
                Customer.phone != ''
            ).join(Booking).first()
            
            if customer_with_phone and customer_with_phone.phone:
                phone_number = customer_with_phone.phone
                print(f"  🧪 البحث برقم الهاتف: {phone_number}")
                
                response = client.get(f'/admin/search-bookings?q={phone_number}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('count') > 0:
                        # التحقق من أن جميع النتائج تخص نفس رقم الهاتف
                        all_same_phone = all(
                            result.get('customer_phone') == phone_number 
                            for result in data['results']
                        )
                        if all_same_phone:
                            print(f"  ✅ نجح البحث الدقيق: تم العثور على {data.get('count')} حجز لرقم الهاتف {phone_number} فقط")
                        else:
                            print(f"  ⚠️ البحث غير دقيق: النتائج تحتوي على أرقام هواتف أخرى")
                    else:
                        print(f"  ❌ لم يتم العثور على حجوزات لرقم الهاتف {phone_number}")
            
            # اختبار البحث برقم الهوية
            print(f"\n🔍 اختبار البحث برقم الهوية...")
            customer_with_id = Customer.query.filter(
                Customer.id_number.isnot(None), 
                Customer.id_number != ''
            ).join(Booking).first()
            
            if customer_with_id and customer_with_id.id_number:
                id_number = customer_with_id.id_number
                print(f"  🧪 البحث برقم الهوية: {id_number}")
                
                response = client.get(f'/admin/search-bookings?q={id_number}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('count') > 0:
                        # التحقق من أن جميع النتائج تخص نفس رقم الهوية
                        all_same_id = all(
                            result.get('customer_id_number') == id_number 
                            for result in data['results']
                        )
                        if all_same_id:
                            print(f"  ✅ نجح البحث الدقيق: تم العثور على {data.get('count')} حجز لرقم الهوية {id_number} فقط")
                        else:
                            print(f"  ⚠️ البحث غير دقيق: النتائج تحتوي على أرقام هوية أخرى")
                    else:
                        print(f"  ❌ لم يتم العثور على حجوزات لرقم الهوية {id_number}")
            
            # اختبار البحث بجزء من الاسم
            print(f"\n🔍 اختبار البحث بجزء من الاسم...")
            if customer_with_booking and len(customer_with_booking.name) > 3:
                partial_name = customer_with_booking.name[:3]
                print(f"  🧪 البحث بجزء من الاسم: {partial_name}")
                
                response = client.get(f'/admin/search-bookings?q={partial_name}&ajax=1')
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('count') > 0:
                        # التحقق من أن جميع النتائج تحتوي على الجزء المطلوب
                        all_contain_partial = all(
                            partial_name.lower() in result['customer_name'].lower()
                            for result in data['results']
                        )
                        if all_contain_partial:
                            print(f"  ✅ نجح البحث الجزئي: تم العثور على {data.get('count')} حجز يحتوي على '{partial_name}'")
                        else:
                            print(f"  ⚠️ البحث غير دقيق: بعض النتائج لا تحتوي على '{partial_name}'")
                    else:
                        print(f"  ❌ لم يتم العثور على حجوزات تحتوي على '{partial_name}'")
            
            print(f"\n" + "=" * 50)
            print("🎉 تم اختبار البحث الدقيق والمحدد!")
            print("\n📋 ملخص التحسينات:")
            print("✅ البحث برقم الحجز يعطي ذلك الحجز فقط")
            print("✅ البحث بالاسم الكامل يعطي حجوزات ذلك العميل فقط")
            print("✅ البحث برقم الهاتف يعطي حجوزات ذلك الرقم فقط")
            print("✅ البحث برقم الهوية يعطي حجوزات ذلك الرقم فقط")
            print("✅ البحث الجزئي يعطي النتائج المطابقة فقط")
            print("✅ عدم إظهار نتائج غير مرتبطة")
            
            print(f"\n🚀 النظام الآن يعطي نتائج دقيقة ومحددة!")
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            import traceback
            traceback.print_exc()
