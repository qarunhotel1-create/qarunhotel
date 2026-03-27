#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار حل مشكلة النص العربي المعكوس في PDF
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display

def test_arabic_solutions():
    """اختبار حلول مختلفة للنص العربي"""
    
    test_text = "مرحباً بكم في فندق قارون - Welcome to Qarun Hotel"
    
    print("اختبار حلول مختلفة للنص العربي:")
    print(f"النص الأصلي: {test_text}")
    print("-" * 50)
    
    # الحل الأول: arabic_reshaper + bidi مع RTL
    try:
        reshaped = arabic_reshaper.reshape(test_text)
        solution1 = get_display(reshaped, base_dir='RTL')
        print(f"الحل 1 (RTL): {solution1}")
    except Exception as e:
        print(f"خطأ في الحل 1: {e}")
    
    # الحل الثاني: arabic_reshaper + bidi مع LTR
    try:
        reshaped = arabic_reshaper.reshape(test_text)
        solution2 = get_display(reshaped, base_dir='LTR')
        print(f"الحل 2 (LTR): {solution2}")
    except Exception as e:
        print(f"خطأ في الحل 2: {e}")
    
    # الحل الثالث: arabic_reshaper فقط
    try:
        solution3 = arabic_reshaper.reshape(test_text)
        print(f"الحل 3 (reshaper only): {solution3}")
    except Exception as e:
        print(f"خطأ في الحل 3: {e}")
    
    # الحل الرابع: bidi فقط
    try:
        solution4 = get_display(test_text, base_dir='RTL')
        print(f"الحل 4 (bidi only): {solution4}")
    except Exception as e:
        print(f"خطأ في الحل 4: {e}")

def format_arabic_text_improved(text):
    """دالة محسنة لتنسيق النص العربي"""
    if not text or not isinstance(text, str):
        return str(text) if text else ""
    
    try:
        # التحقق من وجود نص عربي
        has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
        
        if has_arabic:
            # الحل المحسن: استخدام إعدادات أكثر دقة
            reshaped_text = arabic_reshaper.reshape(
                text,
                configuration={
                    'delete_harakat': False,
                    'support_zwj': True,
                    'use_unshaped_instead_of_isolated': False,
                    'shift_harakat_position': False,
                    'support_ligatures': True,
                    'delete_tatweel': False,
                    'support_arabic_digits': True,
                    'support_persian_digits': True
                }
            )
            
            # تجربة إعدادات مختلفة لـ bidi
            bidi_text = get_display(reshaped_text, base_dir='RTL')
            return bidi_text
        else:
            return text
            
    except Exception as e:
        print(f"خطأ في تنسيق النص: {e}")
        # حل بديل بسيط
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except:
            return text

def create_test_pdf():
    """إنشاء PDF تجريبي لاختبار النص العربي"""
    
    # إعداد الخط العربي
    arabic_font = 'Helvetica'
    
    # تجربة تسجيل خط Amiri
    try:
        amiri_path = os.path.join('fonts', 'Amiri-1.000', 'Amiri-Regular.ttf')
        if os.path.exists(amiri_path):
            pdfmetrics.registerFont(TTFont('AmiriFont', amiri_path))
            arabic_font = 'AmiriFont'
            print(f"تم تسجيل خط Amiri: {amiri_path}")
        else:
            print(f"لم يتم العثور على خط Amiri في: {amiri_path}")
    except Exception as e:
        print(f"خطأ في تسجيل خط Amiri: {e}")
    
    # تجربة خط Noto Sans Arabic كبديل
    try:
        noto_path = os.path.join('fonts', 'NotoSansArabic-Regular.ttf')
        if os.path.exists(noto_path):
            pdfmetrics.registerFont(TTFont('NotoArabic', noto_path))
            arabic_font = 'NotoArabic'
            print(f"تم تسجيل خط Noto Arabic: {noto_path}")
    except Exception as e:
        print(f"خطأ في تسجيل خط Noto: {e}")
    
    # إنشاء PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # إعداد الأنماط
    styles = getSampleStyleSheet()
    
    # نمط للعناوين العربية
    arabic_title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Heading1'],
        fontName=arabic_font,
        fontSize=16,
        alignment=2,  # محاذاة يمين
        spaceAfter=20
    )
    
    # نمط للنص العربي العادي
    arabic_normal_style = ParagraphStyle(
        'ArabicNormal',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=12,
        alignment=2,  # محاذاة يمين
        spaceAfter=12
    )
    
    # عناصر PDF
    elements = []
    
    # اختبار نصوص مختلفة
    test_texts = [
        "مرحباً بكم في فندق قارون",
        "تقرير الحجوزات اليومي",
        "العميل: أحمد محمد علي",
        "الغرفة رقم: 101",
        "تاريخ الوصول: 2025-01-15",
        "المبلغ الإجمالي: 500.00 جنيه",
        "حالة الحجز: مؤكد"
    ]
    
    # إضافة العنوان
    title = Paragraph(format_arabic_text_improved("اختبار النص العربي في PDF"), arabic_title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # اختبار النصوص
    for i, text in enumerate(test_texts, 1):
        formatted_text = format_arabic_text_improved(text)
        elements.append(Paragraph(f"{i}. {formatted_text}", arabic_normal_style))
    
    elements.append(Spacer(1, 20))
    
    # اختبار جدول
    table_data = [
        [format_arabic_text_improved('البيان'), format_arabic_text_improved('القيمة')],
        [format_arabic_text_improved('اسم الفندق'), format_arabic_text_improved('فندق قارون')],
        [format_arabic_text_improved('عدد الغرف'), '50'],
        [format_arabic_text_improved('عدد الحجوزات'), '25'],
        [format_arabic_text_improved('الإيرادات'), format_arabic_text_improved('12,500 جنيه')]
    ]
    
    table = Table(table_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), arabic_font),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # بناء PDF
    doc.build(elements)
    
    # حفظ الملف
    with open('test_arabic_output.pdf', 'wb') as f:
        f.write(buffer.getvalue())
    
    print("تم إنشاء ملف test_arabic_output.pdf للاختبار")
    return buffer.getvalue()

if __name__ == "__main__":
    print("Starting Arabic text solutions test...")
    test_arabic_solutions()
    print("\nCreating test PDF...")
    create_test_pdf()
    print("Test completed!")
