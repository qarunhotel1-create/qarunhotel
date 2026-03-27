#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import arabic_reshaper
from bidi.algorithm import get_display

def test_arabic_quick():
    """اختبار سريع للنص العربي"""
    
    test_text = "مرحبا بكم في فندق قارون"
    
    print("Original text:", repr(test_text))
    
    try:
        # الحل البسيط
        reshaped = arabic_reshaper.reshape(test_text)
        result = get_display(reshaped)
        print("Fixed text:", repr(result))
        
        # إنشاء PDF بسيط للاختبار
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        
        # تسجيل خط عربي
        try:
            noto_path = os.path.join('fonts', 'NotoSansArabic-Regular.ttf')
            if os.path.exists(noto_path):
                pdfmetrics.registerFont(TTFont('NotoArabic', noto_path))
                font_name = 'NotoArabic'
            else:
                font_name = 'Helvetica'
        except:
            font_name = 'Helvetica'
        
        # إنشاء PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.fontName = font_name
        
        elements = []
        elements.append(Paragraph(result, style))
        
        doc.build(elements)
        
        # حفظ PDF
        with open('quick_test.pdf', 'wb') as f:
            f.write(buffer.getvalue())
        
        print("PDF created: quick_test.pdf")
        print("SUCCESS: Arabic text formatting working!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_arabic_quick()
