#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محاكاة حالة الغرف بعد 12 ظهراً لاختبار الإصلاح
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Room, Booking
from datetime import datetime, date, timedelta

def simulate_afternoon_room_status():
    """محاكاة حالة الغرف بعد 12 ظهراً"""
    
    app = create_app()
    with app.app_context():
        print("🕐 محاكاة حالة الغرف بعد 12 ظهراً")
        print("=" * 50)
        
        today = date(2025, 8, 28)
        simulated_hour = 14  # 2 PM
        
        print(f"📅 التاريخ: {today}")
        print(f"⏰ الوقت المحاكى: {simulated_hour}:00")
        
        # جلب جميع الغرف
        rooms = Room.query.order_by(Room.room_number).all()
        
        print(f"\n📋 حالة الغرف بعد 12 ظهراً:")
        print("-" * 60)
        
        available_rooms = []
        occupied_rooms = []
        reserved_rooms = []
        
        for room in rooms:
            # البحث عن الحجوزات النشطة للغرفة
            active_bookings = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.status.in_(['confirmed', 'checked_in']),
                Booking.check_in_date <= today
            ).all()
            
            # تطبيق منطق ما بعد 12 ظهراً
            current_booking = None
            
            for booking in active_bookings:
                is_still_active = False
                
                if booking.status == 'checked_in':
                    # بعد 12 ظهراً: يوم المغادرة يصبح متاحاً
                    is_still_active = booking.check_out_date > today
                
                elif booking.status == 'confirmed':
                    # الحجوزات المؤكدة: تظهر في يوم الدخول بعد 1 PM
                    if booking.check_in_date == today and simulated_hour >= 13:
                        is_still_active = booking.check_out_date > today
                    elif booking.check_in_date < today:
                        is_still_active = booking.check_out_date > today
                
                if is_still_active:
                    current_booking = booking
                    break
            
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
                print(f"    📅 من {current_booking.check_in_date} إلى {current_booking.check_out_date}")
                
            else:
                status = "متاحة"
                status_color = "🟢"
                available_rooms.append(room.room_number)
                print(f"{status_color} غرفة {room.room_number:>3}: {status}")
                
                # البحث عن الحجوزات التي انتهت اليوم
                ended_bookings = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_out_date == today,
                    Booking.status == 'checked_in'
                ).all()
                
                if ended_bookings:
                    print(f"    ✅ تم تحرير الغرفة (انتهى الحجز)")
                    for ended in ended_bookings:
                        print(f"    📋 الحجز المنتهي: {ended.booking_code}")
        
        print(f"\n📊 ملخص الحالة بعد 12 ظهراً:")
        print(f"🟢 متاحة ({len(available_rooms)}): {', '.join(available_rooms) if available_rooms else 'لا توجد'}")
        print(f"🔴 مشغولة ({len(occupied_rooms)}): {', '.join(occupied_rooms) if occupied_rooms else 'لا توجد'}")
        print(f"🟡 محجوزة ({len(reserved_rooms)}): {', '.join(reserved_rooms) if reserved_rooms else 'لا توجد'}")
        
        # مقارنة مع الحالة الحالية
        current_available = Room.query.filter_by(status='available').count()
        print(f"\n📈 المقارنة:")
        print(f"   الحالة الحالية (قبل 12 ظهراً): {current_available} غرفة متاحة")
        print(f"   الحالة المتوقعة (بعد 12 ظهراً): {len(available_rooms)} غرفة متاحة")
        print(f"   الفرق: +{len(available_rooms) - current_available} غرفة ستصبح متاحة")
        
        return {
            'available': available_rooms,
            'occupied': occupied_rooms,
            'reserved': reserved_rooms
        }

def check_bookings_ending_today():
    """فحص الحجوزات التي تنتهي اليوم"""
    
    app = create_app()
    with app.app_context():
        print("\n🔍 الحجوزات التي تنتهي اليوم (28/8)")
        print("=" * 50)
        
        today = date(2025, 8, 28)
        
        ending_bookings = Booking.query.filter(
            Booking.check_out_date == today,
            Booking.status == 'checked_in'
        ).all()
        
        if not ending_bookings:
            print("ℹ️ لا توجد حجوزات تنتهي اليوم")
            return
        
        print(f"📋 الحجوزات التي تنتهي في {today}:")
        
        for booking in ending_bookings:
            print(f"🏨 غرفة {booking.room.room_number}: {booking.booking_code}")
            print(f"   👤 العميل: {booking.customer.name}")
            print(f"   📅 من {booking.check_in_date} إلى {booking.check_out_date}")
            print(f"   ✅ ستصبح متاحة بعد 12 ظهراً")
            print()

def main():
    """الدالة الرئيسية"""
    print("🕐 محاكاة تأثير الإصلاح بعد 12 ظهراً")
    print("=" * 60)
    
    try:
        # 1. فحص الحجوزات التي تنتهي اليوم
        check_bookings_ending_today()
        
        # 2. محاكاة حالة الغرف بعد 12 ظهراً
        afternoon_stats = simulate_afternoon_room_status()
        
        print("\n" + "=" * 60)
        print("✅ المحاكاة اكتملت!")
        
        if len(afternoon_stats['available']) > 1:
            print("🎉 الإصلاح يعمل بشكل صحيح!")
            print("   الغرف ستصبح متاحة تلقائياً بعد 12 ظهراً")
        else:
            print("⚠️ قد تحتاج المراجعة")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في المحاكاة: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()