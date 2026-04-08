#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from flask import Flask
from hotel import create_app, db
from hotel.models import Booking, Customer, Room
from datetime import datetime, timedelta

def test_report_directly():
    """اختبار مباشر لتقرير PDF"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # الحصول على بيانات للاختبار
            bookings = Booking.query.limit(3).all()
            
            # إحصائيات بسيطة
            stats = {
                'total_bookings': 10,
                'confirmed_bookings': 5,
                'pending_bookings': 3,
                'cancelled_bookings': 2,
                'total_revenue': 5000.0,
                'average_price': 500.0
            }
            
            filters = {
                'start_date': '2025-01-01',
                'end_date': '2025-01-31'
            }
            
            # استيراد دالة التقرير
            from hotel.routes.reports import generate_pdf_report
            
            # إنشاء التقرير
            response = generate_pdf_report(bookings, stats, filters)
            
            # استخراج البيانات من Response
            if hasattr(response, 'data'):
                pdf_data = response.data
            elif hasattr(response, 'get_data'):
                pdf_data = response.get_data()
            else:
                pdf_data = response
            
            # حفظ PDF
            with open('arabic_test_report.pdf', 'wb') as f:
                f.write(pdf_data)
            
            print("SUCCESS: PDF report created - arabic_test_report.pdf")
            print("Please open the PDF file to check if Arabic text is now displayed correctly.")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_report_directly()
