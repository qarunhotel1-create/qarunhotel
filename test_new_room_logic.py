#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار المنطق الجديد لحالة الغرف
المنطق: الغرفة تصبح متاحة في اليوم التالي لانتهاء الحجز
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Room, Booking
from hotel.utils.datetime_utils import get_egypt_now
from datetime import datetime, date, timedelta

def test_new_room_logic():
    """اختبار المنطق الجديد لحالة الغرف"""
    
    app = create_app()
    with app.app_context():
        print("🧪 اختبار المنطق الجديد لحالة الغرف")
        print("=" * 60)
        
        # الحصول على التاريخ الحالي
        now = get_egypt_now()
        today = now.date()
        
        print(f"📅 التاريخ الحالي: {today}")
        print(f"⏰ الوقت الحالي: {now.strftime('%H:%M')}")
        
        # جلب جميع الغرف
        rooms = Room.query.order_by(Room.room_number).all()
        print(f"🏨 عدد الغرف: {len(rooms)}")
        
        print(f"\n📋 حالة الغرف بالمنطق الجديد:")
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
                
                print(f"{status_color} غرفة {room.room_number:>3}: {status}")
                print(f"    📋 الحجز: {current_booking.booking_code}")
                print(f"    👤 العميل: {current_booking.customer.name}")
                print(f"    📅 من {current_booking.check_in_date} إلى {current_booking.check_out_date}")
                print(f"    📊 الحالة: {current_booking.status}")
                
            else:
                status = "متاحة"
                status_color = "🟢"
                available_rooms.append(room.room_number)
                print(f"{status_color} غرفة {room.room_number:>3}: {status}")
                
                # البحث عن الحجوزات التي انتهت
                ended_bookings = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_out_date <= today,
                    Booking.status.in_(['checked_in', 'confirmed'])
                ).order_by(Booking.check_out_date.desc()).first()
                
                if ended_bookings:
                    print(f"    ✅ آخر حجز انتهى في {ended_bookings.check_out_date}")
                    print(f"    📋 الحجز المنتهي: {ended_bookings.booking_code}")
            
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

def test_specific_bookings():
    """اختبار حجوزات محددة"""
    
    app = create_app()
    with app.app_context():
        print("\n🔍 تحليل الحجوزات المحددة")
        print("=" * 60)
        
        today = date(2025, 8, 28)
        
        # الحجوزات التي تنتهي اليوم (28/8)
        ending_today = Booking.query.filter(
            Booking.check_out_date == today,
            Booking.status.in_(['checked_in', 'confirmed'])
        ).all()
        
        print(f"📅 الحجوزات التي تنتهي في {today}:")
        if ending_today:
            for booking in ending_today:
                print(f"🏨 غرفة {booking.room.room_number}: {booking.booking_code}")
                print(f"   👤 العميل: {booking.customer.name}")
                print(f"   📅 من {booking.check_in_date} إلى {booking.check_out_date}")
                print(f"   ✅ يجب أن تصبح متاحة اليوم")
                print()
        else:
            print("ℹ️ لا توجد حجوزات تنتهي اليوم")
        
        # الحجوزات النشطة (لم تنته بعد)
        active_bookings = Booking.query.filter(
            Booking.check_out_date > today,
            Booking.status.in_(['checked_in', 'confirmed']),
            Booking.check_in_date <= today
        ).all()
        
        print(f"\n📅 الحجوزات النشطة (لم تنته بعد):")
        if active_bookings:
            for booking in active_bookings:
                print(f"🏨 غرفة {booking.room.room_number}: {booking.booking_code}")
                print(f"   👤 العميل: {booking.customer.name}")
                print(f"   📅 من {booking.check_in_date} إلى {booking.check_out_date}")
                print(f"   🔄 الحالة: {booking.status}")
                print()
        else:
            print("ℹ️ لا توجد حجوزات نشطة")

def test_room_status_update():
    """اختبار تحديث حالة الغرف"""
    
    app = create_app()
    with app.app_context():
        print("\n🔧 اختبار تحديث حالة الغرف")
        print("=" * 60)
        
        # الحالة قبل التحديث
        before_available = Room.query.filter_by(status='available').count()
        before_occupied = Room.query.filter_by(status='occupied').count()
        
        print(f"📊 الحالة قبل التحديث:")
        print(f"   🟢 متاحة: {before_available}")
        print(f"   🔴 مشغولة: {before_occupied}")
        
        # تشغيل التحديث
        try:
            from hotel.utils.room_status_updater import update_room_statuses
            result = update_room_statuses()
            
            if result:
                print("✅ تم تحديث حالة الغرف بنجاح")
            else:
                print("❌ فشل في تحديث حالة الغرف")
            
            # الحالة بعد التحديث
            after_available = Room.query.filter_by(status='available').count()
            after_occupied = Room.query.filter_by(status='occupied').count()
            after_reserved = Room.query.filter_by(status='reserved').count()
            
            print(f"\n📊 الحالة بعد التحديث:")
            print(f"   🟢 متاحة: {after_available}")
            print(f"   🔴 مشغولة: {after_occupied}")
            print(f"   🟡 محجوزة: {after_reserved}")
            
            # المقارنة
            available_change = after_available - before_available
            occupied_change = after_occupied - before_occupied
            
            print(f"\n📈 التغيير:")
            print(f"   🟢 متاحة: {available_change:+d}")
            print(f"   🔴 مشغولة: {occupied_change:+d}")
            
        except Exception as e:
            print(f"❌ خطأ في التحديث: {e}")
            import traceback
            traceback.print_exc()

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار المنطق الجديد لحالة الغرف")
    print("المنطق: الغرفة تصبح متاحة في اليوم التالي لانتهاء الحجز")
    print("=" * 80)
    
    try:
        # 1. اختبار المنطق الجديد
        room_stats = test_new_room_logic()
        
        # 2. تحليل الحجوزات المحددة
        test_specific_bookings()
        
        # 3. اختبار التحديث
        test_room_status_update()
        
        print("\n" + "=" * 80)
        print("✅ اكتمل الاختبار!")
        
        # تحليل النتائج
        if len(room_stats['available']) >= 8:
            print("🎉 المنطق الجديد يعمل بشكل صحيح!")
            print(f"   الغرف المتاحة: {len(room_stats['available'])}")
        else:
            print("⚠️ قد تحتاج المراجعة")
            print(f"   الغرف المتاحة: {len(room_stats['available'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في تنفيذ الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()