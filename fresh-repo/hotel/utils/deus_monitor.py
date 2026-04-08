#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from hotel import db
from hotel.models.booking import Booking

def check_expired_deus():
    """فحص الديوز المنتهي وإرسال إشعارات"""
    try:
        # البحث عن حجوزات الديوز النشطة التي انتهت
        now = datetime.now()
        expired_bookings = Booking.query.filter(
            Booking.is_deus == True,
            Booking.deus_start_time.isnot(None),
            Booking.deus_end_time <= now,
            Booking.deus_expired == False,
            Booking.status == 'checked_in'
        ).all()
        
        notifications = []
        
        for booking in expired_bookings:
            # تحديث حالة الديوز إلى منتهي
            booking.deus_expired = True
            
            # إنشاء إشعار
            notification = {
                'booking_id': booking.id,
                'customer_name': booking.customer.name,
                'room_number': booking.room.room_number,
                'expired_time': booking.deus_end_time,
                'message': f'انتهت فترة الديوز للعميل {booking.customer.name} في الغرفة {booking.room.room_number}'
            }
            notifications.append(notification)
            
            print(f"⏰ انتهى الديوز: العميل {booking.customer.name} - الغرفة {booking.room.room_number}")
        
        if expired_bookings:
            db.session.commit()
            print(f"✅ تم تحديث {len(expired_bookings)} حجز ديوز منتهي")
        
        return notifications
        
    except Exception as e:
        print(f"❌ خطأ في فحص الديوز المنتهي: {e}")
        db.session.rollback()
        return []

def get_active_deus_bookings():
    """الحصول على جميع حجوزات الديوز النشطة"""
    try:
        now = datetime.now()
        active_bookings = Booking.query.filter(
            Booking.is_deus == True,
            Booking.deus_start_time.isnot(None),
            Booking.deus_expired == False,
            Booking.status == 'checked_in'
        ).all()
        
        result = []
        for booking in active_bookings:
            remaining_minutes = booking.deus_remaining_time
            result.append({
                'booking_id': booking.id,
                'customer_name': booking.customer.name,
                'room_number': booking.room.room_number,
                'start_time': booking.deus_start_time,
                'end_time': booking.deus_end_time,
                'remaining_minutes': remaining_minutes,
                'status': 'منتهي' if remaining_minutes <= 0 else f'متبقي {remaining_minutes} دقيقة'
            })
        
        return result
        
    except Exception as e:
        print(f"❌ خطأ في الحصول على الديوز النشط: {e}")
        return []

def send_deus_warning(booking, minutes_left):
    """إرسال تحذير قبل انتهاء الديوز"""
    try:
        warning = {
            'booking_id': booking.id,
            'customer_name': booking.customer.name,
            'room_number': booking.room.room_number,
            'minutes_left': minutes_left,
            'message': f'تحذير: سينتهي الديوز للعميل {booking.customer.name} في الغرفة {booking.room.room_number} خلال {minutes_left} دقيقة'
        }
        
        print(f"⚠️ تحذير الديوز: {warning['message']}")
        return warning
        
    except Exception as e:
        print(f"❌ خطأ في إرسال تحذير الديوز: {e}")
        return None

def check_deus_warnings():
    """فحص الديوز الذي سينتهي قريباً وإرسال تحذيرات"""
    try:
        now = datetime.now()
        active_bookings = Booking.query.filter(
            Booking.is_deus == True,
            Booking.deus_start_time.isnot(None),
            Booking.deus_expired == False,
            Booking.status == 'checked_in'
        ).all()
        
        warnings = []
        
        for booking in active_bookings:
            remaining_minutes = booking.deus_remaining_time
            
            # إرسال تحذيرات في 30، 15، 5 دقائق
            if remaining_minutes in [30, 15, 5]:
                warning = send_deus_warning(booking, remaining_minutes)
                if warning:
                    warnings.append(warning)
        
        return warnings
        
    except Exception as e:
        print(f"❌ خطأ في فحص تحذيرات الديوز: {e}")
        return []
