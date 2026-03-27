#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.customer import Customer
from hotel.models.room import Room
from flask import url_for
import json

# اختبار البحث المباشر للحجوزات
app = create_app()

with app.test_client() as client:
    with app.app_context():
        try:
            print("اختبار البحث المباشر للحجوزات...")
            
            # الحصول على أول حجز موجود
            first_booking = Booking.query.first()
            
            if not first_booking:
                print("⚠️ لا توجد حجوزات للاختبار")
                print("قم بإنشاء حجز أولاً من خلال النظام")
                exit(0)
            
            booking_id = first_booking.id
            print(f"اختبار البحث عن الحجز رقم: {booking_id}")
            
            # محاكاة طلب البحث المباشر
            response = client.get(f'/admin/search-bookings?q={booking_id}&ajax=1&direct=1')
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ استجابة ناجحة: {response.status_code}")
                print(f"عدد النتائج: {data.get('count', 0)}")
                
                if data.get('success') and data.get('count') > 0:
                    result = data['results'][0]
                    print(f"✅ تم العثور على الحجز:")
                    print(f"  - ID: {result['id']}")
                    print(f"  - العميل: {result['customer_name']}")
                    print(f"  - الغرفة: {result['room_number']}")
                    print(f"  - الحالة: {result['status_display']}")
                    print(f"  - URL: {result['url']}")
                    
                    # اختبار الرابط
                    booking_response = client.get(result['url'])
                    if booking_response.status_code == 200:
                        print("✅ رابط تفاصيل الحجز يعمل بشكل صحيح")
                    else:
                        print(f"❌ مشكلة في رابط تفاصيل الحجز: {booking_response.status_code}")
                else:
                    print("❌ لم يتم العثور على الحجز في النتائج")
            else:
                print(f"❌ خطأ في الطلب: {response.status_code}")
                print(response.get_data(as_text=True))
            
            # اختبار البحث برقم غير موجود
            print(f"\nاختبار البحث برقم حجز غير موجود...")
            fake_id = 99999
            response = client.get(f'/admin/search-bookings?q={fake_id}&ajax=1&direct=1')
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('count') == 0:
                    print("✅ البحث عن رقم غير موجود يعطي نتيجة صحيحة (0 نتائج)")
                else:
                    print("❌ البحث عن رقم غير موجود يعطي نتائج خاطئة")
            
            print("\n🎉 اختبار البحث المباشر مكتمل!")
            print("يمكنك الآن اختبار الوظيفة في لوحة التحكم:")
            print("1. اذهب إلى لوحة التحكم")
            print(f"2. اكتب رقم الحجز: {booking_id}")
            print("3. اضغط Enter")
            print("4. يجب أن يتم تحويلك مباشرة لتفاصيل الحجز")
            
        except Exception as e:
            print(f"❌ خطأ في الاختبار: {e}")
            import traceback
            traceback.print_exc()
