#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تشخيص مشكلة Internal Server Error في dashboard
"""

import os
import sys
import traceback
from datetime import date

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_components():
    """اختبار مكونات dashboard واحد تلو الآخر"""
    print("بدء تشخيص مشكلة dashboard...")
    
    try:
        # 1. اختبار الاستيراد الأساسي
        print("\n1. اختبار الاستيراد الأساسي...")
        from hotel import create_app, db
        from hotel.models import User, Room, Booking, Customer, Payment, Permission, ActivityLog
        print("الاستيراد الأساسي نجح")
        
        # 2. إنشاء التطبيق
        print("\n2. إنشاء التطبيق...")
        app = create_app()
        print("إنشاء التطبيق نجح")
        
        # 3. اختبار الاتصال بقاعدة البيانات
        print("\n3. اختبار الاتصال بقاعدة البيانات...")
        with app.app_context():
            total_rooms = Room.query.count()
            print(f"عدد الغرف: {total_rooms}")
            
            total_bookings = Booking.query.count()
            print(f"عدد الحجوزات: {total_bookings}")
            
            total_customers = Customer.query.count()
            print(f"عدد العملاء: {total_customers}")
        
        # 4. اختبار arabic_date
        print("\n4. اختبار arabic_date...")
        from hotel.utils.arabic_date import get_arabic_date
        today = date.today()
        today_formatted = get_arabic_date(today)
        print(f"التاريخ العربي: {today_formatted}")
        
        # 5. اختبار الاستعلامات المعقدة
        print("\n5. اختبار الاستعلامات المعقدة...")
        with app.app_context():
            all_rooms = Room.query.order_by(Room.room_number).all()
            print(f"عدد الغرف المرتبة: {len(all_rooms)}")
            
            # اختبار استعلام الحجوزات النشطة
            active_bookings = Booking.query.filter(
                Booking.status.in_(['pending', 'confirmed', 'checked_in'])
            ).count()
            print(f"الحجوزات النشطة: {active_bookings}")
            
            # اختبار الحجوزات الحديثة
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
            print(f"الحجوزات الحديثة: {len(recent_bookings)}")
        
        # 6. اختبار منطق حالة الغرف
        print("\n6. اختبار منطق حالة الغرف...")
        with app.app_context():
            rooms_tested = 0
            for room in all_rooms[:5]:  # اختبار أول 5 غرف فقط
                try:
                    # البحث عن حجز عادي
                    normal_booking = Booking.query.filter(
                        Booking.room_id == room.id,
                        Booking.check_in_date <= today,
                        Booking.check_out_date > today,
                        Booking.is_deus == False,
                        Booking.status.in_(['confirmed', 'checked_in'])
                    ).first()
                    
                    # البحث عن حجز ديوز
                    deus_booking = Booking.query.filter(
                        Booking.room_id == room.id,
                        Booking.check_in_date <= today,
                        Booking.check_out_date >= today,
                        Booking.is_deus == True,
                        Booking.status == 'checked_in'
                    ).first()
                    
                    active_booking = normal_booking or deus_booking
                    rooms_tested += 1
                    
                except Exception as e:
                    print(f"خطأ في اختبار الغرفة {room.room_number}: {e}")
                    return False
            
            print(f"تم اختبار {rooms_tested} غرفة بنجاح")
        
        # 7. محاكاة dashboard كاملة
        print("\n7. محاكاة dashboard كاملة...")
        with app.app_context():
            # إحصائيات أساسية
            total_rooms = Room.query.count()
            available_rooms = Room.query.filter_by(status='available').count()
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter(Booking.status.in_(['pending', 'confirmed', 'checked_in'])).count()
            total_customers = Customer.query.count()
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
            
            # حالة الغرف
            all_rooms = Room.query.order_by(Room.room_number).all()
            rooms_status = []
            
            for room in all_rooms:
                normal_booking = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_in_date <= today,
                    Booking.check_out_date > today,
                    Booking.is_deus == False,
                    Booking.status.in_(['confirmed', 'checked_in'])
                ).first()
                
                deus_booking = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_in_date <= today,
                    Booking.check_out_date >= today,
                    Booking.is_deus == True,
                    Booking.status == 'checked_in'
                ).first()
                
                active_booking = normal_booking or deus_booking
                
                room_class = 'available'
                status_text = 'فارغة'
                status_icon = 'fas fa-door-open'
                
                if active_booking:
                    if active_booking.is_deus:
                        room_class = 'occupied'
                        status_text = 'ديوز نشط'
                        status_icon = 'fas fa-clock'
                    else:
                        room_class = 'occupied'
                        status_text = 'محجوزة'
                        status_icon = 'fas fa-user'
                
                room_info = {
                    'room': room,
                    'is_occupied': active_booking is not None,
                    'booking': active_booking,
                    'status_class': room_class,
                    'status_text': status_text,
                    'status_icon': status_icon
                }
                rooms_status.append(room_info)
            
            occupied_today = sum(1 for room in rooms_status if room['is_occupied'])
            available_today = total_rooms - occupied_today
            
            print(f"محاكاة dashboard نجحت:")
            print(f"   - إجمالي الغرف: {total_rooms}")
            print(f"   - الغرف المتاحة: {available_rooms}")
            print(f"   - إجمالي الحجوزات: {total_bookings}")
            print(f"   - الحجوزات النشطة: {active_bookings}")
            print(f"   - إجمالي العملاء: {total_customers}")
            print(f"   - المحجوزة اليوم: {occupied_today}")
            print(f"   - المتاحة اليوم: {available_today}")
            print(f"   - التاريخ: {today_formatted}")
        
        print("\nجميع الاختبارات نجحت! dashboard يجب أن يعمل بشكل طبيعي.")
        return True
        
    except Exception as e:
        print(f"\nخطأ في التشخيص: {e}")
        print(f"نوع الخطأ: {type(e).__name__}")
        print("\nتفاصيل الخطأ:")
        traceback.print_exc()
        return False

def test_template_rendering():
    """اختبار عرض القالب"""
    print("\nاختبار عرض القالب...")
    
    try:
        from hotel import create_app
        from flask import render_template
        
        app = create_app()
        
        with app.app_context():
            # محاولة عرض قالب dashboard
            template_path = 'admin/dashboard.html'
            
            # بيانات وهمية للاختبار
            test_data = {
                'title': 'لوحة التحكم',
                'total_rooms': 10,
                'available_rooms': 5,
                'total_bookings': 20,
                'active_bookings': 8,
                'total_customers': 15,
                'recent_bookings': [],
                'rooms_status': [],
                'occupied_today': 5,
                'available_today': 5,
                'today': date.today(),
                'today_formatted': 'الاثنين، 12 أغسطس 2025'
            }
            
            # محاولة عرض القالب
            rendered = render_template(template_path, **test_data)
            print(f"عرض القالب نجح - حجم المحتوى: {len(rendered)} حرف")
            return True
            
    except Exception as e:
        print(f"خطأ في عرض القالب: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("تشخيص مشكلة Internal Server Error في Dashboard")
    print("=" * 60)
    
    # اختبار المكونات
    components_ok = test_dashboard_components()
    
    # اختبار القالب
    template_ok = test_template_rendering()
    
    print("\n" + "=" * 60)
    if components_ok and template_ok:
        print("التشخيص: لا توجد مشاكل واضحة في الكود")
        print("المشكلة قد تكون في:")
        print("   - صلاحيات المستخدم (permission_required)")
        print("   - حالة تسجيل الدخول (login_required)")
        print("   - مشكلة في الخادم أو البيئة")
    else:
        print("تم العثور على مشاكل - راجع الأخطاء أعلاه")
    print("=" * 60)
