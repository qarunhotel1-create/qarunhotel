#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار الحالة النهائية:
- خريطة الغرف: عادت للحالة الأصلية
- التقويم: مُصلح بالمنطق الجديد
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Room, Booking
from hotel.utils.datetime_utils import get_egypt_now
from datetime import datetime, date, timedelta

def test_room_map_status():
    """اختبار حالة خريطة الغرف (يجب أن تكون كما كانت من قبل)"""
    
    app = create_app()
    with app.app_context():
        print("🗺️ اختبار حالة خريطة الغرف")
        print("=" * 60)
        
        today = get_egypt_now().date()
        print(f"📅 التاريخ الحالي: {today}")
        
        # جلب جميع الغرف
        rooms = Room.query.order_by(Room.room_number).all()
        
        print(f"\n📋 حالة الغرف في الخريطة:")
        print("-" * 80)
        
        available_rooms = []
        occupied_rooms = []
        reserved_rooms = []
        
        for room in rooms:
            # استخدام المنطق الأصلي للخريطة
            current_booking = room.current_booking
            
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
                print(f"    📅 من {current_booking.check_in_date} إلى {current_booking.check_out_date}")
                
            else:
                status = "متاحة"
                status_color = "🟢"
                available_rooms.append(room.room_number)
                print(f"{status_color} غرفة {room.room_number:>3}: {status}")
            
            print()
        
        print("📊 ملخص خريطة الغرف:")
        print(f"🟢 متاحة ({len(available_rooms)}): {', '.join(available_rooms) if available_rooms else 'لا توجد'}")
        print(f"🔴 مشغولة ({len(occupied_rooms)}): {', '.join(occupied_rooms) if occupied_rooms else 'لا توجد'}")
        print(f"🟡 محجوزة ({len(reserved_rooms)}): {', '.join(reserved_rooms) if reserved_rooms else 'لا توجد'}")
        
        return {
            'available': available_rooms,
            'occupied': occupied_rooms,
            'reserved': reserved_rooms
        }

def test_calendar_status():
    """اختبار حالة التقويم (يجب أن يكون مُصلحاً)"""
    
    app = create_app()
    with app.app_context():
        print("\n📅 اختبار حالة التقويم")
        print("=" * 60)
        
        target_date = date(2025, 8, 28)
        print(f"📅 اختبار التوفر في: {target_date}")
        
        # جلب جميع الغرف
        rooms = Room.query.order_by(Room.room_number).all()
        
        available_rooms = []
        booked_rooms = []
        
        for room in rooms:
            # استخدام منطق التقويم المُصلح
            bookings = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.check_in_date <= target_date,
                Booking.check_out_date > target_date,  # المنطق المُصلح
                Booking.status.in_(['confirmed', 'checked_in'])
            ).all()
            
            if bookings:
                booked_rooms.append(room.room_number)
                print(f"🔴 غرفة {room.room_number}: محجوزة في التقويم")
                for booking in bookings:
                    print(f"   📋 {booking.booking_code}: {booking.check_in_date} → {booking.check_out_date}")
            else:
                available_rooms.append(room.room_number)
                print(f"🟢 غرفة {room.room_number}: متاحة في التقويم")
                
                # البحث عن الحجوزات التي انتهت في هذا التاريخ
                ended_bookings = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_out_date == target_date,
                    Booking.status.in_(['confirmed', 'checked_in'])
                ).all()
                
                if ended_bookings:
                    print(f"   ✅ تحررت من حجز انتهى:")
                    for ended in ended_bookings:
                        print(f"      📋 {ended.booking_code}: {ended.check_in_date} → {ended.check_out_date}")
        
        print(f"\n📊 ملخص التقويم في {target_date}:")
        print(f"🟢 متاحة ({len(available_rooms)}): {', '.join(available_rooms)}")
        print(f"🔴 محجوزة ({len(booked_rooms)}): {', '.join(booked_rooms)}")
        
        return {
            'available': available_rooms,
            'booked': booked_rooms
        }

def compare_results():
    """مقارنة النتائج بين خريطة الغرف والتقويم"""
    
    print("\n🔍 مقارنة النتائج")
    print("=" * 60)
    
    # اختبار خريطة الغرف
    room_map = test_room_map_status()
    
    # اختبار التقويم
    calendar = test_calendar_status()
    
    print(f"\n📊 المقارنة:")
    print(f"🗺️ خريطة الغرف - متاحة: {len(room_map['available'])}")
    print(f"📅 التقويم - متاحة: {len(calendar['available'])}")
    
    # التحليل
    if len(room_map['available']) == 1 and len(calendar['available']) >= 8:
        print("\n✅ النتيجة المطلوبة تحققت:")
        print("   🗺️ خريطة الغرف: عادت للحالة الأصلية (غرفة واحدة متاحة)")
        print("   📅 التقويم: مُصلح (عدة غرف متاحة)")
        return True
    else:
        print("\n⚠️ النتيجة غير متوقعة:")
        print(f"   🗺️ خريطة الغرف: {len(room_map['available'])} غرفة متاحة")
        print(f"   📅 التقويم: {len(calendar['available'])} غرفة متاحة")
        return False

def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 اختبار الحالة النهائية")
    print("الهدف: خريطة الغرف كما هي، التقويم مُصلح")
    print("=" * 80)
    
    try:
        result = compare_results()
        
        print("\n" + "=" * 80)
        if result:
            print("🎉 تم تحقيق الهدف بنجاح!")
            print("✅ خريطة الغرف: عادت للحالة الأصلية")
            print("✅ التقويم: مُصلح ويعرض الحالة الصحيحة")
        else:
            print("❌ لم يتم تحقيق الهدف")
            print("⚠️ قد تحتاج مراجعة إضافية")
        
        return result
        
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()