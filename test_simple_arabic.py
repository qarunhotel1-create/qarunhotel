#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار مبسط لتنسيق النص العربي
"""

import arabic_reshaper
from bidi.algorithm import get_display

def test_arabic_text():
    """اختبار تنسيق النص العربي"""
    
    test_texts = [
        "تاريخ إنشاء التقرير: 2025-08-09 03:49:01",
        "عدد الحجوزات: 10"
    ]
    
    print("=== اختبار تنسيق النص العربي ===")
    
    for text in test_texts:
        print(f"\nالنص الأصلي: {text}")
        
        # الطريقة الأساسية
        reshaped = arabic_reshaper.reshape(text)
        bidi_basic = get_display(reshaped)
        print(f"الطريقة الأساسية: {bidi_basic}")
        
        # فحص إذا كان معكوس
        if bidi_basic and len(bidi_basic) > 0:
            first_char = bidi_basic[0]
            if first_char.isascii() and (first_char.isalnum() or first_char in '()[]{}'):
                reversed_text = bidi_basic[::-1]
                print(f"بعد العكس: {reversed_text}")
                print("الحالة: تم العكس")
            else:
                print("الحالة: لا حاجة للعكس")

if __name__ == "__main__":
    test_arabic_text()
