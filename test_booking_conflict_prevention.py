#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار منع الحجز المزدوج للغرف
"""

import sys
import os
from datetime import date, timedelta

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models.booking import Booking
from hotel.models.room import Room
from hotel.models.customer import Customer
from hotel.models.user import User
from hotel.routes.booking import check_room_availability_for_booking

def test_booking_conflict_prevention():
    """اختبار منع الحجز المزدوج"""
    app = create_app()
    
    with app.app_context():
        print("🔍 اختبار منع الحجز المزدوج للغرف...")
        
        # البحث عن غرفة موجودة
        room = Room.query.first()
        if not room:
            print("❌ لا توجد غرف في النظام")
            return False
            
        print(f"📍 اختبار الغرفة رقم: {room.room_number}")
        
        # البحث عن عميل موجود
        customer = Customer.query.first()
        if not customer:
            print("❌ لا يوجد عملاء في النظام")
            return False
            
        print(f"👤 العميل: {customer.name}")
        
        # البحث عن مستخدم موجود
        user = User.query.first()
        if not user:
            print("❌ لا يوجد مستخدمين في النظام")
            return False
            
        print(f"🔑 المستخدم: {user.username}")
        
        # تواريخ الاختبار
        today = date.today()
        check_in_date = today + timedelta(days=1)
        check_out_date = today + timedelta(days=3)
        
        print(f"📅 تواريخ الاختبار: من {check_in_date} إلى {check_out_date}")
        
        # اختبار 1: التحقق من توفر الغرفة (يجب أن تكون متاحة)
        print("\n🧪 اختبار 1: التحقق من توفر الغرفة...")
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, check_in_date, check_out_date
        )
        
        if is_available:
            print("✅ الغرفة متاحة للحجز")
        else:
            print(f"⚠️ الغرفة محجوزة بالفعل: {conflicting_booking.check_in_date} - {conflicting_booking.check_out_date}")
            # استخدم تواريخ مختلفة
            check_in_date = today + timedelta(days=10)
            check_out_date = today + timedelta(days=12)
            print(f"🔄 تغيير التواريخ إلى: {check_in_date} - {check_out_date}")
            
            is_available, conflicting_booking = check_room_availability_for_booking(
                room.id, check_in_date, check_out_date
            )
            
            if not is_available:
                print("❌ لا يمكن العثور على تواريخ متاحة للاختبار")
                return False
        
        # اختبار 2: إنشاء حجز جديد
        print("\n🧪 اختبار 2: إنشاء حجز جديد...")
        try:
            booking1 = Booking(
                user_id=user.id,
                room_id=room.id,
                customer_id=customer.id,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                occupancy_type='single',
                is_deus=False,
                base_price=800.0,
                total_price=800.0,
                status='confirmed'
            )
            
            db.session.add(booking1)
            db.session.commit()
            print(f"✅ تم إنشاء الحجز الأول بنجاح - رقم الحجز: {booking1.id}")
            
        except Exception as e:
            print(f"❌ فشل في إنشاء الحجز الأول: {str(e)}")
            return False
        
        # اختبار 3: محاولة إنشاء حجز متضارب (يجب أن يفشل)
        print("\n🧪 اختبار 3: محاولة إنشاء حجز متضارب...")
        
        # نفس التواريخ تماماً
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, check_in_date, check_out_date
        )
        
        if not is_available:
            print("✅ تم منع الحجز المتضارب بنجاح - نفس التواريخ")
        else:
            print("❌ فشل في منع الحجز المتضارب - نفس التواريخ")
            return False
        
        # تواريخ متداخلة جزئياً - بداية متداخلة
        overlap_check_in = check_in_date + timedelta(days=1)
        overlap_check_out = check_out_date + timedelta(days=1)
        
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, overlap_check_in, overlap_check_out
        )
        
        if not is_available:
            print("✅ تم منع الحجز المتضارب بنجاح - تداخل جزئي")
        else:
            print("❌ فشل في منع الحجز المتضارب - تداخل جزئي")
            return False
        
        # تواريخ متداخلة - حجز داخلي
        inner_check_in = check_in_date + timedelta(days=1)
        inner_check_out = check_out_date - timedelta(days=1)
        
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, inner_check_in, inner_check_out
        )
        
        if not is_available:
            print("✅ تم منع الحجز المتضارب بنجاح - حجز داخلي")
        else:
            print("❌ فشل في منع الحجز المتضارب - حجز داخلي")
            return False
        
        # اختبار 4: حجز في تواريخ مختلفة (يجب أن ينجح)
        print("\n🧪 اختبار 4: حجز في تواريخ مختلفة...")
        
        future_check_in = check_out_date + timedelta(days=1)
        future_check_out = future_check_in + timedelta(days=2)
        
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, future_check_in, future_check_out
        )
        
        if is_available:
            print("✅ الغرفة متاحة للحجز في تواريخ مختلفة")
        else:
            print("❌ فشل: الغرفة غير متاحة في تواريخ مختلفة")
            return False
        
        # اختبار 5: اختبار استثناء حجز معين (للتعديل)
        print("\n🧪 اختبار 5: اختبار استثناء حجز معين...")
        
        # يجب أن يكون متاحاً عند استثناء الحجز الحالي
        is_available, conflicting_booking = check_room_availability_for_booking(
            room.id, check_in_date, check_out_date, exclude_booking_id=booking1.id
        )
        
        if is_available:
            print("✅ تم استثناء الحجز الحالي بنجاح")
        else:
            print("❌ فشل في استثناء الحجز الحالي")
            return False
        
        # تنظيف: حذف الحجز التجريبي
        print("\n🧹 تنظيف البيانات التجريبية...")
        try:
            db.session.delete(booking1)
            db.session.commit()
            print("✅ تم حذف الحجز التجريبي")
        except Exception as e:
            print(f"⚠️ تحذير: فشل في حذف الحجز التجريبي: {str(e)}")
        
        print("\n🎉 جميع الاختبارات نجحت! نظام منع الحجز المزدوج يعمل بشكل صحيح.")
        return True

if __name__ == '__main__':
    success = test_booking_conflict_prevention()
    if success:
        print("\n✅ الاختبار مكتمل بنجاح")
        sys.exit(0)
    else:
        print("\n❌ فشل الاختبار")
        sys.exit(1)
