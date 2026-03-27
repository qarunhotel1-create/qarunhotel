#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع لتنسيق النص العربي في تقارير PDF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel.routes.reports import format_arabic_text

def test_arabic_formatting():
    """اختبار تنسيق النص العربي"""
    
    test_texts = [
        "تاريخ إنشاء التقرير: 2025-08-09 03:49:01",
        "عدد الحجوزات: 10",
        "الإحصائيات العامة",
        "تفاصيل الحجوزات",
        "اسم العميل",
        "الجنسية",
        "مصري",
        "سعودي",
        "كويتي"
    ]
    
    print("=== اختبار تنسيق النص العربي ===")
    print()
    
    for text in test_texts:
        try:
            # محاكاة دالة format_arabic_text من reports.py
            import arabic_reshaper
            from bidi.algorithm import get_display
            
            # تطبيق arabic_reshaper مع إعدادات محسنة
            reshaped_text = arabic_reshaper.reshape(
                text,
                support_ligatures=True,
                delete_harakat=False
            )
            
            # تطبيق get_display() مع base_dir='RTL'
            bidi_text = get_display(reshaped_text, base_dir='RTL')
            
            # فحص ذكي محسن
            if bidi_text and len(bidi_text) > 0:
                first_char = bidi_text[0]
                if first_char.isascii() and (first_char.isalnum() or first_char in '()[]{}'):
                    final_text = bidi_text[::-1]
                    print(f"النص الأصلي: {text}")
                    print(f"بعد المعالجة: {final_text}")
                    print(f"تم العكس: نعم")
                    print("---")
                else:
                    print(f"النص الأصلي: {text}")
                    print(f"بعد المعالجة: {bidi_text}")
                    print(f"تم العكس: لا")
                    print("---")
            
        except Exception as e:
            print(f"خطأ في معالجة '{text}': {e}")
            print("---")

if __name__ == "__main__":
    test_arabic_formatting()
