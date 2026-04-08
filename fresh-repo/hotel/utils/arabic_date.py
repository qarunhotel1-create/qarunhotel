# -*- coding: utf-8 -*-
"""
دوال مساعدة للتاريخ العربي
"""

from datetime import date, datetime

def get_arabic_date(date_obj=None, include_time=False):
    """
    تحويل التاريخ إلى تنسيق عربي
    
    Args:
        date_obj: كائن التاريخ (افتراضي: اليوم الحالي)
        include_time: هل نضيف الوقت أم لا
    
    Returns:
        str: التاريخ بالعربية
    """
    if date_obj is None:
        date_obj = date.today()
    
    # إذا كان datetime، نأخذ التاريخ فقط
    if isinstance(date_obj, datetime):
        if include_time:
            time_str = date_obj.strftime('%H:%M')
        date_obj = date_obj.date()
    
    arabic_days = {
        0: 'الاثنين',
        1: 'الثلاثاء', 
        2: 'الأربعاء',
        3: 'الخميس',
        4: 'الجمعة',
        5: 'السبت',
        6: 'الأحد'
    }
    
    arabic_months = {
        1: 'يناير',
        2: 'فبراير',
        3: 'مارس',
        4: 'أبريل',
        5: 'مايو',
        6: 'يونيو',
        7: 'يوليو',
        8: 'أغسطس',
        9: 'سبتمبر',
        10: 'أكتوبر',
        11: 'نوفمبر',
        12: 'ديسمبر'
    }
    
    day_name = arabic_days[date_obj.weekday()]
    month_name = arabic_months[date_obj.month]
    
    result = f"{day_name}، {date_obj.day} {month_name} {date_obj.year}"
    
    if include_time and 'time_str' in locals():
        result += f" - {time_str}"
    
    return result

def get_arabic_month(month_num):
    """
    الحصول على اسم الشهر بالعربية
    
    Args:
        month_num: رقم الشهر (1-12)
    
    Returns:
        str: اسم الشهر بالعربية
    """
    arabic_months = {
        1: 'يناير',
        2: 'فبراير',
        3: 'مارس',
        4: 'أبريل',
        5: 'مايو',
        6: 'يونيو',
        7: 'يوليو',
        8: 'أغسطس',
        9: 'سبتمبر',
        10: 'أكتوبر',
        11: 'نوفمبر',
        12: 'ديسمبر'
    }
    
    return arabic_months.get(month_num, str(month_num))

def get_arabic_day(day_num):
    """
    الحصول على اسم اليوم بالعربية
    
    Args:
        day_num: رقم اليوم (0=الاثنين، 6=الأحد)
    
    Returns:
        str: اسم اليوم بالعربية
    """
    arabic_days = {
        0: 'الاثنين',
        1: 'الثلاثاء', 
        2: 'الأربعاء',
        3: 'الخميس',
        4: 'الجمعة',
        5: 'السبت',
        6: 'الأحد'
    }
    
    return arabic_days.get(day_num, str(day_num))

def format_date_simple(date_obj):
    """
    تنسيق التاريخ بشكل بسيط (بدون اسم اليوم)
    
    Args:
        date_obj: كائن التاريخ
    
    Returns:
        str: التاريخ بالعربية (مثل: 31 يوليو 2025)
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    month_name = get_arabic_month(date_obj.month)
    return f"{date_obj.day} {month_name} {date_obj.year}"
