#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

try:
    from hotel import create_app, db
    from hotel.models import Customer, Room
    
    app = create_app()
    with app.app_context():
        # إضافة عملاء تجريبيين
        test_customers = [
            {'name': 'أحمد محمد علي', 'id_number': '12345678901234', 'phone': '01012345678'},
            {'name': 'فاطمة أحمد حسن', 'id_number': '98765432109876', 'phone': '01098765432'},
            {'name': 'محمد عبد الله', 'id_number': '11111111111111', 'phone': '01111111111'},
        ]
        
        for customer_data in test_customers:
            existing = Customer.query.filter_by(id_number=customer_data['id_number']).first()
            if not existing:
                customer = Customer(
                    name=customer_data['name'],
                    id_number=customer_data['id_number'],
                    phone=customer_data['phone'],
                    email=f"{customer_data['name'].split()[0]}@example.com"
                )
                db.session.add(customer)
        
        db.session.commit()
        
        # عرض العملاء
        customers = Customer.query.all()
        print(f"✅ عدد العملاء: {len(customers)}")
        
        # عرض الغرف
        rooms = Room.query.all()
        print(f"✅ عدد الغرف: {len(rooms)}")
        
        print("✅ النظام جاهز للاختبار!")
        
except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
