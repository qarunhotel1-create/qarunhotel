#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار إصلاح منطق التقويم
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Room, Booking
from hotel.utils.datetime_utils import get_egypt_now
from datetime import datetime, date, timedelta

def test_calendar_logic():
    """اختبار منطق التقويم الجديد"""
    
    app = create_app()
    with app.app_context():
        print("📅 اختبار منطق التقويم الجديد")
        print("=" * 60)
        
        # محاكاة منطق التقويم من user.py
        start_date = get_egypt_now().date()
        end_date = start_date + timedelta(days=7)  # أسبوع واحد للاختبار
        calendar_dates = [start_date + timedelta(days=i) for i in range(7)]
        
        print(f"📅 نطاق التقويم: من {start_date} إلى {end_date}")
        print(f"📅 التواريخ: {[str(d) for d in calendar_dates]}")
        
        # جلب الحجوزات النشطة للتقويم
        active_bookings = Booking.query.filter(
            Booking.check_in_date < end_date,
            Booking.check_out_date > start_date,
            Booking.status.in_(['confirmed', 'checked_in'])
        ).all()
        
        print(f"\n📋 الحجوزات النشطة في النطاق ({len(active_bookings)}):")
        for booking in active_bookings:
            print(f"   🏨 غرفة {booking.room.room_number}: {booking.booking_code}")
            print(f"      📅 من {booking.check_in_date} إلى {booking.check_out_date}")
            print(f"      📊 الحالة: {booking.status}")
        
        # تجميع الحجوزات حسب الغرفة
        bookings_by_room = {}
        for b in active_bookings:
            bookings_by_room.setdefault(b.room_id, []).append(b)
        
        def is_booked_on_day(bookings_list, day):
            """تحديد ما إذا كانت الغرفة محجوزة في يوم معين"""
            for b in bookings_list:
                if b.check_in_date <= day < b.check_out_date:
                    return True
            return False
        
        # جلب الغرف وبناء التقويم
        rooms = Room.query.order_by(Room.room_number).all()
        
        print(f"\n📅 تقويم الغرف:")
        print("-" * 80)
        
        # عرض رأس التقويم
        header = "غرفة  "
        for d in calendar_dates:
            header += f"{d.strftime('%d/%m'):>8}"
        print(header)
        print("-" * 80)
        
        total_available_days = 0
        total_booked_days = 0
        
        for room in rooms:
            bks = bookings_by_room.get(room.id, [])
            statuses = []
            row = f"{room.room_number:>3}   "
            
            for day in calendar_dates:
                is_booked = is_booked_on_day(bks, day)
                if is_booked:
                    row += "   🔴   "
                    statuses.append('booked')
                    total_booked_days += 1
                else:
                    row += "   🟢   "
                    statuses.append('available')
                    total_available_days += 1
            
            print(row)
            
            # عرض تفاصيل الحجوزات للغرفة
            if bks:
                for booking in bks:
                    print(f"      📋 {booking.booking_code}: {booking.check_in_date} → {booking.check_out_date}")
        
        print("-" * 80)
        print(f"📊 الإحصائيات:")
        print(f"   🟢 أيام متاحة: {total_available_days}")
        print(f"   🔴 أيام محجوزة: {total_booked_days}")
        print(f"   📈 نسبة الإشغال: {(total_booked_days / (total_available_days + total_booked_days) * 100):.1f}%")
        
        return {
            'available_days': total_available_days,
            'booked_days': total_booked_days,
            'calendar_dates': calendar_dates
        }

def test_specific_date_availability():
    """اختبار توفر الغرف في تاريخ محدد"""
    
    app = create_app()
    with app.app_context():
        print(f"\n🔍 اختبار توفر الغرف في 28/8/2025")
        print("=" * 60)
        
        target_date = date(2025, 8, 28)
        
        # جلب جميع الغرف
        rooms = Room.query.order_by(Room.room_number).all()
        
        available_rooms = []
        booked_rooms = []
        
        for room in rooms:
            # البحث عن الحجوزات التي تشمل هذا التاريخ
            bookings = Booking.query.filter(
                Booking.room_id == room.id,
                Booking.check_in_date <= target_date,
                Booking.check_out_date > target_date,  # المنطق الجديد: < بدلاً من <=
                Booking.status.in_(['confirmed', 'checked_in'])
            ).all()
            
            if bookings:
                booked_rooms.append(room.room_number)
                print(f"🔴 غرفة {room.room_number}: محجوزة")
                for booking in bookings:
                    print(f"   📋 {booking.booking_code}: {booking.check_in_date} → {booking.check_out_date}")
            else:
                available_rooms.append(room.room_number)
                print(f"🟢 غرفة {room.room_number}: متاحة")
                
                # البحث عن الحجوزات التي انتهت في هذا التاريخ
                ended_bookings = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_out_date == target_date,
                    Booking.status.in_(['confirmed', 'checked_in'])
                ).all()
                
                if ended_bookings:
                    print(f"   ✅ تحررت من حجز انتهى اليوم:")
                    for ended in ended_bookings:
                        print(f"      📋 {ended.booking_code}: {ended.check_in_date} → {ended.check_out_date}")
        
        print(f"\n📊 ملخص التوفر في {target_date}:")
        print(f"🟢 متاحة ({len(available_rooms)}): {', '.join(available_rooms)}")
        print(f"🔴 محجوزة ({len(booked_rooms)}): {', '.join(booked_rooms)}")
        
        return {
            'available': available_rooms,
            'booked': booked_rooms,
            'date': target_date
        }

def main():
    """الدالة الرئيسية للاختبار"""
    print("📅 اختبار إصلاح منطق التقويم")
    print("المنطق الجديد: الحجز نشط من يوم الدخول حتى اليوم السابق للمغادرة")
    print("=" * 80)
    
    try:
        # 1. اختبار منطق التقويم
        calendar_stats = test_calendar_logic()
        
        # 2. اختبار توفر الغرف في تاريخ محدد
        availability_stats = test_specific_date_availability()
        
        print("\n" + "=" * 80)
        print("✅ اكتمل اختبار التقويم!")
        
        # تحليل النتائج
        if len(availability_stats['available']) >= 8:
            print("🎉 إصلاح التقويم نجح!")
            print(f"   الغرف المتاحة في 28/8: {len(availability_stats['available'])}")
            print("   الغرف التي انتهت حجوزاتها أصبحت متاحة")
        else:
            print("⚠️ قد تحتاج مراجعة إضافية")
            print(f"   الغرف المتاحة في 28/8: {len(availability_stats['available'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التقويم: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()