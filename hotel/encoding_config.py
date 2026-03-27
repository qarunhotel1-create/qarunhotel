# -*- coding: utf-8 -*-
"""
تكوين الترميز للتطبيق
"""

# تكوين الترميز الافتراضي
DEFAULT_ENCODING = 'utf-8'

# تكوين ترميز الملفات
FILE_ENCODING = 'utf-8'

# تكوين ترميز قاعدة البيانات
DATABASE_ENCODING = 'utf-8'

# دالة لتنظيف اسم الملف
def clean_filename(filename):
    """تنظيف اسم الملف من الأحرف غير المدعومة"""
    import re
    import unicodedata
    
    # إزالة الأحرف غير المرئية والتحكم
    filename = ''.join(char for char in filename if unicodedata.category(char)[0] != 'C')
    
    # تنظيف شامل لاسم الملف
    clean_name = filename.strip()
    
    # استبدال جميع الأحرف الخاصة والمسافات
    clean_name = re.sub(r'[^\w\-_.]', '_', clean_name)
    
    # تقليل الشرطات السفلية المتعددة
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # إزالة الشرطات من البداية والنهاية
    clean_name = clean_name.strip('_')
    
    # التأكد من وجود اسم ملف صالح
    if not clean_name or clean_name == '':
        clean_name = 'document'
    
    return clean_name

# دالة لإصلاح ترميز البيانات المشفرة
def fix_base64_encoding(encoded_data):
    """إصلاح ترميز البيانات المشفرة بـ base64"""
    import base64
    
    # استبدال المسافات بعلامات +
    encoded_data = encoded_data.replace(' ', '+')
    
    # استبدال الأحرف غير الصالحة
    encoded_data = encoded_data.replace('\n', '').replace('\r', '')
    
    # محاولة فك التشفير
    try:
        decoded_data = base64.b64decode(encoded_data)
        return decoded_data
    except Exception as e:
        # إذا فشل فك التشفير، نعيد None
        return None

# دالة للتحقق من صحة اسم الملف
def validate_filename(filename):
    """التحقق من صحة اسم الملف"""
    import os
    
    # التحقق من وجود اسم ملف
    if not filename or filename.strip() == '':
        return False
    
    # التحقق من عدم وجود أحرف غير مسموح بها
    invalid_chars = '<>:"\\/|?*'
    if any(char in invalid_chars for char in filename):
        return False
    
    # التحقق من عدم وجود أسماء محجوزة
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                      'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                      'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True