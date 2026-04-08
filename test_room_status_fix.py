#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إصلاح مشكلة عرض حالة الغرف في التقويم
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Room, Booking, Customer
from hotel.utils.datetime_utils import get_egypt_now
from datetime import datetime, date, timedelta

def test_room_status_logic():
    """اختبار منطق تحديد حالة الغرف"""
    
    app = create_app()
    with app.app_context():
        print("🧪 اختبار منطق تحديد حالة الغرف")
        print("=" * 50)
        
        # الحصول على التاريخ والوقت الحالي
        now = get_egypt_now()
        today = now.date()
        current_hour = now.hour
        
        print(f"📅 التاريخ الحالي: {today}")
        print(f"⏰ الوقت الحالي: {now.strftime('%H:%M')}")
        print(f"🕐 الساعة: {current_hour}")
        
        # جلب جميع الغرف
        rooms = Room.query.order_by(Room.room_number).all()
        print(f"🏨 عدد الغرف: {len(rooms)}")
        
        print("\n📋 تفاصيل حالة الغرف:")
        print("-" * 80)
        
        available_rooms = []
        occupied_rooms = []
        reserved_rooms = []
        
        for room in rooms:
            # الحصول على الحجز الحالي باستخدام المنطق الجديد
            current_booking = room.current_booking
            
            # تحديد الحالة
            if current_booking:
                if current_booking.status == 'checked_in':
                    status = "مشغولة (مسجل دخول)"
                    status_color = "🔴"
                    occupied_rooms.append(room.room_number)
                elif current_booking.status == 'confirmed':
                    status = "محجوزة (مؤكدة)"
                    status_color = "🟡"
                    reserved_rooms.append(room.room_number)
                else:
                    status = "متاحة"
                    status_color = "🟢"
                    available_rooms.append(room.room_number)
                
                print(f"{status_color} غرفة {room.room_number:>3}: {status}")
                print(f"    📋 الحجز: {current_booking.booking_code}")
                print(f"    👤 العميل: {current_booking.customer.name}")
                print(f"    📅 من {current_booking.check_in_date} إلى {current_booking.check_out_date}")
                print(f"    📊 الحالة: {current_booking.status}")
                
                # تحقق من منطق التوقيت
                if current_booking.status == 'checked_in':
                    if current_hour < 12:
                        should_be_active = current_booking.check_out_date >= today
                    else:
                        should_be_active = current_booking.check_out_date > today
                    
                    if not should_be_active:
                        print(f"    ⚠️  تحذير: هذا الحجز يجب أن يكون منتهياً!")
                
            else:
                status = "متاحة"
                status_color = "🟢"
                available_rooms.append(room.room_number)
                print(f"{status_color} غرفة {room.room_number:>3}: {status}")
            
            print()
        
        print("📊 ملخص الإحصائيات:")
        print(f"🟢 متاحة ({len(available_rooms)}): {', '.join(available_rooms) if available_rooms else 'لا توجد'}")
        print(f"🔴 مشغولة ({len(occupied_rooms)}): {', '.join(occupied_rooms) if occupied_rooms else 'لا توجد'}")
        print(f"🟡 محجوزة ({len(reserved_rooms)}): {', '.join(reserved_rooms) if reserved_rooms else 'لا توجد'}")
        
        return {
            'available': available_rooms,
            'occupied': occupied_rooms,
            'reserved': reserved_rooms
        }

def test_specific_date_bookings():
    """اختبار الحجوزات لتاريخ محدد (28/8)"""
    
    app = create_app()
    with app.app_context():
        print("\n🔍 اختبار الحجوزات لتاريخ 28/8/2025")
        print("=" * 50)
        
        target_date = date(2025, 8, 28)
        
        # البحث عن جميع الحجوزات التي تتضمن هذا التاريخ
        bookings_on_date = Booking.query.filter(
            Booking.check_in_date <= target_date,
            Booking.check_out_date >= target_date,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).all()
        
        print(f"📅 الحجوزات في {target_date}:")
        
        if not bookings_on_date:
            print("ℹ️ لا توجد حجوزات في هذا التاريخ")
            return
        
        for booking in bookings_on_date:
            print(f"📋 حجز {booking.booking_code}:")
            print(f"    🏨 غرفة: {booking.room.room_number}")
            print(f"    👤 العميل: {booking.customer.name}")
            print(f"    📅 من {booking.check_in_date} إلى {booking.check_out_date}")
            print(f"    📊 الحالة: {booking.status}")
            print(f"    🔄 نوع الحساب: {'ديوز' if booking.is_deus else 'عادي'}")
            print()

def test_room_status_update_function():
    """اختبار دالة تحديث حالة الغرف"""
    
    app = create_app()
    with app.app_context():
        print("\n🔧 اختبار دالة تحديث حالة الغرف")
        print("=" * 50)
        
        try:
            from hotel.utils.room_status_updater import update_room_statuses
            
            print("🔄 تشغيل دالة التحديث...")
            result = update_room_statuses()
            
            if result:
                print("✅ تم تحديث حالة الغرف بنجاح")
            else:
                print("❌ فشل في تحديث حالة الغرف")
            
            # عرض الحالة بعد التحديث
            available_count = Room.query.filter_by(status='available').count()
            occupied_count = Room.query.filter_by(status='occupied').count()
            reserved_count = Room.query.filter_by(status='reserved').count()
            maintenance_count = Room.query.filter_by(status='maintenance').count()
            
            print(f"📊 الحالة بعد التحديث:")
            print(f"   🟢 متاحة: {available_count}")
            print(f"   🔴 مشغولة: {occupied_count}")
            print(f"   🟡 محجوزة: {reserved_count}")
            print(f"   🔧 صيانة: {maintenance_count}")
            
        except Exception as e:
            print(f"❌ خطأ في اختبار دالة التحديث: {e}")
            import traceback
            traceback.print_exc()

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار إصلاح مشكلة عرض حالة الغرف")
    print("=" * 60)
    
    try:
        # 1. اختبار منطق تحديد حالة الغرف
        room_stats = test_room_status_logic()
        
        # 2. اختبار الحجوزات لتاريخ محدد
        test_specific_date_bookings()
        
        # 3. اختبار دالة التحديث
        test_room_status_update_function()
        
        print("\n" + "=" * 60)
        print("✅ اكتمل الاختبار بنجاح!")
        
        # تحليل النتائج
        if len(room_stats['available']) > 1:
            print(f"✅ المشكلة تم حلها! يوجد {len(room_stats['available'])} غرف متاحة")
        else:
            print("⚠️ قد تحتاج المشكلة مراجعة إضافية")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()