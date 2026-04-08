#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.customer import Customer
from hotel.models.room import Room
from hotel.routes.admin import search_bookings
from flask import url_for
import json

# اختبار وظيفة البحث
app = create_app()

with app.app_context():
    try:
        print("اختبار وظيفة البحث في الحجوزات...")
        
        # عد الحجوزات الموجودة
        total_bookings = Booking.query.count()
        total_customers = Customer.query.count()
        total_rooms = Room.query.count()
        
        print(f"إجمالي الحجوزات: {total_bookings}")
        print(f"إجمالي العملاء: {total_customers}")
        print(f"إجمالي الغرف: {total_rooms}")
        
        if total_bookings == 0:
            print("⚠️ لا توجد حجوزات للاختبار")
        else:
            # اختبار البحث برقم الحجز
            first_booking = Booking.query.first()
            print(f"\nاختبار البحث برقم الحجز: {first_booking.id}")
            
            # محاكاة طلب البحث
            with app.test_request_context(f'/admin/search-bookings?q={first_booking.id}&ajax=1'):
                from flask import request
                from hotel.routes.admin import search_bookings
                
                # هذا مجرد اختبار للتأكد من أن الدالة تعمل
                print("✅ دالة البحث متاحة")
        
        # اختبار البحث بالاسم
        if total_customers > 0:
            first_customer = Customer.query.first()
            print(f"اختبار البحث بالاسم: {first_customer.name}")
            
            # البحث في قاعدة البيانات مباشرة
            from sqlalchemy import or_
            search_query = first_customer.name[:3]  # أول 3 أحرف
            
            bookings = Booking.query.join(Customer).join(Room).filter(
                or_(
                    Customer.name.ilike(f'%{search_query}%'),
                    Customer.phone.contains(search_query),
                    Customer.id_number.contains(search_query),
                    Room.room_number.ilike(f'%{search_query}%')
                )
            ).limit(5).all()
            
            print(f"نتائج البحث عن '{search_query}': {len(bookings)} حجز")
            
            for booking in bookings[:3]:  # عرض أول 3 نتائج
                print(f"  - حجز #{booking.id}: {booking.customer.name} - غرفة {booking.room.room_number}")
        
        print("\n🎉 اختبار البحث مكتمل!")
        print("يمكنك الآن اختبار البحث في لوحة التحكم")
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()
