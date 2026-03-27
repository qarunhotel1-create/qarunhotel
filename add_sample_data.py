#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
إضافة بيانات تجريبية للنظام
"""

import sys
import os
from datetime import datetime, date, timedelta
import random

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models.user import User, ROLE_ADMIN
from hotel.models.customer import Customer
from hotel.models.room import Room
from hotel.models.booking import Booking, BOOKING_STATUS_PENDING, BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_CHECKED_IN, BOOKING_STATUS_CHECKED_OUT

def add_sample_customers():
    """إضافة عملاء تجريبيين"""
    
    sample_customers = [
        {
            'name': 'أحمد محمد علي',
            'id_number': '29012345678901',
            'nationality': 'مصري',
            'marital_status': 'متزوج/ة',
            'phone': '01012345678',
            'address': 'القاهرة، مصر الجديدة، شارع الحجاز'
        },
        {
            'name': 'فاطمة أحمد حسن',
            'id_number': '29112345678902',
            'nationality': 'مصري',
            'marital_status': 'أعزب',
            'phone': '01123456789',
            'address': 'الجيزة، المهندسين، شارع جامعة الدول العربية'
        },
        {
            'name': 'محمد عبد الرحمن',
            'id_number': '28512345678903',
            'nationality': 'مصري',
            'marital_status': 'متزوج/ة',
            'phone': '01234567890',
            'address': 'الإسكندرية، سيدي جابر، شارع الكورنيش'
        },
        {
            'name': 'سارة محمود إبراهيم',
            'id_number': '29312345678904',
            'nationality': 'مصري',
            'marital_status': 'أعزب',
            'phone': '01098765432',
            'address': 'القاهرة، مدينة نصر، الحي الأول'
        },
        {
            'name': 'عمر خالد محمد',
            'id_number': '28812345678905',
            'nationality': 'مصري',
            'marital_status': 'متزوج/ة',
            'phone': '01187654321',
            'address': 'الجيزة، الدقي، شارع التحرير'
        },
        {
            'name': 'نور الدين أحمد',
            'id_number': '29512345678906',
            'nationality': 'مصري',
            'marital_status': 'أعزب',
            'phone': '01276543210',
            'address': 'القاهرة، الزمالك، شارع 26 يوليو'
        },
        {
            'name': 'ليلى حسام الدين',
            'id_number': '29012345678907',
            'nationality': 'مصري',
            'marital_status': 'أرمل/ة',
            'phone': '01165432109',
            'address': 'الإسكندرية، المنتزه، شارع الجيش'
        },
        {
            'name': 'يوسف عبد الله',
            'id_number': '28712345678908',
            'nationality': 'مصري',
            'marital_status': 'متزوج/ة',
            'phone': '01054321098',
            'address': 'القاهرة، مصر القديمة، شارع المعز'
        },
        {
            'name': 'مريم صلاح الدين',
            'id_number': '29212345678909',
            'nationality': 'مصري',
            'marital_status': 'أعزب',
            'phone': '01143210987',
            'address': 'الجيزة، الهرم، شارع الهرم'
        },
        {
            'name': 'كريم محمد فتحي',
            'id_number': '28912345678910',
            'nationality': 'مصري',
            'marital_status': 'متزوج/ة',
            'phone': '01032109876',
            'address': 'القاهرة، شبرا، شارع شبرا'
        }
    ]
    
    customers = []
    for customer_data in sample_customers:
        # التحقق من عدم وجود العميل
        existing = Customer.query.filter_by(id_number=customer_data['id_number']).first()
        if not existing:
            customer = Customer(
                name=customer_data['name'],
                id_number=customer_data['id_number'],
                nationality=customer_data['nationality'],
                marital_status=customer_data['marital_status'],
                phone=customer_data['phone'],
                address=customer_data['address']
            )
            db.session.add(customer)
            customers.append(customer)
    
    db.session.commit()
    print(f"✅ تم إضافة {len(customers)} عميل تجريبي")
    return customers

def add_sample_bookings():
    """إضافة حجوزات تجريبية"""
    
    # الحصول على المستخدم الإداري
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("❌ لم يتم العثور على المستخدم الإداري")
        return []
    
    # الحصول على العملاء والغرف
    customers = Customer.query.all()
    rooms = Room.query.all()
    
    if not customers or not rooms:
        print("❌ لا توجد عملاء أو غرف في النظام")
        return []
    
    bookings = []
    today = date.today()
    
    # إنشاء حجوزات متنوعة
    booking_scenarios = [
        # حجوزات سابقة (منتهية)
        {
            'check_in': today - timedelta(days=10),
            'check_out': today - timedelta(days=7),
            'status': BOOKING_STATUS_CHECKED_OUT,
            'occupancy_type': 'single',
            'is_deus': False
        },
        {
            'check_in': today - timedelta(days=15),
            'check_out': today - timedelta(days=12),
            'status': BOOKING_STATUS_CHECKED_OUT,
            'occupancy_type': 'double',
            'is_deus': False
        },
        # حجوزات حالية (نشطة)
        {
            'check_in': today - timedelta(days=2),
            'check_out': today + timedelta(days=3),
            'status': BOOKING_STATUS_CHECKED_IN,
            'occupancy_type': 'single',
            'is_deus': False
        },
        {
            'check_in': today - timedelta(days=1),
            'check_out': today + timedelta(days=2),
            'status': BOOKING_STATUS_CHECKED_IN,
            'occupancy_type': 'triple',
            'is_deus': True  # حجز ديوز
        },
        # حجوزات مستقبلية
        {
            'check_in': today + timedelta(days=3),
            'check_out': today + timedelta(days=6),
            'status': BOOKING_STATUS_CONFIRMED,
            'occupancy_type': 'double',
            'is_deus': False
        },
        {
            'check_in': today + timedelta(days=7),
            'check_out': today + timedelta(days=10),
            'status': BOOKING_STATUS_PENDING,
            'occupancy_type': 'single',
            'is_deus': False
        },
        {
            'check_in': today + timedelta(days=5),
            'check_out': today + timedelta(days=8),
            'status': BOOKING_STATUS_CONFIRMED,
            'occupancy_type': 'triple',
            'is_deus': True  # حجز ديوز
        }
    ]
    
    # أسعار حسب نوع الإقامة
    occupancy_prices = {
        'single': 800,
        'double': 1100,
        'triple': 1400
    }
    
    for i, scenario in enumerate(booking_scenarios):
        if i >= len(customers) or i >= len(rooms):
            break
            
        customer = customers[i]
        room = rooms[i % len(rooms)]
        
        # حساب السعر
        base_price = occupancy_prices[scenario['occupancy_type']]
        discount_percentage = random.choice([0, 5, 10, 15]) if not scenario['is_deus'] else 0
        total_price = base_price * (1 - discount_percentage / 100)
        
        # حساب المبلغ المدفوع
        if scenario['status'] == BOOKING_STATUS_CHECKED_OUT:
            paid_amount = total_price  # مدفوع بالكامل
        elif scenario['status'] == BOOKING_STATUS_CHECKED_IN:
            paid_amount = total_price * random.choice([0.5, 0.7, 1.0])  # مدفوع جزئياً أو كاملاً
        else:
            paid_amount = total_price * random.choice([0, 0.3, 0.5])  # مقدم أو غير مدفوع
        
        booking = Booking(
            user_id=admin_user.id,
            room_id=room.id,
            customer_id=customer.id,
            check_in_date=scenario['check_in'],
            check_out_date=scenario['check_out'],
            occupancy_type=scenario['occupancy_type'],
            is_deus=scenario['is_deus'],
            base_price=base_price,
            discount_percentage=discount_percentage,
            total_price=total_price,
            paid_amount=paid_amount,
            notes=f"حجز تجريبي - {scenario['occupancy_type']}"
        )
        booking.status = scenario['status']
        
        # إضافة معلومات الديوز للحجوزات النشطة
        if scenario['is_deus'] and scenario['status'] == BOOKING_STATUS_CHECKED_IN:
            booking.deus_start_time = datetime.combine(scenario['check_in'], datetime.min.time()) + timedelta(hours=14)  # 2 PM
            booking.deus_end_time = booking.deus_start_time + timedelta(hours=6)  # 6 ساعات
        
        db.session.add(booking)
        bookings.append(booking)
    
    db.session.commit()
    print(f"✅ تم إضافة {len(bookings)} حجز تجريبي")
    return bookings

def main():
    """الدالة الرئيسية"""
    app = create_app()
    
    with app.app_context():
        print("🚀 بدء إضافة البيانات التجريبية...")
        
        # إضافة العملاء
        customers = add_sample_customers()
        
        # إضافة الحجوزات
        bookings = add_sample_bookings()
        
        print("\n📊 ملخص البيانات المضافة:")
        print(f"   • العملاء: {len(customers)}")
        print(f"   • الحجوزات: {len(bookings)}")
        print("\n✅ تم إضافة جميع البيانات التجريبية بنجاح!")
        print("\n💡 يمكنك الآن تسجيل الدخول والتحقق من البيانات في النظام")

if __name__ == '__main__':
    main()
