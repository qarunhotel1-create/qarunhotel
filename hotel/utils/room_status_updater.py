# -*- coding: utf-8 -*-
"""
دالة تحديث حالة الغرف تلقائياً
"""


def update_room_statuses():
    """تحديث حالة الغرف تلقائياً بناءً على الحجوزات النشطة"""
    from hotel.models import Room, Booking
    from hotel.utils.datetime_utils import get_egypt_now
    from hotel import db
    from datetime import date
    
    today = get_egypt_now().date()
    rooms = Room.query.all()
    
    for room in rooms:
        # البحث عن الحجوزات النشطة للغرفة
        active_bookings = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.status.in_(['confirmed', 'checked_in']),
            Booking.check_in_date <= today,
            Booking.check_out_date >= today
        ).all()
        
        # تحديد حالة الغرفة
        if active_bookings:
            booking = active_bookings[0]
            if booking.status == 'checked_in':
                new_status = 'occupied'
            elif booking.status == 'confirmed':
                new_status = 'reserved'
            else:
                new_status = 'available'
        else:
            if room.status != 'maintenance':
                new_status = 'available'
            else:
                new_status = room.status
        
        room.status = new_status
    
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تحديث حالة الغرف: {e}")
        return False
