from flask import Blueprint
from datetime import datetime
from hotel.utils.datetime_utils import convert_utc_to_egypt, format_datetime, format_datetime_12h

def register_template_filters(app):
    """
    تسجيل الدوال المساعدة للقوالب
    """
    
    @app.template_filter('egypt_time')
    def egypt_time_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرضه بنظام 12 ساعة
        """
        if dt is None:
            return ""
        return format_datetime_12h(dt, include_date=True, include_seconds=False)
    
    @app.template_filter('egypt_time_24h')
    def egypt_time_24h_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرضه بنظام 24 ساعة (للاستخدام الداخلي)
        """
        if dt is None:
            return ""
        egypt_dt = convert_utc_to_egypt(dt)
        return format_datetime(egypt_dt, '%Y-%m-%d %H:%M:%S')
    
    @app.template_filter('egypt_date')
    def egypt_date_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرض التاريخ فقط
        """
        if dt is None:
            return ""
        egypt_dt = convert_utc_to_egypt(dt)
        return format_datetime(egypt_dt, '%Y-%m-%d')
    
    @app.template_filter('egypt_time_only')
    def egypt_time_only_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرض الوقت فقط بنظام 12 ساعة
        """
        if dt is None:
            return ""
        return format_datetime_12h(dt, include_date=False, include_seconds=False)
    
    @app.template_filter('egypt_time_with_seconds')
    def egypt_time_with_seconds_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرضه بنظام 12 ساعة مع الثواني
        """
        if dt is None:
            return ""
        return format_datetime_12h(dt, include_date=True, include_seconds=True)
    
    @app.template_filter('egypt_time_only_with_seconds')
    def egypt_time_only_with_seconds_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرض الوقت فقط بنظام 12 ساعة مع الثواني
        """
        if dt is None:
            return ""
        return format_datetime_12h(dt, include_date=False, include_seconds=True)
    
    @app.template_filter('egypt_datetime_short')
    def egypt_datetime_short_filter(dt):
        """
        تحويل التاريخ من UTC إلى توقيت مصر وعرضه بتنسيق مختصر (للجداول)
        """
        if dt is None:
            return ""
        return format_datetime_12h(dt, include_date=True, include_seconds=False)

    @app.template_filter('strftime')
    def strftime_filter(dt, fmt='%Y-%m-%d %H:%M:%S'):
        """
        تنسيق التاريخ باستخدام strftime كفلتر Jinja2 للتوافق مع القوالب القديمة
        """
        if dt is None:
            return ""
        try:
            return dt.strftime(fmt)
        except Exception:
            return ""
    
    @app.template_filter('dash')
    def dash_filter(value):
        """إرجاع '-' عند القيم الفارغة/None وإلا إرجاع القيمة كما هي"""
        try:
            if value is None:
                return '-'
            if isinstance(value, str):
                return value.strip() if value.strip() else '-'
            return value
        except Exception:
            return '-'
    
    @app.template_filter('arabic_day_name')
    def arabic_day_name_filter(date_obj):
        """
        الحصول على اسم اليوم بالعربية من كائن التاريخ
        """
        if date_obj is None:
            return ""
        
        try:
            from hotel.utils.arabic_date import get_arabic_day
            
            # إذا كان datetime، نأخذ التاريخ فقط
            if hasattr(date_obj, 'date'):
                date_obj = date_obj.date()
            
            # الحصول على رقم اليوم (0=الاثنين، 6=الأحد)
            day_num = date_obj.weekday()
            return get_arabic_day(day_num)
        except Exception:
            return ""
    
    @app.template_filter('date_with_day')
    def date_with_day_filter(date_obj):
        """
        عرض التاريخ مع اسم اليوم بالعربية
        مثال: السبت 31/12
        """
        if date_obj is None:
            return ""
        
        try:
            from hotel.utils.arabic_date import get_arabic_day
            
            # إذا كان datetime، نأخذ التاريخ فقط
            if hasattr(date_obj, 'date'):
                date_obj = date_obj.date()
            
            # الحصول على اسم اليوم
            day_num = date_obj.weekday()
            day_name = get_arabic_day(day_num)
            
            # تنسيق التاريخ
            date_str = date_obj.strftime('%d/%m')
            
            return f"{day_name} {date_str}"
        except Exception:
            return ""
    
    @app.template_filter('booking_number_only')
    def booking_number_only_filter(booking_code):
        """
        استخراج رقم الحجز فقط من booking_code
        مثال: من "2025/55" يرجع "55"
        """
        if not booking_code:
            return ""
        
        try:
            booking_code_str = str(booking_code)
            # إذا كان يحتوي على "/" نأخذ الجزء الثاني (الرقم)
            if '/' in booking_code_str:
                return booking_code_str.split('/')[-1]
            # إذا لم يحتوي على "/" نرجع الرقم كما هو
            return booking_code_str
        except Exception:
            return str(booking_code) if booking_code else ""
