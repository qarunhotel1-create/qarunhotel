from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# تحديد المنطقة الزمنية لمصر بشكل صحيح مع دعم التوقيت الصيفي
EGYPT_TIMEZONE = ZoneInfo("Africa/Cairo")

def get_egypt_now():
    """
    الحصول على الوقت الحالي بتوقيت مصر (مع دعم التوقيت الصيفي)
    """
    return datetime.now(EGYPT_TIMEZONE)

def get_egypt_now_naive():
    """
    الحصول على الوقت الحالي بتوقيت مصر بدون معلومات المنطقة الزمنية
    مفيد للتخزين في قاعدة البيانات كوقت محلي
    """
    now = get_egypt_now()
    return now.replace(tzinfo=None)

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    تنسيق التاريخ والوقت بالصيغة المطلوبة
    """
    if dt is None:
        return ""
    if hasattr(dt, 'strftime'):
        return dt.strftime(format_str)
    return ""

def format_datetime_12h(dt, include_date=True, include_seconds=False):
    """
    تنسيق التاريخ والوقت بنظام 12 ساعة مع صباحاً/مساءً
    """
    if dt is None:
        return ""
    
    # التأكد من أن التاريخ بتوقيت مصر
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        dt = convert_utc_to_egypt(dt)
    elif hasattr(dt, 'hour'):  # datetime object
        # إذا كان naive datetime، نفترض أنه بتوقيت مصر بالفعل
        pass
    else:
        return ""
    
    if not hasattr(dt, 'hour'):
        # إذا كان date فقط
        if include_date:
            return dt.strftime('%Y-%m-%d')
        return ""
    
    # تحويل إلى نظام 12 ساعة
    hour = dt.hour
    period = "مساءً" if hour >= 12 else "صباحاً"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12
    
    # تنسيق الوقت
    if include_seconds:
        time_str = f"{hour_12}:{dt.minute:02d}:{dt.second:02d} {period}"
    else:
        time_str = f"{hour_12}:{dt.minute:02d} {period}"
    
    # إضافة التاريخ إذا كان مطلوباً
    if include_date:
        date_str = dt.strftime('%Y-%m-%d')
        return f"{date_str} {time_str}"
    else:
        return time_str

def convert_utc_to_egypt(utc_dt):
    """
    تحويل التوقيت من UTC إلى توقيت مصر مع دعم التوقيت الصيفي

    المبدأ:
    - إذا كانت القيمة تحتوي على tzinfo: نحولها مباشرة إلى Africa/Cairo
    - إذا كانت القيمة بدون tzinfo: نفترض أنها UTC ثم نحولها إلى Africa/Cairo
    - إذا كانت Date فقط: نحول منتصف الليل UTC إلى تاريخ مصر المقابل
    """
    if utc_dt is None:
        return None

    # إذا كان DateTime
    if hasattr(utc_dt, 'hour'):
        # tz-aware → حوّل مباشرة
        if getattr(utc_dt, 'tzinfo', None) is not None:
            return utc_dt.astimezone(EGYPT_TIMEZONE)
        # naive → اعتبره UTC ثم حوّل إلى مصر
        return utc_dt.replace(tzinfo=timezone.utc).astimezone(EGYPT_TIMEZONE)

    # إذا كان Date فقط
    dt = datetime(utc_dt.year, utc_dt.month, utc_dt.day, 0, 0, 0, tzinfo=timezone.utc)
    return dt.astimezone(EGYPT_TIMEZONE).date()

def egypt_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    فلتر لتنسيق التاريخ والوقت بتوقيت مصر
    """
    if dt is None:
        return ""

    # إذا كان tz-aware حوّله أولًا
    if getattr(dt, 'tzinfo', None) is not None:
        dt = convert_utc_to_egypt(dt)

    if hasattr(dt, 'strftime'):
        return dt.strftime(format_str)
    return ""